# models/churn_model.py
# PURPOSE: Build a churn prediction model that identifies customers
# unlikely to make a second purchase.

import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score
)
import pickle
import os

DB_PATH  = "data/processed/ecommerce.duckdb"
OUT_PATH = "data/processed"


# ─────────────────────────────────────────
# STEP 1: BUILD THE FEATURE TABLE
# ─────────────────────────────────────────

def build_features(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Build one row per unique customer with features from their
    first order and a target label: did they ever buy again?
    """
    # Load reviews CSV directly into DuckDB as a temporary table
    reviews_df = pd.read_csv("data/raw/olist_order_reviews_dataset.csv")
    conn.execute("""
        CREATE OR REPLACE TABLE olist_order_reviews_dataset
        AS SELECT * FROM reviews_df
    """)

    query = """
    WITH customer_orders AS (
        SELECT
            dc.unique_customer_id,
            fo.order_id,
            fo.purchase_date,
            fo.is_delivered,
            ROW_NUMBER() OVER (
                PARTITION BY dc.unique_customer_id
                ORDER BY fo.purchase_date
            ) AS order_rank,
            COUNT(fo.order_id) OVER (
                PARTITION BY dc.unique_customer_id
            ) AS total_orders
        FROM fact_orders fo
        JOIN dim_customers dc ON fo.customer_id = dc.customer_id
        WHERE fo.is_delivered = true
    ),
    first_orders AS (
        SELECT * FROM customer_orders WHERE order_rank = 1
    ),
    first_order_details AS (
        SELECT
            fo.unique_customer_id,
            fo.order_id,
            fo.purchase_date,
            fo.total_orders,
            CASE WHEN fo.total_orders = 1 THEN 1 ELSE 0
            END                                     AS churned,

            ROUND(SUM(foi.price), 2)                AS total_price,
            ROUND(SUM(foi.freight), 2)              AS total_freight,
            COUNT(foi.quantity)                     AS item_count,

            dp.category_english                     AS category,
            ds.state                                AS seller_state,

            DATEDIFF('day',
                fact_o.purchase_timestamp,
                fact_o.order_delivered_customer_date
            )                                       AS delivery_days,

            DATEDIFF('day',
                fact_o.order_delivered_customer_date,
                fact_o.order_estimated_delivery_date
            )                                       AS days_early_or_late,

            COALESCE(r.review_score, 3)             AS review_score

        FROM first_orders fo
        JOIN fact_orders fact_o   ON fo.order_id = fact_o.order_id
        JOIN fact_order_items foi ON fo.order_id = foi.order_id
        JOIN dim_products dp      ON foi.product_id = dp.product_id
        JOIN dim_sellers ds       ON foi.seller_id = ds.seller_id
        LEFT JOIN (
            SELECT order_id, AVG(review_score) AS review_score
            FROM olist_order_reviews_dataset
            GROUP BY order_id
        ) r ON fo.order_id = r.order_id
        GROUP BY
            fo.unique_customer_id,
            fo.order_id,
            fo.purchase_date,
            fo.total_orders,
            churned,
            dp.category_english,
            ds.state,
            fact_o.purchase_timestamp,
            fact_o.order_delivered_customer_date,
            fact_o.order_estimated_delivery_date,
            r.review_score
    )
    SELECT * FROM first_order_details
    WHERE delivery_days IS NOT NULL
      AND delivery_days >= 0
    """
    return conn.execute(query).fetchdf()


# ─────────────────────────────────────────
# STEP 2: PREPARE DATA FOR MODELLING
# ─────────────────────────────────────────

def prepare_features(df: pd.DataFrame):
    """
    Convert the feature table into X (features) and y (target)
    ready for scikit-learn.
    """
    le_category     = LabelEncoder()
    le_seller_state = LabelEncoder()

    df["category_encoded"]     = le_category.fit_transform(
        df["category"].fillna("unknown")
    )
    df["seller_state_encoded"] = le_seller_state.fit_transform(
        df["seller_state"].fillna("unknown")
    )

    feature_cols = [
        "total_price",
        "total_freight",
        "item_count",
        "delivery_days",
        "days_early_or_late",
        "review_score",
        "category_encoded",
        "seller_state_encoded",
    ]

    X = df[feature_cols]
    y = df["churned"]

    return X, y, feature_cols


# ─────────────────────────────────────────
# STEP 3: TRAIN THE MODEL
# ─────────────────────────────────────────

def train_model(X, y):
    """
    Split data into train/test sets and train a Random Forest classifier.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    return model, X_train, X_test, y_train, y_test


# ─────────────────────────────────────────
# STEP 4: EVALUATE THE MODEL
# ─────────────────────────────────────────

def evaluate_model(model, X_test, y_test, feature_cols):
    """
    Measure how well the model performs and save visualisations.
    """
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n=== Model Performance ===\n")
    print(classification_report(y_test, y_pred,
          target_names=["Returned", "Churned"]))

    auc = roc_auc_score(y_test, y_prob)
    print(f"ROC-AUC Score: {auc:.4f}")

    # ── Confusion matrix ──
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Returned", "Churned"],
                yticklabels=["Returned", "Churned"])
    plt.title("Confusion Matrix")
    plt.ylabel("Actual")
    plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_PATH, "confusion_matrix.png"), dpi=150)
    plt.close()
    print("  Saved: confusion_matrix.png")

    # ── Feature importance ──
    importance_df = pd.DataFrame({
        "feature":    feature_cols,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)

    plt.figure(figsize=(8, 4))
    sns.barplot(data=importance_df, x="importance", y="feature",
                hue="feature", palette="Blues_d", legend=False)
    plt.title("Feature Importance — What drives churn?")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_PATH, "feature_importance.png"), dpi=150)
    plt.close()
    print("  Saved: feature_importance.png")

    return importance_df


# ─────────────────────────────────────────
# STEP 5: SAVE MODEL + PREDICTIONS
# ─────────────────────────────────────────

def save_outputs(model, conn, feature_cols):
    """
    Save the trained model to disk and export churn
    probability scores for every customer to CSV.
    """
    # Save model
    model_path = os.path.join("models", "churn_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"\n  Model saved to: {model_path}")

    # Score all customers
    df = build_features(conn)
    X, y, _ = prepare_features(df)

    df["churn_probability"] = model.predict_proba(X)[:, 1]
    df["churn_prediction"]  = model.predict(X)

    output_cols = [
        "unique_customer_id",
        "total_price",
        "total_freight",
        "delivery_days",
        "days_early_or_late",
        "review_score",
        "item_count",
        "category",
        "seller_state",
        "churned",
        "churn_probability",
        "churn_prediction",
    ]

    out_file = os.path.join(OUT_PATH, "churn_scores.csv")
    df[output_cols].to_csv(out_file, index=False)
    print(f"  Churn scores saved to: {out_file}")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    conn = duckdb.connect(DB_PATH)

    print("Building feature table...")
    df = build_features(conn)
    print(f"  {len(df):,} customers with complete first-order data")
    print(f"  Churn rate: {df['churned'].mean()*100:.1f}%")

    print("\nPreparing features...")
    X, y, feature_cols = prepare_features(df)

    print("Training model...")
    model, X_train, X_test, y_train, y_test = train_model(X, y)

    evaluate_model(model, X_test, y_test, feature_cols)

    save_outputs(model, conn, feature_cols)

    conn.close()
    print("\n=== Churn model complete ===")