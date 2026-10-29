"""Daily Meta Pixel health check.

Born from a real failure: the pixel plugin's init function ran before the
Facebook base code (`fbq`) existed, so `fbq('init')` never fired and almost no
PageViews were recorded, even though ads were sending plenty of traffic. The
fix was a small footer snippet that waits for `fbq`, then calls the plugin's
init. This script makes sure that fix keeps working.

Two checks:
  1. The pixel actually initialises on the live landing pages, tested in a real
     headless browser. This catches the fix being deactivated, a cache or
     consent-plugin change, or a plugin update breaking it. Page *source* is
     the wrong thing to test: a caching/optimisation layer can deliver the
     script in a delayed form that is absent from the HTML, so only the state
     of the rendered page is a reliable signal.
  2. The pixel is receiving PageViews. Alerts only when the count stays under
     MIN_PAGEVIEWS for two consecutive full days. A single low day is noted but
     not alerted (weekends are naturally quieter).

Browser checks can false-alarm (cache lag). If an alert doesn't clear on a
re-run a few minutes later, treat it as real.

Appends one row per run to a CSV log and writes PIXEL_ALERT.txt when something
is wrong (deleted again on a clean run). Exit code 2 on alert.

Requires: pip install requests python-dotenv playwright && playwright install chromium
Configuration: .env (META_ACCESS_TOKEN, META_PIXEL_ID) and site_config.json.
"""
import csv
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT, ".env"))

PIXEL_ID = os.getenv("META_PIXEL_ID")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
MIN_PAGEVIEWS = int(os.getenv("PIXEL_MIN_PAGEVIEWS", 5))
GRAPH = "https://graph.facebook.com/v21.0"
LOG_FILE = os.path.join(ROOT, "pixel_health_log.csv")
ALERT_FILE = os.path.join(ROOT, "PIXEL_ALERT.txt")

# True once the pixel base code has loaded AND init has run for at least one pixel.
# Adjust the first clause if your setup does not use the WordPress plugin's helper.
INIT_CHECK_JS = ("() => !!(window.fbq && window.fbq.getState && "
                 "Object.keys(window.fbq.getState().pixels || {}).length)")


def landing_pages():
    with open(os.path.join(ROOT, "site_config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    base = cfg["base_url"].rstrip("/")
    return [base + p["path"] for p in cfg["pages"] if p.get("needs_tracking_tag")]


def pixel_not_initialised(pages):
    """Load each page in a real browser; return the pages where the pixel did not start."""
    from playwright.sync_api import sync_playwright
    failed = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for url in pages:
                page = browser.new_context(viewport={"width": 1280, "height": 800}).new_page()
                try:
                    page.goto(f"{url}?utm_source=meta&fbclid=IwAR_pixel_health_check",
                              wait_until="load", timeout=45000)
                    page.wait_for_timeout(9000)  # give consent + deferred scripts time to run
                    if not page.evaluate(INIT_CHECK_JS):
                        failed.append(url)
                except Exception as e:
                    failed.append(f"{url} (page check failed: {str(e)[:60]})")
                finally:
                    page.context.close()
            browser.close()
    except Exception as e:
        failed.append(f"browser check could not run: {str(e)[:80]}")
    return failed


def daily_counts():
    now = int(time.time())
    resp = requests.get(
        f"{GRAPH}/{PIXEL_ID}/stats",
        params={"access_token": ACCESS_TOKEN, "aggregation": "event",
                "start_time": now - 4 * 86400, "end_time": now},
        timeout=60,
    )
    resp.raise_for_status()
    counts = defaultdict(lambda: {"PageView": 0, "Lead": 0})
    for bucket in resp.json().get("data", []):
        day = bucket["start_time"][:10]
        for item in bucket.get("data", []):
            if item["value"] in ("PageView", "Lead"):
                counts[day][item["value"]] += item["count"]
    return counts


def main():
    today = datetime.now(timezone.utc).date()
    counts = daily_counts()
    d1, d2 = (today - timedelta(days=1)).isoformat(), (today - timedelta(days=2)).isoformat()
    pv1, pv2 = counts[d1]["PageView"], counts[d2]["PageView"]
    missing = pixel_not_initialised(landing_pages())

    problems, notes = [], []
    if missing:
        problems.append("Pixel did NOT initialise on: " + "; ".join(missing)
                        + ". Check the footer snippet is active and purge page caches.")
    if pv1 < MIN_PAGEVIEWS and pv2 < MIN_PAGEVIEWS:
        problems.append(f"PageViews under {MIN_PAGEVIEWS}/day two days running "
                        f"({d2}: {pv2}, {d1}: {pv1}). A plugin update may have broken the init; "
                        "re-test in a private window with the Meta Pixel Helper.")
    if pv1 < MIN_PAGEVIEWS <= pv2:
        notes.append(f"{d1} was low ({pv1} PageViews); watching, no alert yet.")

    new_log = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_log:
            w.writerow(["run_utc", "date", "pageviews", "leads", "pages_without_pixel"])
        for d in (d2, d1):
            w.writerow([datetime.now(timezone.utc).isoformat(), d,
                        counts[d]["PageView"], counts[d]["Lead"], len(missing)])

    print(f"{d2}: {pv2} PageViews | {d1}: {pv1} PageViews | pixel missing on {len(missing)} page(s)")
    for n in notes:
        print("NOTE:", n)

    if problems:
        text = "META PIXEL ALERT (" + today.isoformat() + ")\n" + "\n".join("- " + p for p in problems) + "\n"
        with open(ALERT_FILE, "w", encoding="utf-8") as f:
            f.write(text)
        print(">>> ALERT:\n" + text)
        return 2
    if os.path.exists(ALERT_FILE):
        os.remove(ALERT_FILE)
    print("Pixel health OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
