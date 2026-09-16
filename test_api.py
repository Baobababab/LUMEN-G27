from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.index import ScenarioRequest, app, evaluate_scenario


_FORBIDDEN_KEYS = {"respondent_id", "first_name", "last_name", "email"}


def _assert_aggregated(value):
    if isinstance(value, dict):
        assert _FORBIDDEN_KEYS.isdisjoint(value)
        for item in value.values():
            _assert_aggregated(item)
    elif isinstance(value, list):
        for item in value:
            _assert_aggregated(item)


def test_api_returns_only_aggregated_scenario_results():
    result = evaluate_scenario(ScenarioRequest(price=2.19, channel="DTC Online", month=7))

    assert result["verdict"] == "GO"
    assert result["metrics"]["price_acceptability_index"] > 0
    assert result["metrics"]["ltv_cac_ratio"] > 0
    assert set(result) == {"verdict", "decided_by", "reasons", "trade_off", "metrics", "data_quality"}
    assert "customer_survey" not in result["metrics"]
    assert result["data_quality"]["pii_columns_excluded"]["count"] >= 4
    _assert_aggregated(result)


def test_api_returns_a_safe_error_for_unsupported_price():
    try:
        evaluate_scenario(ScenarioRequest(price=3.10, channel="DTC Online", month=7))
        assert False, "unsupported price must return an API error"
    except HTTPException as error:
        assert error.status_code == 422
        assert error.detail["message"] == "Acceptance evidence is unavailable for this scenario."


def test_api_hides_synthetic_identifiers_and_has_no_raw_data_routes():
    client = TestClient(app)
    sentinel = "synthetic-respondent-id"
    response = client.post(
        "/api/scenario",
        json={
            "price": 2.19,
            "channel": "DTC Online",
            "month": 7,
            "respondent_id": sentinel,
        },
    )

    assert response.status_code == 422
    assert sentinel not in response.text
    _assert_aggregated(response.json())

    for path in ("/api/customer_survey.csv", f"/api/customer_survey/{sentinel}"):
        raw_response = client.get(path)
        assert raw_response.status_code == 404
        assert sentinel not in raw_response.text
        _assert_aggregated(raw_response.json())
