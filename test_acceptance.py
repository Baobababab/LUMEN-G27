"""Runnable checks for the Task B price-acceptability contract."""

from math import isclose
from unittest.mock import patch

import pandas as pd

from acceptance import AcceptanceDataError, acceptance_rate


EXPECTED_INDEX = {
    1.79: {"DTC Online": 0.530427, "Retail/Grocery": 0.621350, "Gym & Office": 0.682448},
    2.19: {"DTC Online": 0.654800, "Retail/Grocery": 0.437131, "Gym & Office": 0.541966},
    2.59: {"DTC Online": 0.436370, "Retail/Grocery": 0.203726, "Gym & Office": 0.237755},
}


def _assert_raises(error_type: type[Exception], function, *args) -> None:
    """Assert a callable raises the expected exception without a test framework."""
    try:
        function(*args)
    except error_type:
        return
    raise AssertionError(f"Expected {error_type.__name__}")


def run_checks() -> None:
    """Check published values, validation, data errors, and observed price behaviour."""
    for price, expected_by_channel in EXPECTED_INDEX.items():
        for channel, expected in expected_by_channel.items():
            actual = acceptance_rate(price, channel)
            assert 0.0 <= actual <= 1.0
            assert isclose(actual, expected, abs_tol=0.000001)

    _assert_raises(ValueError, acceptance_rate, True, "DTC Online")
    _assert_raises(ValueError, acceptance_rate, 0.0, "DTC Online")
    _assert_raises(ValueError, acceptance_rate, float("inf"), "DTC Online")
    _assert_raises(ValueError, acceptance_rate, 2.19, "Unknown channel")
    _assert_raises(AcceptanceDataError, acceptance_rate, 0.61, "DTC Online")
    _assert_raises(AcceptanceDataError, acceptance_rate, 3.10, "DTC Online")

    missing_segment_frames = {
        "customer_survey": pd.DataFrame(
            {"segment": ["Missing segment"], "preferred_channel": ["DTC Online"]}
        ),
        "price_sensitivity_survey": pd.DataFrame(
            {
                "segment": ["Another segment"],
                "cheap_eur": [1.0],
                "expensive_eur": [2.5],
            }
        ),
    }
    with patch("acceptance.load_all", return_value=missing_segment_frames):
        _assert_raises(AcceptanceDataError, acceptance_rate, 2.19, "DTC Online")

    assert acceptance_rate(1.79, "DTC Online") < acceptance_rate(2.19, "DTC Online")
    assert acceptance_rate(2.19, "Retail/Grocery") >= acceptance_rate(2.59, "Retail/Grocery")


if __name__ == "__main__":
    run_checks()
    print("Acceptance checks passed")
