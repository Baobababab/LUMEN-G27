"""Streamlit interface for the LUMEN launch-scenario decision modules."""

from calendar import month_name
from math import isfinite

import streamlit as st

from acceptance import AcceptanceDataError, acceptance_rate
from constants import ACCEPTANCE_FLOOR, BLENDED_CAC_EUR, DEFAULT_PAYBACK_HORIZON_MONTHS, OBSERVED_PRICE_SUPPORT, SALES_CHANNELS, TARGET_LTV_CAC
from data_loader import cleaning_report
from economics import customer_lifetime_months, ltv, ltv_cac_ratio, monthly_contribution, payback_months, unit_contribution
from verdict import verdict


st.set_page_config(page_title="LUMEN Scenario Cockpit", page_icon="◈", layout="wide")


def money(value: float) -> str:
    """Format an already-calculated monetary metric for display."""
    return f"EUR {value:,.2f}"


def positive_finite_number(text: str, label: str) -> float | None:
    """Validate a user-entered positive finite number before module calls."""
    if not text.strip():
        st.error(f"Enter a {label}.")
        return None
    try:
        value = float(text)
    except ValueError:
        st.error(f"{label.capitalize()} must be a number.")
        return None
    if not isfinite(value) or value <= 0:
        st.error(f"{label.capitalize()} must be a positive, finite number.")
        return None
    return value


def show_data_quality() -> None:
    """Show only the official loader's cleaning report."""
    with st.expander("Data quality and cleaning", expanded=False):
        try:
            report = cleaning_report()
        except (RuntimeError, ValueError, KeyError):
            st.warning("The data-quality report is unavailable right now.")
            return
        st.json(report)


st.title("LUMEN scenario cockpit")
st.caption("Evaluate a proposed German launch scenario using the project’s official analysis modules.")

price_text = st.text_input("Retail price (EUR)", value="2.19")
channel = st.selectbox("Supported sales channel", SALES_CHANNELS)
month = st.selectbox("Launch month", range(1, 13), format_func=lambda value: month_name[value])
horizon_text = st.text_input("Payback horizon (months)", value=str(DEFAULT_PAYBACK_HORIZON_MONTHS))

price = positive_finite_number(price_text, "retail price")
horizon = positive_finite_number(horizon_text, "payback horizon")

if price is not None and horizon is not None:
    if channel not in SALES_CHANNELS:
        st.error("Choose a supported sales channel.")
    elif month not in range(1, 13):
        st.error("Choose a launch month from January through December.")
    else:
        try:
            acceptance = acceptance_rate(price, channel)
            metrics = {
                "Acceptance rate": f"{acceptance:.1%}",
                "Unit contribution": money(unit_contribution(price, channel)),
                "Monthly contribution": money(monthly_contribution(price, channel, month)),
                "Lifetime value": money(ltv(price, channel)),
                "LTV:CAC ratio": f"{ltv_cac_ratio(price, channel):.2f}x",
                "CAC payback": f"{payback_months(price, channel, month):.2f} months",
            }
            decision = verdict(price, channel, month, horizon)
        except AcceptanceDataError as error:
            st.warning("Acceptance evidence is unavailable for this scenario. The acceptance value and launch verdict are therefore not shown.")
            st.caption(str(error))
        except (ValueError, RuntimeError, KeyError):
            st.error("This scenario could not be evaluated with the available business data.")
        else:
            st.subheader("Official metrics")
            columns = st.columns(3)
            for index, (label, value) in enumerate(metrics.items()):
                columns[index % 3].metric(label, value)

            st.subheader(f"{decision['verdict']} recommendation")
            st.write(f"**Decision driver:** {decision['decided_by']}")
            st.write(decision["trade_off"])
            st.write("**Decision checks**")
            for reason in decision["reasons"]:
                st.write(f"- {reason}")

            st.subheader("Assumptions and thresholds")
            st.write(
                f"Selected payback horizon: **{decision['metrics']['payback_horizon_months']:.2f} months**. "
                f"Blended acquisition cost: **{money(BLENDED_CAC_EUR)}**. "
                f"Derived customer lifetime: **{customer_lifetime_months():.1f} months**. "
                f"LTV:CAC threshold: **{TARGET_LTV_CAC:.2f}x**. "
                f"Acceptance threshold: **{ACCEPTANCE_FLOOR:.0%}**. "
                f"Observed price support: **EUR {OBSERVED_PRICE_SUPPORT[0]:.2f}–{OBSERVED_PRICE_SUPPORT[1]:.2f}**."
            )

show_data_quality()
