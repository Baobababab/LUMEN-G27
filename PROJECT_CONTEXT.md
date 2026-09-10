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

## 3. Decisions locked by the team

Agreed before building. Change these only by team decision, and update this section when you do.

| Decision | Choice | Why |
|---|---|---|
| Interface | **Streamlit**, deployed on Streamlit Community Cloud | Python only, connects straight to this repo, everyone can contribute |
| Price acceptance | **Recomputed, segment-weighted per channel** | The supplied acceptance figures are identical across channels; without reweighting, channel choice cannot affect demand |
| Payback horizon | **User-adjustable slider, default 12 months** | Makes the CMO/CFO trade-off visible instead of hiding it in a constant |
| Customer LTV | **Re-derived from the selected price** | Home-market LTV is priced in NL/DK/SE; copying it would make the ratio blind to price |
| Market volume | **Not modelled — per-customer economics only** | Payback and LTV:CAC are per-customer metrics. Market share would be our invented assumption |
| Data defects | **Removed from the calculation, and shown in a data-quality panel** | Silent cleaning is not visible to a grader or a user |
| Team split | **5 modules, one owner each, interface contract merged first** | Five people editing one file guarantees merge conflicts |

## 4. Scope, in build order

Ship M1 before starting M2. Each module is its own branch and pull request.

**M0 — Interface contract.** One small pull request creating the five module files with function
signatures, type hints, docstrings and named constants — no implementations. Merged before anyone
starts real work. This is what lets five people work at once without touching each other's lines.

**M1 — Scenario engine (numbers only, no styling).**
Inputs: retail price, sales channel, launch month. Outputs: unit contribution, segment-weighted
acceptance, monthly contribution per customer, months to payback, LTV:CAC. Correct arithmetic
matters more than presentation here.

**M2 — Verdict layer.**
Same inputs, but the output leads with a judgement: GO / CONDITIONAL / NO-GO, the two or three
numbers that drove it, and one line naming the trade-off accepted. This is the part that turns a
calculator into a decision-support tool and it is the core of our differentiation.

**M3 — CMO vs CFO panel.**
The same scenario scored twice, side by side: brand/premium view against payback/runway view.
Makes the trade-off visible instead of asserted. This is the direct answer to the brief's closing
question.

**Stretch, only if M1–M3 are done and merged.** A short sourced research annex (see §8), a
sensitivity view showing how the verdict flips as one input moves, or market-volume sizing with
its assumption stated in plain sight.

## 5. Module contract — five files, five owners

Merge M0 with these signatures before anyone implements anything. Nobody edits a file they do not
own; if you need a change in someone else's module, ask for it rather than editing it.

```python
# data_loader.py — owner A
def load_all() -> dict[str, pd.DataFrame]:
    """Load every CSV in data/. Drop the 4 exact duplicate rows in historical sales.
    Never load first_name, last_name or email from customer_survey.csv."""

def cleaning_report() -> dict:
    """What was removed and why, for the data-quality panel.
    Keys: duplicate_rows_removed, pii_columns_excluded, anomaly_weeks_flagged."""


# acceptance.py — owner B
def acceptance_rate(price: float, channel: str) -> float:
    """Segment-weighted probability of purchase at this price in this channel, 0.0-1.0.
    Weight each segment by its share of respondents preferring that channel,
    and by its own price sensitivity. Falls back to the supplied flat rate if a
    segment is missing, and says so."""


# economics.py — owner C
def unit_contribution(price: float, channel: str) -> float: ...
def monthly_contribution(price: float, channel: str, month: int) -> float: ...
def customer_lifetime_months() -> float: ...
def ltv(price: float, channel: str) -> float: ...
def payback_months(price: float, channel: str, month: int) -> float: ...
def ltv_cac_ratio(price: float, channel: str) -> float: ...


# verdict.py — owner D (M2, may start once M0 is merged)
def verdict(price: float, channel: str, month: int,
            payback_horizon_months: float = 12.0) -> dict:
    """Returns {"verdict": "GO"|"CONDITIONAL"|"NO-GO",
                "decided_by": str, "reasons": list[str],
                "trade_off": str, "metrics": dict}."""


# app.py — owner E
# Streamlit UI only. Imports the four modules above. Contains no business arithmetic.
```

Shared constants live in one place and are named, never inlined:

```python
BLENDED_CAC_EUR = 44.0
TARGET_LTV_CAC = 3.0
DEFAULT_PAYBACK_HORIZON_MONTHS = 12.0
ACCEPTANCE_FLOOR = 0.35   # provisional, team to confirm
SALES_CHANNELS = ("DTC Online", "Retail/Grocery", "Gym & Office")
```

## 6. Formulas and definitions

```
unit_contribution    = net price to LUMEN in this channel, minus unit cost
monthly_units        = purchase_frequency_per_month, segment-weighted,
                       scaled by the seasonality index for the launch month
monthly_contribution = unit_contribution * monthly_units
ltv                  = monthly_contribution * customer_lifetime_months
payback_months       = BLENDED_CAC_EUR / monthly_contribution
ltv_cac_ratio        = ltv / BLENDED_CAC_EUR
```

Reference values from the data room: blended CAC across marketing channels ≈ **€44**, blended
gross margin in home markets ≈ **30%**, target LTV:CAC ≈ **3:1**.

**Calibration task for owner C.** `customer_lifetime_months()` is not given anywhere. Derive it by
back-solving from the home-market LTV figures in `marketing_funnel_monthly.csv` at home-market
prices, then hold it constant across German price scenarios. Document the derivation in the
docstring and surface the number in the interface. Do not invent a round figure.

## 7. Data facts already verified — read before writing any join

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
unblended, and it is why `acceptance.py` exists as its own module.

**Planted data-quality defects.**
`historical_sales_weekly.csv` contains **4 exact duplicate rows** (weeks beginning 2025-07-14,
2025-09-22, 2025-12-22, 2026-04-27). No other file in `data/` has duplicate rows. There is also an
unusual week: 2025-07-28 totals 24,508 units against a weekly median of 14,519 — but June 2026
weeks also sit above 24,000, so check it against the seasonality index in
`seasonality_and_weather.csv` before treating it as an error. Duplicates are dropped; the anomaly
is flagged, not silently removed. Both appear in the data-quality panel.

**Personal data.**
`customer_survey.csv` carries `first_name`, `last_name` and `email`. We do not load these columns
at all, and we say so in the interface. No deployed endpoint may ever return them.

**Qualitative vs quantitative tension.**
`customer_quotes.csv` does not fully agree with `customer_survey.csv`. The brief flags reconciling
them as a genuine stretch. If we touch it, it belongs in the verdict's caveats, not as a separate
feature.

## 8. External data and research — optional, and deliberately limited

The brief states that pulling a live public data source is **optional, not required**, and the
README accepts "we didn't use any external API" as a valid answer. LUMEN's data room is
self-contained. We do not spend M0–M3 time on external APIs.

If we add research at the end, it earns its place only by changing a specific input or assumption
in the model, and it must be cited. Estimated or externally sourced figures are never presented as
official LUMEN or German market data. A short annex that moves one assumption with a source beats
a long unsourced appendix.

If an API key is ever needed, it goes in an environment variable, never in a committed file.

## 9. Non-goals

- No generic "any variable in, any outcome out" engine.
- No feature without an identified user and a decision it improves.
- No machine learning where arithmetic on the given data is sufficient and explainable.
- No market-share estimate presented as fact.
- No redesign of the case data. It is imperfect on purpose.
- No editing of `AGENTS.md` or anything under `prompts/`.
- No business arithmetic inside `app.py`.

## 10. Definition of done

- The tool runs and produces a verdict for any valid combination of price, channel and month.
- Empty, out-of-range and inconsistent inputs are handled without a crash.
- Every threshold and every assumption is visible in the interface, not buried in code.
- The data-quality panel states what was removed and what was flagged.
- The README checklist is answered, in writing, while building.
- The "Our Approach" paragraph in `README.md` is written in business language.
- Every team member's prompt log is committed and merged. Work that is not merged does not exist.
