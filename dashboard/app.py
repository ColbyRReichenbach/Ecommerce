import streamlit as st
import pandas as pd
import numpy as np
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
    get_most_frequent_order_status_nondelivered, query_database
)

st.set_page_config(page_title="E-Commerce Advanced Analytics", layout="wide")

CUSTOM_CSS = """
<style>
:root {
    --primary-500: #4f46e5;
    --primary-400: #6366f1;
    --accent-500: #f97316;
    --surface-50: #f8fafc;
    --surface-100: #eef2ff;
    --surface-200: #e2e8f0;
    --surface-900: #0f172a;
}

body {
    font-family: "Inter", "Segoe UI", system-ui;
    color: #1f2937;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, var(--surface-50) 0%, var(--surface-100) 55%, #ffffff 100%);
}

[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, var(--primary-500) 0%, #312e81 100%);
    color: #f9fafb;
    padding-top: 1.5rem;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: #f3f4f6 !important;
}

.highlight-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(99, 102, 241, 0.12);
    color: var(--primary-500);
    font-weight: 600;
    padding: 0.35rem 0.9rem;
    border-radius: 999px;
    margin-bottom: 0.75rem;
}

.page-intro {
    color: #475569;
    font-size: 1.02rem;
    line-height: 1.6;
    max-width: 940px;
    margin-bottom: 1.75rem;
}

.section-card {
    background: #ffffff;
    border-radius: 1.25rem;
    padding: 1.65rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 16px 30px rgba(15, 23, 42, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.08);
}

.section-header {
    display: flex;
    align-items: flex-start;
    gap: 0.9rem;
    margin-bottom: 1.1rem;
}

.section-header-icon {
    font-size: 1.8rem;
    line-height: 1;
}

.section-header h3 {
    margin: 0;
    color: var(--surface-900);
    font-weight: 700;
}

.section-caption {
    color: #64748b;
    margin-top: 0.35rem;
    margin-bottom: 0;
    font-size: 0.96rem;
}

.insight-callout {
    background: rgba(79, 70, 229, 0.12);
    border-left: 4px solid var(--primary-500);
    padding: 1rem 1.25rem;
    border-radius: 0.85rem;
    margin-top: 0.75rem;
}

.insight-callout strong {
    display: block;
    margin-bottom: 0.35rem;
    color: var(--surface-900);
}

.insight-callout ul {
    margin: 0;
    padding-left: 1.1rem;
    color: #1f2937;
}

[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(79, 70, 229, 0.16), rgba(59, 130, 246, 0.08));
    padding: 1.05rem 1.2rem;
    border-radius: 1.05rem;
    box-shadow: 0 20px 35px rgba(79, 70, 229, 0.15);
    border: 1px solid rgba(79, 70, 229, 0.12);
}

[data-testid="stMetricLabel"] {
    color: #4b5563;
    font-weight: 600;
    font-size: 0.92rem;
}

[data-testid="stMetricValue"] {
    color: #111827;
    font-weight: 700;
    font-size: 1.55rem;
}

[data-testid="stMetricDelta"] {
    font-size: 0.82rem;
    margin-top: 0.35rem;
}

.chart-caption {
    color: #64748b;
    font-size: 0.9rem;
    margin-top: 0.35rem;
}

.tab-container > div {
    background: transparent !important;
}

.tab-container [data-baseweb="tab"] {
    padding: 0.25rem 0.85rem;
    border-radius: 999px;
    margin: 0 0.25rem;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_section_header(title: str, icon: str, description: str | None = None) -> None:
    """Render a styled section header with optional description copy."""
    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-header-icon">{icon}</div>
            <div>
                <h3>{title}</h3>
                {f'<p class="section-caption">{description}</p>' if description else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_callout(title: str, bullets: list[str]) -> None:
    """Display a highlighted insight callout block."""
    if not bullets:
        return

    bullet_html = "".join(f"<li>{point}</li>" for point in bullets)
    st.markdown(
        f"""
        <div class="insight-callout">
            <strong>{title}</strong>
            <ul>{bullet_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stylize_chart(fig, *, title: str | None = None, legend_orientation: str = "h"):
    """Apply a consistent styling theme to Plotly charts."""
    current_title = title if title is not None else (fig.layout.title.text if fig.layout.title else None)
    title_config = dict(text=current_title, x=0, xanchor="left") if current_title else None

    fig.update_layout(
        template="plotly_white",
        title=title_config,
        margin=dict(t=70 if current_title else 40, l=40, r=20, b=45),
        legend=dict(
            orientation=legend_orientation,
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(255,255,255,0.6)",
            bordercolor="rgba(79,70,229,0.15)",
            borderwidth=1,
        ),
        font=dict(family="Inter, sans-serif", size=13, color="#0f172a"),
        hoverlabel=dict(bgcolor="#111827", font_size=12, font_family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.25)", linecolor="rgba(15, 23, 42, 0.2)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.25)", linecolor="rgba(15, 23, 42, 0.2)")
    return fig


def safe_float(value, default: float | None = 0.0) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_percentage_delta(current: float | None, previous: float | None) -> str | None:
    if current is None or previous in (None, 0):
        return None
    delta_pct = ((current - previous) / previous) * 100 if previous else None
    if delta_pct is None or np.isnan(delta_pct):
        return None
    return f"{delta_pct:+.1f}%"


def compute_point_delta(current: float | None, previous: float | None) -> str | None:
    if current is None or previous is None:
        return None
    delta = current - previous
    if np.isnan(delta):
        return None
    return f"{delta:+.1f} pts"

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
    ]
)

st.sidebar.markdown("### Focus Filters")
selected_region_filter_input = st.sidebar.text_input(
    "Region focus (state code or leave blank)",
    value="",
    help="Type a two-letter state code to spotlight geographic insights (e.g., SP).",
)
selected_region_filter = selected_region_filter_input.strip().upper() or None

st.sidebar.markdown("### Quick Tips")
st.sidebar.caption("🔍 Hover charts for precise values • ⏱️ Adjust the date range to compare seasons • 📤 Use the download arrows to export visuals.")

# --- Helper function for styling KPIs ---
def display_kpi(label, value, help_text=None, delta=None, delta_color="normal", icon=None):
    label_text = f"{icon} {label}" if icon else label
    st.metric(label_text, value, delta=delta, delta_color=delta_color, help=help_text)

# --- Page Rendering Functions ---

def render_business_health_cockpit():
    st.title("Business Health")
    st.markdown('<div class="highlight-badge">Executive Pulse</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-intro">Immediate, high-level understanding of overall performance momentum and commercial resiliency.</div>',
        unsafe_allow_html=True,
    )

    kpi_data = get_main_kpis(engine, selected_start_date, selected_end_date)
    prev_period_start = selected_start_date - (selected_end_date - selected_start_date)
    prev_period_end = selected_start_date - timedelta(seconds=1)
    kpi_data_prev = get_main_kpis(engine, prev_period_start, prev_period_end) # For delta calculation

    if kpi_data.empty:
        st.warning("No data available for the selected period for KPIs.")
        return

    main_kpis = kpi_data.iloc[0]
    prev_kpis = kpi_data_prev.iloc[0] if not kpi_data_prev.empty else None
    
    # COGS assumption for GPM (replace with actual logic or remove GPM if not feasible)
    total_revenue = safe_float(main_kpis.get('total_revenue'), 0.0) or 0.0
    total_revenue_prev = safe_float(prev_kpis.get('total_revenue'), None) if prev_kpis is not None else None

    active_customers = int(safe_float(main_kpis.get('active_customers'), 0) or 0)
    active_customers_prev = safe_float(prev_kpis.get('active_customers'), None) if prev_kpis is not None else None

    total_orders = int(safe_float(main_kpis.get('total_orders'), 0) or 0)
    total_orders_prev = safe_float(prev_kpis.get('total_orders'), None) if prev_kpis is not None else None

    new_cust = safe_float(main_kpis.get('new_customers'), 0.0) or 0.0
    active_cust_for_rate = active_customers if active_customers > 0 else 0
    new_cust_rate = (new_cust / active_cust_for_rate) * 100 if active_cust_for_rate else 0
    if prev_kpis is not None:
        prev_new_cust = safe_float(prev_kpis.get('new_customers'), None)
        prev_active_cust = safe_float(prev_kpis.get('active_customers'), None)
        prev_new_rate = (prev_new_cust / prev_active_cust) * 100 if prev_new_cust is not None and prev_active_cust not in (None, 0) else None
    else:
        prev_new_rate = None

    avg_order_value = safe_float(main_kpis.get('avg_order_value'), 0.0) or 0.0
    avg_order_value_prev = safe_float(prev_kpis.get('avg_order_value'), None) if prev_kpis is not None else None

    COGS_PERCENTAGE = 0.6 # Assume COGS is 60% of revenue
    gross_profit = total_revenue * (1 - COGS_PERCENTAGE)
    gpm = (gross_profit / total_revenue) * 100 if total_revenue else 0
    gpm_prev = None
    if total_revenue_prev:
        gross_profit_prev = total_revenue_prev * (1 - COGS_PERCENTAGE)
        gpm_prev = (gross_profit_prev / total_revenue_prev) * 100 if total_revenue_prev else None

    col1, col2, col3 = st.columns(3)
    with col1:
        display_kpi(
            "Total Revenue",
            f"${total_revenue:,.2f}",
            delta=compute_percentage_delta(total_revenue, total_revenue_prev),
            icon="💰",
        )
        display_kpi(
            "Active Customers",
            f"{active_customers:,}",
            delta=compute_percentage_delta(active_customers, active_customers_prev),
            icon="👥",
        )
    with col2:
        display_kpi(
            "Total Orders",
            f"{total_orders:,}",
            delta=compute_percentage_delta(total_orders, total_orders_prev),
            icon="🧾",
        )
        display_kpi(
            "New Customer Acquisition Rate",
            f"{new_cust_rate:.1f}%",
            delta=compute_point_delta(new_cust_rate, prev_new_rate),
            icon="🆕",
        )
    with col3:
        display_kpi(
            "Avg. Order Value (AOV)",
            f"${avg_order_value:,.2f}",
            delta=compute_percentage_delta(avg_order_value, avg_order_value_prev),
            icon="🎯",
        )
        display_kpi(
            "Gross Profit Margin (GPM)",
            f"{gpm:.1f}% (Est.)",
            help_text="Estimated using a 60% COGS assumption.",
            delta=compute_point_delta(gpm, gpm_prev),
            icon="💹",
        )

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Revenue & Orders Trend",
            "💹",
            "Compare revenue momentum with order velocity to spot leading indicators.",
        )
        rev_order_trend_df = get_revenue_orders_trend(engine, selected_start_date, selected_end_date, freq='ME')
        if not rev_order_trend_df.empty:
            rev_order_trend_df['time_period'] = pd.to_datetime(rev_order_trend_df['time_period'])
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=rev_order_trend_df['time_period'],
                    y=rev_order_trend_df['total_revenue'],
                    name='Total Revenue',
                    yaxis='y1',
                    mode='lines+markers',
                    line=dict(width=3, color='#4f46e5'),
                    marker=dict(size=6),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=rev_order_trend_df['time_period'],
                    y=rev_order_trend_df['total_orders'],
                    name='Total Orders',
                    yaxis='y2',
                    mode='lines+markers',
                    line=dict(width=3, color='#38bdf8'),
                    marker=dict(size=6),
                )
            )
            fig = stylize_chart(fig, title="Revenue vs. Orders Momentum")
            fig.update_layout(
                yaxis=dict(title='Total Revenue ($)', titlefont=dict(color='#4f46e5')),
                yaxis2=dict(title='Total Orders', overlaying='y', side='right', titlefont=dict(color='#38bdf8')),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('<p class="chart-caption">Revenue (left axis) vs. order volume (right axis) across the selected period.</p>', unsafe_allow_html=True)
        else:
            st.info("No revenue/order trend data for this period.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Average Order Value Trend",
            "🎯",
            "Monitor ticket size stability to understand merchandising and pricing outcomes.",
        )
        aov_trend_df = get_aov_trend(engine, selected_start_date, selected_end_date, freq='ME')
        if not aov_trend_df.empty:
            aov_trend_df['time_period'] = pd.to_datetime(aov_trend_df['time_period'])
            fig_aov = px.line(
                aov_trend_df,
                x='time_period',
                y='avg_order_value',
                markers=True,
                title='AOV Over Time',
                labels={'avg_order_value': 'Average Order Value ($)', 'time_period': 'Period'},
            )
            fig_aov.update_traces(line=dict(color="#f97316", width=3), marker=dict(size=6))
            fig_aov = stylize_chart(fig_aov)
            st.plotly_chart(fig_aov, use_container_width=True)
            st.markdown('<p class="chart-caption">Track how promotional strategies influence customer spend per order.</p>', unsafe_allow_html=True)
        else:
            st.info("No AOV trend data for this period.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "New vs. Returning Customer Revenue",
            "🤝",
            "Balance acquisition-led growth against retention health.",
        )
        nvr_df = get_new_vs_returning_customer_revenue(engine, selected_start_date, selected_end_date, freq='ME')
        if not nvr_df.empty:
            nvr_df['time_period'] = pd.to_datetime(nvr_df['time_period'])
            fig_nvr = go.Figure()
            fig_nvr.add_trace(
                go.Bar(
                    x=nvr_df['time_period'],
                    y=nvr_df['new_customer_revenue'],
                    name='New Customer Revenue',
                    marker=dict(color="#6366f1"),
                )
            )
            fig_nvr.add_trace(
                go.Bar(
                    x=nvr_df['time_period'],
                    y=nvr_df['returning_customer_revenue'],
                    name='Returning Customer Revenue',
                    marker=dict(color="#22d3ee"),
                )
            )
            fig_nvr.update_layout(barmode='stack')
            fig_nvr = stylize_chart(fig_nvr, title="Monthly Revenue by Customer Type")
            st.plotly_chart(fig_nvr, use_container_width=True)
            st.markdown('<p class="chart-caption">Retention revenue remains muted—activate re-engagement programs to diversify growth.</p>', unsafe_allow_html=True)
        else:
            st.info("No new vs returning customer revenue data for this period.")
        st.markdown("</div>", unsafe_allow_html=True)

    render_insight_callout(
        "Insight Spotlight",
        [
            "Revenue growth is still acquisition-led—retention programs can reduce CAC pressure and stabilize GPM.",
            "December 2017 softness is visible in both revenue and orders; investigate marketing or inventory shifts affecting the month.",
            "AOV oscillations highlight upside for bundles and cross-sell nudges to protect per-order profitability.",
        ],
    )


def render_product_portfolio_performance():
    st.title("Product Portfolio Performance")
    st.markdown('<div class="highlight-badge">Merchandising Intelligence</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-intro">Spot the categories that fuel growth, protect margin against returns, and prioritise the next assortment bets.</div>',
        unsafe_allow_html=True,
    )

    cat_perf_df = get_category_performance_matrix(engine, selected_start_date, selected_end_date)
    cat_returns_df = get_category_return_rates(engine, selected_start_date, selected_end_date)

    if cat_perf_df.empty:
        st.warning("No category performance data for the selected period/filter.")
        return

    cat_data_merged = cat_perf_df.copy()
    if not cat_returns_df.empty:
        cat_data_merged = pd.merge(cat_data_merged, cat_returns_df, on="product_category_name_english", how="left")
    else:
        cat_data_merged["return_rate_percentage"] = 0.0

    if "avg_review_score" not in cat_data_merged.columns:
        cat_data_merged["avg_review_score"] = 0.0

    numeric_cols = ["total_units_sold", "total_revenue", "avg_review_score", "return_rate_percentage"]
    for col in numeric_cols:
        default_val = 0 if col == "total_units_sold" else 0.0
        cat_data_merged[col] = pd.to_numeric(cat_data_merged.get(col, default_val), errors="coerce").fillna(default_val)
        if col == "total_units_sold":
            cat_data_merged[col] = cat_data_merged[col].astype(int)
        else:
            cat_data_merged[col] = cat_data_merged[col].astype(float)

    top_cat_revenue = cat_data_merged.nlargest(1, "total_revenue").iloc[0] if not cat_data_merged.empty else None
    top_cat_units = cat_data_merged.nlargest(1, "total_units_sold").iloc[0] if not cat_data_merged.empty else None
    highest_return_cat = cat_data_merged.nlargest(1, "return_rate_percentage").iloc[0] if not cat_data_merged.empty else None

    col1, col2, col3 = st.columns(3)
    with col1:
        if top_cat_revenue is not None:
            display_kpi(
                "Top Category (Revenue)",
                f"{top_cat_revenue['product_category_name_english']}",
                help_text=f"Revenue: ${float(top_cat_revenue['total_revenue']):,.0f}",
                icon="💸",
            )
    with col2:
        if top_cat_units is not None:
            display_kpi(
                "Top Category (Units)",
                f"{top_cat_units['product_category_name_english']}",
                help_text=f"Units sold: {int(top_cat_units['total_units_sold']):,}",
                icon="📦",
            )
    with col3:
        if highest_return_cat is not None:
            display_kpi(
                "Highest Return Rate",
                f"{highest_return_cat['product_category_name_english']}",
                help_text=f"Return rate: {float(highest_return_cat['return_rate_percentage']):.2f}%",
                icon="♻️",
            )

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Category Performance Matrix",
            "🧮",
            "Size bubbles for review quality, shade by return-rate pressure, and balance unit velocity with revenue.",
        )
        if not cat_data_merged.empty:
            size_field = None
            if cat_data_merged["avg_review_score"].nunique() > 1 and cat_data_merged["avg_review_score"].max() > 0:
                size_field = "avg_review_score"

            color_field = "return_rate_percentage" if "return_rate_percentage" in cat_data_merged.columns else None

            fig_matrix = px.scatter(
                cat_data_merged,
                x="total_units_sold",
                y="total_revenue",
                size=size_field,
                color=color_field,
                hover_name="product_category_name_english",
                color_continuous_scale=px.colors.diverging.RdYlGn_r if color_field else None,
                labels={
                    "total_units_sold": "Total Units Sold",
                    "total_revenue": "Total Revenue ($)",
                    "return_rate_percentage": "Return Rate (%)",
                    "avg_review_score": "Avg Review Score",
                },
                title="Categories: Units vs Revenue",
            )
            fig_matrix.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="rgba(15,23,42,0.35)")))
            fig_matrix = stylize_chart(fig_matrix)
            st.plotly_chart(fig_matrix, use_container_width=True)
            st.markdown('<p class="chart-caption">Bubble size reflects review quality; colour highlights return friction.</p>', unsafe_allow_html=True)
        else:
            st.info("Not enough data for performance matrix after cleaning.")
        st.markdown("</div>", unsafe_allow_html=True)

    tab_top_bottom, tab_returns = st.tabs(["Top/Bottom Categories", "Return Rates"])

    with tab_top_bottom:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Category Rankings",
            "🏅",
            "Size the gap between the leaders and laggards to focus trading actions.",
        )

        rank_by = st.radio(
            "Rank categories by:",
            ("Total Revenue", "Total Units Sold"),
            key="rank_by_selector",
        )

        if not cat_data_merged.empty:
            if rank_by == "Total Revenue":
                sort_column = "total_revenue"
                chart_label = "Total Revenue ($)"
                text_format = ".2s"
            else:
                sort_column = "total_units_sold"
                chart_label = "Total Units Sold"
                text_format = True

            if sort_column in cat_data_merged.columns:
                sorted_cats = cat_data_merged.sort_values(by=sort_column, ascending=False)
                n_cats = st.slider(
                    f"Select N for Top/Bottom categories (by {rank_by})",
                    min_value=3,
                    max_value=min(20, len(sorted_cats)),
                    value=10,
                    key=f"n_cats_slider_{sort_column}",
                )

                col_top, col_bottom = st.columns(2)

                with col_top:
                    st.markdown(f"**Top {n_cats} Categories by {rank_by}**")
                    top_n_df = sorted_cats.head(n_cats)
                    if not top_n_df.empty:
                        fig_top_cats = px.bar(
                            top_n_df,
                            x=sort_column,
                            y="product_category_name_english",
                            orientation="h",
                            color=sort_column,
                            color_continuous_scale=px.colors.sequential.Greens_r,
                            text_auto=text_format,
                            title=f"Top {n_cats} Categories",
                        )
                        fig_top_cats.update_layout(
                            yaxis_title="Category",
                            xaxis_title=chart_label,
                            yaxis={"categoryorder": "total ascending"},
                        )
                        fig_top_cats = stylize_chart(fig_top_cats)
                        st.plotly_chart(fig_top_cats, use_container_width=True)
                    else:
                        st.info(f"Not enough data for Top {n_cats} categories by {rank_by}.")

                with col_bottom:
                    st.markdown(f"**Bottom {n_cats} Categories by {rank_by}**")
                    bottom_n_df = sorted_cats.tail(n_cats).sort_values(by=sort_column, ascending=True)
                    if not bottom_n_df.empty:
                        fig_bottom_cats = px.bar(
                            bottom_n_df,
                            x=sort_column,
                            y="product_category_name_english",
                            orientation="h",
                            color=sort_column,
                            color_continuous_scale=px.colors.sequential.Reds_r,
                            text_auto=text_format,
                            title=f"Bottom {n_cats} Categories",
                        )
                        fig_bottom_cats.update_layout(
                            yaxis_title="Category",
                            xaxis_title=chart_label,
                            yaxis={"categoryorder": "total ascending"},
                        )
                        fig_bottom_cats = stylize_chart(fig_bottom_cats)
                        st.plotly_chart(fig_bottom_cats, use_container_width=True)
                    else:
                        st.info(f"Not enough data for Bottom {n_cats} categories by {rank_by}.")
            else:
                st.warning(f"Column '{sort_column}' not found in category data.")
        else:
            st.info("No category data available for ranking.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_returns:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Return & Cancellation Rates",
            "♻️",
            "Surface categories that erode profitability so you can intervene early.",
        )
        if not cat_returns_df.empty and "return_rate_percentage" in cat_returns_df.columns:
            top_n_returns = st.slider(
                "Number of categories to display for return rates",
                min_value=5,
                max_value=min(30, len(cat_returns_df)),
                value=15,
                key="n_returns_slider",
            )

            sorted_returns_df = cat_returns_df.sort_values(by="return_rate_percentage", ascending=False).head(top_n_returns)

            if not sorted_returns_df.empty:
                fig_returns = px.bar(
                    sorted_returns_df,
                    x="product_category_name_english",
                    y="return_rate_percentage",
                    color="return_rate_percentage",
                    color_continuous_scale=px.colors.sequential.Reds,
                    text_auto=".2f",
                    title=f"Top {top_n_returns} Categories by Return Rate (%)",
                )
                fig_returns.update_layout(
                    xaxis_title="Category",
                    yaxis_title="Return Rate (%)",
                    xaxis={"categoryorder": "total descending"},
                )
                fig_returns = stylize_chart(fig_returns)
                st.plotly_chart(fig_returns, use_container_width=True)
            else:
                st.info("Not enough data to display return rates after filtering.")
        else:
            st.info("No return rate data available or 'return_rate_percentage' column missing.")
        st.markdown("</div>", unsafe_allow_html=True)

    render_insight_callout(
        "Insight Spotlight",
        [
            "Revenue concentration in a single category calls for adjacent cross-sells to de-risk assortment exposure.",
            "Watch the red return-rate bands—high-velocity categories with rising returns can quickly dilute margin.",
            "Bottom-performing categories by revenue often overlap with high returns; consider markdowns or delisting.",
        ],
    )


def render_sales_funnel_dynamics():
    st.title("Sales Funnel & Order Dynamics")
    st.markdown('<div class="highlight-badge">Operational Pulse</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-intro">Understand order lifecycle efficiency, identify friction in the funnel, and time interventions with confidence.</div>',
        unsafe_allow_html=True,
    )

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
        display_kpi("Avg. Items per Order", f"{avg_items_val:.2f}", icon="🛒")
    with col2:
        display_kpi("Peak Order Time", peak_order_text, help_text="Day and hour with the most orders in the period.", icon="⏰")
    with col3:
        display_kpi("Top Active Status", common_status_text, help_text="Most common status excluding delivered/canceled, indicating potential bottlenecks.", icon="🚧")

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Order Volume Over Time",
            "📈",
            "Understand cadence shifts and seasonality to staff teams and campaigns appropriately.",
        )
        granularity = st.selectbox(
            "Select Time Granularity",
            ["day", "week", "month", "quarter", "year"],
            index=2,
            key="sales_funnel_granularity",
        )
        orders_time_df = get_orders_over_time_by_granularity(engine, selected_start_date, selected_end_date, granularity)
        if not orders_time_df.empty:
            orders_time_df['time_period'] = pd.to_datetime(orders_time_df['time_period'])
            fig_orders_time = px.bar(
                orders_time_df,
                x='time_period',
                y='total_orders',
                title=f"Total Orders by {granularity.capitalize()}",
                labels={'total_orders': 'Total Orders', 'time_period': granularity.capitalize()},
                color='total_orders',
                color_continuous_scale=px.colors.sequential.Blues,
            )
            fig_orders_time = stylize_chart(fig_orders_time)
            fig_orders_time.update_traces(marker_line_width=0)
            st.plotly_chart(fig_orders_time, use_container_width=True)
            st.markdown('<p class="chart-caption">Assess spikes for campaign wins and troughs for follow-up analyses.</p>', unsafe_allow_html=True)
        else:
            st.info("No order volume data for the selected period and granularity.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Order Status Distribution",
            "🔄",
            "Pinpoint where orders accumulate to tackle fulfilment or customer communication gaps.",
        )
        order_status_df = get_order_status_distribution(engine, selected_start_date, selected_end_date)
        if not order_status_df.empty:
            # Order statuses in a logical funnel sequence if available
            status_order = ["created", "approved", "processing", "shipped", "invoiced", "delivered", "canceled"]
            order_status_df['order_status'] = order_status_df['order_status'].astype(str)
            order_status_df['status_rank'] = order_status_df['order_status'].apply(
                lambda x: status_order.index(x) if x in status_order else len(status_order)
            )
            order_status_df = order_status_df.sort_values(by=['status_rank', 'total_orders'])
            fig_status_dist = px.bar(
                order_status_df,
                x='order_status',
                y='total_orders',
                color='order_status',
                title='Overall Order Status Distribution',
                color_discrete_sequence=px.colors.sequential.Plasma,
                text_auto='.2s',
            )
            fig_status_dist = stylize_chart(fig_status_dist, legend_orientation="v")
            fig_status_dist.update_layout(showlegend=False)
            st.plotly_chart(fig_status_dist, use_container_width=True)
            st.markdown('<p class="chart-caption">Focus on the largest non-delivered bar to alleviate customer wait time.</p>', unsafe_allow_html=True)
        else:
            st.info("No order status data for the selected period.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Revenue by Basket Size",
            "🛍️",
            "Reveal how multi-item orders contribute to revenue to fine-tune bundling incentives.",
        )
        revenue_items_df = get_revenue_by_items_in_order(engine, selected_start_date, selected_end_date)
        if revenue_items_df is not None and not revenue_items_df.empty:
            revenue_items_df = revenue_items_df.sort_values(by='items_in_order')
            fig_basket = px.area(
                revenue_items_df,
                x='items_in_order',
                y='total_revenue',
                title='Revenue Contribution by Items per Order',
                labels={'items_in_order': 'Items in Order', 'total_revenue': 'Total Revenue ($)'},
                color_discrete_sequence=["#6366f1"],
            )
            fig_basket = stylize_chart(fig_basket)
            st.plotly_chart(fig_basket, use_container_width=True)
            st.markdown('<p class="chart-caption">Use free shipping thresholds or bundles to shift demand toward higher-value baskets.</p>', unsafe_allow_html=True)
        else:
            st.info("No revenue by items-in-order data for the selected period.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Peak Order Times",
            "📆",
            "Map out demand hotspots by weekday and hour to align staffing, logistics, and campaigns.",
        )
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

                fig_heatmap = px.imshow(
                    heatmap_data,
                    aspect="auto",
                    labels=dict(x="Day of Week", y="Hour of Day", color="Total Orders"),
                    title="Order Volume Heatmap by Hour and Day",
                    color_continuous_scale=px.colors.sequential.Viridis,
                )
                fig_heatmap = stylize_chart(fig_heatmap, legend_orientation="v")
                st.plotly_chart(fig_heatmap, use_container_width=True)
                st.markdown('<p class="chart-caption">Concentrated demand windows help right-size support teams and live campaign pushes.</p>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not generate heatmap. Data might be sparse or not in expected format. Error: {e}")
                st.dataframe(peak_times_df_for_heatmap)
        else:
            st.info("No peak order time data for the selected period.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    render_insight_callout(
        "Insight Spotlight",
        [
            "Order spikes cluster mid-week around the afternoon peak—align email drops and staffing accordingly.",
            "Processing and shipped statuses dominate the funnel; double-check SLAs to prevent backlog.",
            "Multi-item orders punch above their weight in revenue, validating bundle and upsell experimentation.",
        ],
    )

def render_customer_behavior_value():
    st.title("Customer Behavior & Value")
    st.markdown('<div class="highlight-badge">Customer Lens</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-intro">Diagnose loyalty strength, align offers to preferred categories, and remove friction at checkout.</div>',
        unsafe_allow_html=True,
    )

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
    with col1:
        display_kpi("Avg. CLV (in period)", f"${avg_clv:,.2f}", icon="💎")
    with col2:
        display_kpi("Repeat Customer Rate", f"{repeat_rate:.2f}%", icon="🔁")
    with col3:
        display_kpi("Avg. Time Between Orders", f"{avg_time_val:.1f} days", icon="⏳")
    with col4:
        display_kpi("Top Payment Type", top_payment, icon="💳")

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "CLV Distribution",
            "📊",
            "Gauge whether value is concentrated in a few customers or broadly distributed.",
        )
        if not clv_data.empty:
            fig_clv_hist = px.histogram(
                clv_data,
                x="total_spent",
                nbins=50,
                title="Customer Lifetime Value (CLV) Distribution",
                labels={'total_spent': 'Total Spent ($)'},
                color_discrete_sequence=["#22c55e"],
            )
            fig_clv_hist = stylize_chart(fig_clv_hist)
            st.plotly_chart(fig_clv_hist, use_container_width=True)
            st.markdown('<p class="chart-caption">Identify premium cohorts and watch for a long tail of low-value customers.</p>', unsafe_allow_html=True)
        else:
            st.info("No CLV data.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Top Product Categories by Customer Type",
            "🧭",
            "Compare what delights repeat buyers versus first-time shoppers to tailor merchandising and lifecycle plays.",
        )
        col_rep, col_first = st.columns(2)
        with col_rep:
            st.markdown("**Repeat Customers**")
            repeat_cats_df = get_top_categories_for_customer_type(engine, selected_start_date, selected_end_date, customer_type='repeat')
            if not repeat_cats_df.empty:
                fig_rep_cats = px.bar(
                    repeat_cats_df,
                    y='product_category_name_english',
                    x='total_revenue_for_category',
                    orientation='h',
                    title='Top Categories (Repeat Customers)',
                    labels={'product_category_name_english': 'Category', 'total_revenue_for_category': 'Revenue ($)'},
                    color='total_revenue_for_category',
                    color_continuous_scale=px.colors.sequential.Greens,
                    text_auto='.2s',
                )
                fig_rep_cats.update_layout(yaxis={'categoryorder': 'total ascending'})
                fig_rep_cats = stylize_chart(fig_rep_cats)
                st.plotly_chart(fig_rep_cats, use_container_width=True)
            else:
                st.info("No data for repeat customer categories.")
        with col_first:
            st.markdown("**First-Time Customers**")
            first_cats_df = get_top_categories_for_customer_type(engine, selected_start_date, selected_end_date, customer_type='first_time')
            if not first_cats_df.empty:
                fig_first_cats = px.bar(
                    first_cats_df,
                    y='product_category_name_english',
                    x='total_revenue_for_category',
                    orientation='h',
                    title='Top Categories (First-Time Customers)',
                    labels={'product_category_name_english': 'Category', 'total_revenue_for_category': 'Revenue ($)'},
                    color='total_revenue_for_category',
                    color_continuous_scale=px.colors.sequential.Blues,
                    text_auto='.2s',
                )
                fig_first_cats.update_layout(yaxis={'categoryorder': 'total ascending'})
                fig_first_cats = stylize_chart(fig_first_cats)
                st.plotly_chart(fig_first_cats, use_container_width=True)
            else:
                st.info("No data for first-time customer categories.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Payment Preferences",
            "💳",
            "Optimise checkout and payment partnerships with a clear view of preferred methods.",
        )
        if not payment_pref_df.empty:
            fig_payment = px.pie(
                payment_pref_df,
                names='payment_type',
                values='usage_count',
                title='Payment Method Usage',
                color_discrete_sequence=px.colors.sequential.Mint,
            )
            fig_payment.update_traces(textposition='inside', textinfo='percent+label')
            fig_payment = stylize_chart(fig_payment, legend_orientation="v")
            st.plotly_chart(fig_payment, use_container_width=True)
            st.markdown('<p class="chart-caption">Align promotions with dominant payment types and negotiate better rates.</p>', unsafe_allow_html=True)
        else:
            st.info("No payment preference data.")
        st.markdown("</div>", unsafe_allow_html=True)

    render_insight_callout(
        "Insight Spotlight",
        [
            "Repeat customers favour a distinct set of categories—target loyalty perks around those hero lines.",
            "CLV skews right-tailed; nurture high spenders while re-engaging the broad base with lifecycle nudges.",
            "Checkout optimisation should prioritise the top payment method while testing alternatives to reduce abandonment.",
        ],
    )


def render_geographic_logistics():
    st.title("Geographic Performance & Logistics")
    st.markdown('<div class="highlight-badge">Geospatial Pulse</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-intro">Understand regional demand, surface fulfilment hot spots, and zero-in on delivery friction.</div>',
        unsafe_allow_html=True,
    )

    map_data_df = get_revenue_orders_by_state_map_data(engine, selected_start_date, selected_end_date, region_filter=selected_region_filter)
    shipping_matrix_df = get_shipping_performance_matrix_data(engine, selected_start_date, selected_end_date, region_filter=selected_region_filter)

    num_top_states = 5
    if not selected_region_filter:
        num_top_states = st.slider("Number of Top States for Delivery Breakdown", 3, 10, 5, key="num_top_states_delivery")

    delivery_breakdown_df = get_delivery_time_breakdown_by_state(
        engine,
        selected_start_date,
        selected_end_date,
        top_n_states=num_top_states,
        region_filter=selected_region_filter,
    )

    # --- KPIs ---
    top_state_metric = "N/A"
    if map_data_df is not None and not map_data_df.empty and 'total_revenue' in map_data_df.columns:
        top_state_row = map_data_df.sort_values('total_revenue', ascending=False).iloc[0]
        top_state_metric = f"{top_state_row['customer_state']} (${float(top_state_row['total_revenue']):,.0f})"

    avg_variance_metric = "N/A"
    on_time_share_metric = "N/A"
    if shipping_matrix_df is not None and not shipping_matrix_df.empty and 'delivery_variance_days' in shipping_matrix_df.columns:
        avg_variance = shipping_matrix_df['delivery_variance_days'].mean()
        avg_variance_metric = f"{avg_variance:+.1f} days"
        on_time_share = (shipping_matrix_df['delivery_variance_days'] <= 0).mean() * 100
        on_time_share_metric = f"{on_time_share:.0f}% on/early"

    coverage_metric = f"{len(map_data_df['customer_state'].unique()) if map_data_df is not None and not map_data_df.empty else 0} states"
    region_label = selected_region_filter if selected_region_filter else "All Regions"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        display_kpi("Top Revenue State", top_state_metric, icon="📍")
    with col2:
        display_kpi("Avg Delivery Variance", avg_variance_metric, icon="⏱️")
    with col3:
        display_kpi("On-Time / Early Share", on_time_share_metric, icon="🚚")
    with col4:
        display_kpi("States in View", coverage_metric, help_text=f"Region filter: {region_label}", icon="🗺️")

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Revenue & Orders by State",
            "🗺️",
            "Quickly spot regional growth pockets and areas needing demand generation.",
        )
        if map_data_df is not None and not map_data_df.empty and 'customer_state' in map_data_df.columns and 'total_revenue' in map_data_df.columns:
            try:
                fig_map = px.choropleth(
                    map_data_df,
                    locations='customer_state', # Column with state codes
                    geojson='https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson', # Example GeoJSON for Brazil
                    featureidkey='properties.sigla', # Key in GeoJSON that matches 'locations'
                    color='total_revenue',
                    color_continuous_scale="Viridis",
                    scope='south america', # Focus map
                    hover_name='customer_state',
                    hover_data={'total_orders': True, 'avg_order_value': True},
                    title="Revenue by Brazilian State",
                )
                fig_map.update_geos(fitbounds="locations", visible=False)
                fig_map = stylize_chart(fig_map, legend_orientation="v")
                st.plotly_chart(fig_map, use_container_width=True)
                st.markdown('<p class="chart-caption">Hover to compare orders and AOV by state; filter the sidebar to zoom into a region.</p>', unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Could not render map. Ensure state codes are correct and GeoJSON is accessible. Error: {e}")
                st.write("Displaying as bar chart instead:")
                fig_bar_map = px.bar(
                    map_data_df.sort_values('total_revenue', ascending=False),
                    x='customer_state',
                    y='total_revenue',
                    color='total_revenue',
                    title='Revenue by State',
                    color_continuous_scale=px.colors.sequential.Viridis,
                )
                fig_bar_map = stylize_chart(fig_bar_map)
                st.plotly_chart(fig_bar_map, use_container_width=True)
        else:
            st.info("No map data for revenue by state.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Shipping Performance Matrix",
            "📦",
            "Bubble size tracks shipment volume; colour shows whether we are beating or missing promised dates.",
        )
        if shipping_matrix_df is not None and not shipping_matrix_df.empty and 'delivery_variance_days' in shipping_matrix_df.columns:
            shipping_matrix_df = shipping_matrix_df.copy()
            shipping_matrix_df['variance_color'] = shipping_matrix_df['delivery_variance_days'].apply(lambda x: 'Late' if x > 0 else 'Early/OnTime')
            fig_ship_matrix = px.scatter(
                shipping_matrix_df,
                x='avg_actual_delivery_time_days',
                y='delivery_variance_days',
                size='num_orders_to_state',
                color='variance_color',
                color_discrete_map={'Late': '#ef4444', 'Early/OnTime': '#10b981'},
                hover_name='customer_state',
                title="Shipping: Delivery Time vs. Variance from Estimate",
                labels={'avg_actual_delivery_time_days': 'Avg. Actual Delivery (days)', 'delivery_variance_days': 'Variance vs. Promise (days)'},
            )
            fig_ship_matrix = stylize_chart(fig_ship_matrix, legend_orientation="h")
            fig_ship_matrix.update_layout(legend=dict(title=None))
            st.plotly_chart(fig_ship_matrix, use_container_width=True)
            st.markdown('<p class="chart-caption">Prioritise states in red bubbles above the zero line—customers are receiving orders later than promised.</p>', unsafe_allow_html=True)
        else:
            st.info("No shipping performance matrix data.")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Delivery Time Breakdown by State",
            "⏳",
            "Break delivery into payment, seller handling, and carrier legs to target the true bottleneck.",
        )
        if delivery_breakdown_df is not None and not delivery_breakdown_df.empty:
            df_melted = delivery_breakdown_df.melt(
                id_vars=['customer_state'],
                value_vars=['avg_payment_processing_time', 'avg_seller_handling_time', 'avg_carrier_shipping_time'],
                var_name='time_segment',
                value_name='avg_days',
            )
            segment_labels = {
                'avg_payment_processing_time': 'Payment Processing',
                'avg_seller_handling_time': 'Seller Handling',
                'avg_carrier_shipping_time': 'Carrier Shipping',
            }
            df_melted['time_segment'] = df_melted['time_segment'].map(segment_labels)
            fig_delivery_breakdown = px.bar(
                df_melted,
                x='customer_state',
                y='avg_days',
                color='time_segment',
                title='Average Delivery Time Breakdown by Stage and State',
                labels={'avg_days': 'Average Days', 'customer_state': 'State'},
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_delivery_breakdown = stylize_chart(fig_delivery_breakdown)
            st.plotly_chart(fig_delivery_breakdown, use_container_width=True)
            st.markdown('<p class="chart-caption">Look for tall green sections—seller handling delays often dwarf courier time.</p>', unsafe_allow_html=True)
        else:
            st.info("No delivery time breakdown data.")
        st.markdown("</div>", unsafe_allow_html=True)

    render_insight_callout(
        "Insight Spotlight",
        [
            "Top-line growth concentrates in a handful of states—deploy geo-targeted ads to unlock the long tail.",
            "Late deliveries cluster where variance is positive; align ETA promises with actual carrier performance.",
            "Delivery breakdown highlights whether payment, seller prep, or carriers drive the lag—fix the largest slice first.",
        ],
    )


# --- Main App Logic ---
if page == "Business Health":
    render_business_health_cockpit()
elif page == "Product Portfolio Performance":
    render_product_portfolio_performance()
elif page == "Sales Funnel & Order Dynamics":
    render_sales_funnel_dynamics()
elif page == "Customer Behavior & Value":
    render_customer_behavior_value()
elif page == "Geographic Performance & Logistics":
    render_geographic_logistics()

st.sidebar.markdown("---")
