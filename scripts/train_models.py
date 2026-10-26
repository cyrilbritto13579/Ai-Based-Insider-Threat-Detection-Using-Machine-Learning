"""
Model Training & Evaluation
=============================
Phase 8-9: Train and compare LR, RF, XGBoost on the temporally-split
CERT r4.2 user-day features. Persist the best model pipeline.

This script:
  1. Loads the temporal train/val/test splits from Phase 7
  2. Trains Logistic Regression, Random Forest, and XGBoost
  3. Evaluates on validation set, selects best model
  4. Final evaluation on held-out test set
  5. Persists model, feature schema, threshold, metadata
  6. Generates SHAP explanations for the best model

Usage:
    python scripts/train_models.py

Output:
    data/artifacts/best_model.joblib
    data/artifacts/model_comparison.json
    data/artifacts/model_metadata.json
    data/artifacts/feature_schema.json
    data/artifacts/shap_global_importance.json
"""

import os
import sys
import json
import time
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    f1_score,
    precision_score,
    recall_score,
    average_precision_score,
)
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# Optional: XGBoost
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("WARNING: xgboost not installed. Skipping XGBoost model.")

# Optional: SHAP
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    print("WARNING: shap not installed. Skipping SHAP explanations.")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "data", "artifacts")

RANDOM_STATE = 42
LABEL_COL = "is_malicious"
DROP_COLS = ["user", "date_only", "is_malicious"]


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_step(msg: str):
    print(f"  >> {msg}")


# ===========================================================================
# Data Loading
# ===========================================================================
def load_splits():
    """Load the temporal train/val/test splits."""
    print_section("Loading Data Splits")

    train = pd.read_parquet(os.path.join(PROCESSED_DIR, "split_train.parquet"))
    val = pd.read_parquet(os.path.join(PROCESSED_DIR, "split_val.parquet"))
    test = pd.read_parquet(os.path.join(PROCESSED_DIR, "split_test.parquet"))

    for name, df in [("Train", train), ("Val", val), ("Test", test)]:
        n_mal = df[LABEL_COL].sum()
        print_step(f"{name}: {len(df):,} rows, {n_mal:,} malicious ({100*n_mal/len(df):.2f}%)")

    return train, val, test


def prepare_features(train, val, test):
    """
    Extract feature matrices and labels.
    Apply StandardScaler (fit on train only) for Logistic Regression.
    """
    feature_cols = [c for c in train.columns if c not in DROP_COLS]

    X_train = train[feature_cols].values.astype(np.float32)
    y_train = train[LABEL_COL].values
    X_val = val[feature_cols].values.astype(np.float32)
    y_val = val[LABEL_COL].values
    X_test = test[feature_cols].values.astype(np.float32)
    y_test = test[LABEL_COL].values

    # Handle any remaining NaN/inf
    for X in [X_train, X_val, X_test]:
        np.nan_to_num(X, copy=False, nan=0.0, posinf=0.0, neginf=0.0)

    # Fit scaler on training data only
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    print_step(f"Features: {len(feature_cols)}")
    print_step(f"Feature names: {feature_cols}")

    return {
        "feature_cols": feature_cols,
        "X_train": X_train,
        "X_train_scaled": X_train_scaled,
        "y_train": y_train,
        "X_val": X_val,
        "X_val_scaled": X_val_scaled,
        "y_val": y_val,
        "X_test": X_test,
        "X_test_scaled": X_test_scaled,
        "y_test": y_test,
        "scaler": scaler,
    }


# ===========================================================================
# Model Definitions
# ===========================================================================
def get_models(imbalance_ratio: float):
    """
    Initialize models with class-imbalance aware settings.

    Parameters
    ----------
    imbalance_ratio : float
        Ratio of negative to positive samples (e.g., 240 for 0.41% positive).
    """
    models = {}

    models["Logistic Regression"] = {
        "model": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            C=1.0,
            solver="lbfgs",
            random_state=RANDOM_STATE,
        ),
        "needs_scaling": True,
    }

    models["Random Forest"] = {
        "model": RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=10,
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        "needs_scaling": False,
    }

    if HAS_XGBOOST:
        models["XGBoost"] = {
            "model": xgb.XGBClassifier(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                scale_pos_weight=imbalance_ratio,
                eval_metric="aucpr",
                min_child_weight=5,
                subsample=0.8,
                colsample_bytree=0.8,
                n_jobs=-1,
                random_state=RANDOM_STATE,
            ),
            "needs_scaling": False,
        }

    return models


# ===========================================================================
# Training & Evaluation
# ===========================================================================
def find_optimal_threshold(y_true, y_prob, metric="f1"):
    """Find threshold that maximizes F1 on the given data."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)

    best_idx = np.argmax(f1_scores)
    if best_idx < len(thresholds):
        return float(thresholds[best_idx])
    return 0.5


def evaluate_model(y_true, y_prob, threshold=0.5):
    """Compute all evaluation metrics at a given threshold."""
    y_pred = (y_prob >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    metrics = {
        "threshold": round(threshold, 6),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 4),
        "pr_auc": round(float(average_precision_score(y_true, y_prob)), 4),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "total_positives": int(tp + fn),
        "total_negatives": int(tn + fp),
    }

    return metrics


def train_and_evaluate_all(models, data):
    """Train all models, evaluate on validation set, return results."""
    print_section("Phase 8: Model Training & Evaluation")

    results = {}

    for name, config in models.items():
        print(f"\n  --- {name} ---")
        model = config["model"]
        needs_scaling = config["needs_scaling"]

        # Select appropriate feature matrix
        X_tr = data["X_train_scaled"] if needs_scaling else data["X_train"]
        X_va = data["X_val_scaled"] if needs_scaling else data["X_val"]

        # Train
        t0 = time.time()
        model.fit(X_tr, data["y_train"])
        train_time = time.time() - t0
        print_step(f"Training time: {train_time:.1f}s")

        # Get probabilities
        y_prob_val = model.predict_proba(X_va)[:, 1]

        # Find optimal threshold on validation set
        opt_threshold = find_optimal_threshold(data["y_val"], y_prob_val)
        print_step(f"Optimal threshold (F1): {opt_threshold:.4f}")

        # Evaluate at optimal threshold
        val_metrics = evaluate_model(data["y_val"], y_prob_val, opt_threshold)
        val_metrics["train_time_seconds"] = round(train_time, 1)

        print_step(f"Precision: {val_metrics['precision']}")
        print_step(f"Recall:    {val_metrics['recall']}")
        print_step(f"F1:        {val_metrics['f1']}")
        print_step(f"ROC-AUC:   {val_metrics['roc_auc']}")
        print_step(f"PR-AUC:    {val_metrics['pr_auc']}")
        print_step(f"TP: {val_metrics['tp']}  FP: {val_metrics['fp']}  "
                   f"FN: {val_metrics['fn']}  TN: {val_metrics['tn']}")

        results[name] = {
            "model": model,
            "config": config,
            "val_metrics": val_metrics,
            "opt_threshold": opt_threshold,
            "y_prob_val": y_prob_val,
        }

    return results


def select_best_model(results):
    """Select the best model based on PR-AUC (most appropriate for rare events)."""
    print_section("Model Selection")

    # Compare by PR-AUC (primary), then F1 (secondary)
    comparison = []
    for name, r in results.items():
        m = r["val_metrics"]
        comparison.append({
            "model": name,
            "pr_auc": m["pr_auc"],
            "f1": m["f1"],
            "recall": m["recall"],
            "precision": m["precision"],
            "roc_auc": m["roc_auc"],
        })

    comparison.sort(key=lambda x: (x["pr_auc"], x["f1"]), reverse=True)

    print("  Validation Set Ranking:")
    print(f"  {'Model':<25s} {'PR-AUC':>8s} {'F1':>8s} {'Recall':>8s} {'Prec':>8s} {'ROC-AUC':>8s}")
    print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    for c in comparison:
        marker = " <-- BEST" if c == comparison[0] else ""
        print(f"  {c['model']:<25s} {c['pr_auc']:>8.4f} {c['f1']:>8.4f} "
              f"{c['recall']:>8.4f} {c['precision']:>8.4f} {c['roc_auc']:>8.4f}{marker}")

    best_name = comparison[0]["model"]
    print_step(f"Selected: {best_name}")

    return best_name


def final_evaluation(best_name, results, data):
    """Evaluate the best model on the held-out test set."""
    print_section("Final Evaluation (Test Set)")

    r = results[best_name]
    model = r["model"]
    threshold = r["opt_threshold"]
    needs_scaling = r["config"]["needs_scaling"]

    X_te = data["X_test_scaled"] if needs_scaling else data["X_test"]
    y_prob_test = model.predict_proba(X_te)[:, 1]

    test_metrics = evaluate_model(data["y_test"], y_prob_test, threshold)

    print_step(f"Model:     {best_name}")
    print_step(f"Threshold: {threshold:.4f}")
    print_step(f"Precision: {test_metrics['precision']}")
    print_step(f"Recall:    {test_metrics['recall']}")
    print_step(f"F1:        {test_metrics['f1']}")
    print_step(f"ROC-AUC:   {test_metrics['roc_auc']}")
    print_step(f"PR-AUC:    {test_metrics['pr_auc']}")
    print_step(f"TP: {test_metrics['tp']}  FP: {test_metrics['fp']}  "
               f"FN: {test_metrics['fn']}  TN: {test_metrics['tn']}")

    # Also evaluate all models on test for comparison
    all_test_metrics = {}
    for name, res in results.items():
        m = res["model"]
        ns = res["config"]["needs_scaling"]
        X = data["X_test_scaled"] if ns else data["X_test"]
        y_prob = m.predict_proba(X)[:, 1]
        t_metrics = evaluate_model(data["y_test"], y_prob, res["opt_threshold"])
        all_test_metrics[name] = t_metrics

    return test_metrics, all_test_metrics


# ===========================================================================
# SHAP Explainability
# ===========================================================================
def compute_shap_importance(model, X_train, feature_cols, best_name):
    """Compute global SHAP feature importance for tree-based models."""
    if not HAS_SHAP:
        print_step("SHAP not available. Skipping.")
        return None

    print_section("Phase 11: SHAP Explainability")

    is_tree = "Forest" in best_name or "XGBoost" in best_name

    if is_tree:
        print_step("Using TreeExplainer (fast, exact for tree models)...")
        explainer = shap.TreeExplainer(model)

        # Use a sample for global importance (full dataset too slow)
        sample_size = min(5000, len(X_train))
        np.random.seed(RANDOM_STATE)
        indices = np.random.choice(len(X_train), sample_size, replace=False)
        X_sample = X_train[indices]

        shap_values = explainer.shap_values(X_sample)
    else:
        print_step("Using LinearExplainer for Logistic Regression...")
        explainer = shap.LinearExplainer(model, X_train)
        sample_size = min(5000, len(X_train))
        np.random.seed(RANDOM_STATE)
        indices = np.random.choice(len(X_train), sample_size, replace=False)
        X_sample = X_train[indices]
        shap_values = explainer.shap_values(X_sample)

    # Handle multi-output SHAP values (take positive class)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]  # positive class
    elif len(shap_values.shape) == 3:
        shap_values = shap_values[:, :, 1]

    # Compute mean absolute SHAP value per feature
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance = sorted(
        zip(feature_cols, mean_abs_shap.tolist()),
        key=lambda x: x[1],
        reverse=True,
    )

    print_step("Global Feature Importance (SHAP):")
    for i, (feat, val) in enumerate(importance[:15]):
        print(f"    {i+1:2d}. {feat:<40s} {val:.4f}")

    return {
        "importance": [{"feature": f, "mean_abs_shap": round(v, 6)} for f, v in importance],
        "sample_size": sample_size,
        "explainer_type": "TreeExplainer" if is_tree else "LinearExplainer",
    }


# ===========================================================================
# Persistence
# ===========================================================================
def save_artifacts(best_name, results, data, test_metrics, all_test_metrics, shap_result):
    """Save model, metadata, and evaluation results."""
    print_section("Phase 9: Saving Model Artifacts")

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    r = results[best_name]
    model = r["model"]
    threshold = r["opt_threshold"]

    # 1. Save model
    model_path = os.path.join(ARTIFACTS_DIR, "best_model.joblib")
    joblib.dump(model, model_path)
    print_step(f"Model saved: {model_path}")

    # 2. Save scaler (for LR)
    scaler_path = os.path.join(ARTIFACTS_DIR, "scaler.joblib")
    joblib.dump(data["scaler"], scaler_path)
    print_step(f"Scaler saved: {scaler_path}")

    # 3. Save feature schema
    schema = {
        "feature_columns": data["feature_cols"],
        "num_features": len(data["feature_cols"]),
        "label_column": LABEL_COL,
        "drop_columns": DROP_COLS,
    }
    schema_path = os.path.join(ARTIFACTS_DIR, "feature_schema.json")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)
    print_step(f"Feature schema saved: {schema_path}")

    # 4. Save model metadata
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "best_model_name": best_name,
        "best_model_type": type(model).__name__,
        "optimal_threshold": threshold,
        "needs_scaling": r["config"]["needs_scaling"],
        "validation_metrics": r["val_metrics"],
        "test_metrics": test_metrics,
        "risk_tier_thresholds": {
            "low_max": 29,
            "medium_max": 59,
            "high_max": 79,
            "critical_min": 80,
        },
    }
    meta_path = os.path.join(ARTIFACTS_DIR, "model_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    print_step(f"Metadata saved: {meta_path}")

    # 5. Save full comparison results
    comparison = {
        "generated_at": datetime.now().isoformat(),
        "models": {},
    }
    for name, res in results.items():
        comparison["models"][name] = {
            "validation_metrics": res["val_metrics"],
            "test_metrics": all_test_metrics.get(name, {}),
            "optimal_threshold": res["opt_threshold"],
            "model_type": type(res["model"]).__name__,
            "is_best": name == best_name,
        }
    comp_path = os.path.join(ARTIFACTS_DIR, "model_comparison.json")
    with open(comp_path, "w") as f:
        json.dump(comparison, f, indent=2, default=str)
    print_step(f"Comparison saved: {comp_path}")

    # 6. Save SHAP importance
    if shap_result:
        shap_path = os.path.join(ARTIFACTS_DIR, "shap_global_importance.json")
        with open(shap_path, "w") as f:
            json.dump(shap_result, f, indent=2)
        print_step(f"SHAP importance saved: {shap_path}")


# ===========================================================================
# Main
# ===========================================================================
def main():
    t_start = time.time()
    print(f"\n{'='*60}")
    print(f"  Model Training & Evaluation Pipeline")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # Load data
    train, val, test = load_splits()
    data = prepare_features(train, val, test)

    # Compute imbalance ratio
    n_pos = data["y_train"].sum()
    n_neg = len(data["y_train"]) - n_pos
    imbalance_ratio = n_neg / max(n_pos, 1)
    print_step(f"Imbalance ratio: {imbalance_ratio:.1f}:1 (negative:positive)")

    # Get models
    models = get_models(imbalance_ratio)

    # Train and evaluate on validation set
    results = train_and_evaluate_all(models, data)

    # Select best model
    best_name = select_best_model(results)

    # Final evaluation on test set
    test_metrics, all_test_metrics = final_evaluation(best_name, results, data)

    # SHAP
    r = results[best_name]
    needs_scaling = r["config"]["needs_scaling"]
    X_for_shap = data["X_train_scaled"] if needs_scaling else data["X_train"]
    shap_result = compute_shap_importance(
        r["model"], X_for_shap, data["feature_cols"], best_name
    )

    # Save everything
    save_artifacts(best_name, results, data, test_metrics, all_test_metrics, shap_result)

    elapsed = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"  Training pipeline complete in {elapsed:.1f}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
