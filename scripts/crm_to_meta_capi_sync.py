"""Send CRM pipeline progress back to Meta as a staged funnel.

Problem: a lead-gen pixel only ever reports one flat "Lead" event, so Meta
optimises for form fills, including the poor ones. This script reads the CRM
(GoHighLevel here) and reports each qualifying stage change to Meta's
Conversions API as it happens:

    Lead -> Qualified -> EstimateSent -> Purchase

so the algorithm gets a signal about which leads were actually good.

Design points worth copying:
  - Only opportunities whose CRM source says Meta/Facebook/Instagram are sent.
  - State (highest funnel rank already sent per opportunity) is kept in a JSON
    file, so re-runs only send new stage advances and never duplicate.
  - A deterministic event_id per opportunity+rank lets Meta de-duplicate too.
  - Email, phone and CRM contact ID are SHA-256 hashed after normalising.
  - Meta rejects events older than 7 days. Anything older can never be sent, so
    it is marked as synced rather than retried forever.
  - Dry run by default. --live sends; --test-code routes through Meta's Test
    Events tool so you can verify before real delivery.

Usage:
    python crm_to_meta_capi_sync.py                     # dry run, prints what would be sent
    python crm_to_meta_capi_sync.py --live --test-code TEST12345
    python crm_to_meta_capi_sync.py --live

Configuration: .env (GHL_API_KEY, GHL_LOCATION_ID, META_ACCESS_TOKEN, META_PIXEL_ID,
GHL_PIPELINE_ID) and capi_stage_map.json (copy capi_stage_map.example.json).
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")
GHL_PIPELINE_ID = os.getenv("GHL_PIPELINE_ID")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
META_PIXEL_ID = os.getenv("META_PIXEL_ID")
CURRENCY = os.getenv("CAPI_CURRENCY", "CAD")

STATE_FILE = HERE / "capi_sync_state.json"
MAX_EVENT_AGE = timedelta(days=6, hours=12)  # Meta CAPI rejects events older than 7 days

GHL_HEADERS = {"Authorization": f"Bearer {GHL_API_KEY}", "Version": "2021-07-28", "Accept": "application/json"}
RANK_EVENT = {1: "Lead", 2: "Qualified", 3: "EstimateSent", 4: "Purchase"}


def load_stage_rank():
    """Map of CRM stage ID -> funnel rank (1-4). Kept out of the code so it is easy to edit."""
    data = json.loads((HERE / "capi_stage_map.json").read_text())
    return {stage_id: rank for stage_id, rank in data.items() if not stage_id.startswith("_")}


def is_meta_source(source):
    s = (source or "").lower()
    return "meta" in s or "facebook" in s or s == "instagram"


def fetch_meta_opportunities():
    all_opps, start_after, start_after_id = [], None, None
    while True:
        params = {"location_id": GHL_LOCATION_ID, "pipeline_id": GHL_PIPELINE_ID, "limit": 100}
        if start_after:
            params.update({"startAfter": start_after, "startAfterId": start_after_id})
        resp = requests.get("https://services.leadconnectorhq.com/opportunities/search",
                            headers=GHL_HEADERS, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("opportunities", [])
        all_opps.extend(batch)
        meta = data.get("meta", {})
        if not meta.get("nextPage") or not batch or len(all_opps) >= meta.get("total", 0):
            break
        start_after, start_after_id = meta.get("startAfter"), meta.get("startAfterId")
    return [o for o in all_opps if is_meta_source(o.get("source"))]


def sha256_hash(value):
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest() if value else None


def normalize_phone(phone):
    return "".join(c for c in phone if c.isdigit() or c == "+") if phone else None


def to_unix(iso_string):
    if not iso_string:
        return int(datetime.now(timezone.utc).timestamp())
    return int(datetime.fromisoformat(iso_string.replace("Z", "+00:00")).timestamp())


def load_state():
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def build_events(opportunities, state, stage_rank):
    events, updates, skipped_too_old = [], {}, 0
    cutoff = datetime.now(timezone.utc) - MAX_EVENT_AGE
    for o in opportunities:
        opp_id = o["id"]
        current_rank = stage_rank.get(o.get("pipelineStageId"))
        last_rank = state.get(opp_id, 0)
        if current_rank is None or current_rank <= last_rank:
            continue

        contact = o.get("contact") or {}
        event_time = to_unix(o.get("lastStageChangeAt") or o.get("updatedAt"))
        if datetime.fromtimestamp(event_time, tz=timezone.utc) < cutoff:
            skipped_too_old += 1
            updates[opp_id] = current_rank
            continue

        user_data = {}
        if sha256_hash(contact.get("email")):
            user_data["em"] = [sha256_hash(contact["email"])]
        if sha256_hash(normalize_phone(contact.get("phone"))):
            user_data["ph"] = [sha256_hash(normalize_phone(contact["phone"]))]
        if o.get("contactId"):
            user_data["external_id"] = [sha256_hash(o["contactId"])]

        # If a lead jumped several stages between runs, send every step it passed.
        for rank in range(last_rank + 1, current_rank + 1):
            event = {
                "event_name": RANK_EVENT[rank],
                "event_time": event_time,
                "event_id": f"crm-{opp_id}-{rank}",  # stable ID so Meta can de-duplicate
                "action_source": "system_generated",
                "user_data": user_data,
            }
            if RANK_EVENT[rank] == "Purchase":
                event["custom_data"] = {"currency": CURRENCY, "value": o.get("monetaryValue") or 0}
            events.append(event)
        updates[opp_id] = current_rank
    return events, updates, skipped_too_old


def send_events(events, live, test_code):
    url = f"https://graph.facebook.com/v21.0/{META_PIXEL_ID}/events"
    payload = {"data": events, "access_token": META_ACCESS_TOKEN}
    if test_code:
        payload["test_event_code"] = test_code
    if not live:
        print(f"[DRY RUN] Would POST {len(events)} events to Meta")
        return
    resp = requests.post(url, json=payload, timeout=60)
    print(f"POST -> {resp.status_code}")
    print(resp.text)
    resp.raise_for_status()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="actually send events to Meta")
    parser.add_argument("--test-code", default=None, help="route through Meta's Test Events tool")
    args = parser.parse_args()

    opportunities = fetch_meta_opportunities()
    print(f"Meta-sourced opportunities found: {len(opportunities)}")

    state = load_state()
    events, updates, skipped = build_events(opportunities, state, load_stage_rank())
    if skipped:
        print(f"Skipped {skipped}: stage change older than Meta's 7-day window (marked as synced).")
    if not events:
        print("No new stage advances to sync.")
        if updates and args.live:
            state.update(updates)
            save_state(state)
        return

    print(f"\n{len(events)} new event(s):")
    for e in events:
        print(f"  {e['event_name']:<12} {e['event_id']}")
    send_events(events, args.live, args.test_code)

    if args.live:
        state.update(updates)
        save_state(state)
        print(f"\nState saved for {len(updates)} opportunity(ies).")
    else:
        print("\nDry run: state not saved. Re-run with --live to send and persist.")


if __name__ == "__main__":
    main()
