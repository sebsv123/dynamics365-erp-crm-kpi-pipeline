"""
Create simple visuals for the README (saved to outputs/).

Plots generated:
  - sla_breach_by_priority.png  : SLA breach rate grouped by ticket priority
  - opportunities_by_stage.png  : Opportunity count grouped by pipeline stage
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROC_DIR = BASE_DIR / "data" / "processed"
OUT_DIR = BASE_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    cases = pd.read_csv(PROC_DIR / "case_features.csv")
    opps = pd.read_csv(RAW_DIR / "opportunities.csv")

    # Plot 1: SLA breach rate by priority
    breach = cases.groupby("priority")["sla_breached"].mean().sort_values(ascending=False)
    plt.figure(figsize=(10, 6))
    breach.plot(kind="bar")
    plt.title("SLA breach rate by priority")
    plt.ylabel("Breach rate")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "sla_breach_by_priority.png", dpi=160)
    plt.close()

    # Plot 2: Opportunities by stage
    stage_counts = opps["stage"].value_counts()
    plt.figure(figsize=(10, 6))
    stage_counts.plot(kind="bar")
    plt.title("Opportunities by stage")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "opportunities_by_stage.png", dpi=160)
    plt.close()

    print("✅ Wrote outputs/sla_breach_by_priority.png and outputs/opportunities_by_stage.png")


if __name__ == "__main__":
    main()
