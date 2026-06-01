

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def enrich_with_product_details(df: pd.DataFrame, product_ref: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join transactions with product_details on product_id.
    Bring in: standard product name, standard category, standard price.

    Join logic:
    - Use LEFT join so no transaction rows are dropped if product_id is missing from dim table.
    - Suffix '_dim' on dimension columns to disambiguate before reconciliation.
    - After join, prefer dimension values for name/category/price (authoritative master data).
    - For any transaction where product_id is not in the dimension (data quality gap),
      retain the transaction's own values.
    """
    product_ref_renamed = product_ref.rename(columns={
        "product_name": "product_name_dim",
        "category": "category_dim",
        "price": "price_dim",
    })

    df = df.merge(product_ref_renamed, on="product_id", how="left")

    
    df["product_name"] = df["product_name_dim"].combine_first(df["product_name"])
    df["category"] = df["category_dim"].combine_first(df["category"])
    df["price"] = df["price_dim"].combine_first(df["price"])

    df.drop(columns=["product_name_dim", "category_dim", "price_dim"], inplace=True)

    logger.info(f"  Enrichment join complete: {len(df)} rows")
    return df


def calculate_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """
    Revenue = Quantity × Price × (1 - Discount)

    Validation:
    - Quantity and Price must be positive (guaranteed by cleaning module).
    - Discount is clipped to [0, 1] (guaranteed by cleaning module).
    - Revenue must be > 0; rows where it is not are flagged.
    """
    df["revenue"] = df["quantity"] * df["price"] * (1 - df["discount"])
    df["revenue"] = df["revenue"].round(2)

    invalid_rev = df[df["revenue"] <= 0]
    if len(invalid_rev) > 0:
        logger.warning(f"  {len(invalid_rev)} rows with revenue <= 0 — check cleaning")

    logger.info(f"  Revenue calculated. Total: ₹{df['revenue'].sum():,.2f}")
    return df


def add_time_features(df: pd.DataFrame, date_col: str = "transaction_date") -> pd.DataFrame:
    """
    Extract year, month, month_year for time-series analysis and Power BI slicers.
    """
    df[date_col] = pd.to_datetime(df[date_col])
    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.month
    df["month_name"] = df[date_col].dt.strftime("%b")
    df["month_year"] = df[date_col].dt.to_period("M").astype(str)
    df[date_col] = df[date_col].dt.strftime("%Y-%m-%d")
    logger.info("  Time features added (year, month, month_name, month_year)")
    return df


def run_transformation(df: pd.DataFrame, product_ref: pd.DataFrame) -> pd.DataFrame:
    """Full transformation pipeline: enrich → revenue → time features."""
    logger.info("--- Starting Transformation ---")
    df = enrich_with_product_details(df, product_ref)
    df = calculate_revenue(df)
    df = add_time_features(df)
    logger.info("✅ Transformation complete")
    return df


if __name__ == "__main__":
    from ingestion import ingest_all
    from cleaning import clean_transactions
    from masking import apply_pii_masking

    data = ingest_all()
    c1 = clean_transactions(data["retail_data1"], data["product_details"], "retail_data1")
    c2 = clean_transactions(data["retail_data2"], data["product_details"], "retail_data2")
    combined = pd.concat([c1, c2], ignore_index=True)
    masked = apply_pii_masking(combined)
    final = run_transformation(masked, data["product_details"])
    print(final[["transaction_id", "product_name", "category", "price", "quantity", "discount", "revenue"]].head(10))
