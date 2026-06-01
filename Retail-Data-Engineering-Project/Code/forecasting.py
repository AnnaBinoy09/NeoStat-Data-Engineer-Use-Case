
import pandas as pd
import numpy as np
import logging
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


def build_monthly_series(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to monthly revenue time series."""
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    monthly = (
        df.groupby(df["transaction_date"].dt.to_period("M"))
        .agg(actual_revenue=("revenue", "sum"))
        .reset_index()
    )
    monthly["month_str"] = monthly["transaction_date"].astype(str)
    monthly["month_index"] = range(1, len(monthly) + 1)
    return monthly


def train_and_forecast(monthly: pd.DataFrame, forecast_months: int = 6) -> dict:
    """
    Train LinearRegression on month_index → actual_revenue.
    Forecast next `forecast_months` periods.
    """
    X = monthly[["month_index"]].values
    y = monthly["actual_revenue"].values

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)

    logger.info(f"  Model trained | MAE: ₹{mae:,.0f} | RMSE: ₹{rmse:,.0f} | R²: {r2:.3f}")

    
    monthly = monthly.copy()
    monthly["forecast_revenue"] = y_pred.round(2)

    
    last_period = monthly["transaction_date"].iloc[-1]
    future_rows = []
    for i in range(1, forecast_months + 1):
        future_period = last_period + i
        future_idx = monthly["month_index"].max() + i
        future_rev = model.predict([[future_idx]])[0]
        future_rows.append({
            "transaction_date": future_period,
            "month_str": str(future_period),
            "month_index": future_idx,
            "actual_revenue": None,
            "forecast_revenue": round(max(0, future_rev), 2),
        })

    forecast_df = pd.concat([monthly, pd.DataFrame(future_rows)], ignore_index=True)
    forecast_df = forecast_df.rename(columns={"month_str": "month"})

    return {
        "forecast_table": forecast_df[["month", "actual_revenue", "forecast_revenue"]],
        "metrics": {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "R2": round(r2, 4)},
        "model": model,
    }


def run_forecasting(df: pd.DataFrame) -> dict:
    logger.info("--- Starting Sales Forecasting ---")
    monthly = build_monthly_series(df)
    logger.info(f"  Monthly data points: {len(monthly)}")
    result = train_and_forecast(monthly, forecast_months=6)
    logger.info("✅ Forecasting complete")
    logger.info(f"  Evaluation metrics: {result['metrics']}")
    return result


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

    result = run_forecasting(final)
    print(result["forecast_table"].to_string(index=False))
    print("\nMetrics:", result["metrics"])
