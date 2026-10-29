"""Audit negative keywords and look for new wasted search-term spend.

Prints, for every enabled campaign:
  1. the existing negative keywords (campaign level and ad group level)
  2. search terms from the last N days that cost money and did not convert,
     bucketed by *why* they are probably irrelevant, so the next batch of
     negatives is a reviewed list, not guesswork.

The buckets are the categories that most often leak budget on a local
high-ticket service account:
  government/regulatory seekers, research and how-to, wrong location,
  competitors, wrong service, renting/jobs/DIY materials, price-only shoppers.

IMPORTANT, the review step this script supports: before adding any negative,
check whether any search term containing that word ever converted. In one
account, whole groups of "obviously junk" terms (cost, drawings, ceiling) were
pulled from a proposal because they saved almost nothing and at least one had
produced a real lead. A negative is a permanent decision; the check is cheap.

This script is read-only. It never changes the account.

Configuration: .env for credentials; negative_buckets.json for the word lists
(copy negative_buckets.example.json and fill in your own).
"""
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient

ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT, ".env"))

LOOKBACK_DAYS = int(os.getenv("NEG_LOOKBACK_DAYS", 30))
MIN_COST = float(os.getenv("NEG_MIN_COST", 3))


def build_client():
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
        "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
        "use_proto_plus": True,
    })


def load_buckets():
    path = os.path.join(ROOT, "negative_buckets.json")
    with open(path, encoding="utf-8") as f:
        return {k: [w.lower() for w in v] for k, v in json.load(f).items() if not k.startswith("_")}


def main():
    client = build_client()
    cid = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    ga = client.get_service("GoogleAdsService")
    buckets = load_buckets()

    print("=== EXISTING NEGATIVES (campaign level) ===")
    by_campaign = defaultdict(list)
    sql = ("SELECT campaign.name, campaign_criterion.keyword.text, campaign_criterion.keyword.match_type "
           "FROM campaign_criterion WHERE campaign_criterion.negative = TRUE "
           "AND campaign_criterion.type = 'KEYWORD' AND campaign.status = 'ENABLED'")
    for r in ga.search(customer_id=cid, query=sql):
        by_campaign[r.campaign.name].append(
            f"{r.campaign_criterion.keyword.text} ({r.campaign_criterion.keyword.match_type.name})")
    for camp, negs in by_campaign.items():
        print(f"[{camp}] {len(negs)} negatives")
        for n in sorted(negs):
            print(f"  - {n}")

    print("\n=== EXISTING NEGATIVES (ad group level) ===")
    sql = ("SELECT campaign.name, ad_group.name, ad_group_criterion.keyword.text, "
           "ad_group_criterion.keyword.match_type FROM ad_group_criterion "
           "WHERE ad_group_criterion.negative = TRUE AND ad_group_criterion.type = 'KEYWORD' "
           "AND campaign.status = 'ENABLED'")
    found = False
    for r in ga.search(customer_id=cid, query=sql):
        found = True
        print(f"[{r.campaign.name} / {r.ad_group.name}] {r.ad_group_criterion.keyword.text} "
              f"({r.ad_group_criterion.keyword.match_type.name})")
    if not found:
        print("(none)")

    start = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).date()
    end = datetime.now(timezone.utc).date()
    print(f"\n=== SEARCH TERMS THAT COST >= {MIN_COST:.0f} WITH NO CONVERSION ({start} to {end}) ===")
    sql = ("SELECT campaign.name, search_term_view.search_term, metrics.clicks, "
           "metrics.cost_micros, metrics.conversions FROM search_term_view "
           f"WHERE segments.date BETWEEN '{start}' AND '{end}' AND campaign.status = 'ENABLED'")
    converted_words, candidates = set(), []
    for r in ga.search(customer_id=cid, query=sql):
        term = r.search_term_view.search_term.lower()
        cost = r.metrics.cost_micros / 1e6
        if r.metrics.conversions > 0:
            converted_words.update(term.split())
        elif cost >= MIN_COST:
            candidates.append((r.campaign.name, term, r.metrics.clicks, cost))

    grouped = defaultdict(list)
    for camp, term, clicks, cost in candidates:
        bucket = next((name for name, words in buckets.items() if any(w in term for w in words)), "UNSORTED: read these by hand")
        grouped[bucket].append((camp, term, clicks, cost))

    for bucket, rows in sorted(grouped.items()):
        print(f"\n-- {bucket} ({len(rows)} terms, {sum(r[3] for r in rows):.2f} spent)")
        for camp, term, clicks, cost in sorted(rows, key=lambda x: -x[3]):
            warn = "  <-- a converting term shares a word with this; check before blocking" \
                if set(term.split()) & converted_words - {"in", "the", "a", "near", "me", "for", "and"} else ""
            print(f"  {cost:7.2f}  {clicks:>3} clicks  {term}  [{camp[:24]}]{warn}")


if __name__ == "__main__":
    main()
