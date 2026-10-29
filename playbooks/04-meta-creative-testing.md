# Playbook 4: Paid social diagnosis and creative testing

## Start by diagnosing, not rebuilding

When Meta results sagged, the instinct was to launch a fresh campaign. I didn't, because the evidence pointed elsewhere:

| Finding | What it meant |
|---|---|
| A consent default had blocked tracking for weeks | Months of "poor" data were partly a measurement problem |
| Website custom audiences were stuck at the platform's minimum size | Retargeting and lookalike audiences had nothing real to work from |
| Two of three ad sets had produced no leads, while one produced almost all of them | The problem was concentrated, not account-wide |
| Messaging led with trust claims every competitor also made | Creative, not campaign age, was stale |

**Decision:** keep the campaigns (age isn't penalised, and a new campaign throws away learning and pixel history), refresh the creative, and park the starved audiences until their seed audiences were big enough to be real.

## Positioning: differentiate by the stack, not by a single claim

Competitors matched each individual trust signal one by one (registration, years in business, rating, fixed price). What none of them combined was the *whole set*. So the message became "a builder, not just an installer", plus a second angle for multigenerational households that nobody paired with structural credibility.

Guardrails I wrote down: calm authority, no hype or urgency, lead with a checkable claim rather than an adjective, a banned-words list, and only claims that can be verified. Where a competitor's status was unconfirmed, the rule was to say what is checkable about *us*, never to assert something about them.

## Run a fair test

My first creative test was unfair: three ads in one ad set, and the platform sent about 90% of spend to one of them within days. The others got almost no delivery, so nothing could be concluded.

Fix:
- **One concept per ad set**, cloned targeting, equal budget, so delivery is forced to be even.
- **Change one variable.** The image stayed constant and only the copy changed.
- **Put UTM parameters with ad and ad set names on every ad**, so the CRM can attribute each lead to a concept.
- **Pre-register the read date and the metric.** At this cost per lead, each concept would produce only a couple of leads in two weeks, so I judged on link click-through and cost per link click plus CRM leads by UTM, and set a date before which I wouldn't call a winner.
- **Watch for a high-click-through, low-lead ad.** Click-through is not a win until the qualifier page converts.

## What the creative history showed

Auditing every ad built over the year, grouped by format and message theme:

- One ad produced most of the leads, which is **concentration risk**, not a scalable win.
- Before/after and transformation creative earned a lot of cheap clicks and very few enquiries.
- Short videos made from still photos produced no leads, but spend was too low to be a fair test.
- Carousels were the most-used format and cost more per lead than single images.
- Early volume had been inflated by a time-limited government grant angle; when the grant ended, lead *quality* became the real problem.
- A budget-qualifier quiz added friction without improving results, so the next test was showing real price ranges in the ad and page.

I also listed what had **not** been tested (professional project photography, single-variable image tests, short finished-project video), so the next round had a clear brief.

## Reliability habits

- Check the monitoring scripts themselves. One performance check silently missed new ad sets for a week because it queried a stale list of IDs. Query by campaign, not by a hard-coded ID list.
- Fix the metric, then fix older log rows or label them "inflated" so nobody trusts them.
- Cap placements to the one that performs, and say why.

Tools: [meta_ad_performance.py](../scripts/meta_ad_performance.py), [meta_pixel_health_check.py](../scripts/meta_pixel_health_check.py)
