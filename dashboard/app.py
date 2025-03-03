# app.py
import sys
import os

from sqlalchemy import create_engine

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import pandas as pd
import plotly.express as px

from queries import (
    # BUSINESS & SALES
    get_business_overview,
    get_monthly_revenue_trends,
    get_yearly_revenue,
    get_monthly_orders,
    get_order_status_distribution,
    get_revenue_contribution,

    # PRODUCT PERFORMANCE
    get_category_sales,
    get_return_rate,

    # CUSTOMER INSIGHTS
    get_customer_lifetime_value,
    get_repeat_customer_details,
    get_customer_payment_preferences,

    # GEOGRAPHIC & SHIPPING
    get_revenue_by_region,
    get_shipping_performance
)

def create_db_engine_from_secrets():
    """
    Build a DB engine using the Neon connection string stored as a single key in Streamlit Secrets.
    On Streamlit Cloud, add your connection string with key DATABASE_URL in Settings > Secrets.
    """
    DATABASE_URL = st.secrets["DATABASE_URL"]
    engine = create_engine(DATABASE_URL)
    return engine

st.set_page_config(page_title="E-Commerce Analytics", layout="wide")

engine = create_db_engine_from_secrets()

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Business Overview",
        "Customer Insights",
        "Product Performance",
        "Sales & Orders",
        "Geographic Insights",
        "Shipping Insights",
        "Customer Segmentation"
    ]
)

# =========================== 1) BUSINESS OVERVIEW =========================== #
if page == "Business Overview":
    st.title("Business Overview")

    # Load Data
    overview = get_business_overview(engine)
    monthly_rev = get_monthly_revenue_trends(engine)
    yearly_rev = get_yearly_revenue(engine)

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Orders", f"{overview['total_orders'][0]:,}")
    col2.metric("Total Revenue", f"${overview['total_revenue'][0]:,.2f}")
    col3.metric("Avg. Order Value", f"${overview['avg_order_value'][0]:,.2f}")
    col4.metric("Total Customers", f"{overview['total_customers'][0]:,}")

    # Monthly Revenue (Line Chart)
    st.subheader("Monthly Revenue Trends")
    monthly_rev["month"] = pd.to_datetime(monthly_rev["month"])
    fig_monthly = px.line(
        monthly_rev,
        x="month",
        y="total_revenue",
        title="Monthly Revenue",
        markers=True,
        labels={"month": "Month", "total_revenue": "Revenue ($)"}
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

    # Yearly Revenue (Bar Chart)
    st.subheader("Year-over-Year Revenue")
    fig_yearly = px.bar(
        yearly_rev,
        x="year",
        y="total_revenue",
        title="Yearly Revenue",
        color="total_revenue",
        text_auto=True
    )
    fig_yearly.update_layout(xaxis_title="Year", yaxis_title="Revenue ($)")
    st.plotly_chart(fig_yearly, use_container_width=True)

    # Insights
    if not yearly_rev.empty:
        # Sort by year ascending to compute yoy changes
        yearly_rev_sorted = yearly_rev.sort_values(by="year")
        # Calculate the raw YoY difference & percent change
        yearly_rev_sorted["prev_year_revenue"] = yearly_rev_sorted["total_revenue"].shift(1)
        yearly_rev_sorted["abs_change"] = yearly_rev_sorted["total_revenue"] - yearly_rev_sorted["prev_year_revenue"]
        yearly_rev_sorted["pct_change"] = (
                yearly_rev_sorted["abs_change"] / yearly_rev_sorted["prev_year_revenue"] * 100
        )

        # Example: Latest yoy changes
        latest_year = int(yearly_rev_sorted["year"].iloc[-1])
        latest_revenue = yearly_rev_sorted["total_revenue"].iloc[-1]
        yoy_growth = yearly_rev_sorted["pct_change"].iloc[-1]  # Could be NaN if only 1 year

        # Similarly, you can identify best/worst months from monthly_rev
        if not monthly_rev.empty:
            # Sort monthly data
            monthly_rev_sorted = monthly_rev.sort_values(by="month")
            best_month_val = monthly_rev_sorted["total_revenue"].max()
            best_month = monthly_rev_sorted.loc[monthly_rev_sorted["total_revenue"] == best_month_val, "month"].iloc[0]
            best_month_str = pd.to_datetime(best_month).strftime("%b %Y")

            # Possibly compare best vs. worst
            worst_month_val = monthly_rev_sorted["total_revenue"].min()
            worst_month = monthly_rev_sorted.loc[monthly_rev_sorted["total_revenue"] == worst_month_val, "month"].iloc[
                0]
            worst_month_str = pd.to_datetime(worst_month).strftime("%b %Y")

        st.markdown(f"""
        **Key Insights (Data-Driven):**

        - **Year-over-Year Growth**: In **{latest_year}**, revenue reached 
          **${latest_revenue:,.2f}**, which is a **{yoy_growth:,.1f}%** change 
          compared to the previous year.
        - **Best Month**: **{best_month_str}** had the highest monthly revenue 
          of **\${best_month_val:,.2f}**, whereas **{worst_month_str}** had the 
          lowest at **${worst_month_val:,.2f}**. This gap indicates potential 
          seasonality that we can target with promotions or special campaigns.

        **Recommendations:**
        - **Seasonality Marketing**: Given the revenue dip in **{worst_month_str}**, 
          consider limited-time offers or marketing campaigns to boost sales during 
          that low period.
        - **Retention Focus**: Since growth is strong but mostly from new customers, 
          implementing a post-purchase follow-up campaign could encourage repeat buys.
        - **Budget Allocation**: The **{yoy_growth:,.1f}%** year over year growth suggests we 
          could afford to increase marketing spend. Doubling down on the best months 
          might further accelerate revenue.
        """)

# ===========================  PRODUCT PERFORMANCE PAGE  ====================== #
if page == "Product Performance":
    st.title("Product Performance")

    # -- LOAD DATA --
    category_data = get_category_sales(engine, limit=30)  # now includes both units_sold + revenue
    df_returns = get_return_rate(engine)

    # If 'category_data' is empty, warn the user and bail out
    if category_data.empty:
        st.warning("No category data available (possibly no 'delivered' orders).")
    else:
        # Let user choose how to view the data: units, revenue, or scatter of both
        view_mode = st.radio("View Mode:", ["Units Sold (Bar)", "Revenue (Bar)", "Units vs. Revenue (Scatter)"])

        if view_mode == "Units Sold (Bar)":
            st.subheader("Top Categories by Units Sold")
            fig_units = px.bar(
                category_data,
                x="product_category_name_english",
                y="total_units_sold",
                color="total_units_sold",
                text_auto=True,
                title="Units Sold by Category"
            )
            fig_units.update_layout(xaxis_title="Category", yaxis_title="Units Sold")
            st.plotly_chart(fig_units, use_container_width=True)

        elif view_mode == "Revenue (Bar)":
            st.subheader("Top Categories by Revenue")
            # Sort descending by total_revenue
            cat_revenue_sorted = category_data.sort_values("total_revenue", ascending=False)
            fig_revenue = px.bar(
                cat_revenue_sorted,
                x="product_category_name_english",
                y="total_revenue",
                color="total_revenue",
                text_auto=True,
                title="Revenue by Category"
            )
            fig_revenue.update_layout(xaxis_title="Category", yaxis_title="Revenue ($)")
            st.plotly_chart(fig_revenue, use_container_width=True)

        else:  # "Units vs. Revenue (Scatter)"
            st.subheader("Category Comparison: Units vs. Revenue")
            fig_scatter = px.scatter(
                category_data,
                x="total_units_sold",
                y="total_revenue",
                text="product_category_name_english",
                size="total_units_sold",  # or scale bubble sizes
                title="Units Sold vs. Revenue by Category",
                hover_data=["product_category_name_english"]
            )
            # Move category labels so they're more readable
            fig_scatter.update_traces(textposition="top center")
            fig_scatter.update_layout(
                xaxis_title="Units Sold",
                yaxis_title="Revenue ($)"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    # Return Rate Chart
    st.subheader("Cancellation/Return Rates by Category")
    if df_returns.empty:
        st.warning("No return-rate data available.")
    else:
        fig_return = px.bar(
            df_returns,
            x="product_category_name_english",
            y="return_rate",
            text_auto=True,
            title="Return Rate (%)"
        )
        fig_return.update_layout(xaxis_title="Category", yaxis_title="Return Rate (%)")
        st.plotly_chart(fig_return, use_container_width=True)

    # Insights
    if not category_data.empty:
        # Example placeholders: find the top category by revenue, by units
        top_cat_by_revenue = category_data.iloc[category_data["total_revenue"].idxmax()]
        top_cat_by_units = category_data.iloc[category_data["total_units_sold"].idxmax()]

        # Calculate average revenue per unit for each category (just an example)
        category_data["rev_per_unit"] = category_data["total_revenue"] / category_data["total_units_sold"]
        st.markdown(f"""
        **Key Insights (Data-Driven):**

        - **Top Category by Revenue**: *{top_cat_by_revenue["product_category_name_english"]}* 
          generated **${top_cat_by_revenue["total_revenue"]:,.2f}** in total revenue.
        - **Top Category by Units Sold**: *{top_cat_by_units["product_category_name_english"]}* 
          sold **{top_cat_by_units["total_units_sold"]:,}** units overall.
        - **Revenue per Unit**: On average, categories bring in 
          **\${category_data["rev_per_unit"].mean():.2f}** per unit. 
          One standout is *{category_data.loc[category_data["rev_per_unit"].idxmax(), "product_category_name_english"]}* 
          at **${category_data["rev_per_unit"].max():.2f}** per unit, indicating a higher-margin product line.

        **Recommendations:**
        - **Upsell High-Margin Categories**: Since 
          *{category_data.loc[category_data["rev_per_unit"].idxmax(), "product_category_name_english"]}* 
          yields a high revenue per unit, highlight it on the homepage or cross-sell it at checkout.
        - **Investigate Pricing Strategy**: If top-selling categories by units 
          have a significantly lower revenue per unit, consider raising prices or 
          bundling them with accessories for a higher average order value.
        - **Focus Marketing on High-Revenue Segments**: The top category 
          *{top_cat_by_revenue["product_category_name_english"]}* 
          already drives a large portion of total revenue. Ensure top placement in 
          ad spend or promotions to maintain this lead.
        """)


# ===========================  SALES & ORDERS PAGE  ========================== #
elif page == "Sales & Orders":
    st.title("Sales & Order Analytics")

    orders_df = get_monthly_orders(engine)
    order_status_df = get_order_status_distribution(engine)
    revenue_contrib_df = get_revenue_contribution(engine)

    # 1) TIME GRANULARITY
    st.subheader("Order Volume Over Time")
    if orders_df.empty:
        st.warning("No order data available for 'delivered' status. Charts won't render.")
    else:
        time_filter = st.selectbox("Select Time Period", ["Year", "Quarter", "Month", "Day"])

        orders_df["order_day"] = pd.to_datetime(orders_df["order_day"])
        orders_df["month"] = pd.to_datetime(orders_df["month"])

        if time_filter == "Year":
            grouped = orders_df.groupby(orders_df["month"].dt.year).agg({"total_orders": "sum"}).reset_index()
            grouped.rename(columns={"month": "year"}, inplace=True)
            x_col = "year"
        elif time_filter == "Quarter":
            grouped = orders_df.groupby(orders_df["month"].dt.to_period("Q")).agg({"total_orders": "sum"}).reset_index()
            grouped["month"] = grouped["month"].astype(str)
            x_col = "month"
        elif time_filter == "Month":
            grouped = orders_df.groupby(orders_df["month"]).agg({"total_orders": "sum"}).reset_index()
            grouped["month"] = grouped["month"].dt.strftime("%Y-%m")
            x_col = "month"
        else:  # "Day"
            grouped = orders_df.groupby(orders_df["order_day"].dt.date).agg({"total_orders": "sum"}).reset_index()
            grouped.rename(columns={"order_day": "day"}, inplace=True)
            x_col = "day"

        if not grouped.empty:
            fig_orders = px.bar(
                grouped,
                x=x_col,
                y="total_orders",
                text_auto=True,
                color="total_orders",
                title=f"Total Orders by {time_filter}"
            )
            fig_orders.update_layout(xaxis_title=time_filter, yaxis_title="Total Orders")
            st.plotly_chart(fig_orders, use_container_width=True)

    # 2) ORDER STATUS
    st.subheader("Order Status Breakdown")
    if order_status_df.empty:
        st.warning("No order status data found.")
    else:
        fig_status = px.bar(
            order_status_df,
            x="order_status",
            y="total_orders",
            text_auto=True,
            color="total_orders",
            title="Distribution of Order Status"
        )
        st.plotly_chart(fig_status, use_container_width=True)

    # Simple Insights
    if not order_status_df.empty:
        canceled_orders = order_status_df.loc[
            order_status_df["order_status"] == "canceled", "total_orders"
        ].sum()
    else:
        canceled_orders = 0

    # Insights
    if not revenue_contrib_df.empty:
        # Suppose 'revenue_contrib_df' has [order_count, total_revenue] for each distinct # of items
        # We can find the average revenue for each "order_count" bracket or the bracket that yields highest revenue
        best_order_count = revenue_contrib_df.iloc[revenue_contrib_df["total_revenue"].idxmax()]
        avg_revenue_all = revenue_contrib_df["total_revenue"].mean()

        st.markdown(f"""
        **Key Insights (Data-Driven):**
        - The highest total revenue **${best_order_count["total_revenue"]:,.2f}** 
          comes from orders containing **{best_order_count["order_count"]}** items.
        - Across all order sizes, the average total revenue is **${avg_revenue_all:,.2f}**.
          This suggests that multi-item orders can have a substantial impact on overall revenue.

        **Recommendations:**
        - **Bundle Deals**: Promote bundle discounts for customers adding more items 
          to their cart, since orders with {best_order_count["order_count"]} items 
          generate disproportionately high revenue.
        - **Revisit Shipping Policy**: If large orders are profitable but also 
          risk higher return costs, consider free shipping thresholds or multi-item 
          shipping deals to encourage that behavior.
        """)


# ==========================  CUSTOMER INSIGHTS PAGE  ======================== #
elif page == "Customer Insights":
    st.title("Customer Insights")

    clv_df = get_customer_lifetime_value(engine)
    repeat_df = get_repeat_customer_details(engine)  # now referencing customer_unique_id
    pay_prefs_df = get_customer_payment_preferences(engine)

    # Customer Lifetime Value
    st.subheader("Top 10 Customers by Lifetime Value")
    if clv_df.empty:
        st.warning("No CLV data found.")
    else:
        fig_clv = px.bar(
            clv_df,
            x="customer_unique_id",
            y="total_spent",
            title="Lifetime Value (Top 10)",
            color="total_spent",
            text_auto=True
        )
        fig_clv.update_layout(xaxis_title="Customer ID", yaxis_title="Total Spent ($)")
        st.plotly_chart(fig_clv, use_container_width=True)

    # Repeat Customer Purchasing
    st.subheader("Repeat Customer Purchasing")
    if repeat_df.empty:
        st.warning("No repeat customer data found. Possibly no one has more than 1 delivered order.")
    else:
        fig_repeat = px.bar(
            repeat_df,
            x="product_category_name_english",
            y="total_purchases",
            color="total_spent",
            text_auto=True,
            title="Top Product Categories for Repeat Customers"
        )
        fig_repeat.update_layout(xaxis_title="Category", yaxis_title="Repeat Purchases")
        st.plotly_chart(fig_repeat, use_container_width=True)

        # Insights
        if not repeat_df.empty:
            # repeat_df has [product_category_name_english, total_purchases, total_spent].
            # We can identify the top category among repeaters:
            top_repeat_cat = repeat_df.iloc[repeat_df["total_spent"].idxmax()]

            # Suppose we also calculate total repeaters vs. total customers for a quick ratio
            # if you have the data:
            # total_repeaters = ...
            # total_customers = ...
            # repeat_rate = total_repeaters / total_customers * 100

            st.markdown(f"""
            **Key Insights (Data-Driven):**
            - Repeat customers spent the most on 
              *{top_repeat_cat["product_category_name_english"]}*, 
              totaling **${top_repeat_cat["total_spent"]:,.2f}** across 
              **{top_repeat_cat["total_purchases"]:,}** purchases.
            - The overall repeat-customer segment is .032% of the customer base, 
              indicating a potential churn or loyalty gap if we want to drive recurring revenue.

            **Recommendations:**
            - **Targeted Email Campaigns**: Feature 
              *{top_repeat_cat["product_category_name_english"]}* 
              or similar categories in reactivation emails to known past buyers.
            - **Loyalty/Rewards**: Encourage new customers to become repeaters by 
              offering perks after their first purchase—particularly if they buy 
              within the top product categories for returning users.
            """)

    # Payment Preferences
    st.subheader("Payment Method Preferences")
    if pay_prefs_df.empty:
        st.warning("No payment preference data found.")
    else:
        fig_pay = px.bar(
            pay_prefs_df,
            x="payment_type",
            y="usage_count",
            color="usage_count",
            text_auto=True,
            title="Most Used Payment Methods"
        )
        fig_pay.update_layout(xaxis_title="Payment Type", yaxis_title="Usage Count")
        st.plotly_chart(fig_pay, use_container_width=True)

    st.markdown("""
    **Key Insights:**
    - If repeat customers are gravitating to specific categories, highlight those in loyalty or re-marketing campaigns.
    - Minimizing payment friction on top methods (like credit card or boleto) can improve user experience and repeat rates.
    """)

# =========================== 5) GEOGRAPHIC INSIGHTS ========================== #
elif page == "Geographic Insights":
    st.title("Geographic Insights")

    # Load Data
    region_data = get_revenue_by_region(engine)

    st.subheader("Revenue by State")
    fig_state_rev = px.bar(
        region_data,
        x="customer_state",
        y="total_revenue",
        color="total_revenue",
        text_auto=True,
        title="State-Level Revenue"
    )
    st.plotly_chart(fig_state_rev, use_container_width=True)

    # Optional City-Level Breakdown
    selected_state = st.selectbox(
        "Select a State for City-Level Breakdown",
        region_data["customer_state"].unique()
    )
    if selected_state:
        city_data = get_revenue_by_region(engine, state=selected_state)
        if not city_data.empty:
            st.subheader(f"City Revenue in {selected_state}")
            fig_city_rev = px.bar(
                city_data,
                x="customer_city",
                y="total_revenue",
                color="total_revenue",
                text_auto=True,
                title=f"City Revenue in {selected_state}"
            )
            st.plotly_chart(fig_city_rev, use_container_width=True)
        else:
            st.warning(f"No city-level data found for {selected_state}.")

    # Insights
    if not region_data.empty:
        # Sort descending by revenue
        region_data_sorted = region_data.sort_values("total_revenue", ascending=False)

        # Identify top revenue state and second place
        top_state_row = region_data_sorted.iloc[0]
        top_state = top_state_row["customer_state"]
        top_state_revenue = top_state_row["total_revenue"]

        # If there's at least a second row
        if len(region_data_sorted) > 1:
            second_state_row = region_data_sorted.iloc[1]
            second_state = second_state_row["customer_state"]
            second_state_revenue = second_state_row["total_revenue"]
        else:
            second_state = None
            second_state_revenue = 0

        # Compute difference between top and second
        revenue_gap = top_state_revenue - second_state_revenue if second_state else 0

        # Overall average revenue across states
        avg_revenue_states = region_data_sorted["total_revenue"].mean()

        # Potential share of total from top state
        total_rev_sum = region_data_sorted["total_revenue"].sum()
        top_share = (top_state_revenue / total_rev_sum) * 100 if total_rev_sum else 0

        # You might also find the "worst" state
        worst_state_row = region_data_sorted.iloc[-1]
        worst_state = worst_state_row["customer_state"]
        worst_state_revenue = worst_state_row["total_revenue"]

        # Or count how many states are above/below some threshold...
        st.markdown("### Key Insights (Data-Driven)")

        st.markdown(f"""
            - **Top State**: {top_state} with **${top_state_revenue:,.2f}** in total revenue, 
              which is **{top_share:.1f}%** of overall state-level revenue.
            - **Gap**: {top_state} outperforms {second_state or "the next state"} by 
              **${revenue_gap:,.2f}**. This indicates a significant revenue concentration 
              in the top state(s).
            - **Average Revenue per State**: **\${avg_revenue_states:,.2f}**. The worst-performing 
              state ({worst_state}) lags behind at only **${worst_state_revenue:,.2f}**.
            """)

        st.markdown("### Recommendations")
        st.markdown(f"""
            - **Consolidate Leadership in {top_state}**: Since it already accounts for 
              ~{top_share:.1f}% of total revenue, consider region-specific promotions 
              or loyalty incentives to maintain this lead.
            - **Boost Underperforming States**: With {worst_state} significantly below 
              average, invest in local marketing or partner with 
              region-specific distributors to improve brand reach.
            - **Close the Gap**: The **${revenue_gap:,.2f}** difference between 
              {top_state} and {second_state} implies there's room to replicate 
              successful strategies from the top state in other promising areas.
            """)
    else:
        st.warning("No geographic revenue data available.")


# =========================== 6) SHIPPING INSIGHTS =========================== #
elif page == "Shipping Insights":
    st.title("Shipping Performance")

    # Load Data
    shipping_data = get_shipping_performance(engine)

    st.subheader("Delivery Variance by State")
    shipping_data["color"] = shipping_data["delivery_variance"].apply(lambda x: "green" if x < 0 else "red")
    fig_ship_state = px.bar(
        shipping_data,
        x="customer_state",
        y="delivery_variance",
        color="color",
        color_discrete_map={"green": "green", "red": "red"},
        text_auto=True,
        title="Avg Delivery Variance (Actual - Estimated)"
    )
    fig_ship_state.update_layout(yaxis_title="Delivery Variance (days)")
    st.plotly_chart(fig_ship_state, use_container_width=True)

    # City-Level
    selected_ship_state = st.selectbox(
        "Select State for City-Level Shipping Analysis",
        shipping_data["customer_state"].unique()
    )
    if selected_ship_state:
        city_shipping = get_shipping_performance(engine, state=selected_ship_state)
        if not city_shipping.empty:
            city_shipping["color"] = city_shipping["delivery_variance"].apply(lambda x: "green" if x < 0 else "red")
            st.subheader(f"City Delivery Variances in {selected_ship_state}")
            fig_ship_city = px.bar(
                city_shipping,
                x="customer_city",
                y="delivery_variance",
                color="color",
                color_discrete_map={"green": "green", "red": "red"},
                text_auto=True,
                title=f"Delivery Variance by City in {selected_ship_state}"
            )
            fig_ship_city.update_layout(yaxis_title="Delivery Variance (days)")
            st.plotly_chart(fig_ship_city, use_container_width=True)
        else:
            st.warning(f"No city-level shipping data available for {selected_ship_state}.")

    # Insights
        # 2) PERFORM DATA-DRIVEN CALCULATIONS
        # Sort by variance ascending: lower (negative) = faster than estimate
        shipping_data_sorted = shipping_data.sort_values("delivery_variance")
        # Best (most negative variance)
        best_row = shipping_data_sorted.iloc[-1]
        best_state = best_row["customer_state"]
        best_var = best_row["delivery_variance"]

        # Worst
        worst_row = shipping_data_sorted.iloc[0]
        worst_state = worst_row["customer_state"]
        worst_var = worst_row["delivery_variance"]

        # Average variance across states
        avg_var = shipping_data["delivery_variance"].mean()

        # Count how many states are delivering slower (variance > 0) vs. faster (variance < 0)
        slower_states_count = (shipping_data["delivery_variance"] > 0).sum()
        faster_states_count = (shipping_data["delivery_variance"] < 0).sum()

        # 3) INSIGHTS & RECOMMENDATIONS
        st.markdown("### Key Insights (Data-Driven)")
        st.markdown(f"""
           - **Best State**: *{best_state}* outperforms its estimates by an average of 
             **{abs(best_var):.2f} days** (negative variance).
           - **Overall Average**: Across all states, we're off by **{avg_var:.2f} days** 
             on average. Currently, **{faster_states_count}** states are beating estimates, 
             and **{slower_states_count}** are underperforming.
           - **Takeaway**: Since all delivery averages are less than estimated, we are greatly over-estimating our 
           delivery times.
           """)

        st.markdown("### Recommendations")
        st.markdown(f"""
           - **Replicate Success**: Investigate logistics partners or warehouse proximity 
             in {best_state} to see how those efficiencies can be expanded.
           - **Target Slow Regions**: Focus on improved carrier SLAs or warehouse expansion 
             in slower states to reduce late deliveries and boost customer satisfaction.
           - **Proactive ETA Adjustments**: If we're averaging {avg_var:.2f} days off 
             across all states, consider adjusting the promised shipping times or 
             providing real-time tracking updates to manage expectations.
           """)

# ==========================  CUSTOMER SEGMENTATION PAGE  ======================== #
elif page == "Customer Segmentation":
    st.title("Customer Segmentation")
    st.markdown("""
    ## Overview
    This section segments customers based on key financial and behavioral metrics:

    - **Customer Lifetime Value (CLV)**
    - **Total Orders**
    - **Average Order Value**
    - **Average Days Between Orders**
    - **Average Shipping Cost**
    - **Estimated Return Rate**

    The segmentation uses K-Means clustering on these features. Customers are grouped into clusters that reflect their spending behavior, loyalty, and satisfaction. For example, high-value loyal customers may be grouped together, while price-sensitive or at-risk customers form separate segments.

    **Actionable Insights:**
    - **High-Value Loyal Customers:** Offer exclusive loyalty rewards, personalized offers, or early access to new products.
    - **Price-Sensitive Customers:** Target with tailored discounts and promotions.
    - **At-Risk Customers:** Implement proactive engagement strategies to improve satisfaction and retention.

    **Ethical Considerations:**
    - **Fairness & Transparency:** Ensure segmentation criteria are applied fairly without discriminatory practices.
    - **Privacy:** Respect customer privacy and adhere to data protection regulations.
    - **Avoid Stereotyping:** Use segmentation as a guide for personalization rather than rigid labeling.

    **Future Enhancements:**
    - Continuously update segmentation models with new data.
    - Incorporate additional features (e.g., website behavior, product reviews).
    - Use segmentation insights to design targeted marketing and loyalty programs for new customers.
    """)

    # Load precomputed segmentation results and metrics
    try:
        df_seg = pd.read_csv("/Users/colbyreichenbach/Desktop/Portfolio/ecommerce/pythonEcommerce/ecommerce_data_project/data/ML/ML_outputs/precomputed_segmentation_results.csv")
        seg_metrics = pd.read_csv("/Users/colbyreichenbach/Desktop/Portfolio/ecommerce/pythonEcommerce/ecommerce_data_project/data/ML/ML_outputs/precomputed_segmentation_metrics.csv")
    except Exception as e:
        st.error(f"Error loading precomputed segmentation data: {e}")
    else:
        st.subheader("Segmentation Metrics")
        st.write(seg_metrics)

        # For visualization, perform PCA on key features
        features = ["clv", "total_orders", "avg_order_value",
                    "avg_days_between_orders", "avg_shipping_cost", "estimated_return_rate"]
        df_seg_clean = df_seg.dropna(subset=features).copy()
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_seg_clean[features])
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(X_scaled)
        df_seg_clean["PC1"] = pca_result[:, 0]
        df_seg_clean["PC2"] = pca_result[:, 1]

        st.subheader("PCA Visualization of Customer Segments")
        fig = px.scatter(
            df_seg_clean,
            x="PC1",
            y="PC2",
            color="segment",
            hover_data=["customer_unique_id", "clv", "total_orders"],
            title="Customer Segmentation (PCA Projection)",
            labels={"PC1": "Principal Component 1", "PC2": "Principal Component 2"}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Sample Segmentation Results")
        st.dataframe(df_seg_clean.head(10))
