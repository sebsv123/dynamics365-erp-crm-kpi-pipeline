"""
ETL step for the Dynamics 365-like KPI pipeline.

Reads raw CSVs produced by generate_data, parses datetimes, performs basic
data-quality checks, and writes a processed 'case_features' table that joins
Case with Account attributes — ready for KPI computation and ML.
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROC_DIR = BASE_DIR / "data" / "processed"
OUT_DIR = BASE_DIR / "outputs"
PROC_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _read(name: str) -> pd.DataFrame:
    """Load a raw CSV by filename; raises FileNotFoundError with a helpful message."""
    path = RAW_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run `python -m src.generate_data` first.")
    return pd.read_csv(path)


def quality_report(df: pd.DataFrame, name: str) -> dict:
    """Return a dict with row/column counts, missing-cell count, and duplicate-row count."""
    return {
        "table": name,
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def main() -> None:
    accounts = _read("accounts.csv")
    cases = _read("cases.csv")
    opps = _read("opportunities.csv")
    wos = _read("work_orders.csv")

    for col in ["created_at", "resolved_at"]:
        cases[col] = pd.to_datetime(cases[col])
    for col in ["created_at", "close_at"]:
        opps[col] = pd.to_datetime(opps[col], errors="coerce")
    for col in ["created_at", "scheduled_at", "completed_at"]:
        wos[col] = pd.to_datetime(wos[col])

    case_features = cases.merge(accounts, on="account_id", how="left", validate="many_to_one")
    case_features["created_dow"] = case_features["created_at"].dt.dayofweek
    case_features["created_hour"] = case_features["created_at"].dt.hour

    case_features.to_csv(PROC_DIR / "case_features.csv", index=False)

    reports = [
        quality_report(accounts, "accounts"),
        quality_report(cases, "cases"),
        quality_report(opps, "opportunities"),
        quality_report(wos, "work_orders"),
        quality_report(case_features, "case_features"),
    ]
    pd.DataFrame(reports).to_csv(OUT_DIR / "data_quality_report.csv", index=False)

    print("✅ Wrote processed tables to:", PROC_DIR)
    print("✅ Wrote outputs/data_quality_report.csv")


if __name__ == "__main__":
    main()
