from unittest.mock import patch

import pandas as pd

import decision_support


def test_price_sensitivity_finds_selected_non_monotonic_interval_and_respects_limit():
    def synthetic_verdict(price, *_):
        return {"verdict": "GO" if 1.00 <= price <= 1.10 or 2.00 <= price <= 2.10 else "NO-GO"}

    with patch("decision_support.verdict", side_effect=synthetic_verdict):
        result = decision_support.price_sensitivity(2.05, "DTC Online", 7, 12)

    assert result["contiguous_interval"]["verdict"] == "GO"
    assert result["contiguous_interval"]["from_price_eur"] == 2.0
    assert result["contiguous_interval"]["to_price_eur"] == 2.1
    assert len(result["nearest_verdict_changes"]) == 2
    assert result["evaluation_count"] <= result["max_evaluations"] == 250


def test_price_sensitivity_includes_observed_endpoints_and_off_grid_price():
    with patch("decision_support.verdict", return_value={"verdict": "GO"}):
        lower = decision_support.price_sensitivity(0.62, "DTC Online", 7, 12)
        upper = decision_support.price_sensitivity(3.09, "DTC Online", 7, 12)
        off_grid = decision_support.price_sensitivity(2.19, "DTC Online", 7, 12)

    assert lower["contiguous_interval"]["from_price_eur"] == 0.62
    assert upper["contiguous_interval"]["to_price_eur"] == 3.09
    assert off_grid["selected_price_eur"] == 2.19
    assert off_grid["evaluation_count"] == 126


def test_price_sensitivity_rejects_a_price_outside_observed_support():
    try:
        decision_support.price_sensitivity(3.10, "DTC Online", 7, 12)
        assert False, "unsupported price must fail"
    except ValueError as error:
        assert str(error) == "price must be within observed support"


def test_launch_timing_ranks_all_months_and_keeps_ties_in_best_window():
    seasonality = pd.DataFrame(
        {"month": range(1, 13), "seasonality_index_100_avg": [90, 100, 100, 80, 70, 60, 50, 40, 30, 20, 10, 5]}
    )
    with patch("decision_support.load_all", return_value={"seasonality_and_weather": seasonality}):
        result = decision_support.launch_timing(1, {"monthly_contribution_eur": 90, "payback_months": 10})

    assert result["selected_month"]["rank_of_12"] == 3
    assert result["most_favorable_window"]["months"] == ["February", "March"]
    assert result["monthly_contribution_change_to_best_eur"] == 10
    assert result["payback_change_to_best_months"] == -1


def test_launch_timing_returns_each_of_the_twelve_months():
    for month in range(1, 13):
        result = decision_support.launch_timing(
            month, {"monthly_contribution_eur": 10, "payback_months": 8}
        )
        assert result["selected_month"]["number"] == month
