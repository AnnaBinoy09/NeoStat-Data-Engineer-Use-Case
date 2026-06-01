

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def kpi_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Top-level executive KPIs:
      Total Revenue, Total Orders, Total Customers, Average Order Value,
      Total Cities, Total Products Sold
    """
    summary = {
        "Metric": [
            "Total Revenue (₹)",
            "Total Orders",
            "Total Unique Customers",
            "Average Order Value (₹)",
            "Total Cities",
            "Total Unique Products Sold",
        ],
        "Value": [
            round(df["revenue"].sum(), 2),
            df["transaction_id"].nunique(),
            df["customer_id"].nunique(),
            round(df["revenue"].sum() / df["transaction_id"].nunique(), 2),
            df["city"].nunique(),
            df["product_id"].nunique(),
        ],
    }
    result = pd.DataFrame(summary)
    logger.info("  KPI Summary generated")
    return result


def revenue_by_city(df: pd.DataFrame) -> pd.DataFrame:
    """City-level revenue breakdown, sorted descending."""
    result = (
        df.groupby("city")
        .agg(
            total_revenue=("revenue", "sum"),
            total_orders=("transaction_id", "nunique"),
            avg_order_value=("revenue", "mean"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
        .round(2)
    )
    logger.info(f"  Revenue by City: {len(result)} cities")
    return result


def revenue_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Category-level revenue breakdown."""
    result = (
        df.groupby("category")
        .agg(
            total_revenue=("revenue", "sum"),
            total_orders=("transaction_id", "nunique"),
            total_quantity=("quantity", "sum"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
        .round(2)
    )
    logger.info(f"  Revenue by Category: {len(result)} categories")
    return result


def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N products by both revenue and quantity sold."""
    result = (
        df.groupby(["product_id", "product_name"])
        .agg(
            total_revenue=("revenue", "sum"),
            total_quantity=("quantity", "sum"),
            total_orders=("transaction_id", "nunique"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
        .head(n)
        .round(2)
    )
    result["revenue_rank"] = range(1, len(result) + 1)
    result_qty = result.sort_values("total_quantity", ascending=False).copy()
    result_qty["quantity_rank"] = range(1, len(result_qty) + 1)
    
    merged = result[["product_id", "product_name", "total_revenue", "revenue_rank"]].merge(
        result_qty[["product_id", "total_quantity", "quantity_rank"]],
        on="product_id",
    )
    logger.info(f"  Top {n} Products table generated")
    return merged


def generate_all_kpis(df: pd.DataFrame) -> dict:
    """Return dict of all KPI DataFrames."""
    logger.info("--- Generating KPIs ---")
    kpis = {
        "kpi_summary": kpi_summary(df),
        "revenue_by_city": revenue_by_city(df),
        "revenue_by_category": revenue_by_category(df),
        "top_products": top_products(df),
    }
    logger.info("✅ All KPIs generated")
    return kpis


if __name__ == "__main__":
    from ingestion import ingest_all
    from cleaning import clean_transactions
    from masking import apply_pii_masking
    from transformation import run_transformation
    import pandas as pd

    data = ingest_all()
    c1 = clean_transactions(data["retail_data1"], data["product_details"], "retail_data1")
    c2 = clean_transactions(data["retail_data2"], data["product_details"], "retail_data2")
    combined = pd.concat([c1, c2], ignore_index=True)
    masked = apply_pii_masking(combined)
    final = run_transformation(masked, data["product_details"])

    kpis = generate_all_kpis(final)
    for name, df in kpis.items():
        print(f"\n=== {name} ===")
        print(df.to_string(index=False))
