import pandas as pd
import os

RAW_DATA_PATH = "/Users/colbyreichenbach/Desktop/Portfolio/ecommerce/pythonEcommerce/ecommerce_data_project/data/raw/"
CLEANED_DATA_PATH = "/Users/colbyreichenbach/Desktop/Portfolio/ecommerce/pythonEcommerce/ecommerce_data_project/data/cleaned/"

os.makedirs(CLEANED_DATA_PATH, exist_ok=True)


def clean_customers():
    df = pd.read_csv(os.path.join(RAW_DATA_PATH, "olist_customers_dataset.csv"))
    df.drop_duplicates(subset=["customer_id"], inplace=True)
    df.to_csv(os.path.join(CLEANED_DATA_PATH, "customers_cleaned.csv"), index=False)
    print("Customers data cleaned and saved.")


def clean_products():
    df = pd.read_csv(os.path.join(RAW_DATA_PATH, "olist_products_dataset.csv"))
    df.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length"
    }, inplace=True)
    df.fillna({"product_category_name": "unknown"}, inplace=True)
    df_categories = pd.read_csv(os.path.join(RAW_DATA_PATH, "product_category_name_translation.csv"))
    df = df.merge(df_categories, on="product_category_name", how="left")
    df.to_csv(os.path.join(CLEANED_DATA_PATH, "products_cleaned.csv"), index=False)
    print("Products data cleaned and saved.")


def clean_orders():
    df = pd.read_csv(os.path.join(RAW_DATA_PATH, "olist_orders_dataset.csv"))
    df.drop_duplicates(inplace=True)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_approved_at"] = pd.to_datetime(df["order_approved_at"], errors='coerce')
    df["order_delivered_carrier_date"] = pd.to_datetime(df["order_delivered_carrier_date"], errors='coerce')
    df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"], errors='coerce')
    df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"])
    df = df.dropna(subset=["customer_id"])
    df.to_csv(os.path.join(CLEANED_DATA_PATH, "orders_cleaned.csv"), index=False)
    print("Orders data cleaned and saved.")


def clean_order_items():
    df = pd.read_csv(os.path.join(RAW_DATA_PATH, "olist_order_items_dataset.csv"))
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors='coerce')
    df.to_csv(os.path.join(CLEANED_DATA_PATH, "order_items_cleaned.csv"), index=False)
    print("Order Items data cleaned and saved.")

def clean_payments():
    df = pd.read_csv(os.path.join(RAW_DATA_PATH, "olist_order_payments_dataset.csv"))
    df.to_csv(os.path.join(CLEANED_DATA_PATH, "payments_cleaned.csv"), index=False)
    print("Payments data cleaned and saved.")


def clean_reviews():
    df = pd.read_csv(os.path.join(RAW_DATA_PATH, "olist_order_reviews_dataset.csv"))
    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors='coerce')
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors='coerce')
    df = df.drop_duplicates(subset=["review_id"], keep="first")
    df.fillna({"review_comment_title": "No Title", "review_comment_message": "No Message"}, inplace=True)
    df.to_csv(os.path.join(CLEANED_DATA_PATH, "reviews_cleaned.csv"), index=False)
    print("Reviews data cleaned and saved.")


def clean_geolocation():
    df = pd.read_csv(os.path.join(RAW_DATA_PATH, "olist_geolocation_dataset.csv"))
    df.drop_duplicates(subset=["geolocation_zip_code_prefix"], inplace=True)
    df.to_csv(os.path.join(CLEANED_DATA_PATH, "geolocation_cleaned.csv"), index=False)
    print("Geolocation data cleaned and saved.")


def fix_missing_zip_codes():
    customers = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "customers_cleaned.csv"))
    sellers = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "sellers_cleaned.csv"))
    geolocation = pd.read_csv(os.path.join(CLEANED_DATA_PATH, "geolocation_cleaned.csv"))
    missing_customer_zip_codes = set(customers["customer_zip_code_prefix"]) - set(geolocation["geolocation_zip_code_prefix"])
    missing_seller_zip_codes = set(sellers["seller_zip_code_prefix"]) - set(geolocation["geolocation_zip_code_prefix"])
    missing_zip_codes = missing_customer_zip_codes.union(missing_seller_zip_codes)
    if missing_zip_codes:
        print(f"Adding {len(missing_zip_codes)} missing zip codes to geolocation_cleaned.csv")
        missing_geo_df = pd.DataFrame({
            "geolocation_zip_code_prefix": list(missing_zip_codes),
            "geolocation_lat": None,
            "geolocation_lng": None,
            "geolocation_city": "Unknown",
            "geolocation_state": "XX"
        })
        geolocation = pd.concat([geolocation, missing_geo_df], ignore_index=True).drop_duplicates(subset=["geolocation_zip_code_prefix"], keep='first')
        geolocation.to_csv(os.path.join(CLEANED_DATA_PATH, "geolocation_cleaned.csv"), index=False)
        print("Missing zip codes added and verified.")


def clean_sellers():
    df = pd.read_csv(os.path.join(RAW_DATA_PATH, "olist_sellers_dataset.csv"))
    df.to_csv(os.path.join(CLEANED_DATA_PATH, "sellers_cleaned.csv"), index=False)
    print("✅ Sellers data cleaned and saved.")


def run_data_cleaning():
    clean_customers()
    clean_products()
    clean_orders()
    clean_order_items()
    clean_payments()
    clean_reviews()
    clean_geolocation()
    clean_sellers()
    fix_missing_zip_codes()
    print("All datasets cleaned and saved.")


if __name__ == "__main__":
    run_data_cleaning()
