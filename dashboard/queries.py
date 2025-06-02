# queries.py
from sqlalchemy import text
import pandas as pd
import streamlit as st

# --- Utility Function ---
@st.cache_data # Cache the function that executes queries
def query_database(_engine, query, params=None):
    """
    Executes a SQL query with optional parameters using the passed-in engine.
    Returns a Pandas DataFrame.
    """
    with _engine.connect() as conn:
        if params:
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df

# --- 1. Business Health ---

@st.cache_data
def get_main_kpis(_engine, start_date, end_date):
    query = """
    WITH BaseSales AS (
        SELECT
            oi.order_id,
            o.customer_id,
            c.customer_unique_id,
            o.order_purchase_timestamp,
            (oi.price + oi.freight_value) AS item_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
    ),
    OrderTotals AS (
        SELECT
            order_id,
            customer_unique_id,
            order_purchase_timestamp,
            SUM(item_revenue) AS total_order_revenue
        FROM BaseSales
        GROUP BY order_id, customer_unique_id, order_purchase_timestamp
    ),
    CustomerOrderRank AS (
        SELECT
            customer_unique_id,
            order_purchase_timestamp,
            ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp ASC) as customer_order_seq
        FROM OrderTotals
    ),
    NewCustomersInPeriod AS (
        SELECT DISTINCT customer_unique_id
        FROM CustomerOrderRank
        WHERE customer_order_seq = 1
    )
    SELECT
        COUNT(DISTINCT ot.order_id) AS total_orders,
        SUM(ot.total_order_revenue) AS total_revenue,
        SUM(ot.total_order_revenue) / COUNT(DISTINCT ot.order_id) AS avg_order_value,
        COUNT(DISTINCT ot.customer_unique_id) AS active_customers,
        (SELECT COUNT(DISTINCT customer_unique_id) FROM NewCustomersInPeriod) AS new_customers
    FROM OrderTotals ot;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})

@st.cache_data
def get_revenue_orders_trend(_engine, start_date, end_date, freq='ME'): 
    date_trunc_part = 'day'
    if freq == 'ME': date_trunc_part = 'month'
    if freq == 'YE': date_trunc_part = 'year'
    
    query = f"""
    SELECT
        DATE_TRUNC(:date_trunc_part, o.order_purchase_timestamp) AS time_period,
        SUM(oi.price + oi.freight_value) AS total_revenue,
        COUNT(DISTINCT o.order_id) AS total_orders
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
    GROUP BY time_period
    ORDER BY time_period;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date, "date_trunc_part": date_trunc_part})


@st.cache_data
def get_aov_trend(_engine, start_date, end_date, freq='ME'):
    date_trunc_part = 'month' if freq == 'ME' else 'year' if freq == 'YE' else 'day'
    query = f"""
    SELECT
        DATE_TRUNC(:date_trunc_part, o.order_purchase_timestamp) AS time_period,
        SUM(oi.price + oi.freight_value) / COUNT(DISTINCT o.order_id) AS avg_order_value
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
    GROUP BY time_period
    ORDER BY time_period;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date, "date_trunc_part": date_trunc_part})

@st.cache_data
def get_new_vs_returning_customer_revenue(_engine, start_date, end_date, freq='ME'):
    date_trunc_part = 'month' if freq == 'ME' else 'year' if freq == 'YE' else 'day'
    query = f"""
    WITH CustomerOrderRank AS (
        SELECT
            o.order_id,
            c.customer_unique_id,
            o.order_purchase_timestamp,
            ROW_NUMBER() OVER(PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp ASC) as order_rank
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp <= :end_date -- Rank based on all history up to end_date
    )
    SELECT
        DATE_TRUNC(:date_trunc_part, cor.order_purchase_timestamp) AS time_period,
        SUM(CASE WHEN cor.order_rank = 1 THEN oi.price + oi.freight_value ELSE 0 END) AS new_customer_revenue,
        SUM(CASE WHEN cor.order_rank > 1 THEN oi.price + oi.freight_value ELSE 0 END) AS returning_customer_revenue
    FROM CustomerOrderRank cor
    JOIN order_items oi ON cor.order_id = oi.order_id
    WHERE cor.order_purchase_timestamp BETWEEN :start_date AND :end_date -- Filter final aggregation by period
    GROUP BY time_period
    ORDER BY time_period;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date, "date_trunc_part": date_trunc_part})

# --- 2. Product Portfolio Performance ---

@st.cache_data
def get_category_performance_matrix(_engine, start_date, end_date, category_filter=None):
    
    # Revenue, Units, Avg Price. Review Score/Return Rate require more complex joins/subqueries.
    category_condition = "AND p.product_category_name_english = :category_filter" if category_filter else ""

    query = f"""
    SELECT
        p.product_category_name_english,
        SUM(oi.price + oi.freight_value) AS total_revenue,
        COUNT(DISTINCT oi.order_item_id) AS total_units_sold, -- Assuming order_item_id is unique per item line
        COALESCE(AVG(r.review_score), 0) AS avg_review_score -- Added average review score
        -- Add calculation for return rate per category if feasible
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN reviews r ON o.order_id = r.order_id -- Join for review scores
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
      {category_condition}
    GROUP BY p.product_category_name_english
    HAVING p.product_category_name_english IS NOT NULL AND COUNT(DISTINCT oi.order_item_id) > 0;
    """
    params = {"start_date": start_date, "end_date": end_date}
    if category_filter:
        params["category_filter"] = category_filter
    return query_database(_engine, query, params)

@st.cache_data
def get_category_return_rates(_engine, start_date, end_date, category_filter=None):
    # This definition of return rate is based on 'canceled' status.
    category_condition = "AND p.product_category_name_english = :category_filter" if category_filter else ""
    query = f"""
    SELECT
        p.product_category_name_english,
        (COUNT(CASE WHEN o.order_status = 'canceled' THEN o.order_id END) * 100.0 / COUNT(o.order_id)) AS return_rate_percentage
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.order_purchase_timestamp BETWEEN :start_date AND :end_date -- Consider if this date filter applies to cancellations
        {category_condition}
    GROUP BY p.product_category_name_english
    HAVING p.product_category_name_english IS NOT NULL;
    """
    params = {"start_date": start_date, "end_date": end_date}
    if category_filter:
        params["category_filter"] = category_filter
    return query_database(_engine, query, params)


# --- 3. Sales Funnel & Order Dynamics ---

@st.cache_data
def get_orders_over_time_by_granularity(_engine, start_date, end_date, granularity='month'):
    # granularity: 'day', 'week', 'month', 'quarter', 'year'
    query = f"""
    SELECT
        DATE_TRUNC('{granularity}', order_purchase_timestamp) AS time_period,
        COUNT(order_id) AS total_orders
    FROM orders
    WHERE order_status = 'delivered' -- Or consider all statuses for a true funnel view
      AND order_purchase_timestamp BETWEEN :start_date AND :end_date
    GROUP BY time_period
    ORDER BY time_period;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})

@st.cache_data
def get_order_status_distribution(_engine, start_date, end_date): 
    query = """
    SELECT order_status, COUNT(order_id) AS total_orders
    FROM orders
    WHERE order_purchase_timestamp BETWEEN :start_date AND :end_date
    GROUP BY order_status
    ORDER BY total_orders DESC;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})

@st.cache_data
def get_revenue_by_items_in_order(_engine, start_date, end_date): 
    query = """
    SELECT items_per_order, SUM(order_revenue) as total_revenue_from_order_size
    FROM (
        SELECT
            oi.order_id,
            COUNT(oi.order_item_id) AS items_per_order,
            SUM(oi.price + oi.freight_value) AS order_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
        GROUP BY oi.order_id
    ) sub
    GROUP BY items_per_order
    ORDER BY items_per_order;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})

@st.cache_data
def get_peak_order_times(_engine, start_date, end_date):
    # DOW: 0=Sunday, 6=Saturday
    # HOUR: 0-23
    query = """
    SELECT
        EXTRACT(DOW FROM order_purchase_timestamp) AS day_of_week,
        EXTRACT(HOUR FROM order_purchase_timestamp) AS hour_of_day,
        COUNT(order_id) AS total_orders
    FROM orders
    WHERE order_purchase_timestamp BETWEEN :start_date AND :end_date
      -- AND order_status = 'delivered' -- Consider if this filter is needed
    GROUP BY day_of_week, hour_of_day
    ORDER BY day_of_week, hour_of_day;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})

# --- 4. Customer Behavior & Value ---

@st.cache_data
def get_clv_distribution_data(_engine, start_date, end_date): 
    query = """
    SELECT
        c.customer_unique_id,
        SUM(oi.price + oi.freight_value) AS total_spent
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date -- CLV based on activity in period
    GROUP BY c.customer_unique_id;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})

@st.cache_data
def get_customer_counts_for_repeat_rate(_engine, start_date, end_date):
    query = """
    WITH CustomerOrderCounts AS (
        SELECT
            c.customer_unique_id,
            COUNT(DISTINCT o.order_id) as num_orders
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
        GROUP BY c.customer_unique_id
    )
    SELECT
        (SELECT COUNT(customer_unique_id) FROM CustomerOrderCounts) as total_customers_in_period,
        (SELECT COUNT(customer_unique_id) FROM CustomerOrderCounts WHERE num_orders > 1) as repeat_customers_in_period;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})


@st.cache_data
def get_avg_time_between_orders(_engine, start_date, end_date): # For repeat customers
    query = """
    WITH NumberedOrders AS (
        SELECT
            c.customer_unique_id,
            o.order_purchase_timestamp,
            LAG(o.order_purchase_timestamp, 1) OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp) AS previous_order_timestamp
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date -- Focus on orders within the period
    )
    SELECT
        AVG(EXTRACT(EPOCH FROM (order_purchase_timestamp - previous_order_timestamp))/86400.0) AS avg_days_between_orders
    FROM NumberedOrders
    WHERE previous_order_timestamp IS NOT NULL;
    """ # EPOCH gives seconds, /86400 for days
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})

@st.cache_data
def get_top_categories_for_customer_type(_engine, start_date, end_date, customer_type='repeat', limit=10):
    # customer_type: 'repeat' or 'first_time'
    customer_condition = """
    c.customer_unique_id IN (
        SELECT cu.customer_unique_id FROM orders o_sub
        JOIN customers cu ON o_sub.customer_id = cu.customer_id
        WHERE o_sub.order_status = 'delivered' AND o_sub.order_purchase_timestamp <= :end_date
        GROUP BY cu.customer_unique_id HAVING COUNT(DISTINCT o_sub.order_id) > 1
    )
    """ if customer_type == 'repeat' else """
    c.customer_unique_id NOT IN ( -- This is trickier for "first order IN PERIOD" vs "first order EVER"
        SELECT cu.customer_unique_id FROM orders o_sub
        JOIN customers cu ON o_sub.customer_id = cu.customer_id
        WHERE o_sub.order_status = 'delivered' AND o_sub.order_purchase_timestamp < :start_date -- Had orders before this period
        GROUP BY cu.customer_unique_id
    ) AND c.customer_unique_id IN ( -- And their first order overall falls in the period.
        SELECT first_order_customers.customer_unique_id FROM (
            SELECT cust.customer_unique_id, MIN(ord.order_purchase_timestamp) as first_purchase_date
            FROM customers cust JOIN orders ord ON cust.customer_id = ord.customer_id
            WHERE ord.order_status = 'delivered' GROUP BY cust.customer_unique_id
        ) first_order_customers
        WHERE first_order_customers.first_purchase_date BETWEEN :start_date AND :end_date
    )
    """ 

    query = f"""
    SELECT
        p.product_category_name_english,
        COUNT(DISTINCT oi.order_id) AS total_orders_for_category,
        SUM(oi.price + oi.freight_value) AS total_revenue_for_category
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
      AND {customer_condition}
      AND p.product_category_name_english IS NOT NULL
    GROUP BY p.product_category_name_english
    ORDER BY total_revenue_for_category DESC
    LIMIT :limit;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date, "limit": limit})

@st.cache_data
def get_payment_preferences(_engine, start_date, end_date): 
    query = """
    SELECT op.payment_type, COUNT(*) AS usage_count
    FROM payments op
    JOIN orders o ON op.order_id = o.order_id -- Join to filter by order date
    WHERE o.order_purchase_timestamp BETWEEN :start_date AND :end_date
    GROUP BY op.payment_type
    ORDER BY usage_count DESC;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})


# --- 5. Geographic Performance & Logistics ---

@st.cache_data
def get_revenue_orders_by_state_map_data(_engine, start_date, end_date, region_filter=None):
    # Needs to join with geolocation for lat/lng if doing scatter_mapbox
    # Or just state names for choropleth if Plotly supports them directly.
    region_condition = "AND c.customer_state = :region_filter" if region_filter else ""
    query = f"""
    SELECT
        c.customer_state,
        SUM(oi.price + oi.freight_value) AS total_revenue,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.price + oi.freight_value) / COUNT(DISTINCT o.order_id) AS avg_order_value
        -- If using scatter_mapbox, you'd need AVG(gl.geolocation_lat), AVG(gl.geolocation_lng)
        -- And join with your geolocation table:
        -- JOIN geolocation gl ON c.customer_zip_code_prefix = gl.geolocation_zip_code_prefix
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
      {region_condition}
    GROUP BY c.customer_state;
    """
    params = {"start_date": start_date, "end_date": end_date}
    if region_filter:
        params["region_filter"] = region_filter
    return query_database(_engine, query, params)

@st.cache_data
def get_shipping_performance_matrix_data(_engine, start_date, end_date, region_filter=None):
    region_condition = "AND c.customer_state = :region_filter" if region_filter else ""
    query = f"""
    SELECT
        c.customer_state,
        AVG(EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp))/86400.0) AS avg_actual_delivery_time_days,
        AVG(EXTRACT(EPOCH FROM (o.order_estimated_delivery_date - o.order_purchase_timestamp))/86400.0) AS avg_estimated_delivery_time_days,
        COUNT(o.order_id) as num_orders_to_state
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
      AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
      {region_condition}
    GROUP BY c.customer_state;
    """
    params = {"start_date": start_date, "end_date": end_date}
    if region_filter:
        params["region_filter"] = region_filter
    df = query_database(_engine, query, params)
    if not df.empty and 'avg_actual_delivery_time_days' in df.columns and 'avg_estimated_delivery_time_days' in df.columns:
        df['delivery_variance_days'] = df['avg_actual_delivery_time_days'] - df['avg_estimated_delivery_time_days']
    return df

@st.cache_data
def get_delivery_time_breakdown_by_state(_engine, start_date, end_date, top_n_states=5, region_filter=None):
    region_condition = "AND c.customer_state = :region_filter" if region_filter else ""
    # Get top N states by order volume first to limit the query complexity if not filtered by region
    query = f"""
    WITH StateOrderCounts AS (
        SELECT customer_state, COUNT(order_id) as order_count
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
          {region_condition}
        GROUP BY customer_state
        ORDER BY order_count DESC
        LIMIT {top_n_states if not region_filter else 1000} -- Apply limit only if no specific region filter
    )
    SELECT
        c.customer_state,
        AVG(EXTRACT(EPOCH FROM (o.order_approved_at - o.order_purchase_timestamp))/86400.0) AS avg_payment_processing_time,
        AVG(EXTRACT(EPOCH FROM (o.order_delivered_carrier_date - o.order_approved_at))/86400.0) AS avg_seller_handling_time,
        AVG(EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_delivered_carrier_date))/86400.0) AS avg_carrier_shipping_time
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_approved_at IS NOT NULL
      AND o.order_delivered_carrier_date IS NOT NULL
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
      AND c.customer_state IN (SELECT customer_state FROM StateOrderCounts)
    GROUP BY c.customer_state;
    """
    params = {"start_date": start_date, "end_date": end_date}
    if region_filter: 
        params["region_filter"] = region_filter

    return query_database(_engine, query, params)


# --- 6. Customer Segmentation Deep Dive ---
# For segmentation, run ML offline and store results or load precomputed CSVs.

@st.cache_data
def get_segment_summary_metrics(_engine, start_date, end_date): # Assumes a 'customer_segments' table
    # This is a conceptual query if segments are in the DB.
    query = """
    SELECT
        cs.segment_label,
        COUNT(DISTINCT cs.customer_unique_id) as number_of_customers,
        AVG(cs.clv) as avg_clv, -- Assuming CLV is stored per customer in segment table
        AVG(cs.avg_order_value) as avg_aov_segment, -- Assuming AOV is stored
        AVG(cs.order_frequency) as avg_order_frequency_segment -- Assuming Freq is stored
        -- Add more relevant metrics stored in your customer_segments table
    FROM customer_segments cs -- THIS TABLE IS HYPOTHETICAL
    -- Potentially join with orders/order_items if metrics need to be calculated based on period
    -- and not just taken from a static segment table.
    -- This depends heavily on how segmentation is implemented and results stored.
    GROUP BY cs.segment_label;
    """
    # return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})
    return pd.DataFrame()

# queries.py (add these functions)

@st.cache_data
def get_avg_items_per_order(_engine, start_date, end_date):
    query = """
    WITH OrderItemCounts AS (
        SELECT
            o.order_id,
            COUNT(oi.order_item_id) AS item_count
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered' -- Or your relevant status filter
          AND o.order_purchase_timestamp BETWEEN :start_date AND :end_date
        GROUP BY o.order_id
    )
    SELECT
        AVG(item_count) AS avg_items_per_order,
        COUNT(order_id) AS total_orders_for_avg_items -- To ensure there are orders
    FROM OrderItemCounts;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})

@st.cache_data
def get_most_frequent_order_status_nondelivered(_engine, start_date, end_date):
    query = """
    SELECT order_status, COUNT(order_id) AS status_count
    FROM orders
    WHERE order_status <> 'delivered' AND order_status <> 'canceled' -- Exclude final/negative states
      AND order_purchase_timestamp BETWEEN :start_date AND :end_date
    GROUP BY order_status
    ORDER BY status_count DESC
    LIMIT 1;
    """
    return query_database(_engine, query, {"start_date": start_date, "end_date": end_date})


# --- Helper: Get min/max dates from orders table for date picker ---
@st.cache_data
def get_min_max_order_dates(_engine):
    query = "SELECT MIN(order_purchase_timestamp)::date AS min_date, MAX(order_purchase_timestamp)::date AS max_date FROM orders;"
    return query_database(_engine, query)
