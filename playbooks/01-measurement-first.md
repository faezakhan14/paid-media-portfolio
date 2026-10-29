# Playbook 1: Fix measurement before you optimise

**The rule:** don't change bids, budgets or creative until you trust the numbers. On a low-volume, high-ticket account, a few conversions a month is all you have, so a tracking fault can look exactly like a performance problem.

## The stack

CRM form (embedded in an iframe on the landing page) → page script → tag manager → Google Ads, GA4 and Meta, plus call tracking and a CRM-to-Meta server-side sync.

## Faults I found, and how I found them

| Fault | How it showed up | How I confirmed it | Fix |
|---|---|---|---|
| **Cookie-consent banner defaulted to "denied"** | Leads arriving in the CRM with click IDs, but no conversions in the ad platforms | Tag manager Preview mode: tags simply did not fire for anyone who hadn't clicked Accept | Switched the consent default to allow with URL passthrough; purged the page caches so it went live |
| **Iframe form never changes the page URL** | A URL-based "thank-you page" conversion could never fire | Read the form's actual `postMessage` payload in the browser console | Switched to an event-based conversion: listen for the form's message, push a custom event to the data layer, trigger the conversion tags from that |
| **Conversion fired twice per lead** | Inflated conversion counts | The form sends two similar messages per submission; one carries the real contact data | Matched only the message that carries contact data |
| **Conversion fired on layout noise** | Conversions with no matching lead | The listener matched any message mentioning the form ID, including resize messages | Tightened the match to a genuine submission signal |
| **Pixel never initialised** | Pixel saw a tiny fraction of the sessions analytics saw; website audiences stuck at the platform minimum for months | Compared pixel PageViews with analytics sessions from the same source | A small footer snippet that waits for the pixel library to exist before initialising it |
| **Platform lead count ~7x too high** | Cost per lead looked excellent and nothing in the CRM agreed | Compared the script's total with the CRM | Match the exact `lead` action type, never "contains lead" |

## Lessons

1. **Cross-check every platform number against the CRM.** Ad platforms report what they were told; the CRM is closer to the truth.
2. **The same bug can come back.** A tracking fix was "fixed" several times because the live page kept reverting to older versions. The root cause wasn't logic, it was a missing source of truth: edits were pasted into a page builder with no version control. Keep the page code in git and add an automated check that asserts the expected script is present on the live page.
3. **Test the way a real visitor arrives.** Use a private window, a click-ID in the URL and the tag manager's Preview mode. Don't trust a logged-in view or an analytics real-time screen.
4. **Write down what you proved, not what you assumed.** A short log of "tested X, saw Y" stops the next person (or you in a month) from re-diagnosing a solved problem.

## Related scripts

[meta_pixel_health_check.py](../scripts/meta_pixel_health_check.py), [meta_ad_performance.py](../scripts/meta_ad_performance.py), [crm_to_meta_capi_sync.py](../scripts/crm_to_meta_capi_sync.py)
