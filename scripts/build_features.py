"""
CERT r4.2 Data Pipeline
========================
Phases 3-6: Ground truth mapping, event ingestion, user-day aggregation,
behavioral feature engineering, and user-specific baselines.

This script:
  1. Parses insiders.csv to build a user -> malicious-date-range lookup
  2. Ingests logon, device, file, email CSVs with timestamp normalization
  3. Aggregates events into user-day windows
  4. Engineers behavioral features per source and cross-source
  5. Computes user-specific baselines and deviation features
  6. Applies ground-truth labels (user-day is malicious if it falls within
     an insider's malicious time window)
  7. Performs temporal train/validation/test split
  8. Saves the final labeled dataset to data/processed/

Usage:
    python scripts/build_features.py

Output:
    data/processed/user_day_features.parquet
    data/processed/user_day_features_labeled.parquet
    data/processed/pipeline_metadata.json
"""

import os
import sys
import json
import time
import warnings
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

# Working hours definition (for after-hours detection)
WORK_HOUR_START = 7   # 7 AM
WORK_HOUR_END = 18    # 6 PM

# Minimum days of history required before computing baseline
BASELINE_MIN_DAYS = 14

# Train / Validation / Test temporal split boundaries
# CERT data spans 2010-01-02 to 2011-05-17 (~16.5 months)
# Train: first 10 months  (2010-01-01 to 2010-10-31)
# Val:   next 3 months    (2010-11-01 to 2011-01-31)
# Test:  last 3.5 months  (2011-02-01 to 2011-05-31)
TRAIN_END = pd.Timestamp("2010-10-31")
VAL_END = pd.Timestamp("2011-01-31")


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_step(msg: str):
    print(f"  >> {msg}")


# ===========================================================================
# Phase 3: Ground Truth
# ===========================================================================
def load_ground_truth() -> pd.DataFrame:
    """
    Load insiders.csv and build a lookup of malicious user-date ranges.
    Filters to dataset version 4.2 only (matching our raw data).
    Fixes the known bad date for CDE1846.
    """
    print_section("Phase 3: Ground Truth Mapping")

    df = pd.read_csv(os.path.join(RAW_DIR, "insiders.csv"))
    print_step(f"Loaded insiders.csv: {len(df)} entries")

    # Fix known bad date: CDE1846 has '/21/2011 11:43:39' (missing month)
    # From context (dataset 6.2, scenario 4), this is likely '04/21/2011'
    bad_mask = df["start"].str.startswith("/", na=False)
    if bad_mask.any():
        print_step(f"Fixing {bad_mask.sum()} bad date(s)")
        df.loc[bad_mask, "start"] = df.loc[bad_mask, "start"].str.replace(
            "^/", "04/", regex=True
        )

    # Parse dates
    df["start_dt"] = pd.to_datetime(df["start"], format="mixed", dayfirst=False)
    df["end_dt"] = pd.to_datetime(df["end"], format="mixed", dayfirst=False)

    # Filter to r4.2 only
    r42 = df[df["dataset"].astype(str) == "4.2"].copy()
    print_step(f"Release 4.2 entries: {len(r42)}")
    print_step(f"Release 4.2 unique users: {r42['user'].nunique()}")
    print_step(f"Release 4.2 scenarios: {sorted(r42['scenario'].unique().tolist())}")

    # Scenario descriptions (from CERT documentation)
    scenario_desc = {
        1: "User who did not previously use removable drives or work after hours "
           "begins logging in after hours, using a removable drive, and uploading "
           "data to wikileaks.org.",
        2: "User begins surfing job websites and soliciting employment from a "
           "competitor. Before leaving the company, they use a thumb drive to "
           "steal data.",
        3: "System administrator who has been passed over for promotion begins "
           "downloading keylogger software and potential blackmail/extortion.",
    }

    for s in sorted(r42["scenario"].unique()):
        count = len(r42[r42["scenario"] == s])
        desc = scenario_desc.get(s, "Unknown scenario")
        print_step(f"  Scenario {s} ({count} users): {desc}")

    # Build user -> list of (start, end) malicious windows
    gt_records = []
    for _, row in r42.iterrows():
        gt_records.append({
            "user": row["user"],
            "scenario": int(row["scenario"]),
            "mal_start": row["start_dt"],
            "mal_end": row["end_dt"],
        })

    gt_df = pd.DataFrame(gt_records)
    print_step(f"Ground truth records: {len(gt_df)}")

    # Expand to malicious user-dates
    mal_user_dates = set()
    for _, row in gt_df.iterrows():
        dates = pd.date_range(row["mal_start"].normalize(),
                              row["mal_end"].normalize(), freq="D")
        for d in dates:
            mal_user_dates.add((row["user"], d))

    print_step(f"Malicious user-day pairs: {len(mal_user_dates)}")

    return gt_df, mal_user_dates


# ===========================================================================
# Phase 4: Event Ingestion & Normalization
# ===========================================================================
def load_logon() -> pd.DataFrame:
    """Load and normalize logon events."""
    print_step("Loading logon.csv...")
    df = pd.read_csv(os.path.join(RAW_DIR, "logon.csv"),
                     usecols=["date", "user", "pc", "activity"])
    df["timestamp"] = pd.to_datetime(df["date"])
    df["date_only"] = df["timestamp"].dt.normalize()
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek  # 0=Mon, 6=Sun
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_after_hours"] = (
        (df["hour"] < WORK_HOUR_START) | (df["hour"] >= WORK_HOUR_END)
    ).astype(int)
    df["source"] = "logon"
    print_step(f"  Logon events: {len(df):,}")
    return df


def load_device() -> pd.DataFrame:
    """Load and normalize device (USB) events."""
    print_step("Loading device.csv...")
    df = pd.read_csv(os.path.join(RAW_DIR, "device.csv"),
                     usecols=["date", "user", "pc", "activity"])
    df["timestamp"] = pd.to_datetime(df["date"])
    df["date_only"] = df["timestamp"].dt.normalize()
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_after_hours"] = (
        (df["hour"] < WORK_HOUR_START) | (df["hour"] >= WORK_HOUR_END)
    ).astype(int)
    df["source"] = "device"
    print_step(f"  Device events: {len(df):,}")
    return df


def load_file() -> pd.DataFrame:
    """Load and normalize file access events."""
    print_step("Loading file.csv...")
    df = pd.read_csv(os.path.join(RAW_DIR, "file.csv"),
                     usecols=["date", "user", "pc", "filename"])
    df["timestamp"] = pd.to_datetime(df["date"])
    df["date_only"] = df["timestamp"].dt.normalize()
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_after_hours"] = (
        (df["hour"] < WORK_HOUR_START) | (df["hour"] >= WORK_HOUR_END)
    ).astype(int)
    # Extract file extension
    df["file_ext"] = df["filename"].str.extract(r"\.(\w+)$", expand=False).fillna("unknown")
    df["source"] = "file"
    print_step(f"  File events: {len(df):,}")
    return df


def load_email() -> pd.DataFrame:
    """Load and normalize email events. Large file — selective columns."""
    print_step("Loading email.csv (1.3 GB — this will take ~20s)...")
    df = pd.read_csv(
        os.path.join(RAW_DIR, "email.csv"),
        usecols=["date", "user", "pc", "to", "cc", "bcc", "from", "size", "attachments"],
        engine="python",
        on_bad_lines="skip",
        dtype={"size": "float64", "attachments": "float64"},
    )
    df["timestamp"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df["date_only"] = df["timestamp"].dt.normalize()
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_after_hours"] = (
        (df["hour"] < WORK_HOUR_START) | (df["hour"] >= WORK_HOUR_END)
    ).astype(int)

    # Recipient count (to + cc + bcc)
    def count_recipients(field):
        if pd.isna(field) or field == "":
            return 0
        return field.count(";") + 1

    df["to_count"] = df["to"].apply(count_recipients)
    df["cc_count"] = df["cc"].apply(count_recipients)
    df["bcc_count"] = df["bcc"].apply(count_recipients)
    df["total_recipients"] = df["to_count"] + df["cc_count"] + df["bcc_count"]

    # External email detection (not @dtaa.com which is the internal domain)
    def has_external(field):
        if pd.isna(field) or field == "":
            return 0
        addresses = field.split(";")
        for addr in addresses:
            addr = addr.strip().lower()
            if addr and "@dtaa.com" not in addr:
                return 1
        return 0

    df["has_external_to"] = df["to"].apply(has_external)
    df["has_external_cc"] = df["cc"].apply(has_external)
    df["has_attachment"] = (df["attachments"].fillna(0) > 0).astype(int)

    df["source"] = "email"
    print_step(f"  Email events: {len(df):,}")
    return df


# ===========================================================================
# Phase 5: User-Day Aggregation & Feature Engineering
# ===========================================================================
def aggregate_logon_features(logon_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate logon events to user-day level."""
    print_step("Aggregating logon features per user-day...")

    grouped = logon_df.groupby(["user", "date_only"])

    features = pd.DataFrame()
    features["logon_count"] = grouped.apply(
        lambda g: (g["activity"] == "Logon").sum(), include_groups=False
    )
    features["logoff_count"] = grouped.apply(
        lambda g: (g["activity"] == "Logoff").sum(), include_groups=False
    )
    features["logon_unique_pcs"] = grouped["pc"].nunique()
    features["logon_after_hours"] = grouped["is_after_hours"].sum()
    features["logon_weekend"] = grouped["is_weekend"].max()
    features["logon_first_hour"] = grouped["hour"].min()
    features["logon_last_hour"] = grouped["hour"].max()
    features["logon_hour_span"] = features["logon_last_hour"] - features["logon_first_hour"]
    features["logon_total_events"] = grouped.size()

    features = features.reset_index()
    print_step(f"  Logon user-days: {len(features):,}")
    return features


def aggregate_device_features(device_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate device events to user-day level."""
    print_step("Aggregating device features per user-day...")

    grouped = device_df.groupby(["user", "date_only"])

    features = pd.DataFrame()
    features["device_connect_count"] = grouped.apply(
        lambda g: (g["activity"] == "Connect").sum(), include_groups=False
    )
    features["device_disconnect_count"] = grouped.apply(
        lambda g: (g["activity"] == "Disconnect").sum(), include_groups=False
    )
    features["device_unique_pcs"] = grouped["pc"].nunique()
    features["device_after_hours"] = grouped["is_after_hours"].sum()
    features["device_weekend"] = grouped["is_weekend"].max()
    features["device_total_events"] = grouped.size()

    features = features.reset_index()
    print_step(f"  Device user-days: {len(features):,}")
    return features


def aggregate_file_features(file_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate file access events to user-day level."""
    print_step("Aggregating file features per user-day...")

    grouped = file_df.groupby(["user", "date_only"])

    features = pd.DataFrame()
    features["file_access_count"] = grouped.size()
    features["file_unique_count"] = grouped["filename"].nunique()
    features["file_unique_pcs"] = grouped["pc"].nunique()
    features["file_after_hours"] = grouped["is_after_hours"].sum()
    features["file_weekend"] = grouped["is_weekend"].max()
    features["file_unique_extensions"] = grouped["file_ext"].nunique()
    # Doc/PDF ratio (potentially sensitive document types)
    features["file_doc_count"] = grouped.apply(
        lambda g: g["file_ext"].isin(["doc", "docx", "pdf", "xls", "xlsx", "ppt", "pptx"]).sum(),
        include_groups=False
    )

    features = features.reset_index()
    features["file_doc_ratio"] = (
        features["file_doc_count"] / features["file_access_count"].clip(lower=1)
    )
    print_step(f"  File user-days: {len(features):,}")
    return features


def aggregate_email_features(email_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate email events to user-day level."""
    print_step("Aggregating email features per user-day...")

    grouped = email_df.groupby(["user", "date_only"])

    features = pd.DataFrame()
    features["email_count"] = grouped.size()
    features["email_total_recipients"] = grouped["total_recipients"].sum()
    features["email_avg_recipients"] = grouped["total_recipients"].mean()
    features["email_max_recipients"] = grouped["total_recipients"].max()
    features["email_after_hours"] = grouped["is_after_hours"].sum()
    features["email_weekend"] = grouped["is_weekend"].max()
    features["email_with_attachment"] = grouped["has_attachment"].sum()
    features["email_external_to"] = grouped["has_external_to"].sum()
    features["email_external_cc"] = grouped["has_external_cc"].sum()
    features["email_avg_size"] = grouped["size"].mean()
    features["email_total_size"] = grouped["size"].sum()
    features["email_bcc_count"] = grouped["bcc_count"].sum()

    features = features.reset_index()
    features["email_external_ratio"] = (
        features["email_external_to"] / features["email_count"].clip(lower=1)
    )
    features["email_attachment_ratio"] = (
        features["email_with_attachment"] / features["email_count"].clip(lower=1)
    )
    print_step(f"  Email user-days: {len(features):,}")
    return features


def merge_user_day_features(
    logon_feats: pd.DataFrame,
    device_feats: pd.DataFrame,
    file_feats: pd.DataFrame,
    email_feats: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge all per-source user-day features into a single DataFrame.
    Uses outer join so days with only one source type are preserved.
    Missing source features are filled with 0.
    """
    print_step("Merging all source features into user-day table...")

    # Start with logon (broadest coverage — 1000 users)
    merged = logon_feats.copy()

    # Merge device
    merged = merged.merge(device_feats, on=["user", "date_only"], how="outer")

    # Merge file
    merged = merged.merge(file_feats, on=["user", "date_only"], how="outer")

    # Merge email
    merged = merged.merge(email_feats, on=["user", "date_only"], how="outer")

    # Fill missing counts with 0 (no activity that day = 0 events)
    count_cols = [c for c in merged.columns if c not in ["user", "date_only"]]
    merged[count_cols] = merged[count_cols].fillna(0)

    # Row count validation
    print_step(f"  Merged user-days: {len(merged):,}")
    print_step(f"  Unique users: {merged['user'].nunique()}")
    print_step(f"  Date range: {merged['date_only'].min()} -> {merged['date_only'].max()}")
    print_step(f"  Columns: {len(merged.columns)}")

    return merged


# ===========================================================================
# Cross-source features
# ===========================================================================
def add_cross_source_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create cross-source behavioral indicators.
    These capture suspicious combinations of activity from multiple sources
    occurring on the same user-day.
    """
    print_step("Engineering cross-source features...")

    # Device + File activity on same day (USB connected AND files accessed)
    df["device_and_file"] = (
        (df["device_connect_count"] > 0) & (df["file_access_count"] > 0)
    ).astype(int)

    # After-hours device + file (most suspicious combination)
    df["afterhours_device_and_file"] = (
        (df["device_after_hours"] > 0) & (df["file_after_hours"] > 0)
    ).astype(int)

    # After-hours logon + device
    df["afterhours_logon_and_device"] = (
        (df["logon_after_hours"] > 0) & (df["device_after_hours"] > 0)
    ).astype(int)

    # After-hours logon + file + device (triple signal)
    df["afterhours_triple_signal"] = (
        (df["logon_after_hours"] > 0) &
        (df["device_after_hours"] > 0) &
        (df["file_after_hours"] > 0)
    ).astype(int)

    # Total activity volume across all sources
    df["total_activity_count"] = (
        df["logon_total_events"] +
        df["device_total_events"] +
        df["file_access_count"] +
        df["email_count"]
    )

    # After-hours ratio across all activities
    total_after_hours = (
        df["logon_after_hours"] +
        df["device_after_hours"] +
        df["file_after_hours"] +
        df["email_after_hours"]
    )
    df["overall_after_hours_ratio"] = (
        total_after_hours / df["total_activity_count"].clip(lower=1)
    )

    # Multi-PC usage in a day (logon to different PCs)
    df["multi_pc_logon"] = (df["logon_unique_pcs"] > 1).astype(int)

    # External email + device activity (potential data exfiltration pattern)
    df["external_email_and_device"] = (
        (df["email_external_to"] > 0) & (df["device_connect_count"] > 0)
    ).astype(int)

    # High file count + device activity
    df["high_file_and_device"] = (
        (df["file_access_count"] > df["file_access_count"].quantile(0.90)) &
        (df["device_connect_count"] > 0)
    ).astype(int)

    # Weekend activity across any source
    df["any_weekend_activity"] = (
        (df["logon_weekend"] > 0) |
        (df["device_weekend"] > 0) |
        (df["file_weekend"] > 0) |
        (df["email_weekend"] > 0)
    ).astype(int)

    print_step(f"  Cross-source features added: 10")

    return df


# ===========================================================================
# Phase 6: User-Specific Baselines
# ===========================================================================
def compute_user_baselines(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute user-specific behavioral baselines using ONLY historical data.
    For each user-day, the baseline is the user's mean/std computed from
    all PRIOR days (at least BASELINE_MIN_DAYS of history required).

    This prevents future information leakage.
    """
    print_step("Computing user-specific baselines (expanding window)...")
    print_step(f"  Minimum history required: {BASELINE_MIN_DAYS} days")

    # Sort by user and date for expanding window computation
    df = df.sort_values(["user", "date_only"]).reset_index(drop=True)

    # Features to compute baselines for
    baseline_features = [
        "logon_total_events",
        "device_total_events",
        "file_access_count",
        "email_count",
        "logon_after_hours",
        "device_after_hours",
        "file_after_hours",
        "email_after_hours",
        "total_activity_count",
        "logon_first_hour",
    ]

    # For each baseline feature, compute expanding mean and std per user
    # Then compute deviation = (current - user_mean) / user_std
    for feat in baseline_features:
        col_mean = f"user_baseline_{feat}_mean"
        col_std = f"user_baseline_{feat}_std"
        col_dev = f"deviation_{feat}"

        # Expanding mean/std within user groups, shifted by 1 to exclude current day
        grouped = df.groupby("user")[feat]

        # Shift by 1 so current day is not included in its own baseline
        expanding_mean = grouped.transform(
            lambda x: x.expanding(min_periods=BASELINE_MIN_DAYS).mean().shift(1)
        )
        expanding_std = grouped.transform(
            lambda x: x.expanding(min_periods=BASELINE_MIN_DAYS).std().shift(1)
        )

        df[col_mean] = expanding_mean
        df[col_std] = expanding_std

        # Deviation (z-score relative to user's own history)
        # Use max(std, 0.1) to avoid division by zero
        df[col_dev] = (df[feat] - df[col_mean]) / df[col_std].clip(lower=0.1)

        # Fill NaN deviations (not enough history) with 0
        df[col_dev] = df[col_dev].fillna(0)

    # Clean up: drop raw baseline mean/std columns (keep deviations)
    baseline_mean_cols = [c for c in df.columns if c.startswith("user_baseline_")]
    df = df.drop(columns=baseline_mean_cols)

    print_step(f"  Deviation features added: {len(baseline_features)}")

    # Overall behavior deviation (average of all deviations)
    dev_cols = [c for c in df.columns if c.startswith("deviation_")]
    df["overall_behavior_deviation"] = df[dev_cols].mean(axis=1)

    return df


# ===========================================================================
# Ground Truth Labeling
# ===========================================================================
def apply_labels(df: pd.DataFrame, mal_user_dates: set) -> pd.DataFrame:
    """
    Apply ground truth labels based on insider malicious time windows.

    A user-day is labeled as malicious (1) if (user, date) appears in
    the malicious user-date set from insiders.csv r4.2.
    """
    print_step("Applying ground truth labels...")

    df["is_malicious"] = df.apply(
        lambda row: 1 if (row["user"], row["date_only"]) in mal_user_dates else 0,
        axis=1
    )

    n_mal = df["is_malicious"].sum()
    n_total = len(df)
    n_norm = n_total - n_mal
    mal_users = df[df["is_malicious"] == 1]["user"].nunique()

    print_step(f"  Total user-days: {n_total:,}")
    print_step(f"  Malicious user-days: {n_mal:,} ({100*n_mal/n_total:.2f}%)")
    print_step(f"  Normal user-days: {n_norm:,} ({100*n_norm/n_total:.2f}%)")
    print_step(f"  Malicious users represented: {mal_users}")

    return df


# ===========================================================================
# Temporal Split
# ===========================================================================
def temporal_split(df: pd.DataFrame) -> dict:
    """
    Split data temporally to prevent data leakage.

    Train: up to TRAIN_END
    Val:   TRAIN_END+1 to VAL_END
    Test:  VAL_END+1 onwards
    """
    print_step("Performing temporal train/val/test split...")

    train = df[df["date_only"] <= TRAIN_END]
    val = df[(df["date_only"] > TRAIN_END) & (df["date_only"] <= VAL_END)]
    test = df[df["date_only"] > VAL_END]

    for name, split_df in [("Train", train), ("Val", val), ("Test", test)]:
        n = len(split_df)
        n_mal = split_df["is_malicious"].sum()
        dates = f"{split_df['date_only'].min()} -> {split_df['date_only'].max()}"
        print_step(f"  {name}: {n:,} rows, {n_mal:,} malicious ({100*n_mal/max(n,1):.2f}%), {dates}")

    return {"train": train, "val": val, "test": test}


# ===========================================================================
# Main Pipeline
# ===========================================================================
def main():
    t_start = time.time()
    print(f"\n{'='*60}")
    print(f"  CERT r4.2 Data Pipeline")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # -----------------------------------------------------------------------
    # Phase 3: Ground Truth
    # -----------------------------------------------------------------------
    gt_df, mal_user_dates = load_ground_truth()

    # -----------------------------------------------------------------------
    # Phase 4: Load and normalize events
    # -----------------------------------------------------------------------
    print_section("Phase 4: Event Ingestion & Normalization")

    logon_df = load_logon()
    device_df = load_device()
    file_df = load_file()
    email_df = load_email()

    total_events = len(logon_df) + len(device_df) + len(file_df) + len(email_df)
    print_step(f"Total events loaded: {total_events:,}")

    # -----------------------------------------------------------------------
    # Phase 5: Aggregation & Feature Engineering
    # -----------------------------------------------------------------------
    print_section("Phase 5: User-Day Aggregation & Feature Engineering")

    logon_feats = aggregate_logon_features(logon_df)
    device_feats = aggregate_device_features(device_df)
    file_feats = aggregate_file_features(file_df)
    email_feats = aggregate_email_features(email_df)

    # Free memory from raw events
    del logon_df, device_df, file_df, email_df

    # Merge
    merged = merge_user_day_features(logon_feats, device_feats, file_feats, email_feats)
    del logon_feats, device_feats, file_feats, email_feats

    # Cross-source features
    merged = add_cross_source_features(merged)

    # Save unlabeled features (for later reference)
    unlabeled_path = os.path.join(OUTPUT_DIR, "user_day_features.parquet")
    merged.to_parquet(unlabeled_path, index=False)
    print_step(f"Saved unlabeled features: {unlabeled_path}")

    # -----------------------------------------------------------------------
    # Phase 6: User-Specific Baselines
    # -----------------------------------------------------------------------
    print_section("Phase 6: User-Specific Baselines")
    merged = compute_user_baselines(merged)

    # -----------------------------------------------------------------------
    # Labeling
    # -----------------------------------------------------------------------
    print_section("Ground Truth Labeling")
    merged = apply_labels(merged, mal_user_dates)

    # -----------------------------------------------------------------------
    # Temporal Split Info
    # -----------------------------------------------------------------------
    print_section("Phase 7: Temporal Validation Split")
    splits = temporal_split(merged)

    # -----------------------------------------------------------------------
    # Save Final Dataset
    # -----------------------------------------------------------------------
    print_section("Saving Results")

    labeled_path = os.path.join(OUTPUT_DIR, "user_day_features_labeled.parquet")
    merged.to_parquet(labeled_path, index=False)
    print_step(f"Saved labeled dataset: {labeled_path}")
    print_step(f"  Shape: {merged.shape}")
    print_step(f"  Columns: {merged.columns.tolist()}")

    # Save split datasets
    for split_name, split_df in splits.items():
        split_path = os.path.join(OUTPUT_DIR, f"split_{split_name}.parquet")
        split_df.to_parquet(split_path, index=False)
        print_step(f"Saved {split_name} split: {split_path} ({len(split_df):,} rows)")

    # Save pipeline metadata
    feature_cols = [c for c in merged.columns if c not in ["user", "date_only", "is_malicious"]]
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_events_ingested": total_events,
        "total_user_days": len(merged),
        "unique_users": int(merged["user"].nunique()),
        "date_range": [str(merged["date_only"].min()), str(merged["date_only"].max())],
        "feature_columns": feature_cols,
        "num_features": len(feature_cols),
        "label_column": "is_malicious",
        "malicious_user_days": int(merged["is_malicious"].sum()),
        "normal_user_days": int((merged["is_malicious"] == 0).sum()),
        "malicious_rate": round(float(merged["is_malicious"].mean()), 6),
        "temporal_split": {
            "train_end": str(TRAIN_END),
            "val_end": str(VAL_END),
            "train_rows": len(splits["train"]),
            "val_rows": len(splits["val"]),
            "test_rows": len(splits["test"]),
            "train_malicious": int(splits["train"]["is_malicious"].sum()),
            "val_malicious": int(splits["val"]["is_malicious"].sum()),
            "test_malicious": int(splits["test"]["is_malicious"].sum()),
        },
        "work_hours": {"start": WORK_HOUR_START, "end": WORK_HOUR_END},
        "baseline_min_days": BASELINE_MIN_DAYS,
        "ground_truth_r42_users": int(gt_df["user"].nunique()),
        "ground_truth_r42_scenarios": sorted(gt_df["scenario"].unique().tolist()),
    }

    meta_path = os.path.join(OUTPUT_DIR, "pipeline_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    print_step(f"Saved metadata: {meta_path}")

    elapsed = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"  Pipeline complete in {elapsed:.1f}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
