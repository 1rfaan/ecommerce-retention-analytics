# 🛒 E-Commerce Customer Retention Analytics

> An end-to-end data analytics project built to identify customer churn patterns,
> segment customers by value, and deliver actionable business insights through
> an interactive Power BI dashboard.

---

## 📌 Business Problem

A Brazilian e-commerce company is losing customers at an alarming rate.
Analysis reveals that **97% of customers never make a second purchase**,
making retention the single most critical challenge for sustainable growth.

This project answers four key business questions:
1. How has revenue trended over time?
2. What percentage of customers churn after their first order?
3. Which customers are most at risk of not returning?
4. Which product categories drive the most revenue?

---

## 🏗️ Architecture

Raw CSV Data (Olist)
↓
Extract (pipeline/extract.py)
↓
Transform (pipeline/transform.py)
↓
Load → DuckDB Star Schema (pipeline/load.py)
↓
SQL Analytics (sql/views/)
↓
ML Model — Churn Prediction (models/churn_model.py)
↓
Power BI Dashboard (powerbi/ecommerce_dashboard.pbix)


---

## 🔑 Key Findings

| Finding | Value |
|---|---|
| Total Revenue | R$13.22M |
| Total Orders | 96,478 |
| Unique Customers | 93,360 |
| Customer Churn Rate | **97%** |
| Top Revenue Category | Health Beauty (R$1.23M) |
| Highest Churn Risk Category | Computers |
| Avg Order Value | R$137 |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Data Ingestion | Python, pandas |
| Data Storage | DuckDB (star schema) |
| Data Transformation | pandas, SQL |
| Analytics | SQL (CTEs, window functions, RFM) |
| Machine Learning | scikit-learn (Random Forest) |
| Visualisation | Power BI Desktop |
| Version Control | Git, GitHub |

---


## 📁 Project Structure

ecommerce-retention-analytics/
│
├── data/
│   ├── raw/              ← Olist CSV files (not tracked)
│   └── processed/        ← Cleaned data, model outputs
│
├── pipeline/
│   ├── extract.py        ← Load raw CSVs + data audit
│   ├── transform.py      ← Clean and standardise data
│   ├── load.py           ← Build star schema in DuckDB
│   ├── analyse.py        ← Run SQL analytics queries
│   └── export_powerbi.py ← Export CSVs for Power BI
│
├── sql/
│   └── views/
│       ├── 01_monthly_revenue.sql
│       ├── 02_customer_retention.sql
│       ├── 03_rfm_segments.sql
│       └── 04_category_performance.sql
│
├── models/
│   ├── churn_model.py    ← Train + evaluate churn model
│   └── churn_model.pkl   ← Saved model artifact
│
├── powerbi/
│   └── ecommerce_dashboard.pbix
│
├── requirements.txt
└── README.md


---

## 🚀 How to Run

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/ecommerce-retention-analytics.git
cd ecommerce-retention-analytics
```

### 2. Set up environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Download the data
Download the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
and place all CSV files in `data/raw/`.

### 4. Run the full pipeline
```bash
python pipeline/extract.py
python pipeline/transform.py
python pipeline/load.py
python pipeline/analyse.py
python pipeline/export_powerbi.py
```

### 5. Train the churn model
```bash
python models/churn_model.py
```

### 6. Open the dashboard
Open `powerbi/ecommerce_dashboard.pbix` in Power BI Desktop.

---

## 📊 Dashboard Pages

| Page | Description |
|---|---|
| Executive Overview | Revenue trend, KPIs, revenue by state |
| Customer Retention | Churn breakdown, customer type split |
| Churn Risk | ML model scores, high-risk customers |
| Product Performance | Top categories by revenue and orders |

---

## 🧠 What I Learned

- Building a production-style ETL pipeline with Python and pandas
- Designing a star schema in DuckDB for analytical queries
- Writing advanced SQL — CTEs, window functions, RFM segmentation
- Handling class imbalance in machine learning (97:3 ratio)
- Connecting ML model outputs to a business dashboard in Power BI

---

## 📂 Data Source

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
— 100k real orders from 2016–2018, kindly made public by Olist.

---

*Built as a portfolio project to demonstrate end-to-end data analytics skills.*