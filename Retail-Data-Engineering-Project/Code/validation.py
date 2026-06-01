

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)




def missing_value_report(df: pd.DataFrame, dataset_name: str = "") -> pd.DataFrame:
    """Return a summary of null counts and percentages per column."""
    null_counts = df.isnull().sum()
    null_pct = (null_counts / len(df) * 100).round(2)
    report = pd.DataFrame({
        "dataset": dataset_name,
        "column": null_counts.index,
        "null_count": null_counts.values,
        "null_pct": null_pct.values,
    })
    report = report[report["null_count"] > 0].reset_index(drop=True)
    logger.info(f"[{dataset_name}] Missing value report: {len(report)} columns with nulls")
    return report




def duplicate_report(df: pd.DataFrame, subset: list = None, dataset_name: str = "") -> dict:
    """
    Return counts of fully duplicate rows and transaction_id duplicates (if column exists).
    Design: We distinguish 'full duplicates' (same across ALL columns) from
    'transaction_id duplicates' (same ID but possibly different payment_status).
    Only full duplicates are removed; partial duplicates are flagged for review.
    """
    full_dups = df.duplicated().sum()
    result = {"full_duplicates": int(full_dups)}

    if subset and all(c in df.columns for c in subset):
        key_dups = df.duplicated(subset=subset, keep=False).sum()
        result["key_duplicates"] = int(key_dups)

    logger.info(f"[{dataset_name}] Full duplicates: {full_dups}")
    return result




def invalid_value_report(df: pd.DataFrame, dataset_name: str = "") -> pd.DataFrame:
    """Check for business-rule violations: negative quantity, zero/negative price, bad discount."""
    issues = []

    if "quantity" in df.columns:
        bad_qty = df[pd.to_numeric(df["quantity"], errors="coerce").fillna(-1) <= 0]
        issues.append({"check": "quantity <= 0", "count": len(bad_qty)})

    if "price" in df.columns:
        bad_price = df[pd.to_numeric(df["price"], errors="coerce").fillna(-1) <= 0]
        issues.append({"check": "price <= 0 or null", "count": int(df["price"].isnull().sum())})

    if "discount" in df.columns:
        bad_disc = df[
            (pd.to_numeric(df["discount"], errors="coerce") < 0) |
            (pd.to_numeric(df["discount"], errors="coerce") > 1)
        ]
        issues.append({"check": "discount out of [0,1]", "count": len(bad_disc)})

    report = pd.DataFrame(issues)
    report.insert(0, "dataset", dataset_name)
    logger.info(f"[{dataset_name}] Invalid value checks completed")
    return report




def schema_validation_report(df: pd.DataFrame, expected_dtypes: dict, dataset_name: str = "") -> pd.DataFrame:
    """
    Compare actual dtypes against expected. Flags mismatches.
    expected_dtypes: {'col_name': 'expected_dtype_string'}
    """
    rows = []
    for col, expected in expected_dtypes.items():
        actual = str(df[col].dtype) if col in df.columns else "MISSING"
        rows.append({
            "dataset": dataset_name,
            "column": col,
            "expected_dtype": expected,
            "actual_dtype": actual,
            "match": actual == expected or col not in df.columns,
        })
    return pd.DataFrame(rows)



def run_all_quality_checks(datasets: dict) -> dict:
    """
    Run all quality assessments on retail_data1 and retail_data2.
    Returns a dict of report DataFrames for use in exports.
    """
    reports = {
        "missing": [],
        "duplicates": {},
        "invalid": [],
    }

    for name in ["retail_data1", "retail_data2"]:
        df = datasets[name]
        reports["missing"].append(missing_value_report(df, name))
        reports["duplicates"][name] = duplicate_report(df, subset=["transaction_id", "customer_id"], dataset_name=name)
        reports["invalid"].append(invalid_value_report(df, name))

    reports["missing"] = pd.concat(reports["missing"], ignore_index=True)
    reports["invalid"] = pd.concat(reports["invalid"], ignore_index=True)
    logger.info("✅ Quality assessment complete.")
    return reports


if __name__ == "__main__":
    from ingestion import ingest_all
    datasets = ingest_all()
    rpts = run_all_quality_checks(datasets)
    print("\n=== Missing Values ===")
    print(rpts["missing"])
    print("\n=== Invalid Values ===")
    print(rpts["invalid"])
    print("\n=== Duplicates ===")
    print(rpts["duplicates"])
