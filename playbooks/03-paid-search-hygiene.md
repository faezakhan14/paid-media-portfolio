# Playbook 3: Paid search structure, negatives and bidding on a low-volume account

## Structure by intent

Separate campaigns and ad groups for distinct services (for example second suites, basement finishing, whole-home renovation) and for call-focused versus form-focused searches, so the ad copy and landing page match what the person typed. Generic ad groups are cheaper to build and worse at converting.

Keep the keyword set tight. Periodically remove dead keywords, overlapping keywords that compete with each other, and terms with no impressions, then add the new terms that keyword research and search-term reports prove people use.

## Negative keywords: a process, not a list

1. Pull the search-term report and group non-converting spend by *reason*: government or regulatory seekers, research and how-to, wrong location, competitors, wrong service, renters and job-seekers, price-only shoppers.
2. **Check for lead loss before blocking.** For each proposed negative, look for converting terms that contain the same word. In one review I pulled entire groups (cost, drawings, floor plans, ceiling) out of the proposal because they saved almost nothing and at least one had produced a lead.
3. Use phrase match for multi-word negatives and broad for single words, at campaign level. Don't block the core terms the business actually sells.
4. Keep exceptions deliberate. One ad group targeted a fee-related topic, so words like "incentive" and "by-law" were excluded from the *other* campaign only, so the right searchers still matched.
5. Keep a change log (what, when, why) and a proposal document that is explicitly marked *not applied* until reviewed.

Tool: [negative_keyword_audit.py](../scripts/negative_keyword_audit.py)

## Competitor and out-of-area leakage

A meaningful share of clicks on one campaign went to searches for named rivals. Adding them as negatives fixed it, but it came back with new names and new nearby towns. The fix that lasted was a daily watchlist check that flags any spend on those terms.

Tool: [google_ads_leakage_check.py](../scripts/google_ads_leakage_check.py)

## Bidding decisions with few conversions

- Smart bidding needs conversion volume to learn from. With only a few conversions a month, "Maximize Conversions" had too little to work with, and an external consultant's advice (which I agreed with after checking the data) was to go back to Maximize Clicks with a per-click ceiling.
- The ceiling also contained single outlier clicks that had cost far above the average.
- I raised budgets and widened keyword coverage in the same change, and the result was a clear rise in impression share and click volume with average click cost steady.
- **Change one thing at a time where you can, write down the date, and set a no-change window while someone external measures.** I held bid, budget and schedule changes during a review period so the measurement stayed clean; approved negatives were the exception.

## Landing-page experience

After a site outage, Quality Score and landing-page experience dropped across keywords and ad serving was limited. I logged the status daily rather than intervening, and it recovered within weeks. The lesson: it is a rolling signal. Don't make bid or budget moves in response to a temporary penalty. Protect the page, then wait for the signal to clear.

## Reporting honestly

Say how few conversions there are. Report impression share, click volume and cost per click as movement in *visibility*, and keep them separate from lead quality. Never present a platform's conversion count as revenue.
