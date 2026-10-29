"""Daily Google Ads "leakage" check.

Looks at the last three days of search terms and keywords and flags the patterns
that quietly waste budget on a lead-gen account:

  - EXPENSIVE TERM   one search term cost at least EXPENSIVE_TERM with no conversion
  - CONCENTRATION    one keyword took more than CONCENTRATION_SHARE of a day's spend
                     (typical cause: a broad-match keyword that drifted)
  - WATCHLIST        any spend on a competitor name or out-of-area place. These
                     should already be negative keywords, so a hit means a gap.
  - SPEND SPIKE      a day over DAY_SPIKE
  - CPC CAP          average CPC above CPC_CAP (a bid-strategy ceiling that
                     isn't holding)

Every flag is appended to a CSV log (de-duplicated) so you can review patterns
later, and an alert file is written when something new is flagged. The alert
file is removed again on a clean run. Exit code 2 on flags, so a scheduler
wrapper can raise a desktop notification or email.

Note: Google hides low-volume queries from the search terms report, so keyword
level spend can be higher than the sum of the listed terms. That gap is printed
as "unreported terms".

Setup: copy .env.example to .env, fill it in, copy watchlist.example.txt to
watchlist.txt and add your own competitor names and out-of-area towns.
"""
import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient

ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT, ".env"))

# Thresholds: tune these to the account's daily budget and typical CPC.
EXPENSIVE_TERM = float(os.getenv("LEAK_EXPENSIVE_TERM", 12))
CONCENTRATION_SHARE = float(os.getenv("LEAK_CONCENTRATION_SHARE", 0.5))
CONCENTRATION_MIN_DAY = float(os.getenv("LEAK_CONCENTRATION_MIN_DAY", 30))
DAY_SPIKE = float(os.getenv("LEAK_DAY_SPIKE", 180))
CPC_CAP = float(os.getenv("LEAK_CPC_CAP", 12))

LOG_FILE = os.path.join(ROOT, "google_leakage_log.csv")
ALERT_FILE = os.path.join(ROOT, "GOOGLE_LEAKAGE_ALERT.txt")


def load_watchlist():
    path = os.path.join(ROOT, "watchlist.txt")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]


def build_client():
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
        "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
        "use_proto_plus": True,
    })


def main():
    client = build_client()
    cid = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    ga = client.get_service("GoogleAdsService")
    watchlist = load_watchlist()

    def q(sql):
        return ga.search(customer_id=cid, query=sql)

    # LAST_7_DAYS excludes the current day, so use explicit bounds with a day of
    # margin either side to cover the account's time zone.
    now_utc = datetime.now(timezone.utc)
    window = (f"segments.date BETWEEN '{(now_utc - timedelta(days=8)).date()}' "
              f"AND '{(now_utc + timedelta(days=1)).date()}'")

    days, clicks_by_day = defaultdict(float), defaultdict(int)
    for r in q(f"SELECT segments.date, metrics.cost_micros, metrics.clicks FROM customer WHERE {window}"):
        days[r.segments.date] += r.metrics.cost_micros / 1e6
        clicks_by_day[r.segments.date] += r.metrics.clicks
    recent = sorted(days)[-3:]

    flags = []  # (date, kind, subject, campaign, ad_group, clicks, cost, detail)
    for d in recent:
        total = days[d]
        if total > DAY_SPIKE:
            flags.append((d, "SPEND SPIKE", "account", "", "", clicks_by_day[d], total,
                          f"{total:.2f} in one day (threshold {DAY_SPIKE:.0f})"))
        if clicks_by_day[d] and total / clicks_by_day[d] > CPC_CAP:
            flags.append((d, "CPC CAP", "account", "", "", clicks_by_day[d], total,
                          f"avg CPC {total / clicks_by_day[d]:.2f} exceeds the {CPC_CAP:.0f} cap"))

    listed_by_day = defaultdict(float)
    terms_sql = ("SELECT segments.date, search_term_view.search_term, campaign.name, ad_group.name, "
                 "metrics.clicks, metrics.cost_micros, metrics.conversions "
                 f"FROM search_term_view WHERE {window} AND metrics.cost_micros > 0")
    for r in q(terms_sql):
        d = r.segments.date
        if d not in recent:
            continue
        term = r.search_term_view.search_term
        cost, clicks = r.metrics.cost_micros / 1e6, r.metrics.clicks
        listed_by_day[d] += cost
        camp, ag = r.campaign.name[:24], r.ad_group.name[:34]
        if cost >= EXPENSIVE_TERM and r.metrics.conversions == 0:
            flags.append((d, "EXPENSIVE TERM", term, camp, ag, clicks, cost, f"{cost:.2f}, no conversion"))
        hit = next((w for w in watchlist if w in term.lower()), None)
        if hit:
            flags.append((d, "WATCHLIST", term, camp, ag, clicks, cost, f"matches '{hit}' (should be blocked)"))

    kw_sql = ("SELECT segments.date, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, "
              "campaign.name, ad_group.name, metrics.clicks, metrics.cost_micros "
              f"FROM keyword_view WHERE {window} AND metrics.cost_micros > 0")
    for r in q(kw_sql):
        d = r.segments.date
        if d not in recent:
            continue
        cost = r.metrics.cost_micros / 1e6
        if days[d] > CONCENTRATION_MIN_DAY and cost / days[d] > CONCENTRATION_SHARE:
            k = r.ad_group_criterion.keyword
            flags.append((d, "CONCENTRATION", f"{k.text} [{k.match_type.name}]", r.campaign.name[:24],
                          r.ad_group.name[:34], r.metrics.clicks, cost,
                          f"{cost / days[d] * 100:.0f}% of the day's {days[d]:.2f}"))

    # De-duplicate against earlier runs so the same flag doesn't alert every day.
    now = now_utc.isoformat()
    seen = set()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, newline="", encoding="utf-8") as f:
            seen = {(row["date"], row["kind"], row["subject"], row["cost"]) for row in csv.DictReader(f)}
    new_rows = [f for f in flags if (f[0], f[1], f[2], f"{f[6]:.2f}") not in seen]
    write_header = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["run_utc", "date", "kind", "subject", "campaign", "ad_group", "clicks", "cost", "detail"])
        for d, kind, subject, camp, ag, clicks, cost, detail in new_rows:
            w.writerow([now, d, kind, subject, camp, ag, clicks, f"{cost:.2f}", detail])

    print("Daily spend: " + " | ".join(f"{d}: {days[d]:.2f}" for d in recent))
    for d in recent:
        gap = days[d] - listed_by_day[d]
        share = gap / days[d] * 100 if days[d] else 0
        print(f"  {d}: {share:.0f}% of spend ({gap:.2f}) is in terms Google doesn't list individually")

    if not flags:
        if os.path.exists(ALERT_FILE):
            os.remove(ALERT_FILE)
        print("No leakage flags.")
        return 0
    if not new_rows:
        print(f"{len(flags)} flag(s) in the window, all already logged earlier; no new alert.")
        return 0

    text = "GOOGLE ADS LEAKAGE FLAGS (" + now[:10] + ")\n" + "\n".join(
        f"- {d} {kind}: {subject} [{camp} / {ag}] {detail}"
        for d, kind, subject, camp, ag, clicks, cost, detail in new_rows) + "\n"
    with open(ALERT_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
