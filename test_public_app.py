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
