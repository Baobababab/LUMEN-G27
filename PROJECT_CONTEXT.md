# PROJECT_CONTEXT.md — LUMEN Germany entry, team working brief

> Read this after `README.md` and `LUMEN_Case_Brief.md`, and after `AGENTS.md` (which governs
> prompt logging and git workflow and overrides anything here if they ever disagree).
> This file is written by the team, for the team and for Codex. It is not part of the original
> case material. Keep it updated as decisions land.

## 1. The decision we are answering

Freya Lindqvist (Head of Growth) needs a recommendation on **price**, **positioning** and
**launch channel(s)** for LUMEN's entry into Germany — and an explicit statement of **what that
choice deliberately does not optimise for**.

Jonas (CMO) wants premium shelf positioning next to VoltFit and Root & Rise. Elena (CFO) wants
fast payback on marketing spend. No single answer satisfies both. Freya has asked to be shown
where the real trade-off sits rather than handed a number that quietly picks a side.

## 2. What we are building — one sentence

**A decision tool where a manager sets price, sales channel and launch month, and gets back a
verdict: the projected outcome, whether it clears LUMEN's investment thresholds, what it
sacrifices, and a short recommendation in plain business language.**

Not a generic "enter any variable" simulator. The scenario engine exists to serve that one
decision. If a feature does not change the answer to Freya's question, it does not ship.

## 3. Scope, in build order

Ship M1 before starting M2. Each milestone is its own branch and pull request.

**M1 — Scenario engine (numbers only, no styling).**
Inputs: retail price, sales channel, launch month. Outputs: unit contribution, estimated
acceptance, projected monthly volume, months to payback, LTV:CAC ratio. Correct arithmetic
matters more than presentation here.

**M2 — Verdict layer.**
Same inputs, but the output leads with a judgement: GO / CONDITIONAL / NO-GO, the two or three
numbers that drove it, and one line naming the trade-off accepted. This is the part that turns a
calculator into a decision-support tool and it is the core of our differentiation.

**M3 — CMO vs CFO panel.**
The same scenario scored twice, side by side: brand/premium view against payback/runway view.
Makes the trade-off visible instead of asserted. This is the direct answer to the brief's closing
question.

**Stretch, only if M1–M3 are done and merged.** A short, sourced research annex (see §7), or a
sensitivity view showing how the verdict flips as one input moves.

## 4. The verdict rules — explicit, not vibes

Every verdict must be reproducible from the data and explainable to a non-technical reader. No
free-text judgement generated without the numbers behind it visible next to it.

Proposed thresholds, to be confirmed by the team and written into the code as named constants:

- **LTV:CAC** at or above **3.0** — this is the ratio the plan already assumes (Exhibit 7).
- **Payback** within a horizon the team fixes (start from 12 months, justify the choice).
- **Acceptance** above a floor the team fixes, so a high-margin scenario nobody buys cannot pass.

GO = all thresholds cleared. CONDITIONAL = thresholds cleared only under a stated assumption.
NO-GO = at least one threshold missed. Every verdict names which rule decided it and shows the
value against the threshold.

## 5. Formulas and definitions

```
unit_contribution   = from price_test_results.csv / channel_economics.csv (net to LUMEN minus unit cost)
monthly_units       = purchase_frequency_per_month (customer_survey.csv), weighted by segment
monthly_contribution= unit_contribution * monthly_units
payback_months      = CAC / monthly_contribution
ltv_cac_ratio       = LTV / CAC
```

Reference values from the data room: blended CAC across marketing channels ≈ **€44**, blended
gross margin in home markets ≈ **30%**, target LTV:CAC ≈ **3:1**.

Open judgement call the team must make and document: the LTV figures in
`marketing_funnel_monthly.csv` come from the home markets at home-market prices. A German LTV at a
different price point has to be re-derived, not copied. Whichever way we go, the assumption is
stated in the UI, not hidden in the code.

## 6. Data facts already verified — read before writing any join

These were checked directly in the CSVs. They are the traps in this data room.

**Two different channel taxonomies. Do not join them naively.**
Sales channels are `DTC Online`, `Retail/Grocery`, `Gym & Office`. Marketing channels are
`Paid Social`, `Influencer / Content`, `Referral / Subscription`, `Retail Sampling`. CAC lives on
the marketing channels, unit contribution lives on the sales channels. Any mapping between them is
our assumption and must be declared as one.

**Acceptance is uniform across sales channels, and that is the opening.**
`price_test_results.csv` reports the same acceptance at each price regardless of channel
(61.7% at €1.79, 51.7% at €2.19, 26.7% at €2.59). But segments differ in price sensitivity and in
preferred channel: of ~420 survey respondents, 195 prefer Retail/Grocery, 119 DTC Online, 106 Gym
& Office, and Students & Budget-Conscious is the largest segment at 135. Recomputing
segment-weighted acceptance per channel is the analytical contribution the brief deliberately left
unblended.

**Planted data-quality defects.**
`historical_sales_weekly.csv` contains **4 exact duplicate rows** (weeks beginning 2025-07-14,
2025-09-22, 2025-12-22, 2026-04-27). No other file in `data/` has duplicate rows. There is also an
unusual week: 2025-07-28 totals 24,508 units against a weekly median of 14,519 — but June 2026
weeks also sit above 24,000, so check it against the seasonality index in
`seasonality_and_weather.csv` before treating it as an error. Handling these visibly is worth more
than silently dropping them.

**Personal data.**
`customer_survey.csv` carries `first_name`, `last_name` and `email`. Default decision: we do not
load these columns at all, and we say so. If any deployed endpoint ever returns survey rows, the
identity columns must not be in the payload.

**Qualitative vs quantitative tension.**
`customer_quotes.csv` does not fully agree with `customer_survey.csv`. The brief flags reconciling
them as a genuine stretch. If we touch it, it belongs in the verdict's caveats, not as a separate
feature.

## 7. External data and research — optional, and deliberately limited

The brief states that pulling a live public data source is **optional, not required**, and the
README accepts "we didn't use any external API" as a valid answer. LUMEN's data room is
self-contained. We do not spend M1–M3 time on external APIs.

If we add research at the end, it earns its place only by changing a specific input or assumption
in the model, and it must be cited. Estimated or externally sourced figures are never presented as
official LUMEN or German market data. A short annex that moves one assumption with a source beats
a long unsourced appendix.

If an API key is ever needed, it goes in an environment variable, never in a committed file.

## 8. Non-goals

- No generic "any variable in, any outcome out" engine.
- No feature without an identified user and a decision it improves.
- No machine learning where arithmetic on the given data is sufficient and explainable.
- No redesign of the case data. It is imperfect on purpose.
- No editing of `AGENTS.md` or anything under `prompts/`.

## 9. Stack and deployment

Python, pandas, Streamlit. Deploy to Streamlit Community Cloud, which connects straight to this
GitHub repo. If the team prefers a Vercel URL instead, precompute the scenario grid to a JSON file
and ship a single static page that reads it — decide this once, not twice.

Keep the data loading in one module so the numbers can be tested without the UI.

## 10. Definition of done

- The tool runs and produces a verdict for any valid combination of price, channel and month.
- Empty, out-of-range and inconsistent inputs are handled without a crash.
- Every threshold and every assumption is visible in the interface, not buried in code.
- The README checklist is answered, in writing, while building.
- The "Our Approach" paragraph in `README.md` is written in business language.
- Every session's prompt log is committed and merged. Work that is not merged does not exist.
