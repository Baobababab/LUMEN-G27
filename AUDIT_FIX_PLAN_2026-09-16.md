# LUMEN audit fix plan — 2026-09-16

## Status and stop condition

This is a planning document only. It verifies the findings reported in
`AUDIT_lumen-g27_2026-09-16.md` and defines the implementation sequence. No fix described here
has been implemented. Work must not begin until the plan is approved.

The audit was performed against `main` at commit `035e3a0` and the public deployment at
`https://lumen-g27.vercel.app`. The local baseline is healthy: 34 Python tests pass and
`node --check public/app.js` succeeds. The green suite does not cover several reported edge cases.

## Verified findings

| ID | Severity | Verification | Evidence | Planned action |
| --- | --- | --- | --- | --- |
| B1 | High | Confirmed | A sufficiently low price produces `payback_months: null` in JSON while backend prose contains `inf`. `metricValue()` then calls `.toFixed(2)` on the null value. | Phase A |
| T1 | Medium | Confirmed | Verdict, comparison, and adjustment text can expose Python's `inf` token to a manager. | Phase A |
| T2 | Low | Confirmed | The API returns internal `decided_by` identifiers such as `payback_months`, which the frontend can display without a business label. | Phase B |
| T3 | Low | Confirmed | Some trade-off copy describes one scenario as sacrificing reach even though the sentence is based on absolute thresholds, not the comparison with another scenario. | Phase B |
| R1 | Low | Confirmed | The payback horizon has a positive minimum but no upper bound in HTML, Pydantic validation, or direct model validation. A value of `1e308` is accepted. | Phase C |
| R2 | Low | Confirmed | The browser calls `response.json()` before checking response status and content type, so an HTML or malformed server response leaks a parser error instead of a useful message. | Phase C |
| S1 | Low | Confirmed in production | HSTS is present, but CSP, `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` are absent. | Phase D |
| Q1 | Very low | Confirmed | `const window` shadows the browser global in the sensitivity renderer. It currently works because that scope does not need the global. | Phase C |
| M1 | Very low | Confirmed in production | No meta description is declared and `/favicon.ico` and `/robots.txt` return 404. | Phase D |

### Reproduction evidence

- Low-price request: HTTP 200, `payback_months` serialized as `null`, verdict reason includes
  `Payback inf months`, and the comparison text includes `inf months`.
- Extreme horizon request: HTTP 200 for `1e308`; the generated reason is 341 characters long.
- DTC and Retail/Grocery scenarios produced different acceptability values, but the Retail/Grocery
  trade-off still used an absolute “prioritises reach” statement. This confirms T3 is copy logic,
  not a calculation failure.
- Production checks returned 404 for `/favicon.ico` and `/robots.txt`; the four headers in S1 were
  absent.

## Proposed product decisions requiring approval

Implementation should freeze these decisions before Phase A begins:

1. Cap the payback horizon at **120 months** in every input path. This is a proposed usability and
   abuse-prevention bound, not a new economic threshold.
2. Display a non-finite payback as **“Not recoverable”**. Keep the numeric JSON field nullable; do
   not replace it with a string or emit non-standard JSON infinity values.
3. Preserve `decided_by` as the stable machine key for compatibility, but add a manager-facing
   driver label and context to the API response.
4. Describe trade-offs against their approved thresholds. Reserve relative claims such as
   “higher reach” or “weaker returns” for responses that contain a measured scenario delta.
5. Use a same-origin Content Security Policy because all current scripts and styles are local.
6. Let `robots.txt` permit indexing. If this prototype should remain undiscoverable, replace that
   choice with `Disallow: /` before Phase D.

## Phase A — Make non-finite payback safe and readable

**Findings:** B1 and T1. This phase comes first because B1 can prevent the complete result page from
rendering.

### Implementation

1. Add one backend formatting helper for payback values and reuse it in verdict reasons,
   comparison summaries, metric explanations, and model-adjustment prose.
2. For a finite number, preserve the current two-decimal business format. For a non-finite value,
   use “Not recoverable” without a unit or fabricated number.
3. Keep `payback_months` numeric-or-null in the JSON contract. Do not serialize `Infinity`, `inf`,
   or a display string in the metric field.
4. Make the frontend formatter explicitly handle null and non-finite values before calling
   `.toFixed()`. Render the same approved label used by the backend.
5. Check every user-visible response field for the tokens `inf`, `Infinity`, and `NaN`.

### Tests and acceptance criteria

- Add a low-price API regression test proving HTTP 200, `payback_months: null`, and no non-finite
  token in any user-visible string.
- Add unit tests for finite, zero-contribution, and negative-contribution payback formatting.
- Add a frontend rendering test proving a null payback does not throw and displays
  “Not recoverable”.
- Preserve current values and wording for ordinary finite scenarios unless the wording contains a
  non-finite token.
- Run focused tests, the complete suite, the JavaScript syntax check, and the privacy tests.

### Completion record

Implemented on branch `fix/nonfinite-payback`. The API keeps non-recoverable payback and its
comparison delta as `null`; manager-visible text uses `Not recoverable`. Optional launch-month
analysis handles the nullable value. Added regression coverage for verdict text, API serialization,
comparison deltas, adjustment text, and frontend metric formatting. Focused tests passed 34 tests;
the full suite passed 39 tests; `node --check public/app.js` and `python -m compileall .` passed.

## Phase B — Separate machine keys from management language

**Findings:** T2 and T3. This phase depends on Phase A so every driver description can safely format
payback.

### Implementation

1. Retain `decided_by` as an internal key and add explicit response fields for the display label and
   short business context. Define the mapping in the backend, not JavaScript.
2. Use plain labels such as “Customer acquisition cost payback” rather than exposing snake_case.
3. For a GO result, describe the passing metric with the smallest proportional margin to its
   approved threshold. For a failing result, describe the largest proportional miss. Document this
   selection rule and test ties deterministically.
4. Rewrite trade-off text so threshold evidence remains absolute: for example, “Price acceptance
   remains above the approved floor, while LTV:CAC is below target.”
5. Use comparative language only in comparison responses with calculated deltas between named
   scenarios.
6. Clarify that the model-adjustment action evaluates a suggested alternative and makes that
   alternative the new baseline; do not imply it merely expands the current recommendation.

### Tests and acceptance criteria

- Assert that the raw driver key remains stable and the new label/context are present.
- Cover GO, CONDITIONAL, and NO-GO driver selection, including deterministic ties.
- Cover all sales channels and prove no absolute-threshold message claims a relative improvement.
- Prove scenario-delta copy still uses relative language where the API supplies the delta.
- Run focused tests, the complete suite, JavaScript checks, and privacy tests.

### Completion record

Implemented on branch `fix/manager-decision-language`. The API retains `decided_by` and adds a
business label and threshold context. Trade-off text now describes only approved threshold status.
Users can apply an adjustment to the selected scenario and re-evaluate it as the baseline. Added
coverage for business driver labels, GO/CONDITIONAL/NO-GO context, all channels’ threshold wording,
and the frontend apply action. Focused tests passed 27 tests; the full suite passed 41 tests;
`node --check public/app.js` and `python -m compileall .` passed.

## Phase C — Bound inputs and make API failures actionable

**Findings:** R1, R2, and Q1. This phase follows the response-contract changes in Phase B to avoid
editing request and response handling twice.

### Implementation

1. Define `MAX_PAYBACK_HORIZON_MONTHS = 120` in the backend validation layer and reuse it in all
   direct validation paths.
2. Apply the same maximum in Pydantic and in the HTML number input. Keep the existing positive
   minimum.
3. Return the normal structured 422 response for horizons outside the allowed range. State the
   allowed range in plain English near the input or in its validation message.
4. Replace unconditional `response.json()` with a response reader that checks status and content
   type first:
   - show a safe server-supplied detail for expected structured 4xx responses;
   - show a generic business-readable message for HTML, invalid JSON, malformed payloads, 5xx
     responses, and network failures;
   - preserve the existing timeout behavior and avoid exposing response bodies or stack traces.
5. Rename the sensitivity local variable from `window` to `bestWindow`; do not refactor unrelated
   rendering code.

### Tests and acceptance criteria

- Test boundary values 1, 120, 121, zero, negative, and an extreme finite number through the API.
- Test the direct calculation entry point so it cannot bypass the cap.
- Test JSON 4xx, JSON 5xx, HTML 5xx, malformed JSON, network failure, and timeout messages.
- Prove that no raw HTML, parser exception, stack trace, or response body appears in the page.
- Run focused tests, the complete suite, syntax checks, and privacy tests.

### Completion record

Implemented on branch `fix/validate-scenario-requests`. The 120-month maximum is enforced by the
HTML input, Pydantic, and direct verdict validation. The browser reads JSON only for declared JSON
responses and maps every failure class to a safe manager-facing message. The sensitivity local is
renamed `bestWindow`. Added boundary, direct-validation, response-handler, and frontend contract
coverage. Focused tests passed 30 tests; the full suite passed 43 tests; `node --check public/app.js`
and `python -m compileall .` passed.

## Phase D — Add deployment protections and page metadata

**Findings:** S1 and M1. This phase is isolated because correctness must be verified against a Vercel
Preview deployment, not only locally.

### Implementation

1. Add `vercel.json` response headers for all routes:
   - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src
     'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self';
     frame-ancestors 'none'; form-action 'self'`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
2. Keep the existing platform HSTS behavior; do not duplicate a conflicting value without first
   verifying the Vercel response.
3. Add a concise English meta description to `public/index.html`.
4. Add a small local SVG favicon and reference it explicitly.
5. Add `public/robots.txt` with the approved indexing choice.

### Tests and acceptance criteria

- Add static configuration tests for the exact header names and required CSP directives.
- Verify that current scripts, styles, API requests, favicon, and print view work with the CSP.
- On the Vercel Preview URL, inspect response headers and confirm favicon and robots return 200.
- Check desktop and mobile browser consoles for CSP violations.
- Run the complete local suite before opening the phase PR.

### Completion record

Implemented on branch `fix/deployment-headers`. Added route-wide Vercel CSP, `nosniff`, frame-denial,
and referrer-policy headers; an English description; local SVG favicon; and an indexing-permitted
`robots.txt`. Added static configuration and page-asset tests. Focused tests passed 12 tests; the
full suite passed 45 tests; `node --check public/app.js` and `python -m compileall .` passed.

## Phase E — Final regression and production proof

This is a verification phase, not an opportunity for additional features.

1. Run the full Python suite, privacy/API suite, `python -m compileall .`, JavaScript syntax checks,
   and static deployment checks.
2. Exercise in a browser:
   - a low-price non-recoverable-payback scenario;
   - a normal finite scenario;
   - all three sales channels;
   - add, remove, and select baseline among three scenarios;
   - price sensitivity and launch-month analysis;
   - model adjustments for both available and unavailable improvements;
   - the 120-month boundary and rejected 121-month value;
   - mobile layout at 375 × 812, keyboard navigation, and print view.
3. Exercise non-JSON and malformed API failures in an isolated automated test; never alter the
   production endpoint to simulate these failures.
4. After an approved merge, prove that Production reports the same commit as `origin/main`, all
   required headers and assets are present, and the browser console is clean.

## Dependency order and delivery protocol

The required order is **A → B → C → D → E**. Phase A fixes the rendering blocker and establishes
the nullable-payback contract. Phase B builds management language on that contract. Phase C then
hardens request/response handling. Phase D is deployment-specific. Phase E verifies the integrated
result.

Each implementation phase must use a dedicated branch and pull request. At the end of every phase:

1. run focused tests;
2. run the complete suite and privacy checks;
3. update this plan and the relevant README checklist answers;
4. append the verbatim prompt and result to the prompt log;
5. open the phase pull request and wait for CI and Vercel Preview;
6. stop without starting the next phase;
7. begin the next phase only from updated `main` after the previous PR is explicitly approved and
   merged.

## Explicitly deferred or rejected changes

- Do not change economic formulas, thresholds, rankings, or scenario verdicts as part of these
  fixes.
- Do not emit non-standard JSON infinity values or convert numeric metric fields to display text.
- Do not add storage, services, frameworks, or dependencies.
- Do not perform a wholesale `innerHTML` rewrite: current inserted business strings are generated
  from validated repository-controlled values. Reassess this only if untrusted free text enters
  the rendering path.
- Do not remove persistent `analysisRequested` behavior; the analysis staying visible after an
  input edit is intentional until a new evaluation replaces it.
- Do not optimise performance without a reproduced timeout or measured budget failure.
- Do not edit the source audit file; preserve it as supplied evidence.

## Approval gate

Approval of this document authorizes planning only unless the instruction explicitly says to start
Phase A. Before implementation, confirm or amend the six product decisions above, especially the
120-month cap and the `robots.txt` indexing policy.
