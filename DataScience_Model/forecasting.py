# ==========================================
# TIME SERIES FORECASTING (MA + ARIMA)
# ==========================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA

# 🔹 1. Load Dataset
df = pd.read_csv("feature_engineered_dataset.csv")

# 🔹 2. Create Time Series (using trip_day_number)
df = df.sort_values(by="trip_day_number")

ts = df.groupby("trip_day_number")["threat_score"].mean()

print("\nTime Series Created\n")

# 🔹 3. Plot Data
plt.figure(figsize=(10,5))
plt.plot(ts)
plt.title("Threat Score Over Time")
plt.xlabel("Day")
plt.ylabel("Threat Score")
plt.show()

# 🔹 4. Train-Test Split
train_size = int(len(ts) * 0.8)

train = ts[:train_size]
test = ts[train_size:]

print("\nTrain size:", len(train))
print("Test size:", len(test))

# 🔷 5. Moving Average Forecast

window = 3
moving_avg = train.rolling(window=window).mean()

forecast_ma = [moving_avg.iloc[-1]] * len(test)

# 🔷 6. ARIMA Model

model = ARIMA(train, order=(1,1,1))
model_fit = model.fit()

forecast_arima = model_fit.forecast(steps=len(test))

# 🔹 7. Evaluation

mae_ma = mean_absolute_error(test, forecast_ma)
rmse_ma = np.sqrt(mean_squared_error(test, forecast_ma))

mae_arima = mean_absolute_error(test, forecast_arima)
rmse_arima = np.sqrt(mean_squared_error(test, forecast_arima))

print("\n--- Moving Average ---")
print("MAE:", mae_ma)
print("RMSE:", rmse_ma)

print("\n--- ARIMA ---")
print("MAE:", mae_arima)
print("RMSE:", rmse_arima)

# 🔹 8. Plot Forecasts

plt.figure(figsize=(10,5))
plt.plot(test.index, test, label="Actual")
plt.plot(test.index, forecast_ma, label="Moving Average")
plt.plot(test.index, forecast_arima, label="ARIMA")

plt.legend()
plt.title("Forecast Comparison")
plt.show()

# ==========================================
# END
# ==========================================