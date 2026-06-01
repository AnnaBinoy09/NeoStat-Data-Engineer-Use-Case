"""
main.py — Pipeline Orchestrator
Runs all phases in sequence:
  Phase 1  → Ingest
  Phase 2  → Validate
  Phase 3  → Clean
  Phase 4  → Mask PII
  Phase 5  → Enrich + Revenue
  Phase 6  → KPIs
  Phase 7  → Forecast
  Phase 8  → Export to Excel

Run:  python main.py
"""

import sys
import os
import logging
import pandas as pd

# Ensure Code directory is importable
sys.path.insert(0, os.path.dirname(__file__))

from ingestion import ingest_all
from validation import run_all_quality_checks
from cleaning import clean_transactions
from masking import apply_pii_masking
from transformation import run_transformation
from kpi import generate_all_kpis
from forecasting import run_forecasting
from export import export_to_excel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline():
    logger.info("=" * 60)
    logger.info("  ABC RETAIL — DATA ENGINEERING PIPELINE STARTED")
    logger.info("=" * 60)

    # ── Phase 1: Ingest ───────────────────────────────────────
    logger.info("\n[PHASE 1] Data Ingestion")
    datasets = ingest_all()

    # ── Phase 2: Validate ─────────────────────────────────────
    logger.info("\n[PHASE 2] Data Quality Assessment")
    quality_reports = run_all_quality_checks(datasets)
    logger.info(f"  Missing value issues: {len(quality_reports['missing'])} column-dataset pairs")
    logger.info(f"  Invalid value checks: {len(quality_reports['invalid'])} checks run")

    # ── Phase 3: Clean ────────────────────────────────────────
    logger.info("\n[PHASE 3] Data Cleaning")
    cleaned1 = clean_transactions(datasets["retail_data1"], datasets["product_details"], "retail_data1")
    cleaned2 = clean_transactions(datasets["retail_data2"], datasets["product_details"], "retail_data2")
    combined = pd.concat([cleaned1, cleaned2], ignore_index=True)
    logger.info(f"  Combined cleaned rows: {len(combined)}")

    # ── Phase 4: PII Masking ──────────────────────────────────
    logger.info("\n[PHASE 4] PII Protection")
    masked_df = apply_pii_masking(combined)

    # ── Phase 5: Enrich + Revenue ─────────────────────────────
    logger.info("\n[PHASE 5] Enrichment & Revenue Calculation")
    final_df = run_transformation(masked_df, datasets["product_details"])

    # ── Phase 6: KPIs ─────────────────────────────────────────
    logger.info("\n[PHASE 6] KPI Generation")
    kpis = generate_all_kpis(final_df)
    summary = kpis["kpi_summary"]
    total_rev = summary.loc[summary["Metric"] == "Total Revenue (₹)", "Value"].values[0]
    logger.info(f"  Total Revenue: ₹{total_rev:,.2f}")

    # ── Phase 7: Forecasting ──────────────────────────────────
    logger.info("\n[PHASE 7] Sales Forecasting")
    forecast_result = run_forecasting(final_df)
    forecast_table = forecast_result["forecast_table"]
    logger.info(f"  Forecast metrics: {forecast_result['metrics']}")

    # ── Phase 8: Export ───────────────────────────────────────
    logger.info("\n[PHASE 8] Excel Export")

    # Select clean display columns for Cleaned_Data sheet
    display_cols = [
        "transaction_id", "customer_id", "customer_name", "product_id",
        "product_name", "category", "city", "transaction_date",
        "quantity", "price", "discount", "revenue",
        "payment_method", "purchase_location", "payment_status",
        "email", "phone", "year", "month", "month_year",
    ]
    display_df = final_df[[c for c in display_cols if c in final_df.columns]]

    output_path = export_to_excel(display_df, kpis, forecast_table)

    logger.info("\n" + "=" * 60)
    logger.info("  ✅ PIPELINE COMPLETE")
    logger.info(f"  Output: {output_path}")
    logger.info("=" * 60)

    return {
        "final_df": final_df,
        "kpis": kpis,
        "forecast": forecast_result,
        "output_path": output_path,
    }


if __name__ == "__main__":
    run_pipeline()
