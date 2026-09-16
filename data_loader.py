from pathlib import Path
from typing import Any

from functools import lru_cache
import pandas as pd


_DATA_DIR = Path(__file__).resolve().parent / "data"
_PII_COLUMNS = ("respondent_id", "first_name", "last_name", "email")
_ANOMALY_WEEK = "2025-07-28"
_ANOMALY_FLAG_COLUMN = "anomaly_flag"
_report: dict[str, Any] | None = None


def _read_csv(path: Path, **kwargs: Any) -> pd.DataFrame:
    """Read one CSV and turn low-level read failures into a useful application error."""
    try:
        return pd.read_csv(path, **kwargs)
    except Exception as exc:
        raise RuntimeError(f"Unable to read CSV file '{path}': {exc}") from exc


def _anomaly_report(history: pd.DataFrame, seasonality: pd.DataFrame) -> dict[str, Any]:
    """Describe whether the known July week is consistent with seasonal demand."""
    dates = pd.to_datetime(history["week_start_date"], errors="coerce")
    weekly_totals = history.assign(_week=dates).groupby("_week")["units_sold"].sum()
    anomaly_date = pd.Timestamp(_ANOMALY_WEEK)
    anomaly_rows = dates.eq(anomaly_date)
    anomaly_total = float(weekly_totals.get(anomaly_date, 0))
    weekly_median = float(weekly_totals.median())

    july = seasonality.loc[seasonality["month"].eq(anomaly_date.month)]
    seasonal_index = None if july.empty else float(july.iloc[0]["seasonality_index_100_avg"])
    looks_seasonal = seasonal_index is not None and seasonal_index > 100
    classification = "genuine seasonal peak" if looks_seasonal else "possible defect"

    return {
        "week": _ANOMALY_WEEK,
        "file": "historical_sales_weekly.csv",
        "marker_column": _ANOMALY_FLAG_COLUMN,
        "rows_flagged": int(anomaly_rows.sum()),
        "classification": classification,
        "units_sold": int(anomaly_total),
        "weekly_median_units": int(round(weekly_median)),
        "seasonality_index_100_avg": seasonal_index,
        "reason": (
            f"The week totals {int(anomaly_total):,} units versus a weekly median of "
            f"{int(round(weekly_median)):,}; July's seasonality index is "
            f"{seasonal_index:g}, so it looks consistent with a seasonal peak."
            if looks_seasonal
            else "No above-average July seasonality index was found, so the spike should be treated as a possible defect."
        ),
    }


@lru_cache(maxsize=1)
def load_all() -> dict[str, pd.DataFrame]:
    """Load every CSV in ``data/`` and apply the documented cleaning rules."""
    global _report

    if not _DATA_DIR.is_dir():
        raise RuntimeError(f"Data directory does not exist: '{_DATA_DIR}'")

    paths = sorted(_DATA_DIR.glob("*.csv"))
    if not paths:
        raise RuntimeError(f"No CSV files found in data directory: '{_DATA_DIR}'")

    frames: dict[str, pd.DataFrame] = {}
    duplicate_rows_removed = 0
    pii_columns_by_file: dict[str, list[str]] = {}

    for path in paths:
        kwargs: dict[str, Any] = {}
        header = _read_csv(path, nrows=0)
        excluded_columns = [column for column in _PII_COLUMNS if column in header.columns]
        if excluded_columns:
            pii_columns_by_file[path.name] = excluded_columns
            kwargs["usecols"] = lambda column: column not in _PII_COLUMNS

        frame = _read_csv(path, **kwargs)
        if path.name == "historical_sales_weekly.csv":
            before = len(frame)
            frame = frame.drop_duplicates(ignore_index=True)
            duplicate_rows_removed = before - len(frame)
            dates = pd.to_datetime(frame["week_start_date"], errors="coerce")
            frame[_ANOMALY_FLAG_COLUMN] = dates.eq(pd.Timestamp(_ANOMALY_WEEK))

        frames[path.stem] = frame

    history = frames.get("historical_sales_weekly")
    seasonality = frames.get("seasonality_and_weather")
    if history is None or seasonality is None:
        missing = [name for name, frame in (("historical_sales_weekly", history), ("seasonality_and_weather", seasonality)) if frame is None]
        raise RuntimeError(f"Required CSV file(s) missing: {', '.join(missing)}")

    anomaly = _anomaly_report(history, seasonality)
    _report = {
        "duplicate_rows_removed": {
            "count": duplicate_rows_removed,
            "by_file": {
                "historical_sales_weekly.csv": {
                    "rows_removed": duplicate_rows_removed,
                    "rule": "drop exact duplicate rows across all columns, keeping the first occurrence",
                }
            },
        },
        "pii_columns_excluded": {
            "count": sum(len(columns) for columns in pii_columns_by_file.values()),
            "by_file": pii_columns_by_file,
        },
        "anomaly_weeks_flagged": {
            "count": anomaly["rows_flagged"],
            "by_file": {"historical_sales_weekly.csv": [anomaly]},
        },
    }
    return frames


def cleaning_report() -> dict[str, Any]:
    """Return what was removed or excluded and why the known anomaly was flagged."""
    if _report is None:
        load_all()
    return {
        "duplicate_rows_removed": {
            "count": _report["duplicate_rows_removed"]["count"],
            "by_file": {name: dict(details) for name, details in _report["duplicate_rows_removed"]["by_file"].items()},
        },
        "pii_columns_excluded": {
            "count": _report["pii_columns_excluded"]["count"],
            "by_file": {name: list(columns) for name, columns in _report["pii_columns_excluded"]["by_file"].items()},
        },
        "anomaly_weeks_flagged": {
            "count": _report["anomaly_weeks_flagged"]["count"],
            "by_file": {
                name: [dict(item) for item in items]
                for name, items in _report["anomaly_weeks_flagged"]["by_file"].items()
            },
        },
    }
