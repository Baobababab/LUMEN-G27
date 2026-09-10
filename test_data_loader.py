from data_loader import cleaning_report, load_all_data


def test_data_is_loaded_and_cleaned():
    frames = load_all_data()

    assert len(frames) == 12
    assert len(frames["historical_sales_weekly"]) == 702
    assert not frames["historical_sales_weekly"].duplicated().any()
    assert frames["historical_sales_weekly"]["anomaly_flag"].sum() == 9
    assert {"first_name", "last_name", "email"}.isdisjoint(frames["customer_survey"].columns)

    report = cleaning_report()
    assert report["duplicate_rows_removed"]["count"] == 4
    assert report["pii_columns_excluded"]["by_file"]["customer_survey.csv"] == ["first_name", "last_name", "email"]
    assert report["anomaly_weeks_flagged"]["by_file"]["historical_sales_weekly.csv"][0]["week"] == "2025-07-28"
    assert report["anomaly_weeks_flagged"]["by_file"]["historical_sales_weekly.csv"][0]["classification"] == "genuine seasonal peak"
