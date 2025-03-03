from sqlalchemy import create_engine, text
from ecommerce_data_project.config.db_config import DB_URL

engine = create_engine(DB_URL)

queries = [
    {
        "name": "customer_product_purchases",
        "query": """
            INSERT INTO precomputed_features (feature_name, feature_value, computed_at)
            VALUES (
                'customer_product_purchases',
                (
                    SELECT jsonb_agg(jsonb_build_object(
                        'customer_unique_id', subquery.customer_unique_id,
                        'product_id', subquery.product_id,
                        'total_purchases', subquery.total_purchases
                    ))
                    FROM (
                        SELECT c.customer_unique_id, oi.product_id, COUNT(*) AS total_purchases
                        FROM customers c
                        JOIN orders o ON c.customer_id = o.customer_id
                        JOIN order_items oi ON o.order_id = oi.order_id
                        WHERE o.order_status = 'delivered'
                        GROUP BY c.customer_unique_id, oi.product_id
                    ) subquery
                ),
                NOW()
            );
        """
    },
    {
        "name": "top_product_popularity",
        "query": """
            INSERT INTO precomputed_features (feature_name, feature_value, computed_at)
            VALUES (
                'top_product_popularity',
                (
                    SELECT jsonb_agg(jsonb_build_object(
                        'product_id', subquery.product_id,
                        'total_sales', subquery.total_sales
                    ))
                    FROM (
                        SELECT oi.product_id, COUNT(*) AS total_sales
                        FROM order_items oi
                        JOIN orders o ON oi.order_id = o.order_id
                        WHERE o.order_status = 'delivered'
                        GROUP BY oi.product_id
                        ORDER BY total_sales DESC
                    ) subquery
                ),
                NOW()
            );
        """
    },
    {
        "name": "customer_top_categories",
        "query": """
            INSERT INTO precomputed_features (feature_name, feature_value, computed_at)
            VALUES (
                'customer_top_categories',
                (
                    SELECT jsonb_agg(jsonb_build_object(
                        'customer_unique_id', cat_counts.customer_unique_id,
                        'category', cat_counts.product_category_name,
                        'total_purchases', cat_counts.total_purchases
                    ))
                    FROM (
                        SELECT c.customer_unique_id, p.product_category_name, COUNT(oi.product_id) AS total_purchases
                        FROM customers c
                        JOIN orders o ON c.customer_id = o.customer_id
                        JOIN order_items oi ON o.order_id = oi.order_id
                        JOIN products p ON oi.product_id = p.product_id
                        WHERE o.order_status = 'delivered'
                        GROUP BY c.customer_unique_id, p.product_category_name
                    ) cat_counts
                ),
                NOW()
            );
        """
    }
]

def compute_precomputed_features():
    with engine.connect() as conn:
        for q in queries:
            print(f"Executing feature: {q['name']}...")
            conn.execute(text(q["query"]))
            conn.commit()
            print(f"{q['name']} completed.")

if __name__ == "__main__":
    compute_precomputed_features()
