# external_dashboard.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# external_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px

# Import query functions for high-level metrics
from ecommerce_data_project.dashboard.queries import (
    get_business_overview,
    get_monthly_revenue_trends,
    get_yearly_revenue,
    get_new_customers_by_year,
    get_category_growth_by_year,
    get_shipping_performance_by_year, get_category_sales
)

# Set page configuration with a black background overall
st.set_page_config(page_title="Executive E-Commerce Dashboard", layout="wide")

# Inject custom CSS for a black background and for graph containers with rounded edges
st.markdown(
    """
    <style>
    /* Overall dashboard background */
    .stApp {
        background-color: #000000;
    }
    /* Container for graphs with a white background and rounded edges */
    .graph-container {
        background-color: #FFFFFF;
        border: 2px solid #dddddd;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
    }
    /* Header styling */
    .header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Executive Summary",
        "Financial Performance",
        "Product Performance",
        "Customer Segmentation",
        "Conclusion"
    ]
)

# ===========================  Executive Summary Page  =========================== #
if page == "Executive Summary":
    st.title("Executive Summary")
    st.markdown("""
    ## Overview
    This dashboard presents our e-commerce performance through a strategic lens. It aggregates key performance 
    indicators (KPIs) and trends to provide an executive summary of our operations.

    **Highlights:**
    - **Total Orders:** {total_orders:,} delivered orders.
    - **Total Revenue:** ${total_revenue:,.2f} generated.
    - **Average Order Value:** ${avg_order_value:,.2f}.
    - **Customer Growth:** Steady acquisition year-over-year.

    Our monthly revenue trends indicate that peak performance occurs in Q3, driven by seasonal promotions and heightened customer activity.
    """.format(
        total_orders=get_business_overview()["total_orders"][0],
        total_revenue=get_business_overview()["total_revenue"][0],
        avg_order_value=get_business_overview()["avg_order_value"][0]
    ))

    # KPI Cards
    overview = get_business_overview()
    monthly_rev = get_monthly_revenue_trends()
    yearly_rev = get_yearly_revenue()
    new_customers = get_new_customers_by_year()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Orders", f"{overview['total_orders'][0]:,}")
    col2.metric("Total Revenue", f"${overview['total_revenue'][0]:,.2f}")
    col3.metric("Avg. Order Value", f"${overview['avg_order_value'][0]:,.2f}")
    col4.metric("Total Customers", f"{overview['total_customers'][0]:,}")

    st.markdown("""
    **Detailed Insights:**
    - In the latest fiscal year, our total revenue reached approximately ${latest_revenue:,.2f}, up by {growth_percent:.1f}% compared to the previous year.
    - New customer acquisition shows a consistent upward trend, with the most recent year adding {new_customers_count} new customers.
    """.format(
        latest_revenue=yearly_rev["total_revenue"].iloc[-1],
        growth_percent=yearly_rev["total_revenue"].pct_change().iloc[-1] * 100,
        new_customers_count=int(new_customers["new_customers"].sum())
    ))

    st.subheader("Monthly Revenue Trends")
    monthly_rev["month"] = pd.to_datetime(monthly_rev["month"])
    fig_monthly = px.line(
        monthly_rev,
        x="month",
        y="total_revenue",
        title="Monthly Revenue Trends",
        markers=True,
        labels={"month": "Month", "total_revenue": "Revenue ($)"}
    )
    fig_monthly.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    with st.container():
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_monthly, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("New Customers by Year")
    st.dataframe(new_customers)

# ===========================  Financial Performance Page  =========================== #
elif page == "Financial Performance":
    st.title("Financial Performance")
    yearly_rev = get_yearly_revenue()
    st.markdown("""
    ## Financial Trends & Strategic Outlook
    Our annual revenue performance indicates that:
    - In 2022, revenue was approximately ${rev_2022:,.2f}.
    - In 2023, revenue increased to about ${rev_2023:,.2f}, representing a growth of {growth_rate:.1f}%.

    The data suggests that while seasonal dips occur, our overall trajectory is upward. Focused investments during peak periods have proven effective.
    """.format(
        rev_2022=yearly_rev["total_revenue"].iloc[-2] if len(yearly_rev) >= 2 else 0,
        rev_2023=yearly_rev["total_revenue"].iloc[-1],
        growth_rate=(yearly_rev["total_revenue"].iloc[-1] / yearly_rev["total_revenue"].iloc[-2] - 1) * 100 if len(
            yearly_rev) >= 2 else 0
    ))

    yearly_rev = get_yearly_revenue()
    fig_yearly = px.bar(
        yearly_rev,
        x="year",
        y="total_revenue",
        title="Yearly Revenue",
        color="total_revenue",
        text_auto=True
    )
    fig_yearly.update_layout(xaxis_title="Year", yaxis_title="Revenue ($)", margin=dict(l=20, r=20, t=50, b=20))
    with st.container():
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_yearly, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    **Detailed Recommendations:**
    - Enhance marketing during identified low-revenue periods to smooth out seasonal dips.
    - Invest in data-driven promotions that have previously resulted in revenue spikes.
    - Consider reallocating resources to further boost the quarter that shows consistent growth.
    """)

# ===========================  Product Performance Page  =========================== #
elif page == "Product Performance":
    st.title("Product Performance")
    st.markdown("""
    ## Product Portfolio Analysis
    Our product data reveals that certain categories consistently generate higher revenue and profit margins.

    **Key Findings:**
    - The top product category accounts for a significant portion of total revenue.
    - A detailed look at revenue per unit indicates opportunities for premium pricing or bundling.
    """)

    # Load product category sales data from the database using the existing query function
    category_sales = get_category_sales()

    if category_sales.empty:
        st.warning("Category sales data is not available.")
    else:
        fig_cat = px.bar(
            category_sales,
            x="product_category_name_english",
            y="total_revenue",
            title="Revenue by Product Category",
            text_auto=True,
            color="total_revenue"
        )
        fig_cat.update_layout(
            xaxis_title="Product Category",
            yaxis_title="Revenue ($)",
            margin=dict(l=20, r=20, t=50, b=20)
        )
        with st.container():
            st.markdown('<div class="graph-container">', unsafe_allow_html=True)
            st.plotly_chart(fig_cat, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        top_cat = category_sales.sort_values("total_revenue", ascending=False).iloc[0]
        rev_per_unit = (top_cat["total_revenue"] / top_cat["total_units_sold"]) if top_cat[
                                                                                       "total_units_sold"] > 0 else 0
        st.markdown("""
        **Insights:**
        - **Top Category:** *{category}* generated **${revenue:,.2f}** in revenue.
        - **Revenue per Unit:** On average, this category yields **${rev_per_unit:.2f}** per unit, 
          indicating opportunities to optimize pricing through bundling or premium offerings.
        """.format(
            category=top_cat["product_category_name_english"],
            revenue=top_cat["total_revenue"],
            rev_per_unit=rev_per_unit
        ))

# ===========================  Customer Segmentation Page  =========================== #
elif page == "Customer Segmentation":
    st.title("Customer Segmentation - Executive Overview")
    st.markdown("""
    ## Customer Segmentation Analysis
    We have segmented our customers based on key metrics:

    - **Customer Lifetime Value (CLV)**
    - **Total Orders**
    - **Average Order Value**
    - **Average Days Between Orders**
    - **Average Shipping Cost**
    - **Estimated Return Rate**

    The clustering process (using K-Means) has identified distinct customer groups:

    - **High-Value Loyal Customers:** Representing about 40% of our base, driving nearly 60% of revenue.
    - **Price-Sensitive Buyers:** Moderate CLV with high order frequency.
    - **At-Risk Customers:** Lower engagement and spending, indicating opportunities for targeted retention.

    **Strategic Implications:**
    - Tailor premium loyalty programs for high-value clusters.
    - Implement cost-effective promotions for price-sensitive segments.
    - Engage at-risk groups with personalized reactivation campaigns.

    **Ethical Considerations:**
    - Use segmentation responsibly by ensuring fairness and transparency.
    - Respect customer privacy and avoid overgeneralization.

    **Future Enhancements:**
    - Continuously update the segmentation model with new behavioral data.
    - Use dynamic segmentation to personalize onboarding for new customers.
    """)

    try:
        df_seg = pd.read_csv("/Users/colbyreichenbach/Desktop/Portfolio/ecommerce/pythonEcommerce/ecommerce_data_project/data/ML/ML_outputs/precomputed_segmentation_results.csv")
        seg_metrics = pd.read_csv("/Users/colbyreichenbach/Desktop/Portfolio/ecommerce/pythonEcommerce/ecommerce_data_project/data/ML/ML_outputs/precomputed_segmentation_metrics.csv")
    except Exception as e:
        st.error(f"Error loading segmentation data: {e}")
    else:
        st.subheader("Segmentation Metrics")
        st.write(seg_metrics)

        # PCA visualization of segmentation
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
        fig_seg = px.scatter(
            df_seg_clean,
            x="PC1",
            y="PC2",
            color="segment",
            hover_data=["customer_unique_id", "clv", "total_orders"],
            title="Customer Segmentation (PCA Projection)",
            labels={"PC1": "Principal Component 1", "PC2": "Principal Component 2"}
        )
        fig_seg.update_layout(margin=dict(l=20, r=20, t=50, b=20))
        with st.container():
            st.markdown('<div class="graph-container">', unsafe_allow_html=True)
            st.plotly_chart(fig_seg, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("Sample Segmentation Data")
        st.dataframe(df_seg_clean.head(10))

# ===========================  Conclusion Page  =========================== #
elif page == "Conclusion":
    st.title("Conclusion & Strategic Recommendations")
    yearly_rev = get_yearly_revenue()
    st.markdown("""
    ## Summary of Findings
    - **Financial Growth:** Our revenue has grown from approximately \${rev_prev:,.2f} to \${rev_latest:,.2f} year-over-year.
    - **Product Performance:** Certain product categories are significantly outperforming others, 
      offering clear opportunities for targeted promotions and bundling strategies.
    - **Customer Segmentation:** Our segmentation analysis reveals that high-value customers, 
      though constituting 40% of our base, drive 60% of total revenue. In contrast, at-risk segments require targeted engagement.
    - **Operational Efficiency:** Shipping performance has improved, though opportunities remain to further optimize delivery times.

    ## Strategic Recommendations
    - **Enhance Customer Retention:** Implement personalized loyalty programs for high-value segments.
    - **Target Underperforming Segments:** Develop tailored reactivation campaigns for at-risk customers.
    - **Optimize Product Offerings:** Allocate resources to high-margin product categories and explore bundling opportunities.
    - **Invest in Operational Improvements:** Continue refining logistics to further reduce delivery variances.

    ## Final Thoughts
    Our data-driven analysis confirms that strategic investments in customer engagement, product optimization, and operational efficiency can drive sustained growth. With continuous monitoring and model refinement, we can further personalize our marketing efforts, improve customer satisfaction, and secure a competitive edge in the market.
    """.format(
        rev_prev=yearly_rev["total_revenue"].iloc[-2] if len(yearly_rev) >= 2 else 0,
        rev_latest=yearly_rev["total_revenue"].iloc[-1] if not yearly_rev.empty else 0
    ))
