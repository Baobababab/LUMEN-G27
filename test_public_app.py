from pathlib import Path


def test_scenario_reader_uses_fieldset_controls():
    script = Path("public/app.js").read_text(encoding="utf-8")

    assert "new FormData(fields)" not in script
    assert 'fields.elements.namedItem(name).value' in script
