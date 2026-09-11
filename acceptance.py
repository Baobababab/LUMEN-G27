"""Channel-specific price-acceptability calculations."""

from math import isfinite
from numbers import Real

import pandas as pd

from constants import OBSERVED_PRICE_SUPPORT, SALES_CHANNELS
from data_loader import load_all


class AcceptanceDataError(Exception):
    """Raised when available survey data cannot support an acceptability result."""


def _validated_price(price: float) -> float:
    """Validate a numeric, finite, positive price and return it as a float."""
    if isinstance(price, bool) or not isinstance(price, Real):
        raise ValueError("price must be a finite, positive number")

    numeric_price = float(price)
    if not isfinite(numeric_price) or numeric_price <= 0:
        raise ValueError("price must be a finite, positive number")
    return numeric_price


def _required_table(frames: dict[str, pd.DataFrame], name: str) -> pd.DataFrame:
    """Return one required DataFrame or raise a data-support error."""
    table = frames.get(name)
    if not isinstance(table, pd.DataFrame):
        raise AcceptanceDataError(f"Required table is unavailable: {name}")
    return table


def _require_columns(table: pd.DataFrame, table_name: str, columns: tuple[str, ...]) -> None:
    """Require columns needed for a defensible acceptability calculation."""
    missing = [column for column in columns if column not in table.columns]
    if missing:
        raise AcceptanceDataError(
            f"Required column(s) missing from {table_name}: {', '.join(missing)}"
        )


def acceptance_rate(price: float, channel: str) -> float:
    """Return a channel-weighted price-acceptability index from 0.0 to 1.0.

    This is not a calibrated purchase probability. For each customer-survey segment
    that prefers ``channel``, it measures the share of price-sensitivity respondents
    whose acceptable band contains ``price`` (``cheap_eur <= price <= expensive_eur``).
    The segment results are weighted by that segment's share of the channel subset.

    The index can increase below EUR 2.10 because a price can be too cheap for some
    respondents. It is monotone non-increasing only at or above EUR 2.10.

    Raises ValueError for a non-finite, boolean, zero, negative, or non-numeric
    price, or for a channel outside SALES_CHANNELS. Raises AcceptanceDataError when
    required data is unavailable, incomplete, or outside observed price support.
    """
    numeric_price = _validated_price(price)
    if not isinstance(channel, str) or channel not in SALES_CHANNELS:
        raise ValueError(f"channel must be one of: {', '.join(SALES_CHANNELS)}")

    minimum_price, maximum_price = OBSERVED_PRICE_SUPPORT
    if not minimum_price <= numeric_price <= maximum_price:
        raise AcceptanceDataError(
            f"price must be within observed support {minimum_price:.2f}–{maximum_price:.2f}"
        )

    try:
        frames = load_all()
    except Exception as error:
        raise AcceptanceDataError("Unable to load data required for acceptability") from error

    customers = _required_table(frames, "customer_survey")
    sensitivity = _required_table(frames, "price_sensitivity_survey")
    _require_columns(customers, "customer_survey", ("segment", "preferred_channel"))
    _require_columns(
        sensitivity,
        "price_sensitivity_survey",
        ("segment", "cheap_eur", "expensive_eur"),
    )

    channel_customers = customers.loc[customers["preferred_channel"].eq(channel)]
    if channel_customers.empty:
        raise AcceptanceDataError(f"No customer-survey respondents prefer {channel}")
    if channel_customers["segment"].isna().any():
        raise AcceptanceDataError("Channel respondent subset contains a missing segment")

    segment_weights = channel_customers["segment"].value_counts(normalize=True)
    index = 0.0
    for segment, weight in segment_weights.items():
        segment_sensitivity = sensitivity.loc[sensitivity["segment"].eq(segment)]
        if segment_sensitivity.empty:
            raise AcceptanceDataError(
                f"No price-sensitivity data available for segment: {segment}"
            )

        cheap = pd.to_numeric(segment_sensitivity["cheap_eur"], errors="coerce")
        expensive = pd.to_numeric(segment_sensitivity["expensive_eur"], errors="coerce")
        if cheap.isna().any() or expensive.isna().any():
            raise AcceptanceDataError(
                f"Invalid acceptable-price band in segment: {segment}"
            )

        acceptable = cheap.le(numeric_price) & expensive.ge(numeric_price)
        index += float(weight) * float(acceptable.mean())

    return index
