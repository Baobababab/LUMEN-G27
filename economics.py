from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).parent / "data"


def unit_contribution(price: float, channel: str) -> float:
    """Calculate net revenue per unit for the selected channel minus unit cost."""
    raise NotImplementedError


def monthly_contribution(price: float, channel: str, month: int) -> float:
    """Calculate monthly contribution per customer using weighted frequency and launch-month seasonality."""
    raise NotImplementedError


def customer_lifetime_months() -> float:
    """Return the calibrated customer lifetime in months.

    The data room does not provide a lifetime directly, so this is back-solved
    from observed home-market revenue LTV:

    * ``historical_sales_weekly.csv`` contains 78 weeks of Netherlands,
      Denmark, and Sweden sales. After removing the four exact duplicate rows,
      the achieved home-market price is total revenue / total units =
      EUR 1,619,925.81 / 1,199,843 = EUR 1.3501148150 per unit.
    * ``marketing_funnel_monthly.csv`` contains two observations in the
      brief's EUR 137-139 home-market LTV calibration range: EUR 137.28 and
      EUR 138.28. Their mean is EUR 137.78.
    * ``customer_survey.csv`` gives the observed purchase frequency used by
      the scenario model: mean purchase_frequency_per_month = 6.1442857143.

    The implied lifetime is therefore:

        lifetime_months = home_market_ltv / (home_market_price * monthly_frequency)
                        = 137.78 / (1.3501148150 * 6.1442857143)
                        = 16.609... months

    The result is deliberately not rounded to a convenient number. It is held
    constant for German scenarios: changing German price changes monthly
    contribution and contribution-based LTV, but does not silently change
    assumed customer loyalty.
    """
    sales = pd.read_csv(DATA_DIR / "historical_sales_weekly.csv").drop_duplicates()
    home_market_price = sales["revenue_eur"].sum() / sales["units_sold"].sum()

    funnel = pd.read_csv(DATA_DIR / "marketing_funnel_monthly.csv")
    calibration_ltv = funnel.loc[
        funnel["ltv_estimate_eur"].between(137.0, 139.0), "ltv_estimate_eur"
    ].mean()

    survey = pd.read_csv(DATA_DIR / "customer_survey.csv")
    monthly_frequency = survey["purchase_frequency_per_month"].mean()

    return float(calibration_ltv / (home_market_price * monthly_frequency))


def ltv(price: float, channel: str) -> float:
    """Calculate customer lifetime value for the selected price and channel."""
    raise NotImplementedError


def payback_months(price: float, channel: str, month: int) -> float:
    """Calculate months required for monthly contribution to recover blended customer acquisition cost."""
    raise NotImplementedError


def ltv_cac_ratio(price: float, channel: str) -> float:
    """Calculate customer lifetime value divided by blended customer acquisition cost."""
    raise NotImplementedError
