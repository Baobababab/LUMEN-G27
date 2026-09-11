"""Streamlit interface for the LUMEN Germany market-entry scenario."""

import calendar
import math
from collections.abc import Callable
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from acceptance import acceptance_rate
from constants import (
    ACCEPTANCE_FLOOR,
    BLENDED_CAC_EUR,
    DEFAULT_PAYBACK_HORIZON_MONTHS,
    SALES_CHANNELS,
    TARGET_LTV_CAC,
)
from data_loader import cleaning_report, load_all
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


st.set_page_config(page_title="LUMEN — Germany Launch Decision Tool", page_icon="🥤")
st.title("LUMEN — Germany Launch Decision Tool")
st.write(
    "Explore how price, channel and launch timing affect the economics of the "
    "German market entry."
)
st.markdown(
    """
    <style>
    :root {
        --lumen-navy: #123047;
        --lumen-teal: #2f6f73;
        --lumen-ink: #243746;
        --lumen-muted: #64748b;
        --lumen-line: #dce5e8;
        --lumen-surface: #ffffff;
        --lumen-background: #f7f8f6;
    }
    .stApp { background: var(--lumen-background); color: var(--lumen-ink); }
    .block-container { max-width: 1100px; padding: 2.75rem 2.5rem 4rem; }
    [data-testid="stSidebar"] {
        background: #eef3f2;
        border-right: 1px solid var(--lumen-line);
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.8rem; }
    h1 { color: var(--lumen-navy); letter-spacing: -0.03em; margin-bottom: 0.35rem; }
    h2 { color: var(--lumen-navy); letter-spacing: -0.02em; margin-top: 2rem; }
    h3 { color: var(--lumen-teal); margin-top: 1.35rem; }
    p, [data-testid="stCaptionContainer"] { color: var(--lumen-muted); }
    [data-testid="stMetric"] {
        background: var(--lumen-surface);
        border: 1px solid var(--lumen-line);
        border-radius: 12px;
        box-shadow: 0 4px 14px rgba(18, 48, 71, 0.05);
        min-height: 7.5rem;
        padding: 1.1rem 1.2rem;
    }
    [data-testid="stMetricLabel"] { color: var(--lumen-muted); font-size: 0.82rem; }
    [data-testid="stMetricValue"] { color: var(--lumen-navy); font-size: 1.65rem; }
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background: var(--lumen-surface);
        border-color: var(--lumen-line);
        border-radius: 8px;
    }
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--lumen-teal);
        box-shadow: 0 0 0 1px var(--lumen-teal);
    }
    [data-testid="stSlider"] [role="slider"] { background: var(--lumen-teal); }
    [data-testid="stExpander"] {
        background: var(--lumen-surface);
        border: 1px solid var(--lumen-line);
        border-radius: 10px;
    }
    [data-testid="stAlert"] { border-radius: 10px; }
    [data-testid="stMetric"] {
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("1. Choose your scenario")
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


st.subheader("Scenario summary")
summary_columns = st.columns(4)
with summary_columns[0]:
    st.caption("Retail price")
    st.write(_format_metric(price, " €"))
with summary_columns[1]:
    st.caption("Sales channel")
    st.write(channel)
with summary_columns[2]:
    st.caption("Launch month")
    st.write(calendar.month_name[launch_month])
with summary_columns[3]:
    st.caption("Payback horizon")
    st.write(f"{payback_horizon} months")


st.header("2. Review the verdict")
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
        verdict_label = verdict_result.get("verdict", "Unavailable")
        status_styles = {
            "GO": ("#1f7a3f", "#e8f5ed"),
            "CONDITIONAL": ("#a15c00", "#fff4df"),
            "NO-GO": ("#b42318", "#fdeceb"),
        }
        status_color, status_background = status_styles.get(
            verdict_label,
            ("#4b5563", "#f3f4f6"),
        )
        st.markdown(
            f'<div style="background:{status_background}; border-left:8px solid '
            f'{status_color}; border-radius:6px; padding:1rem 1.25rem; '
            f'margin-bottom:1rem;"><div style="color:{status_color}; '
            f'font-size:2rem; font-weight:700;">{verdict_label}</div>'
            '<div style="color:#4b5563; font-size:0.9rem;">Decision verdict</div></div>',
            unsafe_allow_html=True,
        )
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


st.header("3. Explore the economics")
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

metric_groups = (
    ("Demand", ("Acceptance rate",)),
    ("Contribution", ("Unit contribution", "Monthly contribution per customer")),
    (
        "Investment",
        ("Months to payback", "Lifetime value", "LTV:CAC ratio"),
    ),
)
for group_name, group_labels in metric_groups:
    st.subheader(group_name)
    columns = st.columns(len(group_labels))
    for index, label in enumerate(group_labels):
        definition = next(item for item in metric_definitions if item[0] == label)
        _label, _function, explanation, suffix = definition
        with columns[index]:
            _show_metric(label, metric_values.get(label), explanation, suffix)

for error in metric_errors:
    st.info(error)


st.subheader("Model assumptions")
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


st.subheader("Scenario comparison")
st.caption("Compare the available price and channel scenarios using the shared model functions.")
comparison_data, comparison_error = _safe_call(load_all)
if comparison_error:
    st.info(f"Scenario comparison not available yet: {comparison_error}")
elif comparison_data is not None:
    price_data = comparison_data.get("price_test_results")
    if isinstance(price_data, pd.DataFrame) and "price_eur" in price_data:
        comparison_rows: list[dict[str, Any]] = []
        comparison_prices = sorted(price_data["price_eur"].dropna().unique())
        for comparison_price in comparison_prices:
            for comparison_channel in SALES_CHANNELS:
                metric, metric_error = _safe_call(
                    unit_contribution,
                    float(comparison_price),
                    comparison_channel,
                )
                if metric_error is None and metric is not None:
                    comparison_rows.append(
                        {
                            "Scenario": f"€{float(comparison_price):.2f} · {comparison_channel}",
                            "Unit contribution (€)": metric,
                        }
                    )
        if comparison_rows:
            chart_data = pd.DataFrame(comparison_rows)
            chart = (
                alt.Chart(chart_data)
                .mark_bar()
                .encode(
                    x=alt.X("Unit contribution (€):Q", title="Unit contribution (€)"),
                    y=alt.Y("Scenario:N", sort="-x", title=None),
                    tooltip=["Scenario:N", "Unit contribution (€):Q"],
                )
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Scenario comparison will appear when the economics module is implemented.")
    else:
        st.info("Scenario comparison will appear when price-test data is available.")


st.subheader("Thresholds")
st.table(
    pd.DataFrame(
        {
            "Metric": ["Acceptance rate", "Months to payback", "LTV:CAC ratio"],
            "Working threshold": [
                f">= {ACCEPTANCE_FLOOR:.0%}",
                f"<= {payback_horizon} months",
                f">= {TARGET_LTV_CAC:.1f}x",
            ],
        }
    )
)


with st.expander("Data quality"):
    report, report_error = _safe_call(cleaning_report)
    if report_error:
        st.info(report_error)
    elif report is not None:
        st.write("Duplicate rows removed:", report.get("duplicate_rows_removed", "Unavailable"))
        st.write("Personal-data columns excluded:", report.get("pii_columns_excluded", "Unavailable"))
        st.write("Anomaly weeks flagged:", report.get("anomaly_weeks_flagged", "Unavailable"))
