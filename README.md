# Insider Threat Detection (DataScience_Model)

## Setup (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Train / Re-train the model

Core features only (recommended for the demo UI):

```powershell
python .\DataScience_Model\train_model.py
```

All features:

```powershell
python .\DataScience_Model\train_model.py --all-features
```

## Run the Flask app

```powershell
python .\DataScience_Model\app.py
```

Open `http://127.0.0.1:5000/`

Health check: `http://127.0.0.1:5000/health`

## Notes

- ARIMA in the Time Forecasting tab requires `statsmodels` (included in `requirements.txt`). Re-run `python -m pip install -r requirements.txt` if ARIMA shows as unavailable.

## How to read the analysis (non-technical)

### EDA tab

- **Univariate**: shows the distribution of one feature (example: `threat_score`). Use it to see typical values and whether the data is skewed.
- **Bivariate**: shows the relationship between two features (example: `off_hours_ratio` vs `threat_score`) and colors points by `is_malicious` when available.
- **Multivariate**: correlation heatmap for multiple numeric features. Values closer to `1`/`-1` mean a stronger linear relationship; near `0` means weak linear relationship.
- **Insights**: highlights the strongest signals (by absolute correlation with `is_malicious`) and shows quick summary bullets.

### Hypothesis Testing tab (T-test / Chi-square / ANOVA)

- **p-value**: probability of observing the result (or more extreme) if the **null hypothesis (H0)** is true.
- We use **α = 0.05**:
  - If `p < 0.05` → **Reject H0** (evidence of a difference/association).
  - If `p ≥ 0.05` → **Fail to reject H0** (not enough evidence).
- **Outliers detected**: counts unusual values for the plotted metric using the **IQR rule** (below `Q1 - 1.5×IQR` or above `Q3 + 1.5×IQR`), plus the bounds and a few example values.

### Time Forecasting tab

- Builds a simple time series by grouping by `trip_day_number` and taking the mean of a target signal (prefers `threat_score`).
- Compares:
  - **Moving Average** baseline (simple smoothing)
  - **ARIMA** (if `statsmodels` is installed and ARIMA fit succeeds)
- The conclusion states which method performs better on the test split using **RMSE** (lower is better).

## Predict from CLI (no UI)

```powershell
python .\DataScience_Model\predict.py --json "{\"total_activity\": 12, \"off_hours_ratio\": 0.4, \"burn_ratio\": 0.1, \"movement_anomaly\": 0.2, \"employee_risk\": 0.7, \"activity_per_entry\": 3.0}"
```

## Predict via API

```powershell
$body = @{
  total_activity = 12
  off_hours_ratio = 0.4
  burn_ratio = 0.1
  movement_anomaly = 0.2
  employee_risk = 0.7
  activity_per_entry = 3.0
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/predict -ContentType "application/json" -Body $body
```
