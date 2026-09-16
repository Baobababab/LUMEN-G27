from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.index import ScenarioRequest, _metric_state, app, evaluate_scenario


_FORBIDDEN_KEYS = {"respondent_id", "first_name", "last_name", "email"}
_DETAIL_KEYS = {
    "key",
    "name",
    "acronym",
    "value",
    "unit",
    "state",
    "comparison",
    "explanation",
    "formula",
    "source",
    "assumptions",
    "limits",
}


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
    assert set(result) == {
        "verdict",
        "decided_by",
        "reasons",
        "trade_off",
        "metrics",
        "metric_details",
        "competitive_positioning",
        "perspectives",
        "data_quality",
    }
    assert "customer_survey" not in result["metrics"]
    assert result["data_quality"]["pii_columns_excluded"]["count"] >= 4
    assert len(result["metric_details"]) == 6
    details = {item["key"]: item for item in result["metric_details"]}
    assert set(details) == {
        "price_acceptability_index",
        "unit_contribution_eur",
        "monthly_contribution_eur",
        "lifetime_value_eur",
        "ltv_cac_ratio",
        "payback_months",
    }
    for item in details.values():
        assert set(item) == _DETAIL_KEYS
        assert item["state"] in {"favorable", "monitor", "critical"}
        assert item["name"]
        assert item["explanation"]
        assert item["formula"]
        assert item["source"]
        assert item["assumptions"]
        assert item["limits"]
    driver_key = {
        "acceptance_rate": "price_acceptability_index",
        "ltv_cac_ratio": "ltv_cac_ratio",
        "payback_months": "payback_months",
    }[result["decided_by"]]
    assert details[driver_key]["state"] == "monitor"
    assert details["unit_contribution_eur"]["comparison"] == "No approved decision threshold."
    assert result["competitive_positioning"]["competitors"]
    assert result["competitive_positioning"]["label"] in {"Accessible", "Premium", "Very premium"}
    assert set(result["perspectives"]) == {"cmo", "cfo"}
    _assert_aggregated(result)


def test_metric_states_follow_existing_verdict_pass_flags():
    passed = {"acceptance_pass": True, "ltv_cac_pass": True, "payback_pass": True}
    failed = {**passed, "ltv_cac_pass": False}

    assert _metric_state("unit_contribution_eur", passed, "ltv_cac_ratio") == "monitor"
    assert _metric_state("price_acceptability_index", passed, "acceptance_rate") == "monitor"
    assert _metric_state("payback_months", passed, "acceptance_rate") == "favorable"
    assert _metric_state("ltv_cac_ratio", failed, "ltv_cac_ratio") == "critical"


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


def test_compare_api_supports_one_to_three_scenarios_with_backend_deltas():
    client = TestClient(app)
    response = client.post(
        "/api/compare",
        json={
            "baseline_index": 1,
            "scenarios": [
                {"price": 2.19, "channel": "DTC Online", "month": 7},
                {"price": 2.19, "channel": "Retail/Grocery", "month": 7},
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["scenarios"]) == len(payload["differences"]) == 2
    assert payload["baseline_index"] == 1
    assert payload["differences"][1]["monthly_contribution_eur"] == 0
    assert payload["differences"][0]["monthly_contribution_eur"] != 0
    _assert_aggregated(payload)


def test_compare_api_rejects_more_than_three_scenarios_without_echoing_input():
    client = TestClient(app)
    sentinel = "synthetic-fourth-scenario"
    scenario = {"price": 2.19, "channel": "DTC Online", "month": 7}
    response = client.post("/api/compare", json={"scenarios": [scenario, scenario, scenario, {**scenario, "tag": sentinel}]})

    assert response.status_code == 422
    assert sentinel not in response.text


def test_compare_api_rejects_a_baseline_outside_the_scenarios():
    client = TestClient(app)
    response = client.post(
        "/api/compare",
        json={"baseline_index": 1, "scenarios": [{"price": 2.19, "channel": "DTC Online", "month": 7}]},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid scenario input."}


def test_compare_api_returns_optional_selected_scenario_analysis_with_aggregate_limits():
    client = TestClient(app)
    response = client.post(
        "/api/compare",
        json={
            "baseline_index": 1,
            "include_analysis": True,
            "scenarios": [
                {"price": 2.19, "channel": "DTC Online", "month": 7},
                {"price": 2.19, "channel": "Retail/Grocery", "month": 7},
            ],
        },
    )

    assert response.status_code == 200
    analysis = response.json()["analysis"]
    assert analysis["price_sensitivity"]["selected_price_eur"] == 2.19
    assert analysis["price_sensitivity"]["evaluation_count"] <= 250
    assert analysis["launch_timing"]["selected_month"]["number"] == 7
    _assert_aggregated(analysis)


def test_compare_api_returns_aggregated_model_adjustments_only_for_a_non_go_baseline():
    client = TestClient(app)
    response = client.post(
        "/api/compare",
        json={"scenarios": [{"price": 1.79, "channel": "DTC Online", "month": 1}]},
    )

    assert response.status_code == 200
    adjustments = response.json()["model_adjustments"]
    assert adjustments["status"] in {"alternatives_available", "no_single_variable_improvement"}
    assert len(adjustments["alternatives"]) <= 3
    _assert_aggregated(adjustments)


def test_compare_api_returns_a_no_correction_state_for_a_go_baseline():
    client = TestClient(app)
    response = client.post(
        "/api/compare",
        json={"scenarios": [{"price": 2.19, "channel": "DTC Online", "month": 1, "payback_horizon_months": 12}]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenarios"][0]["verdict"] == "GO"
    assert payload["model_adjustments"] == {
        "status": "not_needed",
        "summary": "This scenario already meets all approved decision thresholds, so no adjustment is needed.",
        "alternatives": [],
    }
    _assert_aggregated(payload["model_adjustments"])


def test_compare_api_model_adjustments_follow_the_selected_baseline():
    client = TestClient(app)
    scenarios = [
        {"price": 2.19, "channel": "DTC Online", "month": 7},
        {"price": 1.79, "channel": "DTC Online", "month": 1},
    ]

    go_baseline = client.post("/api/compare", json={"scenarios": scenarios, "baseline_index": 0})
    non_go_baseline = client.post("/api/compare", json={"scenarios": scenarios, "baseline_index": 1})

    assert go_baseline.status_code == non_go_baseline.status_code == 200
    assert go_baseline.json()["model_adjustments"]["status"] == "not_needed"
    assert non_go_baseline.json()["model_adjustments"]["status"] in {"alternatives_available", "no_single_variable_improvement"}
    _assert_aggregated(non_go_baseline.json()["model_adjustments"])
