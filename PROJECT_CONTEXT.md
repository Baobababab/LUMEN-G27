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
| Interface | **Static web frontend plus FastAPI on Vercel** | Vercel is required; the frontend is public while Python calculations and case data remain server-side |
| Price acceptability | **Recomputed, segment-weighted index per channel** | The supplied test figures are identical across channels; without reweighting, channel choice cannot affect price acceptability |
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
price-acceptability index, monthly contribution per customer, months to payback, LTV:CAC. Correct arithmetic
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
    """Segment-weighted PRICE-ACCEPTABILITY INDEX at this price in this channel, 0.0-1.0.
    NOT a calibrated purchase probability — this is the share of the channel's customer
    base for whom price falls inside their Van Westendorp acceptable band
    (cheap_eur <= price <= expensive_eur), weighted by each segment's share of that
    channel's respondents. Never call this a "probability of purchase" in code, UI or
    docstrings.

    Not monotone below EUR 2.10 in any channel (max(cheap_eur) across the price-sensitivity
    survey is EUR 2.10) — a lower price can reduce the index there, because some segments
    perceive it as suspiciously cheap. Monotone non-increasing at or above EUR 2.10 in
    every channel. This is a verified property of the data, not a bug.

    Raises ValueError for a bad argument: non-finite, boolean, zero or negative price, or
    a channel not in SALES_CHANNELS.

    Raises AcceptanceDataError (not a silent fallback) when the data cannot support a
    result: a required table or column is missing, the channel's respondent subset is
    empty, a segment in that subset has no rows in the price-sensitivity data, or price
    falls outside OBSERVED_PRICE_SUPPORT. The API returns a caveat instead of a number and no verdict."""

class AcceptanceDataError(Exception):
    """Raised by acceptance_rate() when the data cannot support a result — see docstring."""


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


# api/index.py — public API
# Validates public input, imports official modules, and returns aggregated results only.
# public/ — web interface only. Contains no business arithmetic and never reads CSV files.
```

Shared constants live in one place and are named, never inlined:

```python
BLENDED_CAC_EUR = 44.0
TARGET_LTV_CAC = 3.0
DEFAULT_PAYBACK_HORIZON_MONTHS = 12.0
ACCEPTANCE_FLOOR = 0.35   # provisional, team to confirm
SALES_CHANNELS = ("DTC Online", "Retail/Grocery", "Gym & Office")
PUBLISHED_TEST_PRICES = (1.79, 2.19, 2.59)   # prices price_test_results.csv actually tested
OBSERVED_PRICE_SUPPORT = (0.62, 3.09)         # min(cheap_eur), max(expensive_eur) in the data
ACCEPTANCE_MONOTONE_FLOOR_EUR = 2.10          # monotonicity only holds at/above this price
```

### 5a. Amendment — acceptance.py (Task B plan review, 2026-09-11)

| Price | DTC Online | Retail/Grocery | Gym & Office | Unweighted diagnostic |
|---:|---:|---:|---:|---:|
| EUR 1.79 | 0.530427 | 0.621350 | 0.682448 | 0.616667 |
| EUR 2.19 | 0.654800 | 0.437131 | 0.541966 | 0.516667 |
| EUR 2.59 | 0.436370 | 0.203726 | 0.237755 | 0.266667 |

1. **Metric semantics changed.** acceptance_rate() is a price-acceptability index, not a
   purchase probability. See the updated docstring above.
2. **Monotonicity requirement narrowed.** The original "acceptance falls as price rises in
   every channel" is replaced by: monotone non-increasing only at or above
   ACCEPTANCE_MONOTONE_FLOOR_EUR (2.10). Below that, behaviour is non-monotone by a
   verified property of the underlying survey data, not an implementation defect.
3. **Cross-module aggregation constraint on economics.py.** Acceptability and purchase
   frequency covary by segment. economics.py must NOT multiply a channel-level
   acceptance_rate() result by a separately-computed channel-level mean purchase frequency
   — that computes a product of averages where the correct quantity is an average of
   products, understating expected units by up to ~21% in the worst observed case
   (Retail/Grocery at EUR 2.59). economics.py must either (a) expose and use a
   segment-resolved helper computing sum(weight_segment * acceptance_segment *
   frequency_segment), or (b) if it never multiplies the two aggregated values, document
   why not. Task C's owner must read this before finishing economics.py.
4. **Fallback replaced by a raised error.** The original flat-rate fallback for a missing
   segment is removed. acceptance_rate() raises AcceptanceDataError instead — see the
   docstring above for exactly when.

> **Temporary development warning:** Task A is not merged yet. Until it is available,
> Task B may use simulated DataFrames only in tests. Simulated data does not prove final
> correctness. Task B is not complete until `acceptance_rate()` passes an integration check
> using the real DataFrames returned by `data_loader.load_all()`.

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

**Published test acceptance is uniform across sales channels, and that is the opening.**
`price_test_results.csv` reports the same test acceptance at each price regardless of channel
(61.7% at €1.79, 51.7% at €2.19, 26.7% at €2.59). But segments differ in price sensitivity and in
preferred channel: of ~420 survey respondents, 195 prefer Retail/Grocery, 119 DTC Online, 106 Gym
& Office, and Students & Budget-Conscious is the largest segment at 135. Recomputing
segment-weighted price acceptability per channel is the analytical contribution the brief deliberately
left unblended, and it is why `acceptance.py` exists as its own module.

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
- acceptance.py raises AcceptanceDataError (not a silent fallback or a bare float) for any
  input the data cannot support, and `api/index.py` returns a safe caveat for the web interface.
- Every team member's prompt log is committed and merged. Work that is not merged does not exist.

## 11. Implemented decision record

The deployed prototype supports one to three temporary browser-only scenarios. One selected
scenario is the baseline for detailed analysis; comparison scenarios are shown relative to it.
The backend returns aggregated results only, including the verdict, decision metrics, CMO and CFO
perspectives, observed competitor context, optional sensitivity and launch-month analysis, and
single-variable model adjustments where a baseline does not pass.

The runtime excludes \`respondent_id\`, \`first_name\`, \`last_name\`, and \`email\` before the survey is
used. Public endpoints do not serve CSV files or raw survey rows. The browser contains presentation
logic only; business calculations remain in Python. The stable public deployment is
\`https://lumen-g27.vercel.app\`. Managers can print an evaluated record with the browser's native
print dialog; the record includes inputs, decision context, metrics, sources, timestamp, and URL.
