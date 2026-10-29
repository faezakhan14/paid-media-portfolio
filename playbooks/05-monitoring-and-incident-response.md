# Playbook 5: Monitoring and incident response

## The incident

A CMS core update auto-installed and was incompatible with a paid plugin, which crashed the whole site. The page cache kept serving saved copies of the plain URLs, so anyone checking the normal address saw a healthy site. But ad clicks carry a click-ID parameter, which bypasses the cache, so every paying visitor (and the admin area) hit a fatal error. It went unnoticed for about a day.

## What I did

1. **Restored service first**, then worked out the cause.
2. **Wrote an after-action report** (timeline, cause, impact, what would have caught it earlier) rather than just fixing it.
3. **Built a check that can't be fooled by the cache** (every request carries a unique click-ID, and the login page, which is never cached and loads every plugin, is always included). Added it to the daily run. See [site_availability_check.py](../scripts/site_availability_check.py).
4. **Watched the ad platform's recovery** instead of reacting. Landing-page experience dropped after the outage and recovered over the following weeks without any bid changes. I corrected my own early read of how large the impact was once more data came in.

## The daily and weekly checks I run

| Check | Frequency | Catches |
|---|---|---|
| Site availability (cache-proof, tracking tag present) | Daily | Crashes, missing tracking |
| Pixel initialisation and PageViews | Daily | Silent tracking loss |
| Spend leakage (expensive terms, concentration, competitors, spikes, CPC ceiling) | Daily | Wasted budget |
| Landing-page experience and serving status | Daily | Quality-score collapses; alerts only on a *change* of status, not "still limited" every day |
| Audience size monitor | Daily | Whether retargeting audiences are big enough to use |
| Cross-platform performance report | Weekly | Trend across Google, Meta, search console, analytics, heatmaps, CRM |
| Call-quality report | Weekly | Call sources and quality |
| Meta ad performance by concept | Weekly | Creative test progress |

## Design rules for alerts

- **One alert file per check**, deleted automatically on a clean run, so an old file never causes a false alarm.
- **Exit code 2 on a flag**, so any scheduler can raise a desktop notification.
- **De-duplicate** against a log, so the same issue doesn't ping every day.
- **Alert only on a state change** for slow signals, and only after consecutive bad days for noisy ones.
- **Expect false alarms from cache lag.** If an alert does not clear on a re-run a few minutes later, treat it as real.
- **Know your own gaps.** The scheduler only ran when the machine was logged in, so an alert could sit unseen for a day or two. I documented that limit rather than pretending the monitoring was real-time.

## A reusable template for the report

*Summary (what happened, in plain language) → Timeline → Root cause → Impact (state uncertainty) → What I changed → What would have caught it earlier → Open items.*
