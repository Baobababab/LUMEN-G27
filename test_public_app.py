from pathlib import Path


def test_scenario_reader_uses_fieldset_controls():
    script = Path("public/app.js").read_text(encoding="utf-8")

    assert "new FormData(fields)" not in script
    assert 'fields.elements.namedItem(name).value' in script


def test_public_app_sends_and_renders_the_selected_baseline():
    script = Path("public/app.js").read_text(encoding="utf-8")

    assert "baseline_index: selectedBaselineIndex()" in script
    assert "showResult(payload.scenarios[payload.baseline_index])" in script
    assert "Selected baseline. Differences are zero." in script


def test_hidden_baseline_badge_overrides_its_display_style():
    stylesheet = Path("public/styles.css").read_text(encoding="utf-8")

    assert ".baseline-badge[hidden] { display: none; }" in stylesheet


def test_public_app_requests_and_renders_optional_backend_analysis_only():
    script = Path("public/app.js").read_text(encoding="utf-8")

    assert "include_analysis: analysisRequested" in script
    assert "Show model sensitivity and month analysis" in Path("public/index.html").read_text(encoding="utf-8")
    assert "Grid resolution" in script
    assert "seasonality_and_weather.csv" not in script


def test_public_app_renders_backend_model_adjustments_without_calculating_them():
    script = Path("public/app.js").read_text(encoding="utf-8")
    page = Path("public/index.html").read_text(encoding="utf-8")

    assert "showAdjustments(payload.model_adjustments, payload.baseline_index)" in script
    assert "item.headline" in script
    assert "Ways to improve this scenario" in page
    assert page.index('id="adjustments"') > page.index('id="data-quality"')
    assert "CONDITIONAL: Sales channel" not in script
    assert 'data.status === "not_needed" ? data.summary' in script


def test_public_app_can_select_each_non_go_scenario_for_its_adjustments():
    script = Path("public/app.js").read_text(encoding="utf-8")
    page = Path("public/index.html").read_text(encoding="utf-8")

    assert 'item.verdict !== "GO"' in script
    assert "Review ways to improve Scenario ${index + 1}" in script
    assert "data-baseline-index" in script
    assert "form.requestSubmit();" in script
    assert 'id="adjustments-title"' in page
    assert "Ways to improve Scenario ${baselineIndex + 1}" in script
    assert "apply only to selected Scenario ${baselineIndex + 1}" in script
