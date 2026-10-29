"""Daily landing-page availability check that a page cache cannot fool.

Why this exists: a CMS core/plugin auto-update once crashed a WordPress site.
The page cache kept serving saved copies of the plain URLs, so a logged-out
check of the normal address looked healthy. But every real ad click carries a
click-ID parameter (?gclid=, ?fbclid=), which bypasses the cache, and those
visitors (plus the admin area) got a fatal error. Nothing noticed for about a
day while the ads kept paying for clicks.

So this check never requests a plain cached URL:
  - every request carries a unique ?gclid= value, forcing the server to render
    the page for real
  - the login page is always included, because it is never cached and loads
    every plugin, which makes it the best "crash canary"

Flags (per URL, after a retry):
  - HTTP status other than 200
  - the body contains the CMS's fatal-error text
  - landing pages: the tag manager container snippet is missing (tracking gone)
  - timeout or connection failure

Writes SITE_ALERT.txt when something is flagged (removed on a clean run) and
appends every run to a CSV log. Exit code 2 on flags so a scheduler wrapper can
notify you.

Configuration is read from site_config.json (copy site_config.example.json).
"""
import csv
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
ALERT_FILE = os.path.join(ROOT, "SITE_ALERT.txt")
LOG_FILE = os.path.join(ROOT, "site_availability_log.csv")

TIMEOUT = 25
ATTEMPTS = 2
RETRY_WAIT = 10
FATAL_TEXT = "critical error on this website"  # WordPress fatal-error page
# Check as a mobile visitor, since that is most ad traffic.
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")


def load_config():
    path = os.path.join(ROOT, "site_config.json")
    if not os.path.exists(path):
        sys.exit("Copy site_config.example.json to site_config.json and fill it in.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def bust(url):
    """Append a unique click-ID so no cache layer can answer the request."""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}gclid=avail{int(time.time())}{random.randint(1000, 9999)}"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, body
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def check(url, need_gtm, gtm_id):
    problem, status, size = "", None, 0
    for attempt in range(1, ATTEMPTS + 1):
        status, body = fetch(bust(url))
        size = len(body) if status else 0
        if status is None:
            problem = f"no response ({body})"
        elif status != 200:
            problem = f"HTTP {status}"
        elif FATAL_TEXT in body:
            problem = "CMS fatal-error page"
        elif need_gtm and gtm_id not in body:
            problem = f"{gtm_id} missing from page (tracking gone)"
        else:
            problem = ""
        if not problem:
            break
        if attempt < ATTEMPTS:
            time.sleep(RETRY_WAIT)
    return status, size, problem


def main():
    cfg = load_config()
    base, gtm_id = cfg["base_url"].rstrip("/"), cfg["gtm_container_id"]
    targets = {base + p["path"]: p["needs_tracking_tag"] for p in cfg["pages"]}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows, flags = [], []
    for url, need_gtm in targets.items():
        status, size, problem = check(url, need_gtm, gtm_id)
        rows.append([now, url, status or "", size, problem or "ok"])
        print(f"{'FAIL' if problem else 'ok  '} {status or '---'} {size:>7}  {url}"
              + (f"  <- {problem}" if problem else ""))
        if problem:
            flags.append(f"{url}: {problem}")

    new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["checked_at", "url", "status", "bytes", "result"])
        w.writerows(rows)

    if flags:
        with open(ALERT_FILE, "w", encoding="utf-8") as f:
            f.write(f"SITE AVAILABILITY FLAGS ({now})\n")
            f.write("Requests carry a unique ?gclid= so the cache cannot hide a crash.\n")
            for line in flags:
                f.write(f"- {line}\n")
            f.write("\nIf the login page fails, the CMS itself is crashing: check the PHP error log and "
                    "recent plugin/theme updates. Consider pausing ads until it is fixed.\n")
        print(f"{len(flags)} flag(s); wrote {os.path.basename(ALERT_FILE)}")
        return 2
    if os.path.exists(ALERT_FILE):
        os.remove(ALERT_FILE)
    print("all pages healthy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
