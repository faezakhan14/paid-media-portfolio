# Case study 1: Paid lead generation for high-ticket construction services

*A design-build renovation company in Ontario, Canada. The client is anonymised and figures are described in relative terms by design.*

## Objective

Build a measurable inbound pipeline for a firm that sells high-ticket jobs: basement conversions, second suites and whole-home renovations. The business needed **qualified homeowner enquiries, not just volume**, and it had no reliable way to see where its leads came from.

## Strategy

Two decisions shaped everything.

1. **Structure the account by intent.** Separate campaigns and ad groups for second suites, basement finishing and call-focused legal-basement searches, so each ad and page matched what the person actually searched for.
2. **Treat measurement as part of the strategy.** Before scaling spend, fix tracking so results can be trusted. See [Playbook 1](../playbooks/01-measurement-first.md).

## Execution

- **Google Search:** keyword build-out and clean-up, a reviewed and growing negative-keyword list, responsive-search-ad copy testing, landing pages per audience. ([Playbook 3](../playbooks/03-paid-search-hygiene.md))
- **Bidding:** moved from Maximize Clicks to Maximize Conversions, then back to Maximize Clicks with a per-click ceiling, once it was clear the account didn't produce enough conversions for automated bidding to learn from. An external consultant's advice and my own check of the data agreed.
- **Meta:** lead-gen campaigns with a post-submission redirect to a renovation landing page to improve quality; a diagnosed-then-refreshed creative strategy rather than a rebuild. ([Playbook 4](../playbooks/04-meta-creative-testing.md))
- **Tracking and attribution:** GA4, tag manager, Meta pixel, call-tracking number pools by source, click-ID capture into the CRM, and a CRM-to-Meta Conversions API sync. ([Playbook 2](../playbooks/02-attribution-and-call-tracking.md))
- **Operations:** daily and weekly automated checks, a repeatable weekly reporting workbook, and an incident write-up after a site outage. ([Playbook 5](../playbooks/05-monitoring-and-incident-response.md))

I owned the messaging, creative briefs, landing pages and tracking setup.

## Results (relative terms)

- Meta lead generation reached a cost per lead **within the company's target** during its strongest period (Meta-reported), then worsened. I did not present that as a sustained result. One ad produced most of the leads, so the real finding was creative concentration risk.
- On Google, the structure and budget changes **clearly increased impression share and click volume**, while average click cost stayed steady.
- The business went from **unattributed enquiries to a pipeline with call and lead sources visible**.
- Organic search impressions and clicks grew several-fold over the period, with a caveat: a large share came from a time-limited grant topic.
- **Still being built when I finished:** qualified-lead quality and revenue attribution by channel. I said so plainly in reporting.

## What went wrong, and what I learned

- **Early volume was inflated by a municipal grant angle.** When the program closed, volume fell and lead *quality*, not lead count, became the real problem.
- **A cookie-consent default had been blocking tracking for weeks.** An external audit helped me separate real performance problems from tracking problems. Measurement has to be fixed before optimisation can be trusted.
- **A budget-qualifier quiz added friction without improving results.** The next test was showing real price ranges in the ad and the page.
- **A site outage** hurt landing-page experience for a while. It recovered without bid changes, and I corrected my own early estimate of the impact when more data arrived.
- **A lead-count bug in my own scripts** overstated Meta leads several times over until I cross-checked against the CRM.

**If I ran it again,** I'd put budget-qualifying language in the ad copy from the first week, and I'd put the landing-page code in version control from day one.
