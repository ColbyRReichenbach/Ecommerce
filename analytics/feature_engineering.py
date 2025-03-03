import pandas as pd
from sqlalchemy import create_engine, text

from ecommerce_data_project.config.db_config import DB_URL

# Database connection setup
engine = create_engine(DB_URL)


# Function to execute queries
def execute_query(query):
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df


# Feature Engineering Queries
queries = {
    "Customer Recency (Days Since Last Purchase)": """
        SELECT 
            c.customer_unique_id,
            COALESCE(EXTRACT(DAY FROM (NOW() - MAX(o.order_purchase_timestamp))), 0) AS days_since_last_purchase
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_unique_id;
    """,

    "Average Days Between Orders": """
        UPDATE customers
        SET avg_days_between_orders = subquery.avg_days
        FROM (
            SELECT 
                customer_unique_id,
                COALESCE(AVG(order_gap), 9999) AS avg_days -- Set single-order customers to 9999
            FROM (
                SELECT 
                    c.customer_unique_id,
                    EXTRACT(DAY FROM (LEAD(o.order_purchase_timestamp) 
                    OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp) 
                    - o.order_purchase_timestamp)) AS order_gap
                FROM customers c
                JOIN orders o ON c.customer_id = o.customer_id
            ) order_gaps
            GROUP BY customer_unique_id
        ) subquery
        WHERE customers.customer_unique_id = subquery.customer_unique_id;


    """,

    "Customer Order Frequency": """
        SELECT 
            c.customer_unique_id,
            COUNT(o.order_id) AS total_orders
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_unique_id;
    """,

    "Customer Lifetime Value (CLV)": """
        SELECT 
            c.customer_unique_id,
            SUM(oi.price) AS total_revenue,
            COUNT(DISTINCT o.order_id) AS total_orders,
            AVG(oi.price) AS avg_order_value
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY c.customer_unique_id;
    """,

    "Average Order Value (AOV)": """
        SELECT 
            c.customer_unique_id,
            AVG(oi.price) AS avg_order_value
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY c.customer_unique_id;
    """,

    "Preferred Payment Method": """
        SELECT 
            c.customer_unique_id,
            p.payment_type,
            COUNT(*) AS total_payments
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN payments p ON o.order_id = p.order_id
        GROUP BY c.customer_unique_id, p.payment_type
        ORDER BY c.customer_unique_id, total_payments DESC;
    """,

    "Average Shipping Cost": """
        SELECT 
            c.customer_unique_id,
            AVG(oi.freight_value) AS avg_shipping_cost
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY c.customer_unique_id;
    """,

    "Estimated Return Rate": """
        SELECT 
            c.customer_unique_id,
            COUNT(CASE WHEN o.order_status = 'canceled' THEN 1 END) * 100.0 / COUNT(*) AS estimated_return_rate
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_unique_id;
    """,

    "Total Oder Value": """
    UPDATE orders
    SET total_order_value = subquery.total_value
    FROM (
        SELECT 
            oi.order_id,
            SUM(oi.price * oi.order_item_id) + SUM(oi.freight_value * oi.order_item_id) AS total_value
        FROM order_items oi
        GROUP BY oi.order_id
    ) subquery
    WHERE orders.order_id = subquery.order_id;
    """

}

# Execute and print each query result
if __name__ == "__main__":
    for feature_name, query in queries.items():
        print(f"\n🔹 {feature_name} 🔹")
        df = execute_query(query)
        print(df.head())
        print("-" * 80)
