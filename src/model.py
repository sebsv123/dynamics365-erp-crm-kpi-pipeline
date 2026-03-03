"""
Train a lightweight baseline model to flag SLA breach risk.

Algorithm : LogisticRegression with class balancing.
Encoding  : OneHotEncoder for categorical fields via ColumnTransformer.
Output    : outputs/model_metrics.json
"""
from __future__ import annotations

import json
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    precision_recall_fscore_support,
)
from sklearn.linear_model import LogisticRegression

BASE_DIR = Path(__file__).resolve().parents[1]
PROC_DIR = BASE_DIR / "data" / "processed"
OUT_DIR = BASE_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(PROC_DIR / "case_features.csv", parse_dates=["created_at", "resolved_at"])

    target = "sla_breached"
    feature_cols = [
        "priority", "channel", "case_type",
        "country", "segment", "tier",
        "employees", "tenure_months",
        "created_dow", "created_hour",
        "sla_hours",
    ]
    X = df[feature_cols].copy()
    y = df[target].astype(int)

    cat_cols = ["priority", "channel", "case_type", "country", "segment", "tier"]
    num_cols = [c for c in feature_cols if c not in cat_cols]

    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )

    clf = LogisticRegression(max_iter=500, class_weight="balanced")
    pipe = Pipeline([("pre", pre), ("clf", clf)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    pipe.fit(X_train, y_train)

    proba = pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    roc = roc_auc_score(y_test, proba)
    ap = average_precision_score(y_test, proba)
    acc = accuracy_score(y_test, pred)
    p, r, f1, _ = precision_recall_fscore_support(
        y_test, pred, average="binary", zero_division=0
    )

    # Metrics dict — each key is explained below:
    #   roc_auc          : area under the ROC curve (discrimination ability)
    #   avg_precision    : area under precision-recall curve (useful for imbalanced classes)
    #   accuracy         : overall fraction of correct predictions
    #   precision        : of all predicted breaches, how many were real
    #   recall           : of all actual breaches, how many were caught
    #   f1               : harmonic mean of precision and recall
    #   positive_rate_test: fraction of test cases that actually breached SLA
    metrics = {
        "roc_auc": float(round(roc, 4)),
        "avg_precision": float(round(ap, 4)),
        "accuracy": float(round(acc, 4)),
        "precision": float(round(p, 4)),
        "recall": float(round(r, 4)),
        "f1": float(round(f1, 4)),
        "positive_rate_test": float(round(float(y_test.mean()), 4)),
        "model": "LogisticRegression + OneHotEncoder",
        "target": "SLA breach risk (sla_breached)",
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "features": feature_cols,
    }

    (OUT_DIR / "model_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("✅ Wrote outputs/model_metrics.json")


if __name__ == "__main__":
    main()
