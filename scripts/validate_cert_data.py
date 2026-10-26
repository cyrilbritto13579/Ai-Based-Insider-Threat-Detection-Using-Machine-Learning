"""
CERT r4.2 Dataset Validation Script
====================================
Phase 2: Inspect and validate all raw CERT CSV files.

This script:
  1. Validates schema (columns, dtypes) for each source file
  2. Reports shape, nulls, duplicates, date ranges, unique users
  3. Cross-references insiders.csv users against activity logs
  4. Saves a structured validation report as JSON

Usage:
    python scripts/validate_cert_data.py

Output:
    data/processed/cert_validation_report.json
    Console summary
"""

import os
import sys
import json
import time
from datetime import datetime

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
REPORT_PATH = os.path.join(OUTPUT_DIR, "cert_validation_report.json")

EXPECTED_FILES = {
    "logon.csv": {
        "required_columns": ["id", "date", "user", "pc", "activity"],
        "expected_activities": ["Logon", "Logoff"],
    },
    "device.csv": {
        "required_columns": ["id", "date", "user", "pc", "activity"],
        "expected_activities": ["Connect", "Disconnect"],
    },
    "file.csv": {
        "required_columns": ["id", "date", "user", "pc", "filename"],
        "expected_activities": None,  # No activity column
    },
    "email.csv": {
        "required_columns": ["id", "date", "user", "pc", "to", "from", "size"],
        "expected_activities": None,  # No activity column
    },
    "insiders.csv": {
        "required_columns": ["dataset", "scenario", "user", "start", "end"],
        "expected_activities": None,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_json(obj):
    """Convert numpy/pandas types to JSON-serializable Python types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_json(v) for v in obj]
    return obj


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_kv(key: str, value, indent: int = 4):
    """Print a key-value pair with indentation."""
    print(f"{' '*indent}{key}: {value}")


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------
def validate_activity_file(filepath: str, spec: dict) -> dict:
    """
    Validate a single CERT activity CSV file.

    Returns a dict with all validation results.
    """
    fname = os.path.basename(filepath)
    print_section(fname)

    result = {
        "file": fname,
        "path": filepath,
        "exists": os.path.exists(filepath),
    }

    if not result["exists"]:
        print(f"    ERROR: File not found at {filepath}")
        result["valid"] = False
        return result

    # File size
    size_bytes = os.path.getsize(filepath)
    size_mb = size_bytes / (1024 * 1024)
    result["size_bytes"] = size_bytes
    result["size_mb"] = round(size_mb, 1)
    print_kv("Size", f"{size_mb:.1f} MB")

    # Load with appropriate strategy
    t0 = time.time()
    if fname == "email.csv":
        # Email is 1.3 GB — load only needed columns first, full later
        print("    Loading (large file, this may take a moment)...")
        df = pd.read_csv(
            filepath,
            engine="python",
            on_bad_lines="skip",
            dtype=str,
        )
    else:
        df = pd.read_csv(filepath, dtype=str)
    load_time = time.time() - t0
    print_kv("Load time", f"{load_time:.1f}s")

    # Shape
    result["rows"] = len(df)
    result["columns"] = df.columns.tolist()
    result["num_columns"] = len(df.columns)
    print_kv("Shape", f"{len(df):,} rows × {len(df.columns)} columns")
    print_kv("Columns", df.columns.tolist())

    # Schema validation
    required = spec["required_columns"]
    missing_cols = [c for c in required if c not in df.columns]
    extra_cols = [c for c in df.columns if c not in required]
    result["required_columns"] = required
    result["missing_columns"] = missing_cols
    result["extra_columns"] = extra_cols

    if missing_cols:
        print_kv("MISSING columns", missing_cols)
    if extra_cols:
        print_kv("Extra columns", extra_cols)
    if not missing_cols:
        print_kv("Schema", "OK — all required columns present")

    # Null values
    null_counts = df.isnull().sum()
    nulls_dict = {col: int(v) for col, v in null_counts.items() if v > 0}
    result["null_counts"] = nulls_dict
    result["total_nulls"] = int(null_counts.sum())
    if nulls_dict:
        print_kv("Nulls", nulls_dict)
    else:
        print_kv("Nulls", "None")

    # Empty string values (since we loaded as str)
    empty_counts = {}
    for col in df.columns:
        empty_count = int((df[col] == "").sum())
        if empty_count > 0:
            empty_counts[col] = empty_count
    result["empty_string_counts"] = empty_counts
    if empty_counts:
        print_kv("Empty strings", empty_counts)

    # Duplicates (by id column if present)
    if "id" in df.columns:
        dup_ids = int(df["id"].duplicated().sum())
        result["duplicate_ids"] = dup_ids
        print_kv("Duplicate IDs", dup_ids)

    full_dups = int(df.duplicated().sum())
    result["duplicate_rows"] = full_dups
    print_kv("Duplicate rows", full_dups)

    # User field
    if "user" in df.columns:
        unique_users = df["user"].nunique()
        result["unique_users"] = unique_users
        result["user_sample"] = df["user"].unique()[:10].tolist()
        print_kv("Unique users", unique_users)
        print_kv("User sample", result["user_sample"][:5])

    # Date field
    if "date" in df.columns:
        dates = pd.to_datetime(df["date"], errors="coerce")
        valid_dates = dates.notna().sum()
        invalid_dates = dates.isna().sum()
        result["valid_dates"] = int(valid_dates)
        result["invalid_dates"] = int(invalid_dates)
        result["date_min"] = str(dates.min()) if valid_dates > 0 else None
        result["date_max"] = str(dates.max()) if valid_dates > 0 else None

        print_kv("Date range", f"{dates.min()} -> {dates.max()}")
        print_kv("Valid dates", f"{valid_dates:,}")
        if invalid_dates > 0:
            print_kv("INVALID dates", f"{invalid_dates:,}")

    # Activity field
    if "activity" in df.columns:
        activities = df["activity"].unique().tolist()
        result["activity_values"] = activities
        result["activity_counts"] = df["activity"].value_counts().to_dict()
        print_kv("Activity values", activities)
        print_kv("Activity distribution", result["activity_counts"])

        # Check against expected
        expected = spec.get("expected_activities")
        if expected:
            unexpected = [a for a in activities if a not in expected]
            if unexpected:
                print_kv("UNEXPECTED activities", unexpected)
                result["unexpected_activities"] = unexpected

    # PC field
    if "pc" in df.columns:
        unique_pcs = df["pc"].nunique()
        result["unique_pcs"] = unique_pcs
        print_kv("Unique PCs", unique_pcs)

    # File-specific: filename field
    if "filename" in df.columns:
        unique_files = df["filename"].nunique()
        result["unique_filenames"] = unique_files
        print_kv("Unique filenames", unique_files)
        print_kv("Filename sample", df["filename"].unique()[:5].tolist())

    # Email-specific fields
    if "to" in df.columns:
        # Count recipients
        avg_recipients = df["to"].dropna().str.count(";").add(1).mean()
        result["avg_recipients"] = round(float(avg_recipients), 2)
        print_kv("Avg recipients per email", round(avg_recipients, 2))

    if "cc" in df.columns:
        cc_used = int((df["cc"].notna() & (df["cc"] != "")).sum())
        result["emails_with_cc"] = cc_used
        print_kv("Emails with CC", f"{cc_used:,}")

    if "bcc" in df.columns:
        bcc_used = int((df["bcc"].notna() & (df["bcc"] != "")).sum())
        result["emails_with_bcc"] = bcc_used
        print_kv("Emails with BCC", f"{bcc_used:,}")

    if "attachments" in df.columns:
        attach_counts = pd.to_numeric(df["attachments"], errors="coerce")
        with_attachments = int((attach_counts > 0).sum())
        result["emails_with_attachments"] = with_attachments
        print_kv("Emails with attachments", f"{with_attachments:,}")

    if "size" in df.columns:
        sizes = pd.to_numeric(df["size"], errors="coerce")
        result["email_size_mean"] = round(float(sizes.mean()), 1)
        result["email_size_median"] = round(float(sizes.median()), 1)
        result["email_size_max"] = int(sizes.max())
        print_kv("Email size (mean/median/max)", f"{sizes.mean():.0f} / {sizes.median():.0f} / {sizes.max():.0f} bytes")

    # Content field (just check presence, don't analyze text)
    if "content" in df.columns:
        content_present = int(df["content"].notna().sum())
        content_empty = int((df["content"].isna() | (df["content"] == "")).sum())
        result["content_present"] = content_present
        result["content_empty"] = content_empty
        print_kv("Content present", f"{content_present:,}")

    # Sample rows
    result["sample_rows"] = df.head(3).to_dict(orient="records")

    result["valid"] = len(missing_cols) == 0
    return result


def validate_insiders(filepath: str) -> dict:
    """
    Validate insiders.csv ground truth file.

    Returns structured validation results.
    """
    print_section("insiders.csv (Ground Truth)")

    result = {
        "file": "insiders.csv",
        "path": filepath,
        "exists": os.path.exists(filepath),
    }

    if not result["exists"]:
        print("    ERROR: File not found!")
        result["valid"] = False
        return result

    df = pd.read_csv(filepath)
    result["rows"] = len(df)
    result["columns"] = df.columns.tolist()
    print_kv("Shape", f"{len(df)} rows × {len(df.columns)} columns")
    print_kv("Columns", df.columns.tolist())

    # Parse dates
    df["start_dt"] = pd.to_datetime(df["start"], errors="coerce")
    df["end_dt"] = pd.to_datetime(df["end"], errors="coerce")

    invalid_starts = int(df["start_dt"].isna().sum())
    invalid_ends = int(df["end_dt"].isna().sum())
    result["invalid_start_dates"] = invalid_starts
    result["invalid_end_dates"] = invalid_ends
    if invalid_starts > 0:
        print_kv("WARNING: Invalid start dates", invalid_starts)
        bad_rows = df[df["start_dt"].isna()][["user", "start"]].to_dict("records")
        print_kv("Bad rows", bad_rows)
        result["bad_start_rows"] = bad_rows
    if invalid_ends > 0:
        print_kv("WARNING: Invalid end dates", invalid_ends)

    # Unique users
    unique_users = df["user"].nunique()
    total_users = len(df)
    result["unique_insider_users"] = unique_users
    result["total_insider_entries"] = total_users
    print_kv("Unique malicious users", unique_users)
    print_kv("Total insider entries", total_users)

    # Users with multiple entries
    user_counts = df["user"].value_counts()
    multi_entry_users = user_counts[user_counts > 1]
    result["users_with_multiple_entries"] = len(multi_entry_users)
    if len(multi_entry_users) > 0:
        print_kv("Users with multiple entries", len(multi_entry_users))
        print_kv("Example", multi_entry_users.head(5).to_dict())

    # Dataset versions
    datasets = sorted(df["dataset"].unique().tolist(), key=lambda x: float(x))
    result["datasets"] = datasets
    print_kv("Dataset versions", datasets)

    # Scenarios
    scenarios = sorted(df["scenario"].unique().tolist())
    result["scenarios"] = scenarios
    print_kv("Scenarios", scenarios)

    # Dataset × scenario breakdown
    breakdown = df.groupby(["dataset", "scenario"]).size().to_dict()
    breakdown_str = {f"{k[0]}-{k[1]}": int(v) for k, v in breakdown.items()}
    result["dataset_scenario_breakdown"] = breakdown_str
    print_kv("Dataset×Scenario counts", breakdown_str)

    # Date range of malicious activity
    valid_dates = df[df["start_dt"].notna() & df["end_dt"].notna()]
    if len(valid_dates) > 0:
        result["malicious_date_range_start"] = str(valid_dates["start_dt"].min())
        result["malicious_date_range_end"] = str(valid_dates["end_dt"].max())
        print_kv("Malicious activity range", f"{valid_dates['start_dt'].min()} -> {valid_dates['end_dt'].max()}")

        # Duration statistics
        durations = (valid_dates["end_dt"] - valid_dates["start_dt"]).dt.total_seconds() / 3600
        result["malicious_duration_hours_mean"] = round(float(durations.mean()), 1)
        result["malicious_duration_hours_median"] = round(float(durations.median()), 1)
        result["malicious_duration_hours_min"] = round(float(durations.min()), 1)
        result["malicious_duration_hours_max"] = round(float(durations.max()), 1)
        print_kv("Duration (hours) mean/median/min/max",
                 f"{durations.mean():.1f} / {durations.median():.1f} / {durations.min():.1f} / {durations.max():.1f}")

    # Insider user list
    result["insider_users"] = sorted(df["user"].unique().tolist())

    # Filter to r4.2 dataset only (since that's what we have)
    r42 = df[df["dataset"].astype(str) == "4.2"]
    result["r42_entries"] = len(r42)
    result["r42_unique_users"] = r42["user"].nunique()
    result["r42_users"] = sorted(r42["user"].unique().tolist())
    result["r42_scenarios"] = sorted(r42["scenario"].unique().tolist())
    print_kv("\nRelease 4.2 entries", len(r42))
    print_kv("Release 4.2 unique users", r42["user"].nunique())
    print_kv("Release 4.2 scenarios", result["r42_scenarios"])
    print_kv("Release 4.2 users", result["r42_users"])

    result["valid"] = True
    return result


def cross_reference_insiders(insider_result: dict, activity_results: dict) -> dict:
    """
    Cross-reference insider users against activity log users.
    """
    print_section("Cross-Reference: Insiders ↔ Activity Logs")

    xref = {}

    # Get all insider users (use full set, not just r4.2)
    insider_users = set(insider_result.get("insider_users", []))
    r42_users = set(insider_result.get("r42_users", []))

    print_kv("Total insider users (all datasets)", len(insider_users))
    print_kv("R4.2 insider users", len(r42_users))

    for fname, result in activity_results.items():
        if fname == "insiders.csv":
            continue

        # Load just the user column to check
        filepath = result.get("path", "")
        if not os.path.exists(filepath):
            continue

        if fname == "email.csv":
            df_users = pd.read_csv(filepath, usecols=["user"], dtype=str,
                                   engine="python", on_bad_lines="skip")
        else:
            df_users = pd.read_csv(filepath, usecols=["user"], dtype=str)

        log_users = set(df_users["user"].unique())

        # Check which insiders appear in this log
        found = r42_users & log_users
        missing = r42_users - log_users

        xref[fname] = {
            "total_log_users": len(log_users),
            "r42_insiders_found": len(found),
            "r42_insiders_missing": len(missing),
            "missing_users": sorted(list(missing)) if missing else [],
        }

        print(f"\n    {fname}:")
        print_kv("Total users in log", len(log_users), indent=8)
        print_kv("R4.2 insiders found", f"{len(found)}/{len(r42_users)}", indent=8)
        if missing:
            print_kv("MISSING insiders", sorted(list(missing)), indent=8)

    return xref


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("  CERT Release 4.2 — Dataset Validation")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    report = {
        "generated_at": datetime.now().isoformat(),
        "raw_data_dir": RAW_DIR,
        "files": {},
    }

    # Validate each activity file
    activity_results = {}
    for fname, spec in EXPECTED_FILES.items():
        if fname == "insiders.csv":
            continue
        filepath = os.path.join(RAW_DIR, fname)
        result = validate_activity_file(filepath, spec)
        report["files"][fname] = safe_json(result)
        activity_results[fname] = result

    # Validate insiders (ground truth)
    insiders_path = os.path.join(RAW_DIR, "insiders.csv")
    insider_result = validate_insiders(insiders_path)
    report["files"]["insiders.csv"] = safe_json(insider_result)

    # Cross-reference
    xref = cross_reference_insiders(insider_result, activity_results)
    report["cross_reference"] = safe_json(xref)

    # Summary
    print_section("VALIDATION SUMMARY")

    all_valid = True
    for fname, result in report["files"].items():
        status = "OK" if result.get("valid") else "FAIL"
        rows = result.get("rows", "?")
        users = result.get("unique_users", result.get("unique_insider_users", "?"))
        print(f"    {status:4s}  {fname:20s}  {str(rows):>12s} rows  {str(users):>6s} users")
        if not result.get("valid"):
            all_valid = False

    report["all_valid"] = all_valid

    # Total events
    total_events = sum(
        r.get("rows", 0) for fname, r in report["files"].items()
        if fname != "insiders.csv"
    )
    report["total_events"] = total_events
    print_kv("\nTotal events across all sources", f"{total_events:,}")

    # Save report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n    Report saved to: {REPORT_PATH}")

    print("\n" + "=" * 60)
    if all_valid:
        print("  ALL VALIDATIONS PASSED")
    else:
        print("  SOME VALIDATIONS FAILED — check details above")
    print("=" * 60 + "\n")

    return report


if __name__ == "__main__":
    main()
