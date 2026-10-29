# Playbook 2: Attribution for a business that sells by phone and quote

High-ticket local services close through calls, conversations and estimates, not a checkout. If you only track form fills, you are measuring the minority of the real pipeline.

## What I put in place

- **Call-tracking number pools by source.** Separate numbers for paid search, paid social and organic, plus the main line, so each inbound call carries a source. Before this, no call had one.
- **Click-ID capture into the CRM.** Google and Meta click IDs stored on the contact record, so a lead can be tied back to a campaign and later uploaded as an offline conversion.
- **CRM stage sync to Meta** (Lead, Qualified, Estimate Sent, Purchase) so the algorithm learns from lead quality, with an offline-conversion upload workflow prepared for Google.
- **A weekly call-quality report.** Per call: source, answered or not, duration, whether the caller matches a CRM opportunity (matched by phone, stored only as a hash), and the opportunity's stage. No names or numbers are written to the log.
- **A "How did you hear about us?" field** on intake, to compare self-reported source with tracked source.

## What the data taught me

- **Call length is a usable first quality signal.** Callers who turned out to be real leads stayed on the line several times longer than callers who never matched an opportunity.
- **The business profile can be the biggest phone source with a visible origin**, bigger than the tracked website numbers, so it needs its own attention.
- **Source labels in a CRM are not truth.** An automation was tagging some paid-search leads as paid-social. I treated the click-ID and UTM fields as the source of record and fixed the automation.
- **Test records contaminate pipelines.** Staff test submissions landing in the live pipeline distort lead counts and any sync built on them. I tagged and excluded them, and flagged "contact count" as a raw number, not a count of qualified leads.
- **Be honest about attribution limits.** Revenue attribution to a specific channel was still being built; I reported it as unfinished rather than implying it was solved.

## Reusable approach

1. Give every channel a distinguishable entry point (number, UTM, click ID).
2. Land all of it in one system of record.
3. Classify outcome (answered, qualified, won) in that system.
4. Report channel-by-outcome weekly, and state clearly what is still unattributed.
