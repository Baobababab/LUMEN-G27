import pandas as pd

import data_loader
from data_loader import cleaning_report, load_all


_FORBIDDEN_COLUMNS = {"respondent_id", "first_name", "last_name", "email"}


def test_data_is_loaded_and_cleaned():
    frames = load_all()

    assert len(frames) == 12
    assert len(frames["historical_sales_weekly"]) == 702
    assert not frames["historical_sales_weekly"].duplicated().any()
    assert frames["historical_sales_weekly"]["anomaly_flag"].sum() == 9
    assert _FORBIDDEN_COLUMNS.isdisjoint(frames["customer_survey"].columns)

    report = cleaning_report()
    assert report["duplicate_rows_removed"]["count"] == 4
    assert report["pii_columns_excluded"]["by_file"]["customer_survey.csv"] == [
        "respondent_id",
        "first_name",
        "last_name",
        "email",
    ]
    assert report["anomaly_weeks_flagged"]["by_file"]["historical_sales_weekly.csv"][0]["week"] == "2025-07-28"
    assert report["anomaly_weeks_flagged"]["by_file"]["historical_sales_weekly.csv"][0]["classification"] == "genuine seasonal peak"


def test_synthetic_identifiers_are_excluded_before_loading(tmp_path, monkeypatch):
    sentinels = {
        "respondent_id": "synthetic-respondent-id",
        "first_name": "SyntheticFirst",
        "last_name": "SyntheticLast",
        "email": "synthetic@example.test",
    }
    pd.DataFrame([{**sentinels, "segment": "Synthetic segment"}]).to_csv(
        tmp_path / "customer_survey.csv", index=False
    )
    pd.DataFrame(
        [{"week_start_date": "2025-07-28", "units_sold": 1}]
    ).to_csv(tmp_path / "historical_sales_weekly.csv", index=False)
    pd.DataFrame(
        [{"month": 7, "seasonality_index_100_avg": 110}]
    ).to_csv(tmp_path / "seasonality_and_weather.csv", index=False)

    monkeypatch.setattr(data_loader, "_DATA_DIR", tmp_path)
    load_all.cache_clear()
    try:
        survey = load_all()["customer_survey"]
        assert _FORBIDDEN_COLUMNS.isdisjoint(survey.columns)
        assert not any(value in survey.to_string() for value in sentinels.values())
        assert cleaning_report()["pii_columns_excluded"]["count"] == 4
    finally:
        load_all.cache_clear()
