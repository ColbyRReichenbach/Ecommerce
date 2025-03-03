import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score


def load_segmentation_dataset(csv_path):
    """Load segmentation dataset from CSV."""
    return pd.read_csv(csv_path)


def compute_segmentation(df, n_clusters=3):
    features = ["clv", "total_orders", "avg_order_value",
                "avg_days_between_orders", "avg_shipping_cost", "estimated_return_rate"]
    df_clean = df.dropna(subset=features)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_clean[features])
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)
    df_clean["segment"] = clusters
    sil_score = silhouette_score(X_scaled, clusters)
    ch_score = calinski_harabasz_score(X_scaled, clusters)
    db_score = davies_bouldin_score(X_scaled, clusters)
    metrics = {
        "Silhouette Score": sil_score,
        "Calinski-Harabasz Score": ch_score,
        "Davies-Bouldin Score": db_score
    }
    return df_clean, metrics


def main():
    segmentation_csv = "datasets/segmentation_dataset.csv"
    df = load_segmentation_dataset(segmentation_csv)
    df_seg, metrics = compute_segmentation(df, n_clusters=3)
    df_seg.to_csv("precomputed_segmentation_results.csv", index=False)
    pd.DataFrame([metrics]).to_csv("../data/ML/ML_outputs/precomputed_segmentation_metrics.csv", index=False)
    print("Segmentation precomputation complete.")


if __name__ == "__main__":
    main()
