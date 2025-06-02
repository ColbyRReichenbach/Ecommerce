import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
from sqlalchemy import create_engine
from datetime import datetime, timedelta

from queries import (
    get_main_kpis, get_revenue_orders_trend, get_aov_trend, get_new_vs_returning_customer_revenue,
    get_category_performance_matrix, get_category_return_rates,
    get_orders_over_time_by_granularity, get_order_status_distribution, get_revenue_by_items_in_order, get_peak_order_times,
    get_clv_distribution_data, get_customer_counts_for_repeat_rate, get_avg_time_between_orders,
    get_top_categories_for_customer_type, get_payment_preferences,
    get_revenue_orders_by_state_map_data, get_shipping_performance_matrix_data, get_delivery_time_breakdown_by_state,
    get_segment_summary_metrics, # This one is conceptual for now
    get_min_max_order_dates, get_avg_items_per_order, 
    get_most_frequent_order_status_nondelivered
)

st.set_page_config(page_title="E-Commerce Advanced Analytics", layout="wide")

# --- Database Connection ---
@st.cache_resource # Cache the engine resource
def init_db_engine():
    try:
        DATABASE_URL = st.secrets["DATABASE_URL"]
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None

engine = init_db_engine()

if not engine:
    st.stop()

# --- Global Filters in Sidebar ---
st.sidebar.title("Global Filters")

# Date Range Selector (already implemented and seems okay)
min_max_dates_df = get_min_max_order_dates(engine)
if not min_max_dates_df.empty:
    MIN_DATE = pd.to_datetime(min_max_dates_df['min_date'].iloc[0])
    MAX_DATE = pd.to_datetime(min_max_dates_df['max_date'].iloc[0])
else:
    MIN_DATE = datetime.now() - timedelta(days=365*3) # Approx 3 years back
    MAX_DATE = datetime.now()

selected_start_date, selected_end_date = st.sidebar.date_input(
    "Select Date Range",
    value=(MAX_DATE - timedelta(days=365), MAX_DATE),
    min_value=MIN_DATE,
    max_value=MAX_DATE,
    key="date_range_selector"
)
selected_start_date = datetime.combine(selected_start_date, datetime.min.time())
selected_end_date = datetime.combine(selected_end_date, datetime.max.time())

# Category Filter
all_categories_df = query_database(engine, "SELECT DISTINCT product_category_name_english FROM products WHERE product_category_name_english IS NOT NULL ORDER BY 1;") # Assuming product_category_name_english column
if not all_categories_df.empty:
    all_categories = ["All"] + all_categories_df["product_category_name_english"].tolist()
    selected_category_filter = st.sidebar.selectbox("Filter by Product Category", all_categories, key="category_filter_global")
    if selected_category_filter == "All":
        selected_category_filter = None # Set to None if 'All' is selected
else:
    st.sidebar.text("No categories found for filter.")
    selected_category_filter = None # Fallback

# Region Filter (Customer State)
all_states_df = query_database(engine, "SELECT DISTINCT customer_state FROM customers WHERE customer_state IS NOT NULL ORDER BY 1;")
if not all_states_df.empty:
    all_states = ["All"] + all_states_df["customer_state"].tolist()
    selected_region_filter = st.sidebar.selectbox("Filter by Customer State", all_states, key="region_filter_global")
    if selected_region_filter == "All":
        selected_region_filter = None # Set to None if 'All' is selected
else:
    st.sidebar.text("No states found for filter.")
    selected_region_filter = None # Fallback



# --- Page Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Business Health",
        "Product Portfolio Performance",
        "Sales Funnel & Order Dynamics",
        "Customer Behavior & Value",
        "Geographic Performance & Logistics",
        "Customer Segmentation Deep Dive"
    ]
)

# --- Helper function for styling KPIs ---
def display_kpi(label, value, help_text=None, delta=None, delta_color="normal"):
    st.metric(label, value, delta=delta, delta_color=delta_color, help=help_text)

# --- Page Rendering Functions ---

def render_business_health_cockpit():
    st.title("📈 Business Health Cockpit")
    st.markdown("Immediate, high-level understanding of overall business health and trajectory.")
    
    kpi_data = get_main_kpis(engine, selected_start_date, selected_end_date)
    prev_period_start = selected_start_date - (selected_end_date - selected_start_date)
    prev_period_end = selected_start_date - timedelta(seconds=1)
    kpi_data_prev = get_main_kpis(engine, prev_period_start, prev_period_end) # For delta calculation

    if kpi_data.empty:
        st.warning("No data available for the selected period for KPIs.")
        return

    main_kpis = kpi_data.iloc[0]
    
    # COGS assumption for GPM (replace with actual logic or remove GPM if not feasible)
    COGS_PERCENTAGE = 0.6 # Assume COGS is 60% of revenue
    total_revenue = main_kpis.get('total_revenue', 0)
    cogs = total_revenue * COGS_PERCENTAGE
    gross_profit = total_revenue - cogs
    gpm = (gross_profit / total_revenue) * 100 if total_revenue else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        display_kpi("Total Revenue", f"${total_revenue:,.2f}" if total_revenue is not None else "$0.00")
        display_kpi("Active Customers", f"{main_kpis.get('active_customers', 0):,}")
    with col2:
        display_kpi("Total Orders", f"{main_kpis.get('total_orders', 0):,}")
        new_cust = main_kpis.get('new_customers',0)
        active_cust = main_kpis.get('active_customers',1) # avoid div by zero
        new_cust_rate = (new_cust / active_cust) * 100 if active_cust > 0 else 0
        display_kpi("New Customer Acquisition Rate", f"{new_cust_rate:.2f}%")
    with col3:
        display_kpi("Avg. Order Value (AOV)", f"${main_kpis.get('avg_order_value', 0):,.2f}")
        display_kpi("Gross Profit Margin (GPM)", f"{gpm:.2f}% (Est.)", help_text="Estimated using assumed COGS.")

    st.subheader("Revenue & Orders Trend")
    rev_order_trend_df = get_revenue_orders_trend(engine, selected_start_date, selected_end_date, freq='ME')
    if not rev_order_trend_df.empty:
        rev_order_trend_df['time_period'] = pd.to_datetime(rev_order_trend_df['time_period'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=rev_order_trend_df['time_period'], y=rev_order_trend_df['total_revenue'], name='Total Revenue', yaxis='y1', mode='lines+markers'))
        fig.add_trace(go.Scatter(x=rev_order_trend_df['time_period'], y=rev_order_trend_df['total_orders'], name='Total Orders', yaxis='y2', mode='lines+markers'))
        fig.update_layout(
            yaxis=dict(title='Total Revenue ($)'),
            yaxis2=dict(title='Total Orders', overlaying='y', side='right'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No revenue/order trend data for this period.")

    # AOV Trend (Line Chart)
    st.subheader("Average Order Value (AOV) Trend")
    aov_trend_df = get_aov_trend(engine, selected_start_date, selected_end_date, freq='ME')
    if not aov_trend_df.empty:
        aov_trend_df['time_period'] = pd.to_datetime(aov_trend_df['time_period'])
        fig_aov = px.line(aov_trend_df, x='time_period', y='avg_order_value', title='AOV Over Time', markers=True, labels={'avg_order_value': 'AOV ($)'})
        st.plotly_chart(fig_aov, use_container_width=True)
    else:
        st.info("No AOV trend data for this period.")

    # New vs. Returning Customer Revenue (Stacked Bar/Area)
    st.subheader("New vs. Returning Customer Revenue")
    nvr_df = get_new_vs_returning_customer_revenue(engine, selected_start_date, selected_end_date, freq='ME')
    if not nvr_df.empty:
        nvr_df['time_period'] = pd.to_datetime(nvr_df['time_period'])
        fig_nvr = go.Figure()
        fig_nvr.add_trace(go.Bar(x=nvr_df['time_period'], y=nvr_df['new_customer_revenue'], name='New Customer Revenue'))
        fig_nvr.add_trace(go.Bar(x=nvr_df['time_period'], y=nvr_df['returning_customer_revenue'], name='Returning Customer Revenue'))
        fig_nvr.update_layout(barmode='stack', title='Monthly Revenue by Customer Type', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_nvr, use_container_width=True)
    else:
        st.info("No new vs returning customer revenue data for this period.")

    st.markdown("""
    **What Does This Mean?**
    - This cockpit provides a snapshot of core business performance.
    - Growth in revenue should ideally be supported by growth in orders and/or AOV.
    - A healthy mix of new and returning customer revenue indicates sustainable growth.
    """)


def render_product_portfolio_performance():
    st.title("🎯 Product Portfolio Performance")
    st.markdown("Identify which products and categories drive success and monitor returns.")

    cat_perf_df = get_category_performance_matrix(engine, selected_start_date, selected_end_date, category_filter=selected_category_filter)
    cat_returns_df = get_category_return_rates(engine, selected_start_date, selected_end_date, category_filter=selected_category_filter)

    if cat_perf_df.empty:
        st.warning("No category performance data for the selected period/filter.")
        return

    # Merge performance and return data
    if not cat_returns_df.empty:
        cat_data_merged = pd.merge(cat_perf_df, cat_returns_df, on="product_category_name_english", how="left")
        cat_data_merged['return_rate_percentage'] = cat_data_merged['return_rate_percentage'].fillna(0)
    else:
        cat_data_merged = cat_perf_df.copy()
        cat_data_merged['return_rate_percentage'] = 0
        cat_data_merged['avg_review_score'] = cat_data_merged.get('avg_review_score', 0)


    # KPIs
    top_cat_revenue = cat_data_merged.loc[cat_data_merged['total_revenue'].idxmax()] if not cat_data_merged.empty else None
    top_cat_units = cat_data_merged.loc[cat_data_merged['total_units_sold'].idxmax()] if not cat_data_merged.empty else None
    highest_return_cat = cat_data_merged.loc[cat_data_merged['return_rate_percentage'].idxmax()] if not cat_data_merged.empty and 'return_rate_percentage' in cat_data_merged.columns else None

    col1, col2, col3 = st.columns(3)
    with col1:
        if top_cat_revenue is not None: display_kpi("Top Category (Revenue)", f"{top_cat_revenue['product_category_name_english']}", f"${top_cat_revenue['total_revenue']:,.0f}")
    with col2:
        if top_cat_units is not None: display_kpi("Top Category (Units)", f"{top_cat_units['product_category_name_english']}", f"{top_cat_units['total_units_sold']:,} units")
    with col3:
        if highest_return_cat is not None: display_kpi("Highest Return Rate Cat.", f"{highest_return_cat['product_category_name_english']}", f"{highest_return_cat['return_rate_percentage']:.2f}%")
    
    st.subheader("Category Performance Matrix (Revenue vs. Units)")
    if not cat_data_merged.empty:
        # green (low) to red (high)
        # larger for higher scores
        fig_matrix = px.scatter(cat_data_merged,
                                x="total_units_sold",
                                y="total_revenue",
                                size="avg_review_score", 
                                color="return_rate_percentage",
                                hover_name="product_category_name_english",
                                color_continuous_scale=px.colors.diverging.RdYlGn_r, 
                                range_color=[0, max(10, cat_data_merged['return_rate_percentage'].max())],
                                title="Categories: Units vs Revenue (Size=Avg Review, Color=Return Rate)",
                                labels={'total_units_sold': 'Total Units Sold', 'total_revenue': 'Total Revenue ($)', 'return_rate_percentage': 'Return Rate (%)', 'avg_review_score':'Avg Review Score'})
        fig_matrix.update_traces(textposition='top center')
        st.plotly_chart(fig_matrix, use_container_width=True)
    else:
        st.info("Not enough data for performance matrix.")

    tab1, tab2 = st.tabs(["Top/Bottom Categories by Revenue", "Return Rates by Category"])
    with tab1:
        st.subheader("Top N & Bottom N Categories by Revenue")
        sorted_cats = cat_data_merged.sort_values(by="total_revenue", ascending=False)
        n_cats = st.slider("Select N for Top/Bottom categories", 5, min(20, len(sorted_cats)), 10)

        col_top, col_bottom = st.columns(2)
        with col_top:
            st.write(f"Top {n_cats} Categories")
            fig_top_cats = px.bar(sorted_cats.head(n_cats), x="total_revenue", y="product_category_name_english", orientation='h', color="total_revenue", text_auto='.2s', title=f"Top {n_cats} Categories by Revenue")
            fig_top_cats.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top_cats, use_container_width=True)
        with col_bottom:
            st.write(f"Bottom {n_cats} Categories")
            fig_bottom_cats = px.bar(sorted_cats.tail(n_cats).sort_values(by="total_revenue", ascending=True), x="total_revenue", y="product_category_name_english", orientation='h', color="total_revenue", text_auto='.2s', title=f"Bottom {n_cats} Categories by Revenue")
            fig_bottom_cats.update_layout(yaxis={'categoryorder':'total ascending'}) # To show smallest at bottom
            st.plotly_chart(fig_bottom_cats, use_container_width=True)
    with tab2:
        st.subheader("Return/Cancellation Rate by Category")
        if not cat_returns_df.empty: 
            fig_returns = px.bar(cat_returns_df.sort_values(by="return_rate_percentage", ascending=False).head(20),
                                 x="product_category_name_english", y="return_rate_percentage",
                                 color="return_rate_percentage", color_continuous_scale=px.colors.sequential.Reds,
                                 title="Return Rate (%) by Category (Top 20)",
                                 labels={'return_rate_percentage': 'Return Rate (%)'})
            st.plotly_chart(fig_returns, use_container_width=True)
        else:
            st.info("No return rate data for this period.")

    st.markdown("""
    **What Does This Mean?**
    - High-performing categories (high revenue, high units, good reviews, low returns) are your stars.
    - Categories with high returns need investigation into product quality, descriptions, or customer expectations.
    - Low revenue/low unit categories might be candidates for discontinuation or revised marketing.
    """)

def render_sales_funnel_dynamics():
    st.title("📈 Sales Funnel & Order Dynamics")
    st.markdown("Understand order lifecycle, purchasing patterns, and operational efficiency.")

    # --- KPIs ---
    # 1. Average Items per Order
    avg_items_df = get_avg_items_per_order(engine, selected_start_date, selected_end_date)
    avg_items_val = avg_items_df['avg_items_per_order'].iloc[0] if not avg_items_df.empty and avg_items_df['avg_items_per_order'].notna().any() else 0

    # 2. Peak Order Hour & Day (from existing get_peak_order_times)
    peak_times_df_for_kpi = get_peak_order_times(engine, selected_start_date, selected_end_date)
    peak_order_text = "N/A"
    if not peak_times_df_for_kpi.empty:
        top_peak = peak_times_df_for_kpi.loc[peak_times_df_for_kpi['total_orders'].idxmax()]
        day_map = {0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat'}
        peak_day_str = day_map.get(int(top_peak['day_of_week']), 'Unknown Day')
        peak_hour_str = f"{int(top_peak['hour_of_day']):02d}:00"
        peak_order_text = f"{peak_day_str} at {peak_hour_str} ({int(top_peak['total_orders'])} orders)"

    # 3. Most Common Non-Delivered/Non-Canceled Order Status
    common_status_df = get_most_frequent_order_status_nondelivered(engine, selected_start_date, selected_end_date)
    common_status_text = "N/A"
    if not common_status_df.empty:
        status_val = common_status_df['order_status'].iloc[0]
        status_count = common_status_df['status_count'].iloc[0]
        common_status_text = f"{status_val} ({status_count:,} orders)"
        
    col1, col2, col3 = st.columns(3)
    with col1:
        display_kpi("Avg. Items per Order", f"{avg_items_val:.2f}")
    with col2:
        display_kpi("Peak Order Time", peak_order_text, help_text="Day and hour with the most orders in the period.")
    with col3:
        display_kpi("Top Active Status", common_status_text, help_text="Most common status excluding delivered/canceled, indicating potential bottlenecks.")


    # --- Visualizations ---
    st.subheader("Order Volume Over Time")
    granularity = st.selectbox("Select Time Granularity", ["day", "week", "month", "quarter", "year"], index=2, key="sales_funnel_granularity") # Added key
    orders_time_df = get_orders_over_time_by_granularity(engine, selected_start_date, selected_end_date, granularity)
    if not orders_time_df.empty:
        orders_time_df['time_period'] = pd.to_datetime(orders_time_df['time_period'])
        fig_orders_time = px.bar(orders_time_df, x='time_period', y='total_orders', title=f"Total Orders by {granularity.capitalize()}", labels={'total_orders':'Total Orders'})
        st.plotly_chart(fig_orders_time, use_container_width=True)
    else:
        st.info("No order volume data for the selected period and granularity.")

    st.subheader("Order Status Distribution")
    order_status_df = get_order_status_distribution(engine, selected_start_date, selected_end_date)
    if not order_status_df.empty:
        fig_status_dist = px.bar(order_status_df, x='order_status', y='total_orders', color='order_status', title='Overall Order Status Distribution')
        # might want to sort this by a logical funnel order, rather than just by count.
        # Plotly Express will sort by x-axis labels or by y-values if no explicit sort.
        st.plotly_chart(fig_status_dist, use_container_width=True)
    else:
        st.info("No order status data for the selected period.")

    st.subheader("Revenue by Number of Items in Order")
    revenue_items_df = get_revenue_by_items_in_order(engine, selected_start_date, selected_end_date)
    if not revenue_items_df.empty:
        fig_rev_items = px.bar(revenue_items_df, x='items_per_order', y='total_revenue_from_order_size', title='Total Revenue by Order Size (Number of Items)')
        fig_rev_items.update_layout(xaxis_title="Number of Items in Order", yaxis_title="Total Revenue ($)")
        st.plotly_chart(fig_rev_items, use_container_width=True)
    else:
        st.info("No data on revenue by items in order for the selected period.")

    st.subheader("Peak Order Times (Heatmap)")
    peak_times_df_for_heatmap = get_peak_order_times(engine, selected_start_date, selected_end_date) # Re-fetch or use previously fetched df
    if not peak_times_df_for_heatmap.empty:
        try:
            heatmap_data = peak_times_df_for_heatmap.pivot(index='hour_of_day', columns='day_of_week', values='total_orders').fillna(0)
            day_map = {0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat'}
            heatmap_data = heatmap_data.rename(columns=day_map)
            # Ensure all days of week are present and in order for the heatmap columns
            all_days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            for day_name in all_days:
                if day_name not in heatmap_data.columns:
                    heatmap_data[day_name] = 0 # Add missing days with 0 orders
            heatmap_data = heatmap_data[all_days] # Reorder columns

            fig_heatmap = px.imshow(heatmap_data, aspect="auto",
                                    labels=dict(x="Day of Week", y="Hour of Day", color="Total Orders"),
                                    title="Order Volume Heatmap by Hour and Day",
                                    color_continuous_scale=px.colors.sequential.Viridis) # Example color scale
            st.plotly_chart(fig_heatmap, use_container_width=True)
        except Exception as e:
            st.error(f"Could not generate heatmap. Data might be sparse or not in expected format. Error: {e}")
            st.dataframe(peak_times_df_for_heatmap)
    else:
        st.info("No peak order time data for the selected period.")
    
    st.markdown("""
    **What Does This Mean?**
    - Understanding **order volume trends** helps in resource planning and identifying growth/decline.
    - **Order status distribution** can highlight bottlenecks. A high number in 'processing' or 'shipped' (but not yet 'delivered') might indicate delays.
    - Knowing **revenue by order size** informs promotions (e.g., bundle deals, free shipping thresholds to encourage larger carts).
    - **Peak order times** guide staffing, marketing campaign timing, and server load management.
    """)

def render_customer_behavior_value():
    st.title("👥 Customer Behavior & Value")
    st.markdown("Understand customer value, loyalty drivers, and preferences.")

    # KPIs
    clv_data = get_clv_distribution_data(engine, selected_start_date, selected_end_date)
    avg_clv = clv_data['total_spent'].mean() if not clv_data.empty else 0

    counts_for_rate = get_customer_counts_for_repeat_rate(engine, selected_start_date, selected_end_date)
    repeat_rate = 0
    if not counts_for_rate.empty:
        total_c = counts_for_rate['total_customers_in_period'].iloc[0]
        repeat_c = counts_for_rate['repeat_customers_in_period'].iloc[0]
        repeat_rate = (repeat_c / total_c) * 100 if total_c > 0 else 0

    avg_time_btw_orders_df = get_avg_time_between_orders(engine, selected_start_date, selected_end_date)
    avg_time_val = avg_time_btw_orders_df['avg_days_between_orders'].iloc[0] if not avg_time_btw_orders_df.empty else 0
    
    payment_pref_df = get_payment_preferences(engine, selected_start_date, selected_end_date)
    top_payment = payment_pref_df['payment_type'].iloc[0] if not payment_pref_df.empty else "N/A"

    col1, col2, col3, col4 = st.columns(4)
    with col1: display_kpi("Avg. CLV (in period)", f"${avg_clv:,.2f}")
    with col2: display_kpi("Repeat Customer Rate", f"{repeat_rate:.2f}%")
    with col3: display_kpi("Avg. Time Between Orders", f"{avg_time_val:.1f} days")
    with col4: display_kpi("Top Payment Type", top_payment)

    st.subheader("CLV Distribution")
    if not clv_data.empty:
        fig_clv_hist = px.histogram(clv_data, x="total_spent", nbins=50, title="Customer Lifetime Value (CLV) Distribution")
        st.plotly_chart(fig_clv_hist, use_container_width=True)
    else:
        st.info("No CLV data.")
    
    # RFM Segmentation - Placeholder (Requires offline calculation or complex live query)
    st.subheader("RFM Segmentation (Placeholder)")
    st.info("RFM Segmentation requires more complex offline data processing or queries. Displaying placeholder.")
    # if rfm_data:
    #   fig_rfm = px.scatter(rfm_data, x='Recency', y='Frequency', size='Monetary', color='Segment')
    #   st.plotly_chart(fig_rfm)

    st.subheader("Top Product Categories: Repeat vs. First-Time Customers")
    col_rep, col_first = st.columns(2)
    with col_rep:
        st.write("For Repeat Customers")
        repeat_cats_df = get_top_categories_for_customer_type(engine, selected_start_date, selected_end_date, customer_type='repeat')
        if not repeat_cats_df.empty:
            fig_rep_cats = px.bar(repeat_cats_df, y='product_category_name_english', x='total_revenue_for_category', orientation='h', title='Top Categories (Repeat Customers)')
            fig_rep_cats.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_rep_cats, use_container_width=True)
        else: st.info("No data for repeat customer categories.")
    with col_first:
        st.write("For First-Time Customers")
        first_cats_df = get_top_categories_for_customer_type(engine, selected_start_date, selected_end_date, customer_type='first_time')
        if not first_cats_df.empty:
            fig_first_cats = px.bar(first_cats_df, y='product_category_name_english', x='total_revenue_for_category', orientation='h', title='Top Categories (First-Time Customers)')
            fig_first_cats.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_first_cats, use_container_width=True)
        else: st.info("No data for first-time customer categories.")

    st.subheader("Payment Preferences")
    if not payment_pref_df.empty:
        fig_payment = px.pie(payment_pref_df, names='payment_type', values='usage_count', title='Payment Method Usage')
        st.plotly_chart(fig_payment, use_container_width=True)
    else:
        st.info("No payment preference data.")

    st.markdown("""
    **What Does This Mean?**
    - CLV distribution shows if value is concentrated in a few customers.
    - Understanding repeat vs. first-time purchase categories helps tailor marketing and product recommendations.
    - Payment preferences inform checkout optimization.
    """)


def render_geographic_logistics():
    st.title("🌍 Geographic Performance & Logistics")
    st.markdown("Understand regional sales, shipping efficiencies, and optimize delivery.")

    # KPIs - Placeholder (derive from the chart data below)
    # top_revenue_state = ...
    # avg_delivery_variance = ...
    # st.metric("Top Revenue State", ...)

    st.subheader("Revenue/Orders by State (Map)")
    map_data_df = get_revenue_orders_by_state_map_data(engine, selected_start_date, selected_end_date, region_filter=selected_region_filter)
    if not map_data_df.empty and 'customer_state' in map_data_df.columns and 'total_revenue' in map_data_df.columns:
        try:
            fig_map = px.choropleth(map_data_df,
                                    locations='customer_state', # Column with state codes
                                    geojson='https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson', # Example GeoJSON for Brazil
                                    featureidkey='properties.sigla', # Key in GeoJSON that matches 'locations'
                                    color='total_revenue',
                                    color_continuous_scale="Viridis",
                                    scope='south america', # Focus map
                                    hover_name='customer_state',
                                    hover_data={'total_orders': True, 'avg_order_value': True},
                                    title="Revenue by Brazilian State")
            fig_map.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig_map, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render map. Ensure state codes are correct and GeoJSON is accessible. Error: {e}")
            st.write("Displaying as bar chart instead:")
            fig_bar_map = px.bar(map_data_df.sort_values('total_revenue', ascending=False), x='customer_state', y='total_revenue', color='total_revenue', title='Revenue by State')
            st.plotly_chart(fig_bar_map, use_container_width=True)

    else:
        st.info("No map data for revenue by state.")

    st.subheader("Shipping Performance Matrix (Delivery Time vs. Variance)")
    shipping_matrix_df = get_shipping_performance_matrix_data(engine, selected_start_date, selected_end_date, region_filter=selected_region_filter)
    if not shipping_matrix_df.empty and 'delivery_variance_days' in shipping_matrix_df.columns:
        shipping_matrix_df['variance_color'] = shipping_matrix_df['delivery_variance_days'].apply(lambda x: 'Late' if x > 0 else 'Early/OnTime')
        fig_ship_matrix = px.scatter(shipping_matrix_df,
                                     x='avg_actual_delivery_time_days',
                                     y='delivery_variance_days',
                                     size='num_orders_to_state',
                                     color='variance_color',
                                     color_discrete_map={'Late':'red', 'Early/OnTime':'green'},
                                     hover_name='customer_state',
                                     title="Shipping: Delivery Time vs. Variance from Estimate (Size=Num Orders)")
        st.plotly_chart(fig_ship_matrix, use_container_width=True)
    else:
        st.info("No shipping performance matrix data.")

    st.subheader("Delivery Time Breakdown by State (Top N or Filtered)")
    # Allow user to select how many top states to show if no region filter
    num_top_states = 5
    if not selected_region_filter:
        num_top_states = st.slider("Number of Top States for Delivery Breakdown", 3, 10, 5, key="num_top_states_delivery")

    delivery_breakdown_df = get_delivery_time_breakdown_by_state(engine, selected_start_date, selected_end_date, top_n_states=num_top_states, region_filter=selected_region_filter)
    if not delivery_breakdown_df.empty:
        # Melt dataframe for stacked bar chart
        df_melted = delivery_breakdown_df.melt(id_vars=['customer_state'],
                                               value_vars=['avg_payment_processing_time', 'avg_seller_handling_time', 'avg_carrier_shipping_time'],
                                               var_name='time_segment', value_name='avg_days')
        fig_delivery_breakdown = px.bar(df_melted, x='customer_state', y='avg_days', color='time_segment',
                                        title='Average Delivery Time Breakdown by Stage and State',
                                        labels={'avg_days': 'Average Days'})
        st.plotly_chart(fig_delivery_breakdown, use_container_width=True)
    else:
        st.info("No delivery time breakdown data.")

    st.markdown("""
    **What Does This Mean?**
    - Geographic maps highlight regional sales strengths and weaknesses.
    - The shipping matrix helps identify if late deliveries are due to long actual times or poor estimates.
    - Delivery time breakdown pinpoints bottlenecks: payment, seller handling, or carrier issues.
    """)


# --- Main App Logic ---
if page == "Business Health Cockpit":
    render_business_health_cockpit()
elif page == "Product Portfolio Performance":
    render_product_portfolio_performance()
elif page == "Sales Funnel & Order Dynamics":
    render_sales_funnel_dynamics()
elif page == "Customer Behavior & Value":
    render_customer_behavior_value()
elif page == "Geographic Performance & Logistics":
    render_geographic_logistics()
elif page == "Customer Segmentation Deep Dive":
    render_customer_segmentation()

st.sidebar.markdown("---")
st.sidebar.info("Dashboard by You! | Data: E-commerce Kaggle Dataset")
