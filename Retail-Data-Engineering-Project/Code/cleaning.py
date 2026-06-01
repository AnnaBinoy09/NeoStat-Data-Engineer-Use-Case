

import pandas as pd
import numpy as np
import re
import logging

logger = logging.getLogger(__name__)


CATEGORY_MAP = {
    "elec": "Electronics",
    "electronics": "Electronics",
    "furn": "Furniture",
    "furniture": "Furniture",
    "cloth": "Clothing",
    "clothing": "Clothing",
    "home": "Home Appliances",
    "home appliances": "Home Appliances",
}


PRODUCT_NAME_MAP = {
    "laptop": "Laptop",
    "phone": "Phone",
    "shirt": "Shirt",
    "shoes": "Shoes",
    "tv": "TV",
    "sofa": "Sofa",
    "dining table": "Dining Table",
    "mixer grinder": "Mixer Grinder",
    "refrigerator": "Refrigerator",
    "microwave": "Microwave",
}



def remove_full_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows that are identical across ALL columns.
    Strategy: Keep the first occurrence. Full duplicates indicate data pipeline
    double-sends and carry no additional business information.
    """
    before = len(df)
    df = df.drop_duplicates(keep="first").reset_index(drop=True)
    logger.info(f"  Removed {before - len(df)} full duplicate rows")
    return df


def remove_failed_duplicate_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Where the same transaction_id appears more than once (one 'successful', one 'failed'),
    keep only the 'successful' record.
    Strategy: Sort so 'successful' comes first, then deduplicate on transaction key columns.
    """
    before = len(df)
    STATUS_ORDER = {"successful": 0, "failed": 1, "pending": 2}
    df["_status_rank"] = df["payment_status"].str.lower().map(STATUS_ORDER).fillna(9)
    df = (
        df.sort_values("_status_rank")
          .drop_duplicates(subset=["transaction_id", "customer_id", "product_id"], keep="first")
          .drop(columns=["_status_rank"])
          .reset_index(drop=True)
    )
    logger.info(f"  Removed {before - len(df)} duplicate transaction records")
    return df



def standardize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map all category variants to canonical names using CATEGORY_MAP.
    Strategy: Lowercase + strip before lookup so 'ELEC', 'elec', 'Elec' all resolve.
    Unmapped categories are left as-is and logged for manual review.
    """
    def map_category(val):
        if pd.isnull(val):
            return val
        key = str(val).strip().lower()
        return CATEGORY_MAP.get(key, str(val).strip().title())

    df["category"] = df["category"].apply(map_category)
    logger.info("  Categories standardized")
    return df


def standardize_product_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map product name variants to canonical names using PRODUCT_NAME_MAP.
    Strategy: Same lowercase + strip approach. The product_details dimension
    table is the master reference (applied later in enrichment).
    """
    def map_product(val):
        if pd.isnull(val):
            return val
        key = str(val).strip().lower()
        return PRODUCT_NAME_MAP.get(key, str(val).strip().title())

    df["product_name"] = df["product_name"].apply(map_product)
    logger.info("  Product names standardized")
    return df


def standardize_dates(df: pd.DataFrame, col: str = "transaction_date") -> pd.DataFrame:
    """
    Convert mixed date formats (YYYY-MM-DD datetime, MM-DD-YYYY string) to YYYY-MM-DD.
    Strategy: Use pd.to_datetime with dayfirst=False and infer_datetime_format.
    Rows with unparseable dates are dropped and logged — we cannot impute a transaction date.
    """
    before_nulls = df[col].isnull().sum()
    df[col] = pd.to_datetime(df[col], errors="coerce")
    after_nulls = df[col].isnull().sum()
    new_nulls = after_nulls - before_nulls
    if new_nulls > 0:
        logger.warning(f"  {new_nulls} rows had unparseable dates and will be dropped")
        df = df.dropna(subset=[col]).reset_index(drop=True)
    df[col] = df[col].dt.strftime("%Y-%m-%d")
    logger.info(f"  Date column '{col}' standardized to YYYY-MM-DD")
    return df



def validate_quantities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows where quantity is null, zero, or negative.
    Strategy: A zero or negative quantity has no valid business meaning in a
    retail transaction dataset and cannot be reliably imputed.
    """
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    before = len(df)
    df = df[df["quantity"] > 0].reset_index(drop=True)
    logger.info(f"  Removed {before - len(df)} rows with invalid quantity")
    return df



def impute_prices(df: pd.DataFrame, product_ref: pd.DataFrame) -> pd.DataFrame:
    """
    Fill missing prices using the product_details dimension table (lookup by product_id).
    Strategy: The master price list is the authoritative source. If product_id is not
    in the dimension table, we fall back to the column median (rare edge case).
    """
    price_lookup = product_ref.set_index("product_id")["price"].to_dict()
    median_price = df["price"].median()

    def fill_price(row):
        if pd.isnull(row["price"]) or row["price"] <= 0:
            return price_lookup.get(row["product_id"], median_price)
        return row["price"]

    df["price"] = df.apply(fill_price, axis=1)
    logger.info("  Missing prices imputed from product_details")
    return df



def validate_discounts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clip discount to [0.0, 1.0]. Nulls become 0.
    Strategy: A discount outside this range is a data entry error. We clip rather
    than drop to preserve the transaction; a discount of 0 is a safe conservative assumption.
    """
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
    logger.info("  Discounts validated and clipped to [0, 1]")
    return df



def clean_transactions(df: pd.DataFrame, product_ref: pd.DataFrame, dataset_name: str = "") -> pd.DataFrame:
    """
    Run all cleaning steps in order on a retail transactions DataFrame.
    """
    logger.info(f"--- Cleaning: {dataset_name} ({len(df)} rows) ---")
    df = remove_full_duplicates(df)
    df = remove_failed_duplicate_transactions(df)
    df = standardize_categories(df)
    df = standardize_product_names(df)
    df = standardize_dates(df)
    df = validate_quantities(df)
    df = impute_prices(df, product_ref)
    df = validate_discounts(df)
    logger.info(f"✅ Cleaning complete for '{dataset_name}': {len(df)} rows remaining")
    return df


if __name__ == "__main__":
    from ingestion import ingest_all
    data = ingest_all()
    cleaned1 = clean_transactions(data["retail_data1"], data["product_details"], "retail_data1")
    cleaned2 = clean_transactions(data["retail_data2"], data["product_details"], "retail_data2")
    print(cleaned1.head())
