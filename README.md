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
- [ ] **API keys**: if your tool calls an external API (weather, or anything else), where is the key stored? Never hardcoded in a file committed to GitHub. (A valid answer: "we didn't use any external API.")
- [ ] **Deployment**: if you deployed a live demo, does any endpoint or response return raw, unfiltered data (e.g. the full survey with name/email) to any visitor?
- [ ] **Files generated along the way**: if your tool (or Codex) created new files derived from the provided data, did you think about whether they should be committed to the repo or not?
- [x] **Storage**: the browser keeps up to three scenario inputs only while the page is open. We use this temporary session state because comparison needs no account, database, history, export, or personal data.
- [ ] **Robustness**: what happens if the user gives an empty, inconsistent, or unexpected input?
- [x] **Explainability**: each decision metric shows its business meaning, status, threshold comparison where approved, and an expandable explanation of formula, source, assumptions, and limits. The browser renders backend-provided metadata and does not calculate business logic.
- [ ] **Business relevance**: does your prototype actually answer the problem posed in the brief, or is it an interesting technical build that's off-target?

These questions aren't here to slow you down — they're part of what's being evaluated. A thoughtful answer to one of them is worth more than an extra feature nobody asked for.

## What We Expect at the End

- A prototype that works, even partially, on the LUMEN case
- Your prompt log (`prompts/<your-id>/session-*.md`) committed and up to date
- A short paragraph below, written in business language (not technical), explaining what you did and why
- A live URL (Vercel or similar) if you deployed it — not required to still get credit, but expected if you did

## Our Approach

LUMEN needs a defensible German launch scenario, not a generic calculator. Our tool lets a manager test a retail price, sales channel, launch month, and payback horizon. It combines channel economics, customer price acceptability, seasonality, and lifetime value to customer acquisition cost into one transparent GO, CONDITIONAL, or NO-GO verdict. It also shows the same scenario through CMO and CFO perspectives, without creating competing verdicts. We deliberately show the trade-off between customer reach and financial return, exclude personal data, and publish only aggregated results.
