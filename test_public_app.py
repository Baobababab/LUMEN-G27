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
