# Insider Threat Detection (Flask + EDA + Testing + Forecasting)

## 1. Project Overview

* Insider threats are risky activities performed by authorized users such as employees or contractors.
* Examples:

  * Unusual off-hours access
  * Suspicious movement patterns
  * Policy violations
  * Abnormal activity behavior
* This project provides a web-based dashboard for analyzing insider threat behavior using:

  * EDA (Exploratory Data Analysis)
  * Statistical Testing
  * Forecasting
  * Machine Learning Prediction

---

# 2. Purpose of the Project

The project converts raw organizational behavior data into:

* Visual analysis
* Statistical evidence
* Forecasting insights
* ML-based risk prediction

All integrated into a single Flask dashboard.

---

# 3. Problems Solved

## For Analysts

* Detect suspicious features quickly
* Identify statistically significant patterns
* Analyze abnormal behavior visually

## For Managers / Non-Technical Users

* Easy interpretation of results
* Clear conclusions:

  * Reject H0
  * Fail to Reject H0
  * Outlier detection
  * Forecast comparison

## For Academic Projects / Demos

Demonstrates the complete Data Science pipeline:

Data Collection → EDA → Statistical Testing → Forecasting → ML Prediction → Dashboard UI

---

# 4. Technologies Used

* Python
* Flask
* Pandas
* NumPy
* Matplotlib
* Seaborn
* Scikit-learn
* Statsmodels (ARIMA)
* HTML/CSS

---

# 5. Quickstart Setup (Windows / PowerShell)

## Create Virtual Environment

```powershell
python -m venv .venv
```

## Activate Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## Upgrade pip

```powershell
python -m pip install --upgrade pip
```

## Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

## Run Flask Application

```powershell
python .\DataScience_Model\app.py
```

---

# 6. Open the Application

## Main Dashboard

```text
http://127.0.0.1:5000/
```

## Health Check

```text
http://127.0.0.1:5000/health
```

---

# 7. Project Structure

## Main Files

* `DataScience_Model/app.py`

  * Main Flask application
  * Handles UI, EDA, testing, forecasting, prediction

* `DataScience_Model/templates/index.html`

  * Frontend HTML template

* `DataScience_Model/static/style.css`

  * Styling for dashboard

* `DataScience_Model/model.pkl`

  * Trained ML model

* `DataScience_Model/feature_engineered_balanced.csv`

  * Dataset used for analysis

---

# 8. Dashboard Tabs and Functionality

# A. Landing Page

## Purpose

* Provides navigation to all analysis modules

## Conclusion

Recommended workflow:

1. Dataset Explorer
2. EDA
3. Hypothesis Testing
4. Prediction

---

# B. Dataset Explorer

## Features

* Dataset preview table
* Missing value summary
* Duplicate value summary

## Special Handling

* Automatically renames duplicate columns
* Example:

```text
employee_years → employee_years__2
```

## Conclusion

Ensures dataset quality before analysis.

---

# C. EDA (Exploratory Data Analysis)

## 1. Univariate Analysis

### Purpose

* Analyze a single feature

### Shows

* Distribution
* Spread
* Skewness
* Typical values

---

## 2. Bivariate Analysis

### Purpose

* Relationship between two variables

### Visualization

* Scatter plots
* Colored by:

```text
is_malicious
```

---

## 3. Multivariate Analysis

### Purpose

* Study relationships among multiple variables

### Visualization

* Correlation Heatmap

---

## 4. Insights Section

### Displays

* Strongest correlations with:

```text
is_malicious
```

### Conclusion

Identifies features that strongly indicate malicious behavior.

---

# D. Hypothesis Testing

## Purpose

Validate statistical significance of relationships.

---

## p-value Concept

* Probability of obtaining results assuming H0 is true.

### Significance Level

```text
α = 0.05
```

### Decision Rules

* If:

```text
p < 0.05
```

→ Reject H0

* If:

```text
p ≥ 0.05
```

→ Fail to Reject H0

---

## 1. T-Test (Welch’s T-Test)

### Purpose

Compares means between:

* Normal users
* Malicious users

### Conclusion

Determines whether a feature differs significantly between groups.

---

## 2. ANOVA

### Purpose

Compares mean differences across 3+ groups.

### Uses

* Variance decomposition
* F-statistic

### Formula

```text
F = Between-group variance / Within-group variance
```

### Conclusion

Checks whether multiple categories behave differently.

---

## 3. Chi-Square Test

### Purpose

Checks association between:

* Two categorical variables

### Conclusion

Determines dependency between categorical behaviors.

---

## 4. Outlier Detection

### Method

* IQR (Interquartile Range)

### Displays

* Lower bound
* Upper bound
* Number of outliers
* Sample outlier values

### Conclusion

Detects unusual behavior points.

---

# E. Prediction Module

## Purpose

Predicts:

```text
Normal OR Malicious
```

using the trained ML model.

---

## Model File

```text
model.pkl
```

---

## Visualizations

### Confusion Matrix

Shows:

* Correct predictions
* Incorrect predictions

---

## Metrics

* Accuracy
* Precision
* Recall
* F1-Score

---

## Conclusion

Used to:

* Score new behavior data
* Validate model quality

---

# F. Time Forecasting

## Purpose

Forecasts behavior trends over time.

---

## Time Series Basis

Grouped using:

```text
trip_day_number
```

---

## Preferred Signal

```text
threat_score
```

---

## Forecasting Methods

### 1. Moving Average

* Simple baseline forecasting

### 2. ARIMA

* Advanced time series forecasting

---

## Evaluation Metrics

* MAE (Mean Absolute Error)
* RMSE (Root Mean Squared Error)

### Interpretation

Lower values indicate better forecasting performance.

---

## Conclusion

Compares forecasting methods and identifies better trend prediction.

---

# 9. Train / Retrain the Model

## Recommended Core Features

```powershell
python .\DataScience_Model\train_model.py
```

---

## Train Using All Features

```powershell
python .\DataScience_Model\train_model.py --all-features
```

---

# 10. Predict Without UI

# A. CLI Prediction

```powershell
python .\DataScience_Model\predict.py --json "{\"total_activity\": 12, \"off_hours_ratio\": 0.4, \"burn_ratio\": 0.1, \"movement_anomaly\": 0.2, \"employee_risk\": 0.7, \"activity_per_entry\": 3.0}"
```

---

# B. API Prediction

```powershell
$body = @{
  total_activity = 12
  off_hours_ratio = 0.4
  burn_ratio = 0.1
  movement_anomaly = 0.2
  employee_risk = 0.7
  activity_per_entry = 3.0
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:5000/api/predict `
  -ContentType "application/json" `
  -Body $body
```

---

# 11. Troubleshooting

## Plot Not Showing

Run:

```powershell
python -m pip install -r requirements.txt
```

---

## ARIMA Not Working

Ensure:

```text
statsmodels
```

is installed.

---

# 12. Dataset Information

## Dataset File

```text
DataScience_Model/feature_engineered_balanced.csv
```

---

## Target Label

```text
is_malicious
```

### Label Meaning

* `0` → Normal
* `1` → Malicious

---

## Duplicate Column Handling

Example:

```text
employee_seniority_years
employee_seniority_years__2
```

The application automatically renames duplicate columns internally.

---

# 13. Final Conclusion

This project demonstrates a complete Insider Threat Detection system using:

* Flask Web Dashboard
* Exploratory Data Analysis
* Statistical Hypothesis Testing
* Time Series Forecasting
* Machine Learning Classification

The system helps organizations:

* Detect suspicious employee behavior
* Understand statistical relationships
* Forecast threat trends
* Predict malicious activity using AI models

All through a simple and interactive web interface.
<img width="1896" height="935" alt="Screenshot 2026-05-11 022806" src="https://github.com/user-attachments/assets/cfc47343-1280-42a6-8df3-277f6b3f0d76" />
