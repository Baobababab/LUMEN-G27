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
    assert "Decision driver: ${data.decision_driver.label}" in script
    assert "Decision driver: ${data.decided_by}" not in script


def test_public_app_renders_a_null_metric_as_not_recoverable_before_formatting():
    script = Path("public/app.js").read_text(encoding="utf-8")

    assert 'metric.value === null || !Number.isFinite(metric.value)' in script
    assert 'return "Not recoverable";' in script


def test_public_app_bounds_payback_and_handles_api_failures_without_parser_errors():
    script = Path("public/app.js").read_text(encoding="utf-8")
    page = Path("public/index.html").read_text(encoding="utf-8")

    assert 'max="120"' in page
    assert "Payback horizon (months, 0.01–120)" in page
    assert "async function readScenarioResponse(response)" in script
    assert 'response.headers.get("content-type")' in script
    assert "await response.json();" in script
    assert "Scenario service returned an invalid response. Try again." in script
    assert "Scenario service is unavailable. Try again." in script
    assert "Scenario request could not be completed. Try again." in script
    assert "const bestWindow = timing.most_favorable_window;" in script
    assert "const window = timing.most_favorable_window;" not in script


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
    assert page.index('id="adjustments"') < page.index('id="data-quality"')
    assert "CONDITIONAL: Sales channel" not in script
    assert 'data.status === "not_needed" ? data.summary' in script


def test_public_app_can_select_each_non_go_scenario_for_its_adjustments():
    script = Path("public/app.js").read_text(encoding="utf-8")
    page = Path("public/index.html").read_text(encoding="utf-8")

    assert 'item.verdict !== "GO"' in script
    assert "Review model adjustments for Scenario ${index + 1}" in script
    assert "data-baseline-index" in script
    assert "form.requestSubmit();" in script
    assert 'id="adjustments-title"' in page
    assert "Ways to improve Scenario ${baselineIndex + 1}" in script
    assert "Evaluate as selected baseline" in script
    assert "Select an alternative to replace the inputs in Scenario ${baselineIndex + 1}" in script
    assert "adjustmentAlternatives" in script
    assert "scenario.elements.namedItem(name).value = value" in script


def test_public_app_uses_native_print_with_a_printable_evaluation_record():
    script = Path("public/app.js").read_text(encoding="utf-8")
    page = Path("public/index.html").read_text(encoding="utf-8")
    stylesheet = Path("public/styles.css").read_text(encoding="utf-8")

    assert 'id="print-result"' in page
    assert 'id="print-metadata"' in page
    assert 'window.print()' in script
    assert "showPrintMetadata();" in script
    assert "Page: ${window.location.href}" in script
    assert "@media print" in stylesheet
    assert "#data-quality-panel" in stylesheet
    assert ".metric:not([open]) > :not(summary)" in stylesheet


def test_public_app_places_result_sections_and_metrics_in_manager_reading_order():
    page = Path("public/index.html").read_text(encoding="utf-8")
    stylesheet = Path("public/styles.css").read_text(encoding="utf-8")

    assert "How to read this page" not in page
    assert 'id="assumptions" class="section-intro"' in page
    assert page.index('id="data-quality"') < page.index('id="print-result"')
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in stylesheet


def test_compare_channels_adds_only_the_missing_channels():
    script = Path("public/app.js").read_text(encoding="utf-8")

    assert 'const firstChannel = first.querySelector("[name=channel]").value;' in script
    assert '["DTC Online", "Retail/Grocery", "Gym & Office"].filter((channel) => channel !== firstChannel)' in script
    assert '["Retail/Grocery", "Gym & Office"].forEach((channel) => {' not in script


def test_public_app_shows_the_api_rejection_reason():
    script = Path("public/app.js").read_text(encoding="utf-8")

    assert 'if (typeof detail?.reason === "string") throw new Error(`Scenario input rejected: ${detail.reason}.`);' in script


def test_money_formatter_does_not_show_negative_zero():
    script = Path("public/app.js").read_text(encoding="utf-8")

    assert ".format(Math.round(value * 100) / 100 || 0);" in script
