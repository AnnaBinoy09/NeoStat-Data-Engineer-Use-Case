
import pandas as pd
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "retail_data1": [
        "transaction_id", "customer_id", "customer_name", "product_id",
        "price", "product_name", "category", "purchase_location", "city",
        "transaction_date", "quantity", "payment_method", "discount",
        "email", "phone", "payment_status",
    ],
    "retail_data2": [
        "transaction_id", "customer_id", "customer_name", "product_id",
        "price", "product_name", "category", "purchase_location", "city",
        "transaction_date", "quantity", "payment_method", "discount",
        "email", "phone", "payment_status",
    ],
    "product_details": ["product_id", "product_name", "category", "price"],
}

SOURCE_FILE = os.path.join(os.path.dirname(__file__), "..", "Data", "source_data.xlsx")


def load_dataset(sheet_name: str) -> pd.DataFrame:
    """Load a single sheet from the source Excel workbook."""
    if not os.path.exists(SOURCE_FILE):
        raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")

    logger.info(f"Loading sheet '{sheet_name}' from {SOURCE_FILE}")
    df = pd.read_excel(SOURCE_FILE, sheet_name=sheet_name)
    logger.info(f"  → Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def validate_schema(df: pd.DataFrame, name: str) -> None:
    """Check that all required columns exist in the dataframe."""
    expected = set(REQUIRED_COLUMNS[name])
    actual = set(df.columns)
    missing = expected - actual
    if missing:
        raise ValueError(f"Schema error in '{name}': missing columns {missing}")
    logger.info(f"  ✓ Schema validated for '{name}'")


def log_stats(df: pd.DataFrame, name: str) -> None:
    logger.info(f"--- Stats: {name} ---")
    logger.info(f"  Rows       : {len(df)}")
    logger.info(f"  Columns    : {list(df.columns)}")
    logger.info(f"  Nulls total: {df.isnull().sum().sum()}")
    logger.info(f"  Duplicates : {df.duplicated().sum()}")


def ingest_all() -> dict:
    """
    Ingest all three datasets.
    Returns a dict: {'retail_data1': df, 'retail_data2': df, 'product_details': df}

    Design decision: We read from a single workbook (three sheets) rather than three
    separate files — this mirrors a realistic scenario where data lands in one Excel
    delivery file from a vendor. The ingestion layer stays ignorant of cleaning logic.
    """
    datasets = {}
    for name in ["retail_data1", "retail_data2", "product_details"]:
        df = load_dataset(name)
        validate_schema(df, name)
        log_stats(df, name)
        datasets[name] = df

    logger.info("✅ Ingestion complete. All datasets loaded successfully.")
    return datasets


if __name__ == "__main__":
    data = ingest_all()
    for k, v in data.items():
        print(f"\n{k}: {v.shape}")
        print(v.head(3).to_string())
