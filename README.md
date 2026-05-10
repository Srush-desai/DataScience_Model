Insider Threat Detection (Flask + EDA + Testing + Forecasting)
Project overview (what this is)
Insider threats are risky actions performed by people who already have access to an organization (employees/contractors). Examples include unusual off-hours activity, abnormal movement/access patterns, and policy violations that may indicate malicious intent.

This project provides a single, easy-to-use web dashboard that helps non-technical users:

Understand the dataset through EDA (univariate, bivariate, multivariate, and insights)
Validate relationships statistically using hypothesis tests (T-test, Chi-square, ANOVA)
View simple time-based behavior trends and forecasts (Moving Average vs ARIMA)
Predict whether a case looks Normal or Malicious / High Risk using a trained ML model
In short: it turns a raw behavior dataset into visual explanations + statistical evidence + a model prediction in one place.

What problem it solves (why it’s useful)
For analysts: quickly identify which features look suspicious and which are statistically meaningful.
For managers/non-technical users: see a clear conclusion (reject/fail-to-reject H0, outlier counts, and forecasting performance) without reading code.
For demos/projects: show the full pipeline (data → EDA → tests → forecasting → prediction) via a UI.
Quickstart (Windows / PowerShell)
From the repository root:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python .\DataScience_Model\app.py
Open: http://127.0.0.1:5000/

Health check: http://127.0.0.1:5000/health

Project structure
DataScience_Model/app.py — Main Flask app (UI + EDA + tests + forecasting + prediction)
DataScience_Model/templates/index.html — UI template
DataScience_Model/static/style.css — UI styling
DataScience_Model/model.pkl — Trained model used by the Prediction tab
DataScience_Model/feature_engineered_balanced.csv — Dataset used by the app
Tabs (what each one does)
Landing
What it shows: quick entry points to dataset exploration and analysis tabs.
Conclusion: start with Dataset Explorer → EDA → Hypothesis Testing, then use Prediction to score new inputs.
Dataset Explorer
What it shows: dataset preview table + cleaning summary (missing values and duplicates).
Notes: if the dataset contains duplicate column names, the app auto-renames duplicates internally (example: col → col__2) so plots work.
Conclusion: confirm the dataset looks correct before analyzing patterns.
EDA (Univariate / Bivariate / Multivariate / Insights)
Univariate: distribution of one numeric feature (typical values, spread, skew).
Bivariate: relationship between two numeric features (colored by is_malicious when available).
Multivariate: correlation heatmap (how multiple numeric features move together).
Insights: strongest signals by absolute correlation with is_malicious + short bullets for quick understanding.
Conclusion: use EDA to identify the features that best separate malicious vs normal behavior.
Hypothesis Testing (T-test / Chi-square / ANOVA)
p-value: probability of seeing the result (or more extreme) if the null hypothesis (H0) were true.
We use α = 0.05:
If p < 0.05 → Reject H0 (evidence of a difference/association)
If p ≥ 0.05 → Fail to reject H0 (not enough evidence)
T-test (Welch): compares the mean of a numeric metric between 2 groups (Normal vs Malicious).
ANOVA: tests whether mean values differ across 3+ categories. It uses variance decomposition (F-statistic = between-group variance / within-group variance) to detect mean differences.
Chi-square: tests association between 2 categorical variables.
Outliers detected: counts outliers using the IQR rule and shows bounds + a few example values.
Conclusion: rejected H0 suggests a feature is statistically linked to behavior differences (useful signal).
Prediction
What it does: uses the trained model (model.pkl) to predict Normal vs Malicious from user inputs.
What the graphs mean: confusion matrix shows correct/incorrect predictions by class.
Conclusion: use this tab to score a new case and sanity-check model quality (Accuracy/Precision/Recall/F1).
Time Forecasting
What it does: builds a time series by grouping by trip_day_number and forecasting the mean of a target signal (prefers threat_score).
Methods: Moving Average baseline + ARIMA (if available).
Metrics: MAE/RMSE (lower is better). The conclusion tells which method performed better on the test split.
Conclusion: this gives a simple trend + short-horizon forecasting comparison for the selected signal.
Train / Re-train the model (optional)
Core features only (recommended for the demo UI):

python .\DataScience_Model\train_model.py
All features:

python .\DataScience_Model\train_model.py --all-features
Predict without the UI
CLI
python .\DataScience_Model\predict.py --json "{\"total_activity\": 12, \"off_hours_ratio\": 0.4, \"burn_ratio\": 0.1, \"movement_anomaly\": 0.2, \"employee_risk\": 0.7, \"activity_per_entry\": 3.0}"
API
$body = @{
  total_activity = 12
  off_hours_ratio = 0.4
  burn_ratio = 0.1
  movement_anomaly = 0.2
  employee_risk = 0.7
  activity_per_entry = 3.0
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/predict -ContentType "application/json" -Body $body
Troubleshooting
If a plot shows as unavailable, check the terminal logs and ensure dependencies are installed:
python -m pip install -r requirements.txt
If ARIMA is unavailable, confirm statsmodels is installed (it is listed in requirements.txt).
Dataset notes (for new users)
The app reads: DataScience_Model/feature_engineered_balanced.csv
The prediction target label is: is_malicious (0 = Normal, 1 = Malicious)
Some datasets may contain duplicate column names (example: employee_seniority_years twice). The app automatically renames duplicates internally (employee_seniority_years__2) so plots and correlations work correctly.
