"""Runnable checks for the Task D verdict contract."""

from math import inf
from unittest.mock import patch

from acceptance import AcceptanceDataError
from constants import ACCEPTANCE_FLOOR, TARGET_LTV_CAC
from verdict import verdict


def _scenario(ltv_ratio: float, payback: float, acceptance: float, horizon: float = 12.0) -> dict:
    with (
        patch("verdict.ltv_cac_ratio", return_value=ltv_ratio),
        patch("verdict.payback_months", return_value=payback),
        patch("verdict.acceptance_rate", return_value=acceptance),
    ):
        return verdict(2.19, "DTC Online", 7, horizon)


def _assert_raises(error_type: type[Exception], *args) -> None:
    try:
        verdict(*args)
    except error_type:
        return
    raise AssertionError(f"Expected {error_type.__name__}")


def test_threshold_boundaries_and_required_metrics():
    below_ltv = _scenario(TARGET_LTV_CAC - 0.01, 12.0, ACCEPTANCE_FLOOR)
    on_ltv = _scenario(TARGET_LTV_CAC, 12.0, ACCEPTANCE_FLOOR)
    above_ltv = _scenario(TARGET_LTV_CAC + 0.01, 12.0, ACCEPTANCE_FLOOR)
    assert below_ltv["verdict"] == "CONDITIONAL"
    assert on_ltv["verdict"] == above_ltv["verdict"] == "GO"

    below_payback = _scenario(TARGET_LTV_CAC, 12.01, ACCEPTANCE_FLOOR)
    on_payback = _scenario(TARGET_LTV_CAC, 12.0, ACCEPTANCE_FLOOR)
    above_payback = _scenario(TARGET_LTV_CAC, 11.99, ACCEPTANCE_FLOOR)
    assert below_payback["verdict"] == "CONDITIONAL"
    assert on_payback["verdict"] == above_payback["verdict"] == "GO"

    below_acceptance = _scenario(TARGET_LTV_CAC, 12.0, ACCEPTANCE_FLOOR - 0.01)
    on_acceptance = _scenario(TARGET_LTV_CAC, 12.0, ACCEPTANCE_FLOOR)
    above_acceptance = _scenario(TARGET_LTV_CAC, 12.0, ACCEPTANCE_FLOOR + 0.01)
    assert below_acceptance["verdict"] == "CONDITIONAL"
    assert on_acceptance["verdict"] == above_acceptance["verdict"] == "GO"

    metrics = on_ltv["metrics"]
    assert set(on_ltv) == {"verdict", "decided_by", "reasons", "trade_off", "metrics"}
    assert metrics["ltv_cac_ratio"] == TARGET_LTV_CAC
    assert metrics["payback_months"] == 12.0
    assert metrics["acceptance_rate"] == ACCEPTANCE_FLOOR
    assert metrics["target_ltv_cac"] == TARGET_LTV_CAC
    assert metrics["payback_horizon_months"] == 12.0
    assert metrics["acceptance_floor"] == ACCEPTANCE_FLOOR
    assert all(metrics[key] for key in ("ltv_cac_pass", "payback_pass", "acceptance_pass"))
    for conditional in (below_ltv, below_payback, below_acceptance):
        assert any(reason.startswith("Assumption:") for reason in conditional["reasons"])


def test_labels_assumptions_trade_offs_and_deterministic_decisions():
    conditional = _scenario(TARGET_LTV_CAC, 12.1, ACCEPTANCE_FLOOR)
    no_go = _scenario(2.0, 15.0, 0.20)
    go = _scenario(3.2, 10.0, 0.50)
    assert conditional["verdict"] == "CONDITIONAL"
    assert conditional["decided_by"] == "payback_months"
    assert any(reason.startswith("Assumption:") and "12.00" in reason for reason in conditional["reasons"])
    assert no_go["verdict"] == "NO-GO"
    assert no_go["decided_by"] == "acceptance_rate"
    assert go["verdict"] == "GO"
    assert go["decided_by"] == "ltv_cac_ratio"

    no_go_tie = _scenario(0.0, 12.0, 0.0)
    assert no_go_tie["decided_by"] == "ltv_cac_ratio"
    go_tie = _scenario(3.0, 12.0, ACCEPTANCE_FLOOR)
    assert go_tie["decided_by"] == "ltv_cac_ratio"
    for result in (conditional, no_go, go):
        assert result["reasons"]
        assert result["trade_off"]
        assert "LTV:CAC" in result["trade_off"]
    assert "returns over customer reach" in _scenario(3.5, 10.0, 0.2)["trade_off"]
    assert "Prioritises reach" in _scenario(2.5, 13.0, 0.5)["trade_off"]


def test_payback_horizon_and_invalid_inputs_and_data_error_propagation():
    assert _scenario(3.5, 10.0, 0.6, horizon=9.0)["verdict"] == "CONDITIONAL"
    assert _scenario(3.5, 10.0, 0.6, horizon=15.0)["verdict"] == "GO"
    for bad_price in (True, "2.19", float("nan"), float("inf"), 0, -1):
        _assert_raises(ValueError, bad_price, "DTC Online", 7)
    for bad_month in (True, 7.0, "7", 0, 13):
        _assert_raises(ValueError, 2.19, "DTC Online", bad_month)
    for bad_horizon in (True, "12", float("nan"), float("inf"), 0, -1):
        _assert_raises(ValueError, 2.19, "DTC Online", 7, bad_horizon)
    _assert_raises(ValueError, 2.19, "Unknown channel", 7)

    with patch("verdict.acceptance_rate", side_effect=AcceptanceDataError("unsupported price")):
        _assert_raises(AcceptanceDataError, 2.19, "DTC Online", 7)
    assert _scenario(3.0, inf, ACCEPTANCE_FLOOR)["verdict"] == "CONDITIONAL"


if __name__ == "__main__":
    test_threshold_boundaries_and_required_metrics()
    test_labels_assumptions_trade_offs_and_deterministic_decisions()
    test_payback_horizon_and_invalid_inputs_and_data_error_propagation()
    print("test_verdict.py: all tests passed")
