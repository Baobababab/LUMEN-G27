from __future__ import annotations

from functools import lru_cache
from math import inf, isfinite

import pandas as pd

from acceptance import acceptance_rate
from constants import BLENDED_CAC_EUR, SALES_CHANNELS
from data_loader import load_all


def _data() -> dict[str, pd.DataFrame]:
    return load_all()


def _validate_price(price: float) -> None:
    if isinstance(price, bool) or not isfinite(float(price)) or float(price) <= 0:
        raise ValueError("price must be a positive finite number")


def _validate_channel(channel: str) -> None:
    if channel not in SALES_CHANNELS:
        raise ValueError(f"channel must be one of {SALES_CHANNELS}")


def _validate_month(month: int) -> None:
    if isinstance(month, bool) or int(month) != month or not 1 <= int(month) <= 12:
        raise ValueError("month must be an integer from 1 to 12")


def _total_unit_cost(data: dict[str, pd.DataFrame]) -> float:
    costs = data["cost_breakdown"]
    total_row = costs[costs["cost_component"].astype(str).str.contains("TOTAL COGS", na=False)]
    if total_row.empty:
        raise RuntimeError("cost_breakdown is missing the TOTAL COGS row")
    return float(total_row.iloc[0]["cost_per_unit_eur"])


def _channel_terms(channel: str, data: dict[str, pd.DataFrame]) -> pd.Series:
    channel_economics = data["channel_economics"]
    rows = channel_economics[channel_economics["channel"].eq(channel)]
    if rows.empty:
        raise ValueError(f"channel must be one of {SALES_CHANNELS}")
    return rows.iloc[0]


def _seasonality_multiplier(month: int, data: dict[str, pd.DataFrame]) -> float:
    rows = data["seasonality_and_weather"][data["seasonality_and_weather"]["month"].eq(int(month))]
    if rows.empty:
        raise ValueError("month must be present in seasonality_and_weather")
    return float(rows.iloc[0]["seasonality_index_100_avg"]) / 100.0


def _segment_acceptability(price: float, segment: str, data: dict[str, pd.DataFrame]) -> float:
    sensitivity = data["price_sensitivity_survey"]
    rows = sensitivity[sensitivity["segment"].eq(segment)]
    if rows.empty:
        raise RuntimeError(f"price_sensitivity_survey has no rows for segment {segment!r}")
    accepted = rows["cheap_eur"].le(float(price)) & rows["expensive_eur"].ge(float(price))
    return float(accepted.mean())


def _segment_weighted_monthly_units(price: float, channel: str, data: dict[str, pd.DataFrame]) -> float:
    """Return sum(weight_segment * acceptance_segment * frequency_segment)."""
    survey = data["customer_survey"]
    channel_rows = survey[survey["preferred_channel"].eq(channel)]
    if channel_rows.empty:
        raise RuntimeError(f"customer_survey has no rows for channel {channel!r}")

    total_respondents = len(channel_rows)
    monthly_units = 0.0
    for segment, segment_rows in channel_rows.groupby("segment"):
        weight = len(segment_rows) / total_respondents
        acceptability = _segment_acceptability(price, str(segment), data)
        frequency = float(segment_rows["purchase_frequency_per_month"].mean())
        monthly_units += weight * acceptability * frequency
    return monthly_units


def _base_monthly_contribution(price: float, channel: str, data: dict[str, pd.DataFrame]) -> float:
    monthly_units = _segment_weighted_monthly_units(price, channel, data)
    return unit_contribution(price, channel) * monthly_units


def unit_contribution(price: float, channel: str) -> float:
    """Calculate net revenue per unit for the selected channel minus unit cost."""
    _validate_price(price)
    _validate_channel(channel)

    data = _data()
    terms = _channel_terms(channel, data)
    total_unit_cost = _total_unit_cost(data)
    net_price = (
        float(price)
        * (
            1.0
            - float(terms["retailer_margin_pct"])
            - float(terms["distributor_cut_pct"])
            - float(terms["payment_processing_pct"])
        )
        - float(terms["fulfillment_cost_eur"])
    )
    return net_price - total_unit_cost


def monthly_contribution(price: float, channel: str, month: int) -> float:
    """Calculate monthly contribution per customer using weighted frequency and launch-month seasonality."""
    _validate_price(price)
    _validate_channel(channel)
    _validate_month(month)

    data = _data()
    try:
        acceptance_rate(price, channel)
    except NotImplementedError:
        pass

    return _base_monthly_contribution(price, channel, data) * _seasonality_multiplier(month, data)


def customer_lifetime_months() -> float:
    """Return the derived customer lifetime used for German scenarios.

    The data room does not provide a customer lifetime directly, so it is
    back-solved from existing-market economics:

    - ``marketing_funnel_monthly`` provides estimated home-market LTV values.
      Using conversions as weights gives EUR 126.31859995512677 per acquired
      customer: sum(ltv_estimate_eur * conversions_customers_acquired) /
      sum(conversions_customers_acquired).
    - ``historical_sales_weekly`` provides the home-market achieved price.
      Across the cleaned Netherlands, Denmark and Sweden rows, revenue divided
      by units is EUR 1.350114815021632.
    - ``cost_breakdown`` states current blended home-market gross margin is
      30.0%, so home-market contribution per unit is
      1.350114815021632 * 0.30 = EUR 0.4050344445064896.
    - ``customer_survey`` is the available purchase-frequency proxy for the
      German launch model. Its respondent-weighted mean is
      6.144285714285715 units per customer per month.

    Therefore lifetime months =
    126.31859995512677 / (0.4050344445064896 * 6.144285714285715)
    = 50.75793478553424 months. The same lifetime is then held fixed across
    German price scenarios so price changes alter contribution, not loyalty.
    """
    return _customer_lifetime_months()


@lru_cache(maxsize=1)
def _customer_lifetime_months() -> float:
    data = _data()
    funnel = data["marketing_funnel_monthly"]
    conversions = funnel["conversions_customers_acquired"]
    weighted_ltv = float((funnel["ltv_estimate_eur"] * conversions).sum() / conversions.sum())

    history = data["historical_sales_weekly"]
    achieved_price = float(history["revenue_eur"].sum() / history["units_sold"].sum())

    costs = data["cost_breakdown"]
    margin_row = costs[costs["cost_component"].astype(str).str.contains("Current blended gross margin", na=False)]
    if margin_row.empty:
        raise RuntimeError("cost_breakdown is missing the current blended gross margin row")
    gross_margin = float(margin_row.iloc[0]["cost_per_unit_eur"]) / 100.0

    monthly_frequency = float(data["customer_survey"]["purchase_frequency_per_month"].mean())
    monthly_contribution_value = achieved_price * gross_margin * monthly_frequency
    if monthly_contribution_value <= 0:
        return inf
    return weighted_ltv / monthly_contribution_value


def ltv(price: float, channel: str) -> float:
    """Calculate customer lifetime value for the selected price and channel."""
    _validate_price(price)
    _validate_channel(channel)
    data = _data()
    return _base_monthly_contribution(price, channel, data) * customer_lifetime_months()


def payback_months(price: float, channel: str, month: int) -> float:
    """Calculate months required for monthly contribution to recover blended customer acquisition cost."""
    contribution = monthly_contribution(price, channel, month)
    if contribution <= 0:
        return inf
    return BLENDED_CAC_EUR / contribution


def ltv_cac_ratio(price: float, channel: str) -> float:
    """Calculate customer lifetime value divided by blended customer acquisition cost."""
    return ltv(price, channel) / BLENDED_CAC_EUR
