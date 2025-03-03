import pandas as pd
from ecommerce_data_project.config.db_config import get_db_session, engine
import os

# Define cleaned data path
CLEANED_DATA_PATH = "/Users/colbyreichenbach/Desktop/Portfolio/ecommerce/pythonEcommerce/ecommerce_data_project/data/cleaned/"


def insert_data():
    """Reads cleaned CSV files and inserts data into the SQL database."""
    session = get_db_session()

    # Load and Insert Geolocation Data
    df_geolocation = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "geolocation_cleaned.csv"))
    df_geolocation.to_sql("geolocation", con=engine, if_exists="append", index=False)

    # Load and Insert Customers Data
    df_customers = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "customers_cleaned.csv"))
    df_customers.to_sql("customers", con=engine, if_exists="append", index=False)

    # Load and Insert Sellers Data
    df_sellers = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "sellers_cleaned.csv"))
    df_sellers.to_sql("sellers", con=engine, if_exists="append", index=False)

    # Load and Insert Products Data
    df_products = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "products_cleaned.csv"))
    df_products.to_sql("products", con=engine, if_exists="append", index=False)

    # Load and Insert Orders Data
    df_orders = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "orders_cleaned.csv"))
    df_orders.to_sql("orders", con=engine, if_exists="append", index=False)

    # Load and Insert Order Items Data
    df_order_items = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "order_items_cleaned.csv"))
    df_order_items.to_sql("order_items", con=engine, if_exists="append", index=False)

    # Load and Insert Payments Data
    df_payments = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "payments_cleaned.csv"))
    df_payments.to_sql("payments", con=engine, if_exists="append", index=False)

    # Load and Insert Reviews Data
    df_reviews = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "reviews_cleaned.csv"))
    df_reviews.to_sql("reviews", con=engine, if_exists="append", index=False)

    session.commit()
    session.close()
    print("Cleaned data inserted successfully!")


if __name__ == "__main__":
    insert_data()
