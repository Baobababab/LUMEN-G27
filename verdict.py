"""Decision rules for LUMEN launch scenarios.

Tie-breaking is fixed as LTV:CAC, payback, then acceptance.  It is used for
equal proportional misses in NO-GO results and equal safety margins in GO
results, making ``decided_by`` stable and explainable.
"""

from math import isfinite
from numbers import Real

from acceptance import acceptance_rate
from constants import ACCEPTANCE_FLOOR, MAX_PAYBACK_HORIZON_MONTHS, SALES_CHANNELS, TARGET_LTV_CAC
from economics import ltv_cac_ratio, payback_months


_METRIC_ORDER = ("ltv_cac_ratio", "payback_months", "acceptance_rate")


def format_payback_months(value: float | None) -> str:
    """Return manager-facing payback text without exposing non-finite values."""
    return f"{value:.2f} months" if value is not None and isfinite(value) else "Not recoverable"


def _validate_inputs(
    price: float, channel: str, month: int, payback_horizon_months: float
) -> tuple[float, int, float]:
    """Validate inputs before any data-backed metric function is called."""
    if isinstance(price, bool) or not isinstance(price, Real):
        raise ValueError("price must be a positive finite number")
    numeric_price = float(price)
    if not isfinite(numeric_price) or numeric_price <= 0:
        raise ValueError("price must be a positive finite number")

    if not isinstance(channel, str) or channel not in SALES_CHANNELS:
        raise ValueError(f"channel must be one of {SALES_CHANNELS}")

    if isinstance(month, bool) or not isinstance(month, int) or not 1 <= month <= 12:
        raise ValueError("month must be an integer from 1 to 12")

    if isinstance(payback_horizon_months, bool) or not isinstance(payback_horizon_months, Real):
        raise ValueError("payback_horizon_months must be a positive finite number")
    horizon = float(payback_horizon_months)
    if not isfinite(horizon) or not 0 < horizon <= MAX_PAYBACK_HORIZON_MONTHS:
        raise ValueError(f"payback_horizon_months must be between 0 and {MAX_PAYBACK_HORIZON_MONTHS:g}")
    return numeric_price, month, horizon


def _deciding_metric(values: dict[str, float], passed: dict[str, bool], horizon: float) -> str:
    """Choose the metric by proportional miss or safety margin in fixed order."""
    misses = {
        "ltv_cac_ratio": (TARGET_LTV_CAC - values["ltv_cac_ratio"]) / TARGET_LTV_CAC,
        "payback_months": (values["payback_months"] - horizon) / horizon,
        "acceptance_rate": (ACCEPTANCE_FLOOR - values["acceptance_rate"]) / ACCEPTANCE_FLOOR,
    }
    margins = {
        "ltv_cac_ratio": (values["ltv_cac_ratio"] - TARGET_LTV_CAC) / TARGET_LTV_CAC,
        "payback_months": (horizon - values["payback_months"]) / horizon,
        "acceptance_rate": (values["acceptance_rate"] - ACCEPTANCE_FLOOR) / ACCEPTANCE_FLOOR,
    }
    candidates = [metric for metric in _METRIC_ORDER if not passed[metric]]
    if candidates:
        return max(candidates, key=lambda metric: (misses[metric], -_METRIC_ORDER.index(metric)))
    return min(_METRIC_ORDER, key=lambda metric: (margins[metric], _METRIC_ORDER.index(metric)))


def _conditional_assumption(metric: str, values: dict[str, float], horizon: float) -> str:
    if metric == "ltv_cac_ratio":
        return (
            f"Assumption: LTV:CAC must improve from {values[metric]:.2f} "
            f"to {TARGET_LTV_CAC:.2f}."
        )
    if metric == "payback_months":
        if not isfinite(values[metric]):
            return (
                "Assumption: payback must become recoverable within the "
                f"{horizon:.2f}-month horizon."
            )
        return (
            f"Assumption: the acceptable payback horizon must increase from {horizon:.2f} "
            f"to {values[metric]:.2f} months."
        )
    return (
        f"Assumption: acceptance must improve from {values[metric]:.1%} "
        f"to {ACCEPTANCE_FLOOR:.1%}."
    )


def _trade_off(values: dict[str, float], passed: dict[str, bool], horizon: float) -> str:
    economics_pass = passed["ltv_cac_ratio"] and passed["payback_months"]
    acceptance_pass = passed["acceptance_rate"]
    summary = (
        f"LTV:CAC is {values['ltv_cac_ratio']:.2f} against {TARGET_LTV_CAC:.2f}; "
        f"payback is {format_payback_months(values['payback_months']).lower()} against {horizon:.2f} months; "
        f"acceptance is {values['acceptance_rate']:.1%} against {ACCEPTANCE_FLOOR:.1%}."
    )
    if economics_pass and not acceptance_pass:
        return f"Price acceptability is below its approved floor; economic metrics meet their approved thresholds: {summary}"
    if acceptance_pass and not economics_pass:
        return f"Price acceptability meets its approved floor; one or more economic metrics miss their approved thresholds: {summary}"
    if economics_pass:
        return f"All approved decision metrics meet their thresholds: {summary}"
    return f"Price acceptability and one or more economic metrics miss their approved thresholds: {summary}"


def verdict(
    price: float,
    channel: str,
    month: int,
    payback_horizon_months: float = 12.0,
) -> dict:
    """Return a transparent GO, CONDITIONAL, or NO-GO scenario decision."""
    price, month, horizon = _validate_inputs(price, channel, month, payback_horizon_months)
    values = {
        "ltv_cac_ratio": ltv_cac_ratio(price, channel),
        "payback_months": payback_months(price, channel, month),
        "acceptance_rate": acceptance_rate(price, channel),
    }
    passed = {
        "ltv_cac_ratio": values["ltv_cac_ratio"] >= TARGET_LTV_CAC,
        "payback_months": values["payback_months"] <= horizon,
        "acceptance_rate": values["acceptance_rate"] >= ACCEPTANCE_FLOOR,
    }
    failed_count = sum(not result for result in passed.values())
    result = "GO" if failed_count == 0 else "CONDITIONAL" if failed_count == 1 else "NO-GO"
    decided_by = _deciding_metric(values, passed, horizon)
    reasons = [
        f"LTV:CAC {values['ltv_cac_ratio']:.2f} vs {TARGET_LTV_CAC:.2f}: "
        f"{'PASS' if passed['ltv_cac_ratio'] else 'FAIL'}.",
        f"Payback {format_payback_months(values['payback_months']).lower()} vs {horizon:.2f} months: "
        f"{'PASS' if passed['payback_months'] else 'FAIL'}.",
        f"Acceptance {values['acceptance_rate']:.1%} vs {ACCEPTANCE_FLOOR:.1%}: "
        f"{'PASS' if passed['acceptance_rate'] else 'FAIL'}.",
    ]
    if result == "CONDITIONAL":
        reasons.append(_conditional_assumption(decided_by, values, horizon))

    return {
        "verdict": result,
        "decided_by": decided_by,
        "reasons": reasons,
        "trade_off": _trade_off(values, passed, horizon),
        "metrics": {
            **values,
            "target_ltv_cac": TARGET_LTV_CAC,
            "payback_horizon_months": horizon,
            "acceptance_floor": ACCEPTANCE_FLOOR,
            "ltv_cac_pass": passed["ltv_cac_ratio"],
            "payback_pass": passed["payback_months"],
            "acceptance_pass": passed["acceptance_rate"],
        },
    }
