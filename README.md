# LUMEN — Pricing & Go-to-Market Case — ATELIA × ESCP Starter Kit

> This repo is your starting point. Codex should read this README first.

## How to Get Started

This repo is a **template**: click **Fork** (top right), not "Use this template." Fork keeps your copy linked back to the original — that's what lets ATELIA automatically find every team's work, without anyone needing to send a link.

Once you've forked it, add your teammates as collaborators (Settings → Collaborators on your fork), and leave the visibility as **Public** — don't switch it to Private, or we lose access to your work.

## The Brief

The full brief is in `LUMEN_Case_Brief.md` (and a formatted version in `LUMEN_Case_Brief.pdf`). The data is in the `data/` folder, documented in `data/README_data.md`.

Before using or publishing any case data, read [`DATA_CONFIDENTIALITY.md`](DATA_CONFIDENTIALITY.md).
The recommended internal and external data sources are listed in [`DATA_PLAN.md`](DATA_PLAN.md).

One-sentence summary: LUMEN, a functional beverage brand, has to decide **price, positioning, and launch channel(s)** to enter the German market — with no real German sales data (LUMEN isn't there yet), and a real trade-off between the CMO (premium positioning) and the CFO (fast return on investment).

## Run Locally

Use Python 3.12 and install the project dependencies:

```bash
python -m pip install -r requirements.txt
vercel dev
```

Open the local URL printed by Vercel. The public page is served from `public/`; `api/index.py` calculates scenarios on the same origin.

## Rule #1 — Prompt Logging Is Automatic

This repo includes an `AGENTS.md` file, which Codex reads automatically at the start of every task — you don't need to open or edit it. The first time you talk to Codex in a new conversation, it will ask for your **student ID**. Answer it, and from then on Codex logs every prompt you send it — automatically, verbatim — into `prompts/<your-id>/session-*.md`, without you doing anything else.

**You don't fill this in by hand.** Your only job is to make sure that log file gets committed along with your code changes — Codex writes it, but you still need to include it when your pull request is created and merged. If a pull request only has code changes and no updated log file, that's a sign something didn't get logged.

Why we're doing this: it's not to monitor you. It's what lets us understand, at the end, how you reasoned — not just what you produced. A good result reached with a clear prompt from the start isn't scored the same as a good result reached after fifteen random attempts.

## Rule #2 — Before You Code, Ask Yourself These Questions

Check each box in this README as you go — not at the end, while you're working:

- [x] **Data**: `data/customer_survey.csv` is unchanged from the public `ateliaworkshop-ai/lumen-pricing-case-template`. The runtime excludes `respondent_id`, `first_name`, `last_name`, and `email` before loading the survey. The tool uses only aggregated analysis fields, and public API responses never return survey rows or identifiers. The case owner must confirm the dataset's synthetic or authorised status before any reuse outside this workshop.
- [x] **API keys**: we do not use external APIs or keys. Launch-month analysis uses only the supplied `seasonality_and_weather.csv`; it does not call a weather service.
- [x] **Deployment**: public scenario and comparison responses contain only aggregated metrics, explanations, observed competitor references, and optional aggregated model analysis. CSV files and survey rows have no public route.
- [ ] **Files generated along the way**: if your tool (or Codex) created new files derived from the provided data, did you think about whether they should be committed to the repo or not?
- [x] **Storage**: the browser keeps up to three scenario inputs only while the page is open. We use this temporary session state because comparison needs no account, database, history, export, or personal data.
- [x] **Robustness**: browser inputs restrict price to the observed EUR 0.62–3.09 support. The API validates scenario fields, a maximum of three scenarios, and the selected baseline; invalid input receives a safe 422 response without echoing it.
- [x] **Explainability**: each decision metric shows its business meaning, status, threshold comparison where approved, and an expandable explanation of formula, source, assumptions, and limits. The browser renders backend-provided metadata and does not calculate business logic.
- [x] **Business relevance**: the tool shows one decision verdict, channel trade-offs, price sensitivity within observed support, supplied seasonal context, and up to three single-variable model adjustments for scenarios that do not pass. It labels these outputs as model analysis, not demand forecasts.

These questions aren't here to slow you down — they're part of what's being evaluated. A thoughtful answer to one of them is worth more than an extra feature nobody asked for.

## What We Expect at the End

- A prototype that works, even partially, on the LUMEN case
- Your prompt log (`prompts/<your-id>/session-*.md`) committed and up to date
- A short paragraph below, written in business language (not technical), explaining what you did and why
- A live URL (Vercel or similar) if you deployed it — not required to still get credit, but expected if you did

## Our Approach

LUMEN needs a defensible German launch scenario, not a generic calculator. Our tool lets a manager test a retail price, sales channel, launch month, and payback horizon. It combines channel economics, customer price acceptability, seasonality, and lifetime value to customer acquisition cost into one transparent GO, CONDITIONAL, or NO-GO verdict. It also shows the same scenario through CMO and CFO perspectives, without creating competing verdicts. On request, the selected baseline also shows model price sensitivity and launch-month context. A manager can print the evaluated inputs, decision, trade-off, metrics, sources, timestamp, and page URL through the browser print dialog. We deliberately show the trade-off between customer reach and financial return, exclude personal data, and publish only aggregated results.

## Price sensitivity and launch month

Price sensitivity evaluates one selected baseline scenario only, on request. It scans the supplied EUR 0.62–3.09 observed support and groups consecutive evaluated prices that keep the same verdict. It does not use binary search because price acceptability can rise below EUR 2.10 before falling.

The grid is EUR 0.02. The selected price and both support endpoints are always evaluated, for at most 126 evaluations per request (below the hard 250-evaluation limit). On 2026-09-16 with Python 3.11, warmed local data cache, DTC Online, July, and a 12-month horizon, three scans measured median latencies of 3,901 ms at EUR 0.01 (248 evaluations), 1,892 ms at EUR 0.02 (125 grid evaluations), and 768 ms at EUR 0.05 (51 grid evaluations). We set a 2,500 ms response budget and chose EUR 0.02 as the most precise tested step within it. Grid resolution is not economic precision and the result is not a demand forecast.

Launch-month analysis ranks the supplied twelve `seasonality_and_weather.csv` indices with price, channel, and payback horizon fixed. It reports the selected month, its seasonal rank, contribution and payback change against the most favourable supplied month or tied window. It does not use live weather or infer causal demand effects.

## Model adjustments

For a `CONDITIONAL` or `NO-GO` selected baseline, the backend tests supported price points, other official channels, and other launch months. Each candidate changes one variable only. It ranks candidates by verdict, fewer failed approved thresholds, and smaller normalized distance from those thresholds; ties use price, then channel, then month order. At the end of the results, “Ways to improve this scenario” explains up to three supported changes in business language, including what stays fixed and any trade-off. A `GO` scenario instead confirms that no corrective adjustment is needed. These are model adjustments, not commercial promises.
