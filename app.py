"""Streamlit interface for the LUMEN Germany market-entry scenario."""

import calendar
import math
from collections.abc import Callable
from typing import Any

import streamlit as st

from acceptance import acceptance_rate
from constants import (
    ACCEPTANCE_FLOOR,
    BLENDED_CAC_EUR,
    DEFAULT_PAYBACK_HORIZON_MONTHS,
    SALES_CHANNELS,
    TARGET_LTV_CAC,
)
from data_loader import cleaning_report
from economics import (
    customer_lifetime_months,
    ltv,
    ltv_cac_ratio,
    monthly_contribution,
    payback_months,
    unit_contribution,
)
from verdict import verdict


LAUNCH_MONTHS = tuple(range(1, 13))
# UI affordance only; this range is not a model threshold or business rule.
PAYBACK_HORIZON_UI_RANGE = (1, 24)


def _parse_price(raw_price: str) -> tuple[float | None, str | None]:
    """Parse and validate the user-entered retail price without calculating business metrics."""
    if not raw_price.strip():
        return None, "Enter a retail price to evaluate the scenario."

    try:
        price = float(raw_price)
    except ValueError:
        return None, "Retail price must be a number, for example 2.19."

    if not math.isfinite(price):
        return None, "Retail price must be a finite number."
    if price <= 0:
        return None, "Retail price must be greater than zero."

    return price, None


def _safe_call(function: Callable[..., Any], *args: Any) -> tuple[Any | None, str | None]:
    """Call a contract function and turn incomplete-module failures into UI messages."""
    try:
        return function(*args), None
    except NotImplementedError:
        return None, "This module is not implemented yet."
    except (KeyError, TypeError, ValueError) as error:
        return None, f"The selected scenario is not available: {error}"
    except Exception as error:  # Keep the page usable for unexpected data issues.
        return None, f"The selected scenario could not be evaluated: {error}"


def _format_metric(value: Any, suffix: str = "") -> str:
    """Format a returned metric for display without changing its value."""
    if value is None:
        return "Unavailable"
    if isinstance(value, float):
        return f"{value:,.2f}{suffix}"
    return f"{value}{suffix}"


def _show_metric(label: str, value: Any, explanation: str, suffix: str = "") -> None:
    """Render one labelled metric and its plain-English explanation."""
    st.metric(label, _format_metric(value, suffix))
    st.caption(explanation)


st.set_page_config(page_title="LUMEN Germany Market Entry", page_icon="🥤")
st.title("LUMEN Germany Market Entry")
st.write(
    "Set a price, channel, and launch month to see the per-customer economics "
    "of the scenario."
)


st.subheader("Scenario inputs")
price_text = st.text_input("Retail price (€)", placeholder="For example: 2.19")
channel = st.selectbox("Sales channel", options=SALES_CHANNELS)
launch_month = st.selectbox(
    "Launch month",
    options=LAUNCH_MONTHS,
    format_func=lambda month: calendar.month_name[month],
)
payback_horizon = st.slider(
    "Payback horizon (months)",
    min_value=PAYBACK_HORIZON_UI_RANGE[0],
    max_value=PAYBACK_HORIZON_UI_RANGE[1],
    value=int(DEFAULT_PAYBACK_HORIZON_MONTHS),
    step=1,
    help="This is captured for the verdict layer; this milestone does not calculate a verdict.",
)


price, price_error = _parse_price(price_text)
input_error = price_error
if launch_month not in LAUNCH_MONTHS:
    input_error = "Choose a launch month from January through December."

if input_error:
    st.warning(input_error)


st.subheader("Decision verdict")
if price is None or input_error is not None:
    st.info("Verdict unavailable until all scenario inputs are valid.")
else:
    verdict_result, verdict_error = _safe_call(
        verdict,
        price,
        channel,
        launch_month,
        payback_horizon,
    )
    if verdict_error:
        st.info(f"Verdict not available yet: {verdict_error}")
    elif verdict_result is None:
        st.info("Verdict unavailable for this scenario.")
    else:
        st.metric("Verdict", verdict_result.get("verdict", "Unavailable"))
        st.write("Decided by:", verdict_result.get("decided_by", "Unavailable"))
        st.write("Reasons:")
        reasons = verdict_result.get("reasons")
        if reasons:
            for reason in reasons:
                st.write(f"- {reason}")
        else:
            st.write("Unavailable")
        st.write("Trade-off:", verdict_result.get("trade_off", "Unavailable"))
        st.write("Returned metrics:")
        returned_metrics = verdict_result.get("metrics")
        if returned_metrics:
            st.json(returned_metrics)
        else:
            st.write("Unavailable")


st.subheader("Scenario economics")
metric_definitions = (
    (
        "Unit contribution",
        unit_contribution,
        "Net contribution from one unit after the channel-specific unit cost.",
        " €",
    ),
    (
        "Acceptance rate",
        acceptance_rate,
        "The estimated share of the selected channel's segments likely to buy at this price.",
        "",
    ),
    (
        "Monthly contribution per customer",
        monthly_contribution,
        "The contribution this customer is expected to generate in one month.",
        " €",
    ),
    (
        "Months to payback",
        payback_months,
        "How long before this customer has repaid what we spent to acquire them.",
        " months",
    ),
    (
        "Lifetime value",
        ltv,
        "The expected contribution from this customer over the derived customer lifetime.",
        " €",
    ),
    (
        "LTV:CAC ratio",
        ltv_cac_ratio,
        "How much lifetime contribution we expect for each euro spent acquiring the customer.",
        "",
    ),
)

metric_values: dict[str, Any] = {}
metric_errors: list[str] = []
if price is not None and input_error is None:
    for label, function, _explanation, _suffix in metric_definitions:
        if label in {"Monthly contribution per customer", "Months to payback"}:
            value, error = _safe_call(function, price, channel, launch_month)
        else:
            value, error = _safe_call(function, price, channel)
        metric_values[label] = value
        if error and error not in metric_errors:
            metric_errors.append(error)

columns = st.columns(3)
for index, (label, _function, explanation, suffix) in enumerate(metric_definitions):
    with columns[index % len(columns)]:
        _show_metric(label, metric_values.get(label), explanation, suffix)

for error in metric_errors:
    st.info(error)


st.subheader("Stated assumptions")
lifetime, lifetime_error = _safe_call(customer_lifetime_months)
assumption_columns = st.columns(2)
with assumption_columns[0]:
    st.metric("Derived customer lifetime", _format_metric(lifetime, " months"))
    st.caption("Back-solved from the home-market LTV data and held constant across scenarios.")
with assumption_columns[1]:
    st.metric("Blended acquisition cost", _format_metric(BLENDED_CAC_EUR, " €"))
    st.caption("The acquisition cost assumption used by the economics module.")
if lifetime_error:
    st.info(lifetime_error)
st.caption(
    "Display-only thresholds from the model contract: "
    f"target LTV:CAC {TARGET_LTV_CAC}; acceptance floor {ACCEPTANCE_FLOOR:.2f}."
)


with st.expander("Data quality and cleaning report"):
    report, report_error = _safe_call(cleaning_report)
    if report_error:
        st.info(report_error)
    elif report is not None:
        st.write("Duplicate rows removed:", report.get("duplicate_rows_removed", "Unavailable"))
        st.write("Personal-data columns excluded:", report.get("pii_columns_excluded", "Unavailable"))
        st.write("Anomaly weeks flagged:", report.get("anomaly_weeks_flagged", "Unavailable"))
from pathlib import Path

import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).parent / "data"
CUSTOMER_LIFETIME_MONTHS = 12
LTV_CAC_TARGET = 3.0
PAYBACK_TARGET_MONTHS = 12.0
ACCEPTANCE_FLOOR = 0.40


st.set_page_config(
    page_title="LUMEN Scenario Cockpit",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data
def load_data():
    price_tests = pd.read_csv(DATA_DIR / "price_test_results.csv")
    customers = pd.read_csv(DATA_DIR / "customer_survey.csv")
    funnel = pd.read_csv(DATA_DIR / "marketing_funnel_monthly.csv", parse_dates=["month"])
    seasonality = pd.read_csv(DATA_DIR / "seasonality_and_weather.csv")
    return price_tests, customers, funnel, seasonality


def money(value):
    return f"EUR {value:,.2f}"


def metric_card(label, value, detail="", accent=False):
    accent_class = " accent" if accent else ""
    return f"""
    <div class="metric-card{accent_class}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-detail">{detail}</div>
    </div>
    """


st.markdown(
    """
    <style>
    :root {
      --ink: #211d2b;
      --muted: #756f82;
      --line: #ebe7f3;
      --purple: #6d4aff;
      --purple-soft: #f3efff;
      --green: #19724b;
      --amber: #9a6710;
      --red: #a13745;
    }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
      background: #ffffff;
    }
    .block-container {
      max-width: 1180px;
      padding-top: 2.25rem;
      padding-bottom: 3rem;
    }
    h1, h2, h3, p, label, [data-testid="stMarkdownContainer"] {
      color: var(--ink);
    }
    h1 {
      font-size: 2.1rem !important;
      letter-spacing: 0 !important;
      margin-bottom: 0.25rem !important;
    }
    .eyebrow {
      color: var(--purple);
      font-size: 0.74rem;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 0.45rem;
    }
    .subtitle {
      color: var(--muted);
      font-size: 0.98rem;
      margin-bottom: 1.8rem;
    }
    .control-strip {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 1rem 1.15rem 0.45rem;
      background: #fff;
      margin-bottom: 1.25rem;
    }
    .section-label {
      color: var(--muted);
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin: 0.35rem 0 0.5rem;
    }
    div[data-baseweb="select"] > div {
      border-color: #d9d2ed;
      border-radius: 6px;
    }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 0.75rem;
      margin: 0.75rem 0 1.5rem;
    }
    .metric-card {
      border: 1px solid var(--line);
      border-top: 3px solid #dcd5eb;
      border-radius: 8px;
      padding: 1rem 1rem 0.9rem;
      min-height: 126px;
      background: #fff;
    }
    .metric-card.accent {
      border-top-color: var(--purple);
      background: var(--purple-soft);
    }
    .metric-label {
      color: var(--muted);
      font-size: 0.74rem;
      font-weight: 700;
      line-height: 1.25;
      min-height: 2.1em;
    }
    .metric-value {
      color: var(--ink);
      font-size: 1.45rem;
      font-weight: 800;
      line-height: 1.2;
      margin-top: 0.55rem;
      white-space: nowrap;
    }
    .metric-detail {
      color: var(--muted);
      font-size: 0.72rem;
      line-height: 1.35;
      margin-top: 0.42rem;
    }
    .verdict {
      border-radius: 8px;
      padding: 0.8rem 1rem;
      margin: 0.25rem 0 1.5rem;
      border: 1px solid var(--line);
      background: #faf9fc;
    }
    .verdict.go { border-left: 4px solid var(--green); }
    .verdict.conditional { border-left: 4px solid var(--amber); }
    .verdict.no-go { border-left: 4px solid var(--red); }
    .verdict-title { font-weight: 800; margin-bottom: 0.2rem; }
    .verdict-copy { color: var(--muted); font-size: 0.87rem; }
    .small-note {
      color: var(--muted);
      font-size: 0.78rem;
      line-height: 1.45;
    }
    @media (max-width: 900px) {
      .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 560px) {
      .block-container { padding-top: 1.25rem; }
      h1 { font-size: 1.65rem !important; }
      .metric-grid { grid-template-columns: 1fr; }
      .metric-card { min-height: 112px; }
      .metric-value { white-space: normal; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


price_tests, customers, funnel, seasonality = load_data()
prices = sorted(price_tests["price_eur"].unique())
channels = ["DTC Online", "Retail/Grocery", "Gym & Office"]
months = list(range(1, 13))
month_names = dict(zip(months, pd.to_datetime([f"2026-{m:02d}-01" for m in months]).strftime("%B")))


st.markdown('<div class="eyebrow">LUMEN / Germany launch</div>', unsafe_allow_html=True)
st.title("Scenario cockpit")
st.markdown(
    '<div class="subtitle">Choose one launch scenario and see the economics update instantly.</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="control-strip">', unsafe_allow_html=True)
st.markdown('<div class="section-label">Scenario inputs</div>', unsafe_allow_html=True)
control_cols = st.columns(3)
with control_cols[0]:
    selected_price = st.selectbox(
        "Launch price",
        prices,
        index=prices.index(2.19),
        format_func=lambda value: f"EUR {value:.2f}",
    )
with control_cols[1]:
    selected_channel = st.selectbox("Sales channel", channels, index=2)
with control_cols[2]:
    selected_month = st.selectbox(
        "Launch month",
        months,
        index=4,
        format_func=lambda value: month_names[value],
    )
st.markdown("</div>", unsafe_allow_html=True)

compare_button_slot = st.empty()


selected_test = price_tests[
    (price_tests["price_eur"] == selected_price)
    & (price_tests["channel"] == selected_channel)
].iloc[0]

month_row = seasonality[seasonality["month"] == selected_month].iloc[0]
month_funnel = funnel[funnel["month"].dt.month == selected_month]
blended_cac = month_funnel["spend_eur"].sum() / month_funnel["conversions_customers_acquired"].sum()
survey_frequency = customers["purchase_frequency_per_month"].mean()
unit_contribution = float(selected_test["unit_contribution_eur"])
acceptance = float(selected_test["estimated_acceptance_pct_of_survey"]) / 100
seasonality_factor = float(month_row["seasonality_index_100_avg"]) / 100
monthly_profit = unit_contribution * survey_frequency * seasonality_factor
payback_months = blended_cac / monthly_profit if monthly_profit else float("inf")
clv = monthly_profit * CUSTOMER_LIFETIME_MONTHS
clv_cac_ratio = clv / blended_cac if blended_cac else 0

scenario_key = (round(float(selected_price), 2), selected_channel, selected_month)
scenario_label = f"EUR {selected_price:.2f} · {selected_channel} · {month_names[selected_month]}"
scenario_metrics = {
    "Profit per unit": unit_contribution,
    "Monthly profit per customer": monthly_profit,
    "Break-even on CAC": payback_months,
    "CLV vs CAC": clv,
    "CLV:CAC ratio": clv_cac_ratio,
}
if "comparison_scenarios" not in st.session_state:
    st.session_state.comparison_scenarios = []

with compare_button_slot:
    if st.button("Compare on a histogram", type="secondary", width="stretch"):
        already_added = any(item["key"] == scenario_key for item in st.session_state.comparison_scenarios)
        if already_added:
            st.info("This scenario is already in the comparison.")
        else:
            st.session_state.comparison_scenarios.append(
                {
                    "key": scenario_key,
                    "label": scenario_label,
                    **scenario_metrics,
                }
            )
            st.success(f"Added {scenario_label} to the comparison.")

passed = [
    clv_cac_ratio >= LTV_CAC_TARGET,
    payback_months <= PAYBACK_TARGET_MONTHS,
    acceptance >= ACCEPTANCE_FLOOR,
]
if all(passed):
    verdict, verdict_class = "GO", "go"
    tradeoff = "This scenario clears the working acceptance, payback, and LTV:CAC thresholds."
elif sum(passed) >= 2:
    verdict, verdict_class = "CONDITIONAL", "conditional"
    tradeoff = "This scenario is close to the thresholds; the result depends on the assumptions shown below."
else:
    verdict, verdict_class = "NO-GO", "no-go"
    tradeoff = "This scenario misses more than one working threshold and needs a different price, channel, or month."


kpi_cols = st.columns(5)
kpi_cards = [
    metric_card("Profit per unit", money(unit_contribution), f"{selected_channel} contribution", True),
    metric_card("Monthly profit per customer", money(monthly_profit), f"{survey_frequency:.1f} purchases/month"),
    metric_card("Break-even on CAC", f"{payback_months:.1f} months", f"CAC: {money(blended_cac)}"),
    metric_card("CLV vs CAC", money(clv), f"CAC: {money(blended_cac)}"),
    metric_card("CLV:CAC ratio", f"{clv_cac_ratio:.1f}x", f"Target: {LTV_CAC_TARGET:.1f}x", True),
]
for column, card in zip(kpi_cols, kpi_cards):
    with column:
        st.markdown(card, unsafe_allow_html=True)


if st.session_state.comparison_scenarios:
    st.divider()
    st.subheader("Scenario comparison")
    st.markdown(
        '<div class="small-note">Choose the outputs to compare. Each bar represents one saved price, channel, and launch-month scenario.</div>',
        unsafe_allow_html=True,
    )
    comparison_options = list(scenario_metrics.keys())
    selected_metrics = st.multiselect(
        "Outputs to compare",
        comparison_options,
        default=comparison_options[:2],
    )
    if selected_metrics:
        comparison_df = pd.DataFrame(st.session_state.comparison_scenarios).rename(
            columns={"label": "Scenarios"}
        )
        st.bar_chart(
            comparison_df,
            x="Scenarios",
            y=selected_metrics,
            x_label="Scenarios",
            y_label="Value",
            stack=False,
            height=420,
            width="stretch",
        )
        st.caption("Values retain their original units: EUR, months, or ratio.")
    else:
        st.info("Select at least one output to display the histogram.")

    if st.button("Clear comparison", type="secondary"):
        st.session_state.comparison_scenarios = []
        st.rerun()

st.markdown(
    f'<div class="verdict {verdict_class}">'
    f'<div class="verdict-title">{verdict} · {month_names[selected_month]} launch at EUR {selected_price:.2f}</div>'
    f'<div class="verdict-copy">{tradeoff}</div>'
    "</div>",
    unsafe_allow_html=True,
)


detail_cols = st.columns([1.15, 1])
with detail_cols[0]:
    st.subheader("Calculation trail")
    trail = pd.DataFrame(
        {
            "Measure": [
                "Selected price",
                "Estimated acceptance",
                "Unit contribution",
                "Survey purchase frequency",
                "Seasonality factor",
                "Blended CAC for launch month",
                "Customer lifetime assumption",
            ],
            "Value": [
                f"EUR {selected_price:.2f}",
                f"{acceptance:.1%}",
                money(unit_contribution),
                f"{survey_frequency:.1f} purchases/month",
                f"{seasonality_factor:.2f}x",
                money(blended_cac),
                f"{CUSTOMER_LIFETIME_MONTHS} months",
            ],
        }
    )
    st.dataframe(trail, hide_index=True, width="stretch")

with detail_cols[1]:
    st.subheader("Thresholds")
    threshold_rows = pd.DataFrame(
        {
            "Check": ["Acceptance", "Payback", "CLV:CAC"],
            "Scenario": [f"{acceptance:.1%}", f"{payback_months:.1f} months", f"{clv_cac_ratio:.1f}x"],
            "Working threshold": [f">= {ACCEPTANCE_FLOOR:.0%}", f"<= {PAYBACK_TARGET_MONTHS:.0f} months", f">= {LTV_CAC_TARGET:.1f}x"],
        }
    )
    st.dataframe(threshold_rows, hide_index=True, width="stretch")
    st.markdown(
        '<div class="small-note">CLV is contribution-based: seasonally adjusted monthly customer profit multiplied by the visible 12-month lifetime assumption. CAC is the blended marketing CAC for the selected calendar month.</div>',
        unsafe_allow_html=True,
    )

st.divider()
st.markdown(
    '<div class="small-note">Sources: price test results, customer survey, marketing funnel, and seasonality data in the repository. Customer names, emails, and respondent IDs are not loaded.</div>',
    unsafe_allow_html=True,
)
