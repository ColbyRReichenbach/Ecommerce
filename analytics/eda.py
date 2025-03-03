import pandas as pd
from sqlalchemy import create_engine
from ecommerce_data_project.config.db_config import DB_URL

engine = create_engine(DB_URL)

queries = {
    "Customer Lifetime Value (CLV)":
        """SELECT c.customer_unique_id, COUNT(o.order_id) AS total_orders,
           SUM(oi.price) AS total_revenue,
           SUM(oi.price) / COUNT(o.order_id) AS avg_order_value
           FROM customers c
           JOIN orders o ON c.customer_id = o.customer_id
           JOIN order_items oi ON o.order_id = oi.order_id
           WHERE o.order_status = 'delivered'
           GROUP BY c.customer_unique_id
           ORDER BY total_revenue DESC;""",
    "Repeat Purchase Rate":
        """SELECT COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) * 100.0 / 
           COUNT(DISTINCT customer_unique_id) AS repeat_purchase_rate
           FROM (SELECT customer_unique_id, COUNT(order_id) AS order_count
                 FROM customers c
                 JOIN orders o ON c.customer_id = o.customer_id
                 WHERE o.order_status = 'delivered'
                 GROUP BY customer_unique_id) subquery;""",
    "Churn Rate (6 months inactive)":
        """SELECT COUNT(DISTINCT customer_unique_id) * 100.0 /
           (SELECT COUNT(DISTINCT customer_unique_id) FROM customers) AS churn_rate
           FROM (SELECT customer_unique_id, MAX(o.order_purchase_timestamp) AS last_order_date
                 FROM customers c
                 JOIN orders o ON c.customer_id = o.customer_id
                 WHERE o.order_status = 'delivered'
                 GROUP BY customer_unique_id) subquery
           WHERE last_order_date < (CURRENT_DATE - INTERVAL '6 months');""",
    "Average Order Value (AOV)":
        """SELECT SUM(price) / COUNT(DISTINCT order_id) AS avg_order_value FROM order_items;""",
    "Payment Method Performance":
        """SELECT payment_type, COUNT(*) AS total_transactions, SUM(payment_value) AS total_revenue
           FROM payments GROUP BY payment_type ORDER BY total_revenue DESC;""",
    "Revenue Trends Over Time":
        """SELECT DATE_TRUNC('month', o.order_purchase_timestamp) AS month, 
           SUM(oi.price) AS total_revenue
           FROM orders o
           JOIN order_items oi ON o.order_id = oi.order_id
           WHERE o.order_status = 'delivered'
           GROUP BY month ORDER BY month;""",
    "Estimated Return Rate":
        """SELECT COUNT(order_id) * 100.0 / 
           (SELECT COUNT(order_id) FROM orders WHERE order_status = 'delivered') AS estimated_return_rate
           FROM orders WHERE order_status = 'canceled';""",
    "Top-Selling Product Categories":
        """SELECT p.product_category_name_english AS category, COUNT(oi.product_id) AS total_sales
           FROM products p
           JOIN order_items oi ON p.product_id = oi.product_id
           GROUP BY category ORDER BY total_sales DESC LIMIT 10;""",
    "Customer Satisfaction (Review Scores)":
        """SELECT review_score, COUNT(*) AS review_count, 
           COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reviews) AS percentage
           FROM reviews GROUP BY review_score ORDER BY review_score DESC;""",
    "Average Review Response Time":
        """SELECT AVG(EXTRACT(DAY FROM (review_answer_timestamp - review_creation_date))) AS avg_response_time
           FROM reviews;""",
    "Average Delivery Time vs. Estimated Time":
        """SELECT AVG(EXTRACT(DAY FROM (order_delivered_customer_date - order_purchase_timestamp))) AS avg_actual_delivery_time,
           AVG(EXTRACT(DAY FROM (order_estimated_delivery_date - order_purchase_timestamp))) AS avg_estimated_delivery_time
           FROM orders 
           WHERE order_status = 'delivered';""",
    "Shipping Cost Per Order":
        """SELECT AVG(freight_value) AS avg_shipping_cost FROM order_items;"""
}


def run_eda_queries():
    with engine.connect() as connection:
        for query_name, query in queries.items():
            print(f"\n{query_name}\n")
            df = pd.read_sql(query, connection)
            print(df.head())


if __name__ == "__main__":
    run_eda_queries()
