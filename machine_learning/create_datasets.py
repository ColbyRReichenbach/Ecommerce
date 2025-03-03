import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from ecommerce_data_project.config.db_config import DB_URL

engine = create_engine(DB_URL)
OUTPUT_DIR = "/Users/colbyreichenbach/Desktop/Portfolio/ecommerce/pythonEcommerce/ecommerce_data_project/data/ML/ML_outputs"

def remove_outliers_log(df, column, factor=1.5):
    if (df[column] <= 0).any():
        raise ValueError("Non-positive values found; cannot apply log transform.")
    log_vals = np.log(df[column])
    Q1 = log_vals.quantile(0.25)
    Q3 = log_vals.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR
    mask = (log_vals >= lower_bound) & (log_vals <= upper_bound)
    return df[mask]


def create_aggregated_forecasting_datasets(save=False, output_dir='datasets'):
    queries = {
        'quarterly': """
            SELECT DATE_TRUNC('quarter', order_purchase_timestamp)::date AS ds,
                   SUM(total_order_value) AS y
            FROM orders
            WHERE order_status = 'delivered'
            GROUP BY 1
            ORDER BY 1;
        """,
        'weekly': """
            SELECT DATE_TRUNC('week', order_purchase_timestamp)::date AS ds,
                   SUM(total_order_value) AS y
            FROM orders
            WHERE order_status = 'delivered'
            GROUP BY 1
            ORDER BY 1;
        """,
        'daily': """
            SELECT DATE_TRUNC('day', order_purchase_timestamp)::date AS ds,
                   SUM(total_order_value) AS y
            FROM orders
            WHERE order_status = 'delivered'
            GROUP BY 1
            ORDER BY 1;
        """
    }
    datasets = {}
    for freq, query in queries.items():
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        datasets[freq] = df
        if save:
            file_path = f"{output_dir}/forecasting_dataset_{freq}.csv"
            df.to_csv(file_path, index=False)
    return datasets


def create_segmentation_dataset():
    query = """
        SELECT c.customer_unique_id, c.customer_state, c.customer_city, c.clv, c.total_orders,
               c.avg_order_value, c.avg_days_between_orders, c.avg_shipping_cost, c.estimated_return_rate
        FROM customers c;
    """
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


def create_recommendation_dataset():
    query = """
        SELECT c.customer_unique_id, oi.product_id, COUNT(*) AS purchase_count
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_unique_id, oi.product_id;
    """
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


def main(save_to_csv: bool = True):
    if save_to_csv:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    datasets = create_aggregated_forecasting_datasets(save=False)
    for freq, df in datasets.items():
        df_clean = remove_outliers_log(df, 'y')
        file_path = os.path.join(OUTPUT_DIR, f"forecasting_dataset_{freq}.csv")
        df_clean.to_csv(file_path, index=False)
    df_seg = create_segmentation_dataset()
    print("\nSegmentation dataset preview:")
    print(df_seg.head())
    if save_to_csv:
        df_seg.to_csv(os.path.join(OUTPUT_DIR, "segmentation_dataset.csv"), index=False)
    df_recs = create_recommendation_dataset()
    print("\nRecommendation dataset preview:")
    print(df_recs.head())
    if save_to_csv:
        df_recs.to_csv(os.path.join(OUTPUT_DIR, "recommendation_dataset.csv"), index=False)


if __name__ == "__main__":
    main(save_to_csv=True)
