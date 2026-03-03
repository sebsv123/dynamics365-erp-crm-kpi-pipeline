# Demo Checklist — Dynamics 365 ERP/CRM KPI Pipeline

Use this checklist when walking through the project during an interview or demo.

## Setup
- [ ] Clone the repo
- [ ] `pip install -r requirements.txt`

## Run the pipeline
- [ ] `python -m src.generate_data`  — generates synthetic Dynamics-like tables
- [ ] `python -m src.etl`            — parses datetimes, joins, quality report
- [ ] `python -m src.kpis`           — writes `outputs/kpi_table.csv`
- [ ] `python -m src.model`          — trains SLA breach risk model, writes `outputs/model_metrics.json`
- [ ] `python -m src.plots`          — writes two PNG plots to `outputs/`

## Notebooks
- [ ] Open `notebooks/00_Quickstart.ipynb` and run all cells end-to-end
- [ ] Open `notebooks/01_Model_SLA_Risk.ipynb` and walk through the model deep-dive

## Key talking points
- [ ] Explain the Dynamics 365 entity model (Account → Case / Opportunity / Work Order)
- [ ] Explain SLA breach risk as a classification problem
- [ ] Describe how `src/d365_connector_template.py` would integrate with a live Dataverse org
- [ ] Show KPI catalogue in `outputs/kpi_table.csv`
- [ ] Show model metrics (ROC AUC ≈ 0.83, Avg Precision ≈ 0.60) in `outputs/model_metrics.json`
