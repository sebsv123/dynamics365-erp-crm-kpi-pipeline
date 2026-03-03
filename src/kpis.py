"""
Compute business KPIs from processed tables.

Support KPIs  : SLA compliance rate, average resolution hours, CSAT, breach rate by priority.
Sales KPIs    : closed-won count, win rate, open pipeline value.

Writes outputs/kpi_table.csv.
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PROC_DIR = BASE_DIR / "data" / "processed"
RAW_DIR = BASE_DIR / "data" / "raw"
OUT_DIR = BASE_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    case_features = pd.read_csv(
        PROC_DIR / "case_features.csv", parse_dates=["created_at", "resolved_at"]
    )
    opps = pd.read_csv(RAW_DIR / "opportunities.csv", parse_dates=["created_at", "close_at"])

    kpis = []

    # ── Support KPIs ──────────────────────────────────────────────────────────
    total_cases = len(case_features)
    sla_rate = 1 - case_features["sla_breached"].mean()          # % cases resolved within SLA
    avg_res_h = case_features["resolution_hours"].mean()          # mean time-to-resolution
    csat_avg = case_features["csat"].mean()                       # average customer satisfaction

    kpis += [
        ("support_total_cases", int(total_cases)),
        ("support_sla_compliance_rate", round(float(sla_rate), 4)),
        ("support_avg_resolution_hours", round(float(avg_res_h), 2)),
        ("support_avg_csat", round(float(csat_avg), 2)),
    ]

    # SLA breach rate broken down by ticket priority
    prio = (
        case_features.groupby("priority")["sla_breached"].mean()
        .sort_values(ascending=False)
    )
    for p, v in prio.items():
        kpis.append((f"support_sla_breach_rate_{p.lower()}", round(float(v), 4)))

    # ── Sales KPIs ────────────────────────────────────────────────────────────
    won = (opps["stage"] == "Closed Won").sum()
    lost = (opps["stage"] == "Closed Lost").sum()
    closed = won + lost
    win_rate = (won / closed) if closed else 0.0                  # closed-won / (won + lost)
    pipe_value = opps.loc[                                        # EUR value in active stages
        ~opps["stage"].str.contains("Closed"), "amount_eur"
    ].sum()

    kpis += [
        ("sales_closed_won", int(won)),
        ("sales_closed_lost", int(lost)),
        ("sales_win_rate", round(float(win_rate), 4)),
        ("sales_open_pipeline_value_eur", round(float(pipe_value), 2)),
    ]

    out = pd.DataFrame(kpis, columns=["metric", "value"])
    out.to_csv(OUT_DIR / "kpi_table.csv", index=False)
    print("✅ Wrote outputs/kpi_table.csv")


if __name__ == "__main__":
    main()
