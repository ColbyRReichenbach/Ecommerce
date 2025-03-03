# E-Commerce Analytics Dashboard

This repository hosts an **internal analytics dashboard** for Company XYZ’s E-Commerce division. Built in **Streamlit**, it provides **interactive visualizations** and **data-driven insights** on sales, customers, shipping, and more. The primary aim is to **facilitate strategic decisions** that boost growth, efficiency, and customer satisfaction.

## Table of Contents
- [Project Overview](#project-overview)  
- [Key Features](#key-features)  
- [ML Models (Customer Segmentation)](#ml-models-customer-segmentation)  
- [Data Sources](#data-sources)  
- [Dashboard Link](#dashboard-link)  
- [Read-Only Database Access (Neon)](#read-only-database-access-neon)  
- [Future Enhancements](#future-enhancements)  
- [Contact](#contact)  
- [License](#license)

---

## Project Overview
The dashboard consolidates crucial KPIs and trends, including:

- **Sales & Orders**: Volume trends, average order values, revenue contributions.  
- **Customer Insights**: Lifetime value, repeat purchasing, segmentation.  
- **Product Performance**: Category-level revenue, return/cancellation rates, top sellers.  
- **Geographic & Shipping**: Regional revenue breakdown, delivery variance, optimization opportunities.

By providing an **actionable** snapshot of operational metrics, I can identify **growth levers** (e.g., targeted promotions, shipping improvements) and track the **impact** of our initiatives.

---

## Key Features
1. **Interactive Visuals**: Built using Streamlit + Plotly for dynamic charts and user-driven filters.  
2. **KPI Dashboards**: High-level metrics for revenue, orders, average order value, etc.  
3. **Customer Segmentation**: Clustering customers by behavior and value to tailor marketing and retention strategies.  
4. **Regional/Logistics Insights**: Delivery variances vs. estimated dates, top states/cities by revenue.  
5. **Secure Config**: Database credentials are handled via **Streamlit secrets**, ensuring no sensitive info is exposed in this repo.

---

## ML Models (Customer Segmentation)
- **Implemented**: **Customer Segmentation** using K-Means (or another clustering technique) on RFM-like features (total orders, CLV, average shipping cost, etc.). This helps identify loyal high-value customers vs. price-sensitive or at-risk segments.  
- **Planned**: Additional ML models—such as **Forecasting** and **Recommendation Systems**—once I gather more data. The current dataset is insufficiently large or consistent for advanced forecasting, but I will integrate such models as soon as the data matures.

---

## Data Sources
1. **Core E-Commerce DB**  
   - Contains orders, order_items, customers, products, shipping data, etc.  
   - Hosted in a read-only Postgres instance on Neon for demonstration.  
2. **Supplemental or Synthetic Data**  
   - For user privacy or testing, some data columns may be anonymized or synthetically generated.  

For a detailed breakdown of each table’s schema and lineage, see [`DATA_SOURCES.txt`](DATA_SOURCES.txt).

---

## Dashboard Link
I have deployed a **live** version of this dashboard at:  
**[Streamlit Cloud Link](https://your-streamlit-cloud-app-url)**  

Use the sidebar to navigate betIen different analytics modules (e.g., Business Overview, Product Performance, Shipping Insights). For any issues, contact the data team.

---

## Read-Only Database Access (Neon)
The production dataset is hosted on **Neon** for demonstration:
https://console.neon.tech/app/projects/blue-frog-75979168/branches/br-green-moon-a8wf1y3r/tables?database=ecommerce


Credentials for this read-only user are managed via Streamlit secrets, so they are **not** publicly visible in this repository. If you need direct read-only access for advanced queries, request it from the Data Engineering team.

---

## Future Enhancements
1. **Forecasting Models**: Once I accumulate sufficient historical data, I plan to integrate ARIMA/Prophet for monthly or Iekly revenue forecasts.  
2. **Recommendation Systems**: Cross-sell and upsell suggestions using item-based or user-based collaborative filtering.  
3. **Pricing Optimization**: Leverage advanced elasticity analysis if competitor or demand data becomes available.  
4. **Scalability**: Dockerize the application for broader internal deployment or multi-tenant usage.

---

## Contact
- **Project Lead**: Colby Reichenbach [colbyrreichenbach@gmail.com](mailto:colbyrreichenbach@gmail.com)  
[Linkedin](https://www.linkedin.com/in/colby-reichenbach/)
Please reach out for assistance, feedback, or inquiries regarding the system’s usage and further development.

---

## License
This project is an **internal, proprietary tool** for Company XYZ. Refer to [LICENSE.md](LICENSE.md) for terms of use. Unauthorized distribution or replication of data is prohibited.

---

