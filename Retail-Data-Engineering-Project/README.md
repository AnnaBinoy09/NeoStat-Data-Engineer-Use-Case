# ABC Retail — End-to-End Data Engineering Project

> **The following project** demonstrating a production-style retail data pipeline:  
> ingestion → cleaning → PII masking → enrichment → KPI generation → forecasting → Excel output → Power BI.

---

## Business Problem

ABC Retail Solutions receives transaction data from multiple source systems.  
Data issues include duplicates, missing values, inconsistent categories/product names,  
mixed date formats, invalid quantities, and PII fields.

This pipeline cleans, transforms, and enriches ~8,000 transactions across  
**5 cities**, **4 product categories**, and **10 products**, producing an  
analytics-ready dataset with business KPIs and a 6-month revenue forecast.

---

## Project Structure

```
Retail Data Project/
├── Data/
│   └── source_data.xlsx          # 3 sheets: retail_data1, retail_data2, product_details
├── Code/
│   ├── ingestion.py              # Phase 1 — Read & validate source files
│   ├── validation.py             # Phase 2 — Data quality reports
│   ├── cleaning.py               # Phase 3 — Rule-based data cleaning
│   ├── masking.py                # Phase 4 — PII protection (email, phone, name)
│   ├── transformation.py         # Phase 5 & 6 — Enrichment + revenue calculation
│   ├── kpi.py                    # Phase 3 — KPI generation
│   ├── forecasting.py            # Phase 4 — Linear Regression sales forecast
│   ├── export.py                 # Phase 5 — OpenPyXL Excel output layer
│   └── main.py                   # Pipeline orchestrator — run this
├── Output/
│   └── Retail_Analytics_Output.xlsx   # Generated output (6 sheets)
├── Documentation/
│   └── (architecture diagrams, data dictionary — see below)
└── README.md
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Pandas | Data manipulation |
| NumPy | Numerical operations |
| OpenPyXL | Excel output formatting |
| Scikit-Learn | Linear Regression (forecasting ONLY) |
| Logging | Pipeline observability |
| Power BI | Dashboard layer |

---

## How to Run

```bash
# 1. Install dependencies
pip install pandas numpy openpyxl scikit-learn

# 2. source_data.xlsx in Data/ folder

# 3. Run the pipeline
cd Code
python main.py
```

Output: `Output/Retail_Analytics_Output.xlsx`

---

## Pipeline Phases

| Phase | Module | What it does |
|-------|--------|-------------|
| 1 | ingestion.py | Read 3 sheets, validate schema, log stats |
| 2 | validation.py | Missing value / duplicate / invalid value reports |
| 3 | cleaning.py | Remove duplicates, standardize categories & product names, fix dates, impute prices |
| 4 | masking.py | Mask email, phone, customer name |
| 5 | transformation.py | Join with product_details, calculate revenue |
| 6 | kpi.py | KPI Summary, Revenue by City/Category, Top Products |
| 7 | forecasting.py | Monthly aggregation → Linear Regression → 6-month forecast |
| 8 | export.py | Write 6-sheet formatted Excel workbook |

---

## Data Quality Issues Handled

| Issue | Strategy |
|-------|---------|
| Full duplicate rows | Drop, keep first |
| Same transaction_id with failed + successful status | Keep successful, drop failed |
| Missing price | Lookup product_details by product_id; fallback to median |
| Missing/invalid quantity (≤ 0) | Drop row — cannot be imputed |
| Mixed date formats | `pd.to_datetime(errors='coerce')` → drop unparseable |
| Category inconsistencies (ELEC, elec, electronics) | Lowercase lookup map → canonical name |
| Product name inconsistencies (laptop, LAPTOP) | Lowercase lookup + product dimension override |
| Discount out of [0,1] | Clip to valid range |

---

## PII Masking Strategy

| Field | Before | After |
|-------|--------|-------|
| Email | john@gmail.com | jo****@gmail.com |
| Phone | 9876543210 | ******3210 |
| Customer Name | John Smith | J*** S**** |

Masking is applied **before enrichment** — minimal exposure principle.

---

## KPIs Generated

- **Total Revenue** — ₹1.16B  
- **Total Orders** — ~7,900+  
- **Total Unique Customers**  
- **Average Order Value**  
- **Revenue by City** (Bangalore, Chennai, Delhi, Hyderabad, Mumbai)  
- **Revenue by Category** (Electronics, Furniture, Clothing, Home Appliances)  
- **Top 10 Products** by Revenue and Quantity  

---

## Sales Forecasting

- **Method**: Linear Regression (`sklearn`)  
- **Feature**: Month index (1, 2, 3, …)  
- **Target**: Monthly aggregated revenue  
- **Output**: Historical actuals + 6-month forward forecast  
- **Metrics**: MAE, RMSE, R²  
- **Assumption**: Linear trend; no seasonality. For production use, replace with Prophet or SARIMA.

---

## Excel Output Sheets

| Sheet | Contents |
|-------|---------|
| Cleaned_Data | All 7,900+ cleaned, masked, enriched transactions |
| KPI_Summary | Executive KPI card table |
| Revenue_By_City | City-level revenue aggregation |
| Revenue_By_Category | Category-level breakdown |
| Top_Products | Top 10 by revenue and quantity |
| Sales_Forecast | Monthly actuals + 6-month prediction |

---

## Power BI Dashboard (5 Pages)

1. **Executive Dashboard** — KPI cards: Total Revenue, Orders, Customers, AOV  
2. **Revenue Analysis** — Revenue trend line, by city bar chart, by category donut  
3. **Product Performance** — Top products bar charts by revenue and quantity  
4. **Regional Insights** — City heatmap, category breakdown by region  
5. **Forecast & Future Insights** — Historical vs forecast line chart, predicted growth %

**Data source**: Connect Power BI Desktop to `Output/Retail_Analytics_Output.xlsx`

---


## Architecture Diagram

```
Raw Data (source_data.xlsx)
         │
         ▼
   [ingestion.py]      ← Schema validation, logging
         │
         ▼
  [validation.py]      ← Missing / duplicate / invalid value reports
         │
         ▼
   [cleaning.py]       ← Rule-based: dedup, standardize, impute, validate
         │
         ▼
    [masking.py]       ← PII: email, phone, name masking
         │
         ▼
[transformation.py]    ← Join product_details + Revenue = Qty × Price × (1-Disc)
         │
         ▼
      [kpi.py]         ← KPI Summary, City, Category, Top Products
         │
         ▼
  [forecasting.py]     ← Monthly aggregation → LinearRegression → 6-month forecast
         │
         ▼
     [export.py]       ← OpenPyXL → Retail_Analytics_Output.xlsx (6 sheets)
         │
         ▼
     Power BI          ← 5-page dashboard
```
