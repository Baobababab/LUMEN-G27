from fastapi import HTTPException

from api.index import ScenarioRequest, evaluate_scenario


def test_api_returns_only_aggregated_scenario_results():
    result = evaluate_scenario(ScenarioRequest(price=2.19, channel="DTC Online", month=7))

    assert result["verdict"] == "GO"
    assert result["metrics"]["price_acceptability_index"] > 0
    assert result["metrics"]["ltv_cac_ratio"] > 0
    assert set(result) == {"verdict", "decided_by", "reasons", "trade_off", "metrics", "data_quality"}
    assert "customer_survey" not in result["metrics"]
    assert result["data_quality"]["pii_columns_excluded"]["count"] == 3


def test_api_returns_a_safe_error_for_unsupported_price():
    try:
        evaluate_scenario(ScenarioRequest(price=3.10, channel="DTC Online", month=7))
        assert False, "unsupported price must return an API error"
    except HTTPException as error:
        assert error.status_code == 422
        assert error.detail["message"] == "Acceptance evidence is unavailable for this scenario."
