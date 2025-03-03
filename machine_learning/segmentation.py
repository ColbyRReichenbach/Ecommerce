import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score


def load_segmentation_dataset(csv_path):
    """
    Loads a customer segmentation dataset from CSV.
    Expected columns include:
      - customer_unique_id, clv, total_orders, avg_order_value,
        avg_days_between_orders, avg_shipping_cost, estimated_return_rate, etc.
    """
    df = pd.read_csv(csv_path)
    return df


def customer_segmentation(df, n_clusters=3):
    """
    Performs customer segmentation using K-Means clustering.

    Parameters:
      - df: DataFrame with customer segmentation data.
      - n_clusters: Desired number of clusters.

    Returns:
      - df: Original DataFrame with an added 'segment' column.
      - kmeans: The fitted KMeans model.
      - X_scaled: Scaled feature matrix used for clustering.
    """
    # Define features to use for clustering
    features = ["clv", "total_orders", "avg_order_value",
                "avg_days_between_orders", "avg_shipping_cost", "estimated_return_rate"]

    # Ensure the features exist and drop rows with missing values
    X = df[features].dropna()

    # Scale features (important for clustering)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Run K-Means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)

    # Assign cluster labels back to the DataFrame
    df.loc[X.index, "segment"] = clusters

    return df, kmeans, X_scaled


def evaluate_segmentation(X_scaled, clusters):
    """
    Computes segmentation metrics:
      - Silhouette Score (higher is better; range: -1 to 1)
      - Calinski-Harabasz Score (higher is better)
      - Davies-Bouldin Score (lower is better)
    """
    sil_score = silhouette_score(X_scaled, clusters)
    ch_score = calinski_harabasz_score(X_scaled, clusters)
    db_score = davies_bouldin_score(X_scaled, clusters)

    metrics = {
        "Silhouette Score": sil_score,
        "Calinski-Harabasz Score": ch_score,
        "Davies-Bouldin Score": db_score
    }
    return metrics


def main():
    segmentation_csv = "datasets/segmentation_dataset.csv"  # update this path as needed
    df_seg = load_segmentation_dataset(segmentation_csv)

    # Run segmentation (using 3 clusters by default)
    df_seg, kmeans_model, X_scaled = customer_segmentation(df_seg, n_clusters=3)
    clusters = kmeans_model.labels_

    # Evaluate segmentation performance
    metrics = evaluate_segmentation(X_scaled, clusters)

    print("Customer Segmentation Metrics:")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")

    # Optionally output cluster centers and sample segmentation results
    print("\nCluster centers (in scaled space):")
    print(kmeans_model.cluster_centers_)

    print("\nSegmentation results (first 10 rows):")
    print(df_seg.head(10))


if __name__ == "__main__":
    main()
