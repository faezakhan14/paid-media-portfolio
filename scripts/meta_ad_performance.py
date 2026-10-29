"""Per-ad Meta performance report using the EXACT lead event.

The bug this script is built around: summing every action type whose name
contains "lead" counts one real lead about seven times, because a single
submission fires several related action types (onsite, offsite pixel, grouped
and custom variants). Two monitoring scripts quietly reported leads, and cost
per lead, wildly out of line with the CRM for weeks before it was caught.

The fix is one line: match the action type exactly (`lead`). The habit is
bigger: always cross-check platform-reported leads against the CRM before
drawing a conclusion, and read ad results only after equal delivery.

Output is one row per ad: spend, impressions, link clicks, CTR, leads and cost
per lead, sorted by spend. Read-only.

Usage:
    python meta_ad_performance.py                # last 14 days
    python meta_ad_performance.py --days 30
"""
import argparse
import os

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT, ".env"))

GRAPH = "https://graph.facebook.com/v21.0"
TOKEN = os.getenv("META_ACCESS_TOKEN")
ACCOUNT = os.getenv("META_AD_ACCOUNT_ID")  # e.g. act_1234567890

LEAD_ACTION = "lead"  # exact match. NOT `"lead" in action_type`: that is the overcount bug.


def action_value(actions, action_type):
    for a in actions or []:
        if a.get("action_type") == action_type:
            return float(a["value"])
    return 0.0


def fetch(days):
    params = {
        "access_token": TOKEN,
        "level": "ad",
        "fields": "campaign_name,adset_name,ad_name,spend,impressions,inline_link_clicks,actions",
        "date_preset": "last_30d" if days > 14 else "last_14d",
        "limit": 200,
    }
    url, rows = f"{GRAPH}/{ACCOUNT}/insights", []
    while url:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        rows.extend(data.get("data", []))
        url, params = data.get("paging", {}).get("next"), None  # next URL already carries the params
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14, help="14 or 30 (Meta date presets)")
    args = parser.parse_args()

    rows = fetch(args.days)
    print(f"{'Spend':>9} {'Impr':>8} {'Clicks':>7} {'CTR':>6} {'Leads':>6} {'CPL':>9}  Ad  [Ad set]")
    for r in sorted(rows, key=lambda x: -float(x.get("spend", 0))):
        spend = float(r.get("spend", 0))
        impr = int(r.get("impressions", 0))
        clicks = int(r.get("inline_link_clicks", 0))
        leads = action_value(r.get("actions"), LEAD_ACTION)
        ctr = clicks / impr * 100 if impr else 0
        cpl = f"{spend / leads:9.2f}" if leads else "        -"
        print(f"{spend:9.2f} {impr:8d} {clicks:7d} {ctr:5.1f}% {leads:6.0f} {cpl}  "
              f"{r.get('ad_name', '')[:40]}  [{r.get('adset_name', '')[:30]}]")
    print("\nReminder: these are platform-reported leads. Cross-check against the CRM before acting.")


if __name__ == "__main__":
    main()
