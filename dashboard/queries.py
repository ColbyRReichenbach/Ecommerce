# queries.py
from sqlalchemy import text
import pandas as pd

def query_database(query, engine, params=None):
    """
    Executes a SQL query with optional parameters using the passed-in engine.
    Returns a Pandas DataFrame.
    """
    with engine.connect() as conn:
        if params:
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))
        return pd.DataFrame(result.fetchall(), columns=result.keys())


# -------------------------  BUSINESS & SALES  ------------------------- #

def get_business_overview(engine):
    query = """
        SELECT 
            COUNT(DISTINCT o.order_id) AS total_orders,  
            SUM(oi.price + oi.freight_value) AS total_revenue,  
            AVG(oi.price + oi.freight_value) AS avg_order_value,
            COUNT(DISTINCT c.customer_unique_id) AS total_customers
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered';
    """
    return query_database(query, engine)


def get_monthly_revenue_trends(engine):
    query = """
        SELECT DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
               SUM(oi.price + oi.freight_value) AS total_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY month
        ORDER BY month;
    """
    return query_database(query, engine)


def get_yearly_revenue(engine):
    query = """
        SELECT EXTRACT(YEAR FROM o.order_purchase_timestamp) AS year,
               SUM(oi.price + oi.freight_value) AS total_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY year
        ORDER BY year;
    """
    return query_database(query, engine)


def get_monthly_orders(engine):
    query = """
        SELECT DATE_TRUNC('day', order_purchase_timestamp) AS order_day,
               DATE_TRUNC('month', order_purchase_timestamp) AS month,
               COUNT(order_id) AS total_orders
        FROM orders
        WHERE order_status = 'delivered'
        GROUP BY order_day, month
        ORDER BY order_day;
    """
    return query_database(query, engine)


def get_order_status_distribution(engine):
    query = """
        SELECT order_status, COUNT(order_id) AS total_orders
        FROM orders
        GROUP BY order_status
        ORDER BY total_orders DESC;
    """
    return query_database(query, engine)


def get_revenue_contribution(engine):
    query = """
        SELECT order_count, 
               SUM(total_revenue) AS total_revenue
        FROM (
            SELECT o.order_id, 
                   COUNT(oi.product_id) AS order_count,
                   SUM(oi.price + oi.freight_value) AS total_revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY o.order_id
        ) AS order_data
        GROUP BY order_count
        ORDER BY order_count;
    """
    return query_database(query, engine)


# -------------------------  PRODUCT PERFORMANCE  ------------------------- #

def get_category_sales(engine, limit=30):
    query = """
        SELECT p.product_category_name_english,
               COUNT(oi.product_id) AS total_units_sold,
               SUM(oi.price + oi.freight_value) AS total_revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY p.product_category_name_english
        ORDER BY total_units_sold DESC
        LIMIT :limit;
    """
    return query_database(query, engine, {"limit": limit})


def get_return_rate(engine, limit=10):
    query = """
        SELECT 
            p.product_category_name_english,
            COUNT(CASE WHEN o.order_status = 'canceled' THEN 1 END) * 100.0 / COUNT(*) AS return_rate
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.product_category_name_english
        ORDER BY return_rate DESC
        LIMIT :limit;
    """
    return query_database(query, engine, {"limit": limit})


# -------------------------  CUSTOMER INSIGHTS  ------------------------- #

def get_customer_lifetime_value(engine):
    query = """
        SELECT 
            c.customer_unique_id, 
            SUM(oi.price + oi.freight_value) AS total_spent,
            COUNT(DISTINCT o.order_id) AS total_orders,
            ROUND(SUM(oi.price + oi.freight_value) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_unique_id
        ORDER BY total_spent DESC
        LIMIT 10;
    """
    return query_database(query, engine)


def get_repeat_customer_details(engine, limit=10):
    query = """
        SELECT p.product_category_name_english,
               COUNT(*) AS total_purchases,
               SUM(oi.price + oi.freight_value) AS total_spent
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE o.order_status = 'delivered'
          AND c.customer_unique_id IN (
              SELECT c2.customer_unique_id
              FROM orders o2
              JOIN customers c2 ON o2.customer_id = c2.customer_id
              WHERE o2.order_status = 'delivered'
              GROUP BY c2.customer_unique_id
              HAVING COUNT(DISTINCT o2.order_id) > 1
          )
        GROUP BY p.product_category_name_english
        ORDER BY total_purchases DESC
        LIMIT :limit;
    """
    return query_database(query, engine, {"limit": limit})


def get_customer_payment_preferences(engine):
    query = """
        SELECT payment_type, COUNT(*) AS usage_count
        FROM payments
        GROUP BY payment_type
        ORDER BY usage_count DESC;
    """
    return query_database(query, engine)


# -------------------------  GEOGRAPHIC & SHIPPING  ------------------------- #

def get_revenue_by_region(engine, state=None):
    if state:
        query = """
            SELECT c.customer_state, c.customer_city, 
                   ROUND(SUM(oi.price + oi.freight_value), 2) AS total_revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered' 
              AND c.customer_state = :state
            GROUP BY c.customer_state, c.customer_city
            ORDER BY total_revenue DESC;
        """
        return query_database(query, engine, {"state": state})
    else:
        query = """
            SELECT c.customer_state, 
                   ROUND(SUM(oi.price + oi.freight_value), 2) AS total_revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_state
            ORDER BY total_revenue DESC;
        """
        return query_database(query, engine)


def get_shipping_performance(engine, state=None):
    if state:
        query = """
            SELECT c.customer_state, c.customer_city, 
                   ROUND(AVG(EXTRACT(DAY FROM (o.order_delivered_customer_date - o.order_purchase_timestamp))), 2)
                   AS avg_actual_delivery_time,
                   ROUND(AVG(EXTRACT(DAY FROM (o.order_estimated_delivery_date - o.order_purchase_timestamp))), 2)
                   AS avg_estimated_delivery_time
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered'
              AND c.customer_state = :state
            GROUP BY c.customer_state, c.customer_city
            ORDER BY avg_actual_delivery_time DESC;
        """
        data = query_database(query, engine, {"state": state})
    else:
        query = """
            SELECT c.customer_state, 
                   ROUND(AVG(EXTRACT(DAY FROM (o.order_delivered_customer_date - o.order_purchase_timestamp))), 2)
                   AS avg_actual_delivery_time,
                   ROUND(AVG(EXTRACT(DAY FROM (o.order_estimated_delivery_date - o.order_purchase_timestamp))), 2)
                   AS avg_estimated_delivery_time
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_state
            ORDER BY avg_actual_delivery_time DESC;
        """
        data = query_database(query, engine)

    if not data.empty:
        data["delivery_variance"] = data["avg_actual_delivery_time"] - data["avg_estimated_delivery_time"]
    return data


# Additional queries if needed...
