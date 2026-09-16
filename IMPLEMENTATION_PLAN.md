# Official LUMEN implementation plan

## Purpose and verified baseline

This plan records approved work and completed implementation evidence for the LUMEN prototype.
Planning began from a static frontend in `public/`, FastAPI in `api/index.py`, and calculations
in Python modules. The original verified baseline was `main` at
`b40838303222bed86942a7ed6e6091507ecc55dc`, with a successful Production deployment and nine
local Python 3.11 tests. GitHub Actions on Python 3.12 remains the official gate.

The objective is a clear decision tool for a non-technical manager choosing price, position,
launch channel, and launch month for Germany. It presents the CMO and CFO trade-off while producing
one verdict only: `GO`, `CONDITIONAL`, or `NO-GO`. Changes to verdict rules require documented
rationale, focused tests, and approval.

## Architecture and information contract

| Layer | Responsibility |
| --- | --- |
| `public/index.html` | Accessible page structure and controls |
| `public/styles.css` | Presentation, responsive layout, visual states, and print |
| `public/app.js` | Temporary browser state, API calls, and rendering |
| `api/index.py` | Request validation and aggregated-response serialization |
| Python modules | Approved formulas, decision rules, and data access |

JavaScript contains no economic formulas, decision thresholds, competitive classifications, or
scenario-improvement logic. The browser retains up to three scenarios only while the page remains
open. Public endpoints return aggregated results only and never serve CSV files, survey rows, or
identifiers.

Visible application text uses clear business English for non-technical managers. The application
is not bilingual. Each metric includes name, value, unit, visual status, approved threshold
comparison where available, business explanation, and expandable formula, source, assumptions,
and limits.

Verdict thresholds are LTV:CAC of 3.0, the user-selected payback horizon, and a 35% price
acceptability index.

- `critical`: the metric fails its approved threshold;
- `monitor`: the metric passes but decides the verdict, or has no approved threshold;
- `favorable`: the metric passes and does not decide the verdict.

Metrics without an approved threshold display `Monitor` and `No approved decision threshold`.
Expandable controls have explicit labels, work with keyboard and screen readers, and support global
open and close actions.

## Analysis contracts

### Competitive position and CMO/CFO perspectives

The backend compares selected price with observations in
`competitor_prices_by_channel.csv` for the same channel and comparable format. It returns the
competitor name, recorded positioning, observed range, and distance from LUMEN price. Affordable,
premium, and highly premium are management labels derived from supplied observations, not general
market claims. The tool states any overlap and never estimates a missing competitor price.

The CMO perspective uses price acceptability, observed competitor price position, and consistency
with the premium objective in the brief. The CFO perspective uses unit and monthly contribution,
LTV:CAC, payback, and threshold performance. No metric is added without an approved formula,
source, and meaning. Both panels describe the same selected scenario and verdict, including the
decision driver, main risk, and accepted trade-off.

### Scenario, channel, sensitivity, and month analysis

The page starts with one scenario and supports up to three. Users can duplicate, edit, and remove
scenarios. The backend returns full results and aggregated differences for at most three valid
scenarios. `Compare channels` creates all official channels with unchanged price, month, and
horizon. The frontend does not calculate economic differences.

Price sensitivity uses discrete prices within `OBSERVED_PRICE_SUPPORT`. It does not use binary
search because acceptability is non-monotonic below EUR 2.10. The selected price is always
evaluated. The service groups consecutive prices with the same verdict and returns the selected
interval plus nearest verdict changes. Each request has a 250-evaluation limit and runs only for
the selected baseline.

The selected step is the most precise one that meets the measured latency budget. The application
reports the actual step, evaluation count, method, and latency, and calls the output model
sensitivity rather than a demand forecast.

Launch-month analysis keeps price, channel, and horizon fixed. It uses only
`seasonality_and_weather.csv` and returns the selected month index, its rank, contribution and
payback change, and the most favorable supplied-data window. It does not call a weather service.

### Model adjustments

For `CONDITIONAL` and `NO-GO` outcomes, the backend evaluates one changed variable at a time:
supported price, another official channel, or another month. Ranking favors a better verdict, fewer
failed thresholds, then shorter normalized distance from thresholds, with deterministic tie-breaks.
The interface labels results as model adjustments. It does not create arbitrary advice or a
multi-objective optimizer. A `GO` baseline explicitly states that no adjustment is needed.

## Privacy and security

`data/customer_survey.csv` is unchanged from the public university template
`ateliaworkshop-ai/lumen-pricing-case-template`. Runtime processing excludes `respondent_id`,
`first_name`, `last_name`, and `email`.

The implementation must retain:

- no identifiers in frontend, API responses, or application logs;
- no endpoint for CSV files or raw rows;
- no transfer to external services;
- aggregated results only;
- safe API errors that reveal no individual row or personal value.

Tests use only suite-created synthetic fixtures and sentinels. They never copy personal values from
the supplied CSV. Privacy tests verify absent forbidden keys and sentinels, aggregated
`/api/scenario` and `/api/compare` responses, safe 404-style raw-data failures, and aggregated
data-quality output.

## Build order and completed phases

The implementation order was:

`Phase 0 → Phase 1 → Phase 2 → Phase 3 → Addendum 3A → Phase 4 → Phase 5 → Addendum 5A →
Addendum 5B → Addendum 5C → Phase 6 → Phase 7`.

Each phase began from updated `main` after the preceding merge.

### Phase 0: privacy baseline

Runtime exclusion of all four identifiers, safe 422 validation, 404 raw-data routes, synthetic
sentinel tests, and immediate README Data documentation were implemented on 2026-09-16. Five
focused and eleven full tests passed locally.

### Phase 1: explanations and manager text

The API now provides aggregated metadata for six metrics: status, comparison, explanation,
formula, source, assumptions, and limits. The frontend renders accessible details and global
open/close controls. Plain business English and no browser business calculations were documented.

### Phase 2: competitive position and CMO/CFO panels

The API compares price with observed competitors in the same channel and format. CMO and CFO panels
reuse the selected scenario and its single verdict. No competitor, threshold, or additional verdict
was invented.

### Phase 3 and Addendum 3A: scenario comparison and selected baseline

`/api/compare` accepts one to three scenarios, calculates results and aggregated differences in
the backend, and supports the official channel comparison. Browser state is temporary. The selected
baseline drives detailed panels and all relative differences.

### Phase 4: price sensitivity and month analysis

Optional analysis runs for one selected baseline only. Sensitivity uses EUR 0.02 resolution,
observed endpoints EUR 0.62 and EUR 3.09, plus the selected price, for no more than 126 effective
evaluations under the hard 250 limit. Warmed-cache benchmarks on Python 3.11 measured 3.901 ms at
EUR 0.01, 1.892 ms at EUR 0.02, and 768 ms at EUR 0.05; EUR 0.02 met the 2,500 ms budget.
Month analysis uses supplied seasonal indices only.

### Phase 5 and addenda: model adjustments

For `CONDITIONAL` and `NO-GO`, the backend evaluates supported price changes, alternative
official channels, and alternative months, one variable at a time. The interface shows at most
three manager-readable adjustments at the end of the results. It also displays a clear no-change
message for `GO`.

### Phase 6: print mode

`Print evaluation` uses the native browser dialog. The print record includes evaluated inputs,
recommendation, trade-off, perspectives, metrics, sources, timestamp, and page URL. Print CSS
hides controls and Data quality. No PDF library, server-side generator, email, or archive was added.

### Phase 7: final verification

README now completes the university checklist and states the stable Vercel domain. PROJECT_CONTEXT
records delivered privacy boundaries, browser/Python responsibilities, and native printing.
Privacy/API checks passed 13 tests; the full suite passed 33 tests; `python -m compileall .`
passed. PR #55 merged. Production succeeded on `894c5de`, and the public-site smoke test passed.

### Post-Phase 7 result-layout adjustment

The results page places metric-reading guidance directly below Decision metrics, rather than in a
separate panel. On desktop, decision metrics use a three-column grid. The final sections appear in
this order: model adjustments, Data quality and cleaning, then Print evaluation.

### Post-audit Phase A: safe non-recoverable payback

Non-finite payback values remain nullable numeric API fields. All manager-visible verdict,
metric, perspective, adjustment, and browser text now uses `Not recoverable`; it never exposes
`inf`, `Infinity`, or `NaN`. Comparison deltas are nullable when either payback is non-recoverable.
Focused tests and the complete suite passed locally before the phase pull request.

### Post-audit Phase B: manager decision language

The stable `decided_by` machine key remains in the API. A separate manager-facing driver now gives
the metric label, its threshold context, and the deterministic selection rule: largest proportional
miss for a failed threshold, or smallest safety margin for a passing decision. Trade-off language
states approved threshold performance without implying a relative scenario comparison. A model
adjustment can replace the selected scenario inputs and evaluate that alternative as the new
baseline. Focused tests and the complete suite passed locally before the phase pull request.

### Post-audit Phase C: bounded input and safe API failures

The payback horizon has one shared maximum of 120 months in browser controls, API validation, and
direct verdict validation. The browser now checks response content type and status before parsing
JSON. It shows only business-readable messages for expected validation failures, unavailable
service, malformed content, timeouts, and network failure. The sensitivity local name is
`bestWindow`, avoiding a shadowed browser global. Focused tests and the complete suite passed
locally before the phase pull request.

### Post-audit Phase D: deployment protection and metadata

Vercel applies a same-origin content security policy, `nosniff`, frame-denial, and referrer-policy
headers across all routes. The page includes an English meta description and local SVG favicon.
`robots.txt` permits indexing, as selected in the audit plan. Static configuration tests and the
complete suite passed locally before the phase pull request.

## Mandatory phase stop protocol

After each phase:

1. run focused tests;
2. run the complete suite;
3. update this plan;
4. update affected documentation and relevant README checklist answers;
5. include the prompt log;
6. verify no browser business logic and no non-aggregated API data;
7. open a pull request and wait for GitHub Actions on Python 3.12;
8. stop before the next phase.

## Translation follow-up

This separate task translates repository-authored Italian documentation into English while preserving
technical meaning and data. It does not translate CSV values, supplied PDF material, or verbatim
prompt logs.

Translation result, 2026-09-16: `IMPLEMENTATION_PLAN.md` is now English. CSV values, supplied
PDF material, and prompt logs remain unchanged because they are source data, source material, or
verbatim records rather than repository-authored documentation.
