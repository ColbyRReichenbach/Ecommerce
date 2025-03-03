from sqlalchemy import create_engine, text
from ecommerce_data_project.config.db_config import DB_URL

engine = create_engine(DB_URL)

update_queries = {
    "add_clv_column": "ALTER TABLE customers ADD COLUMN IF NOT EXISTS clv FLOAT;",
    "add_popularity_score": "ALTER TABLE products ADD COLUMN IF NOT EXISTS popularity_score FLOAT;",
    "add_customer_product_purchases": "ALTER TABLE customers ADD COLUMN IF NOT EXISTS product_purchases JSONB;",
    "add_avg_days_between_orders": "ALTER TABLE customers ADD COLUMN IF NOT EXISTS avg_days_between_orders FLOAT;",
    "add_total_orders": "ALTER TABLE customers ADD COLUMN IF NOT EXISTS total_orders INT;",
    "add_avg_order_value": "ALTER TABLE customers ADD COLUMN IF NOT EXISTS avg_order_value FLOAT;",
    "add_avg_shipping_cost": "ALTER TABLE customers ADD COLUMN IF NOT EXISTS avg_shipping_cost FLOAT;",
    "add_estimated_return_rate": "ALTER TABLE customers ADD COLUMN IF NOT EXISTS estimated_return_rate FLOAT;",
    "add_total_order_value_column": "ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_order_value FLOAT;",
    "update_clv": """
        UPDATE customers
        SET clv = subquery.clv_value
        FROM (
            SELECT c.customer_unique_id, SUM(oi.price + oi.freight_value) AS clv_value
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id
        ) subquery
        WHERE customers.customer_unique_id = subquery.customer_unique_id;
    """,
    "update_product_popularity": """
        UPDATE products
        SET popularity_score = subquery.popularity
        FROM (
            SELECT p.product_id, COUNT(*) AS popularity
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.order_status = 'delivered'
            GROUP BY p.product_id
        ) subquery
        WHERE products.product_id = subquery.product_id;
    """,
    "update_customer_product_purchases": """
        UPDATE customers
        SET product_purchases = subquery.purchases
        FROM (
            SELECT 
                product_counts.customer_unique_id,
                JSONB_AGG(JSONB_BUILD_OBJECT('product_id', product_counts.product_id, 'total_purchases', product_counts.total_purchases)) AS purchases
            FROM (
                SELECT c.customer_unique_id, oi.product_id, COUNT(*) AS total_purchases
                FROM customers c
                JOIN orders o ON c.customer_id = o.customer_id
                JOIN order_items oi ON o.order_id = oi.order_id
                WHERE o.order_status = 'delivered'
                GROUP BY c.customer_unique_id, oi.product_id
            ) AS product_counts
            GROUP BY product_counts.customer_unique_id
        ) subquery
        WHERE customers.customer_unique_id = subquery.customer_unique_id;
    """,
    "update_avg_days_between_orders": """
        UPDATE customers
        SET avg_days_between_orders = subquery.avg_days
        FROM (
            SELECT 
                order_gaps.customer_unique_id,
                COALESCE(AVG(order_gaps.order_gap), 0) AS avg_days
            FROM (
                SELECT c.customer_unique_id,
                       EXTRACT(DAY FROM (LEAD(o.order_purchase_timestamp) OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp) - o.order_purchase_timestamp)) AS order_gap
                FROM customers c
                JOIN orders o ON c.customer_id = o.customer_id
                WHERE o.order_status = 'delivered'
            ) AS order_gaps
            GROUP BY order_gaps.customer_unique_id
        ) subquery
        WHERE customers.customer_unique_id = subquery.customer_unique_id;
    """,
    "update_total_orders": """
        UPDATE customers
        SET total_orders = subquery.order_count
        FROM (
            SELECT c.customer_unique_id, COUNT(o.order_id) AS order_count
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id
        ) subquery
        WHERE customers.customer_unique_id = subquery.customer_unique_id;
    """,
    "update_avg_order_value": """
        UPDATE customers
        SET avg_order_value = subquery.aov
        FROM (
            SELECT c.customer_unique_id, COALESCE(AVG(oi.price + oi.freight_value), 0) AS aov
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id
        ) subquery
        WHERE customers.customer_unique_id = subquery.customer_unique_id;
    """,
    "update_avg_shipping_cost": """
        UPDATE customers
        SET avg_shipping_cost = subquery.avg_shipping
        FROM (
            SELECT c.customer_unique_id, COALESCE(AVG(oi.freight_value), 0) AS avg_shipping
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id
        ) subquery
        WHERE customers.customer_unique_id = subquery.customer_unique_id;
    """,
    "update_estimated_return_rate": """
        UPDATE customers
        SET estimated_return_rate = subquery.return_rate
        FROM (
            SELECT c.customer_unique_id,
                   COUNT(CASE WHEN o.order_status = 'canceled' THEN 1 END)*100.0 / NULLIF(COUNT(o.order_id), 0) AS return_rate
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_unique_id
        ) subquery
        WHERE customers.customer_unique_id = subquery.customer_unique_id;
    """,
    "update_total_order_value": """
        UPDATE orders
        SET total_order_value = subquery.total
        FROM (
            SELECT oi.order_id, SUM(oi.price * oi.order_item_id) + SUM(oi.freight_value * oi.order_item_id) AS total
            FROM order_items oi
            GROUP BY oi.order_id
        ) subquery
        WHERE orders.order_id = subquery.order_id;
    """
}


def update_tables():
    with engine.connect() as conn:
        for name, query in update_queries.items():
            print(f"Executing: {name}...")
            conn.execute(text(query))
            conn.commit()
            print(f"{name} completed.")


if __name__ == "__main__":
    update_tables()
