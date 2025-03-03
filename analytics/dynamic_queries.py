import sqlalchemy
import pandas as pd
from sqlalchemy import create_engine, text
from ecommerce_data_project.config.db_config import DB_URL

engine = create_engine(DB_URL)


def execute_query(query, params={}):
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        return pd.DataFrame(result.fetchall(), columns=result.keys())


def get_revenue_over_time(start_date, end_date):
    query = """
        SELECT DATE_TRUNC('month', order_purchase_timestamp) AS month, 
               SUM(price) AS total_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered' 
          AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
        GROUP BY month
        ORDER BY month;
    """
    return execute_query(query, {"start_date": start_date, "end_date": end_date})


def get_customer_rfm():
    query = """
        SELECT c.customer_unique_id,
               MAX(o.order_purchase_timestamp) AS last_purchase_date,
               COUNT(o.order_id) AS purchase_frequency,
               SUM(oi.price) AS total_monetary_value
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_unique_id
        ORDER BY total_monetary_value DESC;
    """
    return execute_query(query)


def get_top_selling_products(start_date, end_date, top_n):
    query = """
        SELECT p.product_id, p.product_category_name,
               COUNT(oi.order_id) AS total_sales,
               SUM(oi.price) AS total_revenue
        FROM products p
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
        GROUP BY p.product_id, p.product_category_name
        ORDER BY total_sales DESC
        LIMIT :top_n;
    """
    return execute_query(query, {"start_date": start_date, "end_date": end_date, "top_n": top_n})


def get_delivery_times_by_region(start_date, end_date):
    query = """
        SELECT c.customer_state, 
               AVG(o.order_delivered_customer_date - o.order_purchase_timestamp) AS avg_delivery_days
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
        GROUP BY c.customer_state
        ORDER BY avg_delivery_days DESC;
    """
    return execute_query(query, {"start_date": start_date, "end_date": end_date})


def get_payment_method_performance():
    query = """
        SELECT payment_type, COUNT(*) AS total_transactions, SUM(payment_value) AS total_revenue
        FROM payments
        GROUP BY payment_type
        ORDER BY total_revenue DESC;
    """
    return execute_query(query)


def get_churn_rate():
    query = """
        SELECT COUNT(DISTINCT CASE WHEN o.order_purchase_timestamp < NOW() - INTERVAL '6 months' THEN c.customer_unique_id END) * 100.0 / COUNT(DISTINCT c.customer_unique_id) AS churn_rate
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id;
    """
    return execute_query(query)


def get_review_scores():
    query = """
        SELECT review_score, COUNT(*) AS review_count, COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reviews) AS percentage
        FROM reviews
        GROUP BY review_score
        ORDER BY review_score DESC;
    """
    return execute_query(query)


def get_shipping_cost():
    query = "SELECT AVG(freight_value) AS avg_shipping_cost FROM order_items;"
    return execute_query(query)


def get_estimated_return_rate():
    query = """
        SELECT COUNT(CASE WHEN order_status = 'canceled' THEN 1 END) * 100.0 / COUNT(*) AS estimated_return_rate
        FROM orders;
    """
    return execute_query(query)


if __name__ == "__main__":
    print("Revenue Over Time:", get_revenue_over_time("2017-01-01", "2018-12-31"))
    print("Customer RFM:", get_customer_rfm().head())
    print("Top-Selling Products:", get_top_selling_products("2017-01-01", "2018-12-31", 10))
    print("Delivery Times by Region:", get_delivery_times_by_region("2017-01-01", "2018-12-31"))
