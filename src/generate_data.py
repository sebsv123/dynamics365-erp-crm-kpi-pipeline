"""
Generate synthetic Dynamics 365-like ERP/CRM tables.

Mimics the core entities you'd find in a Dynamics 365 / Dataverse environment:
  - Account         (master)
  - Opportunity     (Sales module)
  - Case            (Customer Service module, including SLA / CSAT)
  - Work Order      (Field Service module)

Tables are written to data/raw/ and are fully reproducible from a fixed seed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def _date_range(start: str, end: str, n: int) -> pd.DatetimeIndex:
    start_dt = np.datetime64(start)
    end_dt = np.datetime64(end)
    span = (end_dt - start_dt).astype("timedelta64[s]").astype(int)
    seconds = RNG.integers(0, max(span, 1), size=n)
    return pd.to_datetime(start_dt + seconds.astype("timedelta64[s]"))


def make_accounts(n: int = 350) -> pd.DataFrame:
    """Return a DataFrame of synthetic Account records."""
    countries = ["ES", "PT", "FR", "DE", "IT"]
    segments = ["SMB", "Mid", "Enterprise"]
    tiers = ["Bronze", "Silver", "Gold", "Platinum"]

    df = pd.DataFrame({
        "account_id": [f"A{str(i).zfill(5)}" for i in range(1, n + 1)],
        "country": RNG.choice(countries, size=n, p=[0.55, 0.10, 0.15, 0.10, 0.10]),
        "segment": RNG.choice(segments, size=n, p=[0.60, 0.30, 0.10]),
        "tier": RNG.choice(tiers, size=n, p=[0.35, 0.35, 0.22, 0.08]),
        "employees": RNG.integers(5, 5000, size=n),
        "tenure_months": RNG.integers(1, 120, size=n),
    })
    return df


def make_opportunities(accounts: pd.DataFrame, n: int = 1200) -> pd.DataFrame:
    """Return a DataFrame of synthetic Opportunity records linked to accounts."""
    stages = ["Lead", "Qualify", "Propose", "Negotiate", "Closed Won", "Closed Lost"]
    stage_probs = [0.15, 0.20, 0.20, 0.15, 0.15, 0.15]
    created = _date_range("2025-09-01", "2026-03-01", n)

    base_amount = RNG.lognormal(mean=9.5, sigma=0.8, size=n)
    tier_multiplier = accounts.set_index("account_id")["tier"].map({
        "Bronze": 0.8, "Silver": 1.0, "Gold": 1.2, "Platinum": 1.5
    })
    acc_ids = RNG.choice(accounts["account_id"], size=n)
    mult = tier_multiplier.loc[acc_ids].to_numpy()
    amount = (base_amount * mult).round(2)

    stage = RNG.choice(stages, size=n, p=stage_probs)
    close_days = RNG.integers(7, 120, size=n)
    close_date = created + pd.to_timedelta(close_days, unit="D")
    close_date = close_date.where(pd.Series(stage).str.contains("Closed"), pd.NaT)

    df = pd.DataFrame({
        "opportunity_id": [f"O{str(i).zfill(6)}" for i in range(1, n + 1)],
        "account_id": acc_ids,
        "created_at": created,
        "stage": stage,
        "amount_eur": amount,
        "close_at": close_date,
    })
    df["is_won"] = (df["stage"] == "Closed Won").astype(int)
    return df


def make_cases(accounts: pd.DataFrame, n: int = 2200) -> pd.DataFrame:
    """Return a DataFrame of synthetic Case records with SLA and CSAT fields."""
    priorities = ["Low", "Medium", "High", "Critical"]
    channels = ["Email", "Phone", "Web", "Chat"]
    case_types = ["Bug", "HowTo", "Billing", "Outage", "FeatureRequest"]

    created = _date_range("2025-09-01", "2026-03-01", n)

    acc_ids = RNG.choice(accounts["account_id"], size=n)
    prio = RNG.choice(priorities, size=n, p=[0.25, 0.45, 0.22, 0.08])
    channel = RNG.choice(channels, size=n, p=[0.40, 0.20, 0.25, 0.15])
    ctype = RNG.choice(case_types, size=n, p=[0.30, 0.20, 0.20, 0.10, 0.20])

    sla_hours = pd.Series(prio).map({"Low": 72, "Medium": 48, "High": 24, "Critical": 8}).to_numpy()

    tier = accounts.set_index("account_id").loc[acc_ids, "tier"].to_numpy()
    tier_factor = pd.Series(tier).map({"Bronze": 1.15, "Silver": 1.0, "Gold": 0.9, "Platinum": 0.8}).to_numpy()
    base_res_hours = RNG.gamma(shape=2.5, scale=10.0, size=n)
    prio_factor = pd.Series(prio).map({"Low": 1.1, "Medium": 1.0, "High": 0.9, "Critical": 0.75}).to_numpy()
    type_factor = pd.Series(ctype).map(
        {"Bug": 1.0, "HowTo": 0.9, "Billing": 0.85, "Outage": 1.4, "FeatureRequest": 1.2}
    ).to_numpy()

    res_hours = base_res_hours * prio_factor * tier_factor * type_factor

    day = pd.to_datetime(created).normalize()
    load = pd.Series(day).map(
        lambda d: 1.0 + 0.35 * np.sin((d.dayofyear / 365) * 2 * np.pi) + 0.25 * (d.weekday() in [0, 1])
    ).to_numpy()
    res_hours *= load

    resolved = pd.to_datetime(created) + pd.to_timedelta(res_hours, unit="h")

    df = pd.DataFrame({
        "case_id": [f"C{str(i).zfill(7)}" for i in range(1, n + 1)],
        "account_id": acc_ids,
        "created_at": pd.to_datetime(created),
        "resolved_at": resolved,
        "priority": prio,
        "channel": channel,
        "case_type": ctype,
        "sla_hours": sla_hours.astype(int),
        "resolution_hours": np.round(res_hours, 2),
    })
    df["sla_breached"] = (df["resolution_hours"] > df["sla_hours"]).astype(int)
    sat = 5 - (df["resolution_hours"] / 48).clip(0, 4) - 1.2 * df["sla_breached"]
    df["csat"] = sat.clip(1, 5).round(1)
    return df


def make_work_orders(accounts: pd.DataFrame, n: int = 900) -> pd.DataFrame:
    """Return a DataFrame of synthetic Work Order records (Field Service)."""
    wo_types = ["Preventive", "Corrective", "Installation", "Inspection"]
    created = _date_range("2025-09-01", "2026-03-01", n)
    acc_ids = RNG.choice(accounts["account_id"], size=n)
    wotype = RNG.choice(wo_types, size=n, p=[0.30, 0.35, 0.20, 0.15])

    planned = RNG.normal(loc=6.0, scale=2.0, size=n).clip(1.0, 16.0)
    type_factor = pd.Series(wotype).map(
        {"Preventive": 0.9, "Corrective": 1.2, "Installation": 1.4, "Inspection": 0.8}
    ).to_numpy()
    actual = planned * type_factor * RNG.normal(1.0, 0.15, size=n)
    actual = actual.clip(0.5, 24.0)

    scheduled = pd.to_datetime(created) + pd.to_timedelta(RNG.integers(1, 14, size=n), unit="D")
    completed = scheduled + pd.to_timedelta(actual, unit="h")

    df = pd.DataFrame({
        "work_order_id": [f"W{str(i).zfill(6)}" for i in range(1, n + 1)],
        "account_id": acc_ids,
        "created_at": pd.to_datetime(created),
        "scheduled_at": scheduled,
        "completed_at": completed,
        "wo_type": wotype,
        "planned_hours": np.round(planned, 2),
        "actual_hours": np.round(actual, 2),
    })
    df["on_time"] = (df["actual_hours"] <= df["planned_hours"] * 1.05).astype(int)
    return df


def main() -> None:
    accounts = make_accounts()
    opps = make_opportunities(accounts)
    cases = make_cases(accounts)
    wos = make_work_orders(accounts)

    accounts.to_csv(RAW_DIR / "accounts.csv", index=False)
    opps.to_csv(RAW_DIR / "opportunities.csv", index=False)
    cases.to_csv(RAW_DIR / "cases.csv", index=False)
    wos.to_csv(RAW_DIR / "work_orders.csv", index=False)

    print("✅ Wrote raw tables to:", RAW_DIR)


if __name__ == "__main__":
    main()
