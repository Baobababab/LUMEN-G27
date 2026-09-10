from data_loader import cleaning_report, load_all


frames = load_all()

assert len(frames["historical_sales_weekly"]) == 702
assert not frames["historical_sales_weekly"].duplicated().any()
assert {"first_name", "last_name", "email"}.isdisjoint(frames["customer_survey"].columns)

report = cleaning_report()
assert report["duplicate_rows_removed"] == 4
assert report["pii_columns_excluded"] == ["first_name", "last_name", "email"]
assert report["anomaly_weeks_flagged"][0]["week"] == "2025-07-28"
assert report["anomaly_weeks_flagged"][0]["classification"] == "genuine seasonal peak"
