import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, mean_absolute_error, r2_score
import math, os


def load_forecasting_data(csv_path):
    """Load forecasting data with columns ['ds', 'y'] and set datetime index."""
    df = pd.read_csv(csv_path)
    df["ds"] = pd.to_datetime(df["ds"])
    df.sort_values("ds", inplace=True)
    df.set_index("ds", inplace=True)
    return df


def train_test_split_time_series(df, test_size=6):
    n = len(df)
    split_point = n - test_size
    df_train = df.iloc[:split_point].copy()
    df_test = df.iloc[split_point:].copy()
    print(f"Total rows: {n}, Training: {len(df_train)}, Test: {len(df_test)}")
    return df_train, df_test


def compute_metrics(y_true, y_pred):
    mape = mean_absolute_percentage_error(y_true, y_pred) * 100
    rmse = math.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return {"MAPE (%)": mape, "RMSE": rmse, "MAE": mae, "R²": r2}

def run_arima_forecast(df_train, df_test):
    train_values = df_train["y"].astype(float)
    model = SARIMAX(train_values, order=(1, 1, 1), enforce_stationarity=False, enforce_invertibility=False)
    results = model.fit(disp=False)
    steps_ahead = len(df_test)
    forecast_arima = results.forecast(steps=steps_ahead)
    forecast_arima.index = df_test.index
    return forecast_arima


def run_prophet_forecast(df_train, df_test):
    print("Prophet - Training set rows:", len(df_train))
    if len(df_train.dropna()) < 2:
        print("Insufficient training data for Prophet. Returning NaNs.")
        return pd.Series([np.nan] * len(df_test), index=df_test.index)
    prophet_train = df_train.reset_index()
    model = Prophet(seasonality_mode='additive', yearly_seasonality=True)
    try:
        model.fit(prophet_train[["ds", "y"]])
    except Exception as e:
        print("Prophet fit error:", e)
        return pd.Series([np.nan] * len(df_test), index=df_test.index)
    steps_ahead = len(df_test)
    future = model.make_future_dataframe(periods=steps_ahead, freq='W')
    forecast = model.predict(future)
    forecast_prophet = forecast.iloc[-steps_ahead:][["ds", "yhat"]].copy()
    forecast_prophet["ds"] = pd.to_datetime(forecast_prophet["ds"])
    forecast_prophet.set_index("ds", inplace=True)
    forecast_prophet.rename(columns={"yhat": "forecast"}, inplace=True)
    forecast_prophet = forecast_prophet.reindex(df_test.index, method='nearest')
    return forecast_prophet["forecast"]


def run_forecasting_experiment(csv_path, test_size=6, output_plots_dir="plots"):
    df = load_forecasting_data(csv_path)
    df_train, df_test = train_test_split_time_series(df, test_size=test_size)
    forecast_arima = run_arima_forecast(df_train, df_test)
    forecast_prophet = run_prophet_forecast(df_train, df_test)
    forecast_ensemble = (forecast_arima + forecast_prophet) / 2
    metrics_arima = compute_metrics(df_test["y"], forecast_arima)
    metrics_prophet = (compute_metrics(df_test["y"], forecast_prophet)
                       if not forecast_prophet.isna().all() else {"MAPE (%)": np.nan, "RMSE": np.nan, "MAE": np.nan, "R²": np.nan})
    metrics_ensemble = compute_metrics(df_test["y"], forecast_ensemble)
    metrics_df = pd.DataFrame([metrics_arima, metrics_prophet, metrics_ensemble],
                              index=["ARIMA", "Prophet", "Ensemble"])
    print(f"Forecast Metrics for {os.path.basename(csv_path)}:")
    print(metrics_df, "\n")
    results_df = pd.DataFrame({
        "Actual": df_test["y"],
        "ARIMA Forecast": forecast_arima,
        "Prophet Forecast": forecast_prophet,
        "Ensemble Forecast": forecast_ensemble
    })
    print("Forecast Results:")
    print(results_df, "\n")
    os.makedirs(output_plots_dir, exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.plot(df_test.index, df_test["y"], label="Actual")
    plt.plot(df_test.index, forecast_arima, label="ARIMA Forecast", linestyle="--")
    plt.title("ARIMA Forecast vs Actual")
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.legend()
    plt.savefig(os.path.join(output_plots_dir, f"ARIMA_{os.path.basename(csv_path)}.png"))
    plt.close()
    plt.figure(figsize=(10, 6))
    plt.plot(df_test.index, df_test["y"], label="Actual")
    plt.plot(df_test.index, forecast_prophet, label="Prophet Forecast", linestyle="--")
    plt.title("Prophet Forecast vs Actual")
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.legend()
    plt.savefig(os.path.join(output_plots_dir, f"Prophet_{os.path.basename(csv_path)}.png"))
    plt.close()
    plt.figure(figsize=(10, 6))
    plt.plot(df_test.index, df_test["y"], label="Actual")
    plt.plot(df_test.index, forecast_ensemble, label="Ensemble Forecast", linestyle="--")
    plt.title("Ensemble Forecast vs Actual")
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.legend()
    plt.savefig(os.path.join(output_plots_dir, f"Ensemble_{os.path.basename(csv_path)}.png"))
    plt.close()
    return {"metrics": metrics_df, "results": results_df}


def main():
    frequencies = ["weekly", "daily"]
    base_path = "datasets"
    all_metrics = {}
    for freq in frequencies:
        csv_file = f"{base_path}/forecasting_dataset_{freq}.csv"
        print(f"\nProcessing {freq} dataset from: {csv_file}")
        output = run_forecasting_experiment(csv_file, test_size=6, output_plots_dir="plots")
        all_metrics[freq] = output["metrics"]
    for freq, metrics in all_metrics.items():
        print(f"\nMetrics for {freq} dataset:")
        print(metrics)
    combined_metrics = pd.concat(all_metrics)
    combined_metrics.to_csv("combined_forecast_metrics.csv", index=True)


if __name__ == "__main__":
    main()
