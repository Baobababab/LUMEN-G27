"""Aggregated price-sensitivity and launch-timing analysis."""

from decimal import Decimal
from math import isfinite

from constants import OBSERVED_PRICE_SUPPORT
from data_loader import load_all
from verdict import verdict


PRICE_GRID_STEP_EUR = Decimal("0.02")
MAX_PRICE_EVALUATIONS = 250
PRICE_SENSITIVITY_BUDGET_MS = 2500
_MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def _grid_prices() -> list[Decimal]:
    """Return the approved observed-price grid, including both endpoints."""
    lower, upper = (Decimal(f"{price:.2f}") for price in OBSERVED_PRICE_SUPPORT)
    prices = []
    price = lower
    while price <= upper:
        prices.append(price)
        price += PRICE_GRID_STEP_EUR
    if prices[-1] != upper:
        prices.append(upper)
    return prices


def price_sensitivity(
    price: float, channel: str, month: int, payback_horizon_months: float
) -> dict:
    """Scan verdict changes without assuming price acceptability is monotonic."""
    selected = Decimal(str(price))
    lower, upper = (Decimal(f"{item:.2f}") for item in OBSERVED_PRICE_SUPPORT)
    if not lower <= selected <= upper:
        raise ValueError("price must be within observed support")
    prices = _grid_prices()
    if selected not in prices:
        prices.append(selected)
    prices.sort()
    if len(prices) > MAX_PRICE_EVALUATIONS:
        raise RuntimeError("Price-sensitivity evaluation limit exceeded")

    points = [
        {
            "price_eur": float(item),
            "verdict": verdict(float(item), channel, month, payback_horizon_months)["verdict"],
        }
        for item in prices
    ]
    groups: list[list[dict]] = []
    for point in points:
        if not groups or groups[-1][-1]["verdict"] != point["verdict"]:
            groups.append([point])
        else:
            groups[-1].append(point)
    selected_group = next(group for group in groups if any(item["price_eur"] == float(selected) for item in group))
    selected_index = groups.index(selected_group)

    changes = []
    if selected_index:
        previous = groups[selected_index - 1][-1]
        current = selected_group[0]
        changes.append({"from": previous, "to": current})
    if selected_index < len(groups) - 1:
        current = selected_group[-1]
        following = groups[selected_index + 1][0]
        changes.append({"from": current, "to": following})

    return {
        "selected_price_eur": float(selected),
        "grid_step_eur": float(PRICE_GRID_STEP_EUR),
        "evaluation_count": len(points),
        "max_evaluations": MAX_PRICE_EVALUATIONS,
        "contiguous_interval": {
            "from_price_eur": selected_group[0]["price_eur"],
            "to_price_eur": selected_group[-1]["price_eur"],
            "verdict": selected_group[0]["verdict"],
        },
        "nearest_verdict_changes": changes,
        "method": "The model evaluates discrete observed prices; it does not assume acceptance changes in one direction.",
        "limit": "Grid resolution is EUR 0.02. It is not a claim of economic precision or a demand forecast.",
    }


def launch_timing(month: int, metrics: dict) -> dict:
    """Compare one scenario month with the twelve supplied seasonal indices."""
    rows = load_all()["seasonality_and_weather"]
    indices = {
        int(row.month): float(row.seasonality_index_100_avg)
        for row in rows[["month", "seasonality_index_100_avg"]].itertuples()
    }
    if set(indices) != set(range(1, 13)):
        raise RuntimeError("Seasonality data must contain each month exactly once")
    selected_index = indices[month]
    best_index = max(indices.values())
    best_months = [item for item, value in indices.items() if value == best_index]
    monthly_contribution = float(metrics["monthly_contribution_eur"])
    payback = float(metrics["payback_months"])
    best_contribution = monthly_contribution * best_index / selected_index
    best_payback = payback * selected_index / best_index if isfinite(payback) else None

    return {
        "selected_month": {
            "number": month,
            "name": _MONTH_NAMES[month - 1],
            "seasonality_index": selected_index,
            "rank_of_12": 1 + sum(value > selected_index for value in indices.values()),
            "monthly_contribution_eur": monthly_contribution,
            "payback_months": payback,
        },
        "most_favorable_window": {
            "months": [_MONTH_NAMES[item - 1] for item in best_months],
            "seasonality_index": best_index,
            "monthly_contribution_eur": best_contribution,
            "payback_months": best_payback,
        },
        "monthly_contribution_change_to_best_eur": best_contribution - monthly_contribution,
        "payback_change_to_best_months": best_payback - payback if best_payback is not None else None,
        "source": "seasonality_and_weather.csv",
        "limit": "This compares supplied seasonal indices with price, channel, and payback horizon held fixed. It does not use live weather or forecast demand.",
    }


def scenario_analysis(
    price: float, channel: str, month: int, payback_horizon_months: float, metrics: dict
) -> dict:
    """Return optional analysis for one selected scenario only."""
    return {
        "price_sensitivity": price_sensitivity(price, channel, month, payback_horizon_months),
        "launch_timing": launch_timing(month, metrics),
    }
