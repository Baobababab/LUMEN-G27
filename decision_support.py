"""Aggregated price-sensitivity and launch-timing analysis."""

from decimal import Decimal
from math import isfinite

from constants import ACCEPTANCE_FLOOR, OBSERVED_PRICE_SUPPORT, SALES_CHANNELS, TARGET_LTV_CAC
from data_loader import load_all
from verdict import verdict


PRICE_GRID_STEP_EUR = Decimal("0.02")
MAX_PRICE_EVALUATIONS = 250
PRICE_SENSITIVITY_BUDGET_MS = 2500
_MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
_VERDICT_RANK = {"NO-GO": 0, "CONDITIONAL": 1, "GO": 2}
_ADJUSTMENT_LIMIT = 3


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


def _quality(decision: dict) -> tuple[int, int, float]:
    """Rank a decision using only approved verdict thresholds."""
    metrics = decision["metrics"]
    failed = sum(
        not metrics[key]
        for key in ("ltv_cac_pass", "payback_pass", "acceptance_pass")
    )
    distance = (
        max(0.0, (TARGET_LTV_CAC - metrics["ltv_cac_ratio"]) / TARGET_LTV_CAC)
        + max(0.0, (metrics["payback_months"] - metrics["payback_horizon_months"]) / metrics["payback_horizon_months"])
        + max(0.0, (ACCEPTANCE_FLOOR - metrics["acceptance_rate"]) / ACCEPTANCE_FLOOR)
    )
    return _VERDICT_RANK[decision["verdict"]], -failed, -distance


def _metric_changes(before: dict, after: dict) -> tuple[list[str], list[str]]:
    """Describe changes to approved verdict metrics in manager-facing language."""
    comparisons = (
        ("Lifetime value to customer acquisition cost", "ltv_cac_ratio", 1, "x"),
        ("Customer acquisition cost payback", "payback_months", -1, " months"),
        ("Price acceptability index", "acceptance_rate", 1, "%"),
    )
    improvements, trade_offs = [], []
    for name, key, better_direction, suffix in comparisons:
        old, new = before[key], after[key]
        if old == new:
            continue
        if key == "acceptance_rate":
            change = f"{name}: {old:.1%} to {new:.1%}"
        elif key == "payback_months":
            change = f"{name}: {old:.2f} to {new:.2f}{suffix}"
        else:
            change = f"{name}: {old:.2f} to {new:.2f}{suffix}"
        (improvements if (new - old) * better_direction > 0 else trade_offs).append(change)
    return improvements, trade_offs


def model_adjustments(
    price: float, channel: str, month: int, payback_horizon_months: float
) -> dict:
    """Return up to three single-variable model adjustments for a non-GO scenario."""
    baseline = verdict(price, channel, month, payback_horizon_months)
    if baseline["verdict"] == "GO":
        return {
            "status": "not_needed",
            "summary": "This scenario already meets all approved decision thresholds.",
            "alternatives": [],
        }

    candidates = []
    for candidate_price in _grid_prices():
        numeric_price = float(candidate_price)
        if numeric_price != price:
            candidates.append(("price", numeric_price, channel, month))
    candidates.extend(("channel", price, candidate, month) for candidate in SALES_CHANNELS if candidate != channel)
    candidates.extend(("month", price, channel, candidate) for candidate in range(1, 13) if candidate != month)

    baseline_quality = _quality(baseline)
    adjustments = []
    for change_type, candidate_price, candidate_channel, candidate_month in candidates:
        candidate = verdict(candidate_price, candidate_channel, candidate_month, payback_horizon_months)
        if _quality(candidate) <= baseline_quality:
            continue
        improvements, trade_offs = _metric_changes(baseline["metrics"], candidate["metrics"])
        if change_type == "price":
            change = f"Retail price: EUR {price:.2f} to EUR {candidate_price:.2f}"
            held_constant = "Sales channel, launch month, and payback horizon stay fixed."
            tie_break = (0, candidate_price)
        elif change_type == "channel":
            change = f"Sales channel: {channel} to {candidate_channel}"
            held_constant = "Retail price, launch month, and payback horizon stay fixed."
            tie_break = (1, SALES_CHANNELS.index(candidate_channel))
        else:
            change = f"Launch month: {_MONTH_NAMES[month - 1]} to {_MONTH_NAMES[candidate_month - 1]}"
            held_constant = "Retail price, sales channel, and payback horizon stay fixed."
            tie_break = (2, candidate_month)
        adjustments.append(
            {
                "change": change,
                "verdict": candidate["verdict"],
                "inputs": {
                    "price": candidate_price,
                    "channel": candidate_channel,
                    "month": candidate_month,
                    "payback_horizon_months": payback_horizon_months,
                },
                "improvements": improvements,
                "trade_offs": trade_offs,
                "held_constant": held_constant,
                "_quality": _quality(candidate),
                "_tie_break": tie_break,
                "_change_type": change_type,
            }
        )

    adjustments.sort(key=lambda item: (-item["_quality"][0], -item["_quality"][1], -item["_quality"][2], item["_tie_break"]))
    alternatives = []
    seen_types = set()
    for item in adjustments:
        if item["_change_type"] not in seen_types:
            alternatives.append(item)
            seen_types.add(item["_change_type"])
        if len(alternatives) == _ADJUSTMENT_LIMIT:
            break
    for item in alternatives:
        item.pop("_quality")
        item.pop("_tie_break")
        item.pop("_change_type")
    return {
        "status": "alternatives_available" if alternatives else "no_single_variable_improvement",
        "summary": (
            "Model adjustments improve this scenario under approved decision rules. They do not promise a commercial outcome."
            if alternatives
            else "No one-variable model adjustment improves this scenario under approved decision rules."
        ),
        "alternatives": alternatives,
    }
