# Scripts

Small, single-purpose Python tools I built to run paid media for a high-ticket service business. Each one exists because something went wrong once and I wanted it caught automatically the next time. All credentials, IDs, domains and competitor lists are placeholders you fill in yourself.

| Script | What it does | The problem behind it |
|---|---|---|
| [google_ads_leakage_check.py](google_ads_leakage_check.py) | Daily scan for wasted spend: expensive non-converting terms, one keyword taking most of a day's budget, competitor or out-of-area clicks, spend spikes, CPC above its ceiling | A drifting broad-match keyword and a few competitor-name searches quietly burned budget before anyone looked |
| [negative_keyword_audit.py](negative_keyword_audit.py) | Lists existing negatives, then buckets non-converting search terms by *why* they're irrelevant, and warns when a "junk" word also appears in a converting term | Negatives are permanent decisions; some "obviously junk" words had produced real leads |
| [site_availability_check.py](site_availability_check.py) | Checks landing pages with a unique click-ID on every request so a page cache can't hide a crash; also confirms the tracking tag is present | A CMS auto-update crashed the site while the cache made it look fine, and ads kept paying for clicks |
| [meta_pixel_health_check.py](meta_pixel_health_check.py) | Loads landing pages in a real headless browser to confirm the Meta pixel initialises, and checks it is receiving PageViews | A load-order bug meant the pixel never started, silently starving audiences |
| [crm_to_meta_capi_sync.py](crm_to_meta_capi_sync.py) | Sends CRM pipeline progress (Lead, Qualified, Estimate Sent, Purchase) to Meta's Conversions API, with hashed identifiers, no duplicates and a safe dry-run mode | The pixel only reported a flat "Lead" event, so Meta optimised for form fills rather than good leads |
| [meta_ad_performance.py](meta_ad_performance.py) | Per-ad report using the *exact* lead event | Counting every action containing "lead" overstated leads about seven times |

## Setup

```bash
pip install -r requirements.txt
playwright install chromium        # only needed for the pixel check
cp .env.example .env               # then fill in your own credentials
cp site_config.example.json site_config.json
cp watchlist.example.txt watchlist.txt
```

Run any script directly, for example `python google_ads_leakage_check.py`. The monitoring scripts exit with code `2` when they flag something, so a scheduler (Windows Task Scheduler, cron) can raise a notification. The CAPI sync is a dry run unless you pass `--live`.

## Safety notes

- `.env` and your filled-in config files are listed in `.gitignore`. Check `git status` before every commit.
- Every script is read-only against ad accounts except the CAPI sync, which only *sends* conversion events and defaults to a dry run.
- Use the Meta Test Events tool (`--test-code`) before sending live events.
