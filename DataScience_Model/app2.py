# import base64
# import io
# import os
# from typing import Dict, List, Optional

# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# from flask import Flask, render_template, request, send_file
# from sklearn.metrics import (
#     accuracy_score,
#     confusion_matrix,
#     f1_score,
#     precision_score,
#     recall_score,
# )
# from sklearn.model_selection import train_test_split

# try:
#     import pickle
# except ImportError:  # pragma: no cover
#     pickle = None

# try:
#     import seaborn as sns
# except ImportError:  # pragma: no cover
#     sns = None

# try:
#     from scipy.stats import chi2_contingency, f_oneway, ttest_ind
# except ImportError:  # pragma: no cover
#     chi2_contingency = None
#     f_oneway = None
#     ttest_ind = None

# try:
#     from statsmodels.tsa.arima.model import ARIMA
# except ImportError:  # pragma: no cover
#     ARIMA = None


# app = Flask(__name__)

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATASET_PATH = os.path.join(BASE_DIR, "feature_engineered_dataset.csv")
# MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
# POWER_BI_PATH = os.path.join(BASE_DIR, "dsci_project.pbix")

# RAW_DF = pd.read_csv(DATASET_PATH)
# TARGET_COLUMN = "is_malicious"
# CORE_PREDICTION_FIELDS = [
#     "total_activity",
#     "off_hours_ratio",
#     "burn_ratio",
#     "movement_anomaly",
#     "employee_risk",
#     "activity_per_entry",
#     "threat_score",
# ]


# def clean_dataset(df: pd.DataFrame) -> Dict[str, object]:
#     cleaned = df.copy()

#     missing_before = int(cleaned.isna().sum().sum())
#     duplicates_before = int(cleaned.duplicated().sum())

#     for column in cleaned.columns:
#         if cleaned[column].isna().sum() == 0:
#             continue
#         if pd.api.types.is_numeric_dtype(cleaned[column]):
#             cleaned[column] = cleaned[column].fillna(cleaned[column].median())
#         else:
#             mode = cleaned[column].mode(dropna=True)
#             fallback = mode.iloc[0] if not mode.empty else "Unknown"
#             cleaned[column] = cleaned[column].fillna(fallback)

#     cleaned = cleaned.drop_duplicates().copy()

#     duplicates_after = int(cleaned.duplicated().sum())
#     missing_after = int(cleaned.isna().sum().sum())

#     for column in cleaned.columns:
#         if cleaned[column].dtype == bool:
#             cleaned[column] = cleaned[column].astype(int)

#     return {
#         "df": cleaned,
#         "steps": [
#             {
#                 "title": "Remove Null Values",
#                 "detail": f"Missing values reduced from {missing_before} to {missing_after}.",
#             },
#             {
#                 "title": "Remove Duplicates",
#                 "detail": f"Duplicate rows reduced from {duplicates_before} to {duplicates_after}.",
#             },
#             {
#                 "title": "Normalize Data Types",
#                 "detail": "Boolean indicators were converted into numeric flags for cleaner analysis.",
#             },
#         ],
#         "missing_before": missing_before,
#         "missing_after": missing_after,
#         "duplicates_before": duplicates_before,
#         "duplicates_after": duplicates_after,
#     }


# CLEANING_RESULT = clean_dataset(RAW_DF)
# CLEAN_DF = CLEANING_RESULT["df"]
# NUMERIC_COLUMNS = CLEAN_DF.select_dtypes(include=[np.number]).columns.tolist()
# DISPLAY_COLUMNS = [column for column in NUMERIC_COLUMNS if column != TARGET_COLUMN][:10]
# SUMMARY_DEFAULT_COLUMNS = [
#     column
#     for column in ["threat_score", "total_activity", "off_hours_ratio", "movement_anomaly"]
#     if column in CLEAN_DF.columns
# ]


# def load_model():
#     if pickle is None or not os.path.exists(MODEL_PATH):
#         return None
#     with open(MODEL_PATH, "rb") as model_file:
#         return pickle.load(model_file)


# MODEL = load_model()
# MODEL_FEATURES = list(getattr(MODEL, "feature_names_in_", CORE_PREDICTION_FIELDS)) if MODEL is not None else CORE_PREDICTION_FIELDS
# PREDICTION_FORM_FIELDS = [field for field in CORE_PREDICTION_FIELDS if field in CLEAN_DF.columns]


# def encode_plot(fig) -> str:
#     buffer = io.BytesIO()
#     fig.tight_layout()
#     fig.savefig(buffer, format="png", dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
#     plt.close(fig)
#     buffer.seek(0)
#     return base64.b64encode(buffer.read()).decode("utf-8")


# def plot_theme():
#     plt.style.use("seaborn-v0_8-whitegrid")


# def make_histogram(series: pd.Series, title: str, color: str = "#f97316") -> str:
#     plot_theme()
#     fig, ax = plt.subplots(figsize=(7, 4), facecolor="#fffaf3")
#     ax.hist(series.dropna(), bins=24, color=color, edgecolor="#1f2937", alpha=0.9)
#     ax.set_title(title, color="#111827", fontsize=14, fontweight="bold")
#     ax.set_xlabel(series.name.replace("_", " ").title(), color="#374151")
#     ax.set_ylabel("Frequency", color="#374151")
#     return encode_plot(fig)


# def make_scatter(df: pd.DataFrame, x_col: str, y_col: str, hue_col: Optional[str] = None) -> str:
#     plot_theme()
#     fig, ax = plt.subplots(figsize=(7, 4), facecolor="#fffaf3")
#     if sns is not None and hue_col and hue_col in df.columns:
#         sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue_col, palette="magma", alpha=0.7, ax=ax)
#     else:
#         ax.scatter(df[x_col], df[y_col], color="#2563eb", alpha=0.45)
#     ax.set_title(f"{x_col.replace('_', ' ').title()} vs {y_col.replace('_', ' ').title()}", fontsize=14, fontweight="bold")
#     return encode_plot(fig)


# def make_heatmap(df: pd.DataFrame, columns: List[str], title: str) -> str:
#     plot_theme()
#     fig, ax = plt.subplots(figsize=(8, 5), facecolor="#fffaf3")
#     correlation = df[columns].corr(numeric_only=True)
#     if sns is not None:
#         sns.heatmap(correlation, cmap="YlOrRd", annot=False, ax=ax)
#     else:
#         heatmap = ax.imshow(correlation, cmap="YlOrRd")
#         fig.colorbar(heatmap, ax=ax)
#         ax.set_xticks(range(len(columns)))
#         ax.set_yticks(range(len(columns)))
#         ax.set_xticklabels(columns, rotation=45, ha="right")
#         ax.set_yticklabels(columns)
#     ax.set_title(title, fontsize=14, fontweight="bold")
#     return encode_plot(fig)


# def make_bar(values: pd.Series, title: str, color: str = "#0f766e") -> str:
#     plot_theme()
#     fig, ax = plt.subplots(figsize=(7, 4), facecolor="#fffaf3")
#     values.plot(kind="bar", color=color, ax=ax)
#     ax.set_title(title, fontsize=14, fontweight="bold")
#     ax.set_ylabel("Value")
#     ax.tick_params(axis="x", rotation=35)
#     return encode_plot(fig)


# def make_boxplot(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> str:
#     plot_theme()
#     fig, ax = plt.subplots(figsize=(7, 4), facecolor="#fffaf3")
#     if sns is not None:
#         sns.boxplot(data=df, x=x_col, y=y_col, palette="Set2", ax=ax)
#     else:
#         grouped = [group[y_col].dropna().values for _, group in df.groupby(x_col)]
#         ax.boxplot(grouped)
#         ax.set_xticks(range(1, len(df[x_col].dropna().unique()) + 1))
#         ax.set_xticklabels(sorted(df[x_col].dropna().unique()))
#     ax.set_title(title, fontsize=14, fontweight="bold")
#     return encode_plot(fig)


# def compute_outliers(series: pd.Series) -> Dict[str, object]:
#     cleaned = series.dropna()
#     if cleaned.empty:
#         return {"count": 0, "examples": []}
#     q1 = cleaned.quantile(0.25)
#     q3 = cleaned.quantile(0.75)
#     iqr = q3 - q1
#     lower = q1 - (1.5 * iqr)
#     upper = q3 + (1.5 * iqr)
#     outliers = cleaned[(cleaned < lower) | (cleaned > upper)]
#     return {
#         "count": int(outliers.shape[0]),
#         "examples": [round(value, 3) for value in outliers.head(6).tolist()],
#         "bounds": (round(lower, 3), round(upper, 3)),
#     }


# def get_preview(df: pd.DataFrame, columns: List[str], rows: int = 12) -> List[Dict[str, object]]:
#     preview_df = df[columns].head(rows).copy()
#     preview_df = preview_df.replace({np.nan: None})
#     return preview_df.to_dict(orient="records")


# def evaluate_model() -> Dict[str, object]:
#     if MODEL is None or TARGET_COLUMN not in CLEAN_DF.columns:
#         return {"available": False, "message": "Model evaluation is not available."}

#     feature_columns = [column for column in MODEL_FEATURES if column in CLEAN_DF.columns]
#     if not feature_columns:
#         return {"available": False, "message": "Model features could not be matched with the dataset."}

#     try:
#         X = CLEAN_DF[feature_columns]
#         y = CLEAN_DF[TARGET_COLUMN]
#         _, X_test, _, y_test = train_test_split(
#             X,
#             y,
#             test_size=0.2,
#             random_state=42,
#             stratify=y if y.nunique() > 1 else None,
#         )
#         y_pred = MODEL.predict(X_test)
#         cm = confusion_matrix(y_test, y_pred)

#         plot_theme()
#         fig, ax = plt.subplots(figsize=(5, 4), facecolor="#fffaf3")
#         if sns is not None:
#             sns.heatmap(cm, annot=True, fmt="d", cmap="Oranges", cbar=False, ax=ax)
#         else:
#             heatmap = ax.imshow(cm, cmap="Oranges")
#             fig.colorbar(heatmap, ax=ax)
#             for row_index in range(cm.shape[0]):
#                 for col_index in range(cm.shape[1]):
#                     ax.text(col_index, row_index, str(cm[row_index, col_index]), ha="center", va="center")
#         ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold")
#         ax.set_xlabel("Predicted")
#         ax.set_ylabel("Actual")

#         return {
#             "available": True,
#             "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
#             "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
#             "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
#             "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
#             "plot": encode_plot(fig),
#         }
#     except Exception as exc:  # pragma: no cover
#         return {"available": False, "message": f"Model evaluation failed: {exc}"}


# MODEL_METRICS = evaluate_model()


# def build_prediction_result(form_values: Dict[str, str]) -> Optional[Dict[str, object]]:
#     if MODEL is None:
#         return None

#     payload = {}
#     medians = CLEAN_DF.median(numeric_only=True)

#     for feature in MODEL_FEATURES:
#         default_value = float(medians.get(feature, 0.0))
#         payload[feature] = default_value

#     user_snapshot = {}
#     for field in PREDICTION_FORM_FIELDS:
#         raw_value = form_values.get(field, "").strip()
#         if raw_value == "":
#             payload[field] = float(medians.get(field, 0.0))
#             user_snapshot[field] = payload[field]
#             continue
#         payload[field] = float(raw_value)
#         user_snapshot[field] = float(raw_value)

#     input_frame = pd.DataFrame([payload])
#     prediction = int(MODEL.predict(input_frame)[0])

#     probability = None
#     if hasattr(MODEL, "predict_proba"):
#         try:
#             probability = float(MODEL.predict_proba(input_frame)[0][1])
#         except Exception:  # pragma: no cover
#             probability = None

#     drivers = []
#     for field in PREDICTION_FORM_FIELDS:
#         baseline = float(medians.get(field, 0.0))
#         delta = user_snapshot[field] - baseline
#         if abs(delta) > 0:
#             drivers.append((field, delta))
#     drivers.sort(key=lambda item: abs(item[1]), reverse=True)

#     outcome = "Malicious / High Risk" if prediction == 1 else "Normal / Lower Risk"
#     explanation_parts = [
#         f"The model predicts: {outcome}.",
#     ]
#     if probability is not None:
#         explanation_parts.append(f"Estimated malicious probability: {round(probability * 100, 2)}%.")
#     if drivers:
#         top_drivers = ", ".join(
#             f"{field.replace('_', ' ')} ({'above' if delta > 0 else 'below'} baseline)"
#             for field, delta in drivers[:3]
#         )
#         explanation_parts.append(f"Main drivers compared with dataset baseline: {top_drivers}.")

#     return {
#         "outcome": outcome,
#         "probability": None if probability is None else round(probability, 4),
#         "explanation": " ".join(explanation_parts),
#         "inputs": user_snapshot,
#     }


# def build_eda_view(eda_focus: str, summary_columns: List[str], show_summary: bool) -> Dict[str, object]:
#     eda_data: Dict[str, object] = {"focus": eda_focus}

#     if eda_focus == "univariate":
#         column = "threat_score" if "threat_score" in CLEAN_DF.columns else NUMERIC_COLUMNS[0]
#         eda_data["title"] = "Univariate Analysis"
#         eda_data["description"] = f"Distribution overview for {column.replace('_', ' ')}."
#         eda_data["plot"] = make_histogram(CLEAN_DF[column], f"{column.replace('_', ' ').title()} Distribution")
#     elif eda_focus == "bivariate":
#         x_col = "off_hours_ratio" if "off_hours_ratio" in CLEAN_DF.columns else NUMERIC_COLUMNS[0]
#         y_col = "threat_score" if "threat_score" in CLEAN_DF.columns else NUMERIC_COLUMNS[min(1, len(NUMERIC_COLUMNS) - 1)]
#         eda_data["title"] = "Bivariate Analysis"
#         eda_data["description"] = f"Relationship between {x_col} and {y_col}."
#         eda_data["plot"] = make_scatter(CLEAN_DF, x_col, y_col, TARGET_COLUMN if TARGET_COLUMN in CLEAN_DF.columns else None)
#     elif eda_focus == "multivariate":
#         columns = [column for column in SUMMARY_DEFAULT_COLUMNS if column in CLEAN_DF.columns][:4]
#         if TARGET_COLUMN in CLEAN_DF.columns:
#             columns.append(TARGET_COLUMN)
#         columns = list(dict.fromkeys(columns))[:6]
#         eda_data["title"] = "Multivariate Analysis"
#         eda_data["description"] = "Correlation pattern across the most important engineered features."
#         eda_data["plot"] = make_heatmap(CLEAN_DF, columns, "Feature Correlation Matrix")
#     else:
#         target_corr = CLEAN_DF.corr(numeric_only=True)[TARGET_COLUMN].drop(TARGET_COLUMN).abs().sort_values(ascending=False).head(6)
#         eda_data["title"] = "Insights"
#         eda_data["description"] = "The strongest risk signals are shown below based on absolute correlation with the target."
#         eda_data["plot"] = make_bar(target_corr, "Top Signals Linked To Malicious Behaviour", "#b91c1c")
#         eda_data["insights"] = [
#             f"Highest average threat score: {round(float(CLEAN_DF['threat_score'].mean()), 3)}"
#             if "threat_score" in CLEAN_DF.columns
#             else "Threat score is not available.",
#             f"Malicious class share: {round(float(CLEAN_DF[TARGET_COLUMN].mean()) * 100, 2)}%"
#             if TARGET_COLUMN in CLEAN_DF.columns
#             else "Target column is not available.",
#             f"Most correlated signal: {target_corr.index[0].replace('_', ' ')} ({round(float(target_corr.iloc[0]), 3)})"
#             if not target_corr.empty
#             else "Correlation insight is not available.",
#         ]

#     if show_summary and summary_columns:
#         numeric_summary = CLEAN_DF[summary_columns].describe().round(3).reset_index()
#         eda_data["summary_table"] = numeric_summary.to_dict(orient="records")
#         eda_data["summary_headers"] = numeric_summary.columns.tolist()
#         eda_data["summary_plot"] = make_heatmap(CLEAN_DF, summary_columns[: min(6, len(summary_columns))], "Statistical Summary Correlation")
#         if len(summary_columns) == 1:
#             eda_data["summary_graph"] = make_histogram(CLEAN_DF[summary_columns[0]], f"{summary_columns[0].replace('_', ' ').title()} Summary View", "#0f766e")
#         else:
#             eda_data["summary_graph"] = make_scatter(CLEAN_DF, summary_columns[0], summary_columns[1], TARGET_COLUMN if TARGET_COLUMN in CLEAN_DF.columns else None)

#     return eda_data


# def build_hypothesis_view(test_name: str) -> Dict[str, object]:
#     if chi2_contingency is None or f_oneway is None or ttest_ind is None:
#         return {
#             "title": "Hypothesis Testing",
#             "description": "SciPy is required to run the requested tests.",
#             "result": None,
#             "plot": None,
#             "outliers": {"count": 0, "examples": [], "bounds": None},
#         }

#     if test_name == "chi_square":
#         feature = "late_exit_flag" if "late_exit_flag" in CLEAN_DF.columns else NUMERIC_COLUMNS[0]
#         contingency = pd.crosstab(CLEAN_DF[feature], CLEAN_DF[TARGET_COLUMN])
#         statistic, p_value, _, _ = chi2_contingency(contingency)
#         related_plot = make_bar(contingency.sum(axis=1), f"{feature.replace('_', ' ').title()} Category Count", "#7c3aed")
#         outliers = compute_outliers(CLEAN_DF["movement_anomaly"] if "movement_anomaly" in CLEAN_DF.columns else CLEAN_DF[NUMERIC_COLUMNS[0]])
#         return {
#             "title": "Chi-Square Test",
#             "description": f"Testing association between {feature} and {TARGET_COLUMN}. Chi-square statistic = {round(float(statistic), 4)}, p-value = {round(float(p_value), 4)}.",
#             "result": "Reject the null hypothesis." if p_value < 0.05 else "Fail to reject the null hypothesis.",
#             "plot": related_plot,
#             "outliers": outliers,
#         }

#     if test_name == "anova":
#         metric = "threat_score" if "threat_score" in CLEAN_DF.columns else NUMERIC_COLUMNS[0]
#         group_column = "employee_risk" if "employee_risk" in CLEAN_DF.columns else TARGET_COLUMN
#         grouped_series = [group[metric].dropna() for _, group in CLEAN_DF.groupby(group_column) if len(group[metric].dropna()) > 1]
#         statistic, p_value = f_oneway(*grouped_series)
#         filtered_df = CLEAN_DF[[group_column, metric]].copy()
#         return {
#             "title": "ANOVA",
#             "description": f"Comparing {metric} across {group_column} groups. F-statistic = {round(float(statistic), 4)}, p-value = {round(float(p_value), 4)}.",
#             "result": "Reject the null hypothesis." if p_value < 0.05 else "Fail to reject the null hypothesis.",
#             "plot": make_boxplot(filtered_df, group_column, metric, f"{metric.replace('_', ' ').title()} by {group_column.replace('_', ' ').title()}"),
#             "outliers": compute_outliers(filtered_df[metric]),
#         }

#     metric = "off_hours_ratio" if "off_hours_ratio" in CLEAN_DF.columns else NUMERIC_COLUMNS[0]
#     normal_group = CLEAN_DF[CLEAN_DF[TARGET_COLUMN] == 0][metric]
#     malicious_group = CLEAN_DF[CLEAN_DF[TARGET_COLUMN] == 1][metric]
#     statistic, p_value = ttest_ind(normal_group, malicious_group, equal_var=False, nan_policy="omit")
#     plot_df = CLEAN_DF[[TARGET_COLUMN, metric]].copy()
#     return {
#         "title": "T-Test",
#         "description": f"Comparing {metric} between normal and malicious groups. T-statistic = {round(float(statistic), 4)}, p-value = {round(float(p_value), 4)}.",
#         "result": "Reject the null hypothesis." if p_value < 0.05 else "Fail to reject the null hypothesis.",
#         "plot": make_boxplot(plot_df, TARGET_COLUMN, metric, f"{metric.replace('_', ' ').title()} by Class"),
#         "outliers": compute_outliers(plot_df[metric]),
#     }


# def build_forecasting_view() -> Dict[str, object]:
#     if "trip_day_number" not in CLEAN_DF.columns or "threat_score" not in CLEAN_DF.columns:
#         return {"available": False, "message": "Forecasting requires trip_day_number and threat_score columns."}

#     ts = CLEAN_DF.sort_values("trip_day_number").groupby("trip_day_number")["threat_score"].mean()
#     if ts.empty or len(ts) < 8:
#         return {"available": False, "message": "Not enough time points are available for forecasting."}

#     split_index = int(len(ts) * 0.8)
#     train = ts.iloc[:split_index]
#     test = ts.iloc[split_index:]

#     window = min(5, max(2, len(train) // 8))
#     train_rolling = train.rolling(window=window).mean()
#     moving_average_level = float(train_rolling.dropna().iloc[-1]) if not train_rolling.dropna().empty else float(train.iloc[-1])
#     forecast_ma = np.repeat(moving_average_level, len(test))

#     arima_forecast = None
#     arima_error = None
#     if ARIMA is not None:
#         try:
#             arima_model = ARIMA(train, order=(1, 1, 1))
#             arima_fit = arima_model.fit()
#             arima_forecast = np.asarray(arima_fit.forecast(steps=len(test)))
#         except Exception as exc:  # pragma: no cover
#             arima_error = str(exc)
#     else:
#         arima_error = "statsmodels is not installed."

#     mae_ma = round(float(np.mean(np.abs(test.values - forecast_ma))), 4)
#     rmse_ma = round(float(np.sqrt(np.mean((test.values - forecast_ma) ** 2))), 4)

#     mae_arima = None
#     rmse_arima = None
#     if arima_forecast is not None:
#         mae_arima = round(float(np.mean(np.abs(test.values - arima_forecast))), 4)
#         rmse_arima = round(float(np.sqrt(np.mean((test.values - arima_forecast) ** 2))), 4)

#     plot_theme()
#     fig1, ax1 = plt.subplots(figsize=(8, 4), facecolor="#fffaf3")
#     ax1.plot(ts.index, ts.values, color="#1d4ed8", linewidth=1.5, label="Threat Score")
#     ax1.plot(ts.index, ts.rolling(window=window).mean(), color="#f97316", linewidth=2, label="Rolling Mean")
#     ax1.set_title("Trend and Seasonality View", fontsize=14, fontweight="bold")
#     ax1.set_xlabel("Trip Day Number")
#     ax1.set_ylabel("Average Threat Score")
#     ax1.legend()

#     fig2, ax2 = plt.subplots(figsize=(8, 4), facecolor="#fffaf3")
#     ax2.plot(test.index, test.values, label="Actual", color="#111827", linewidth=2)
#     ax2.plot(test.index, forecast_ma, label="Moving Average", color="#0f766e", linewidth=2)
#     if arima_forecast is not None:
#         ax2.plot(test.index, arima_forecast, label="ARIMA", color="#b91c1c", linewidth=2)
#     ax2.set_title("Forecast on Test Data", fontsize=14, fontweight="bold")
#     ax2.set_xlabel("Trip Day Number")
#     ax2.set_ylabel("Threat Score")
#     ax2.legend()

#     conclusion = "Moving Average and ARIMA were both generated."
#     if mae_arima is not None and rmse_arima is not None:
#         better_model = "ARIMA" if rmse_arima < rmse_ma else "Moving Average"
#         conclusion = f"{better_model} performs better on the test set based on RMSE comparison."
#     elif arima_error:
#         conclusion = f"ARIMA could not be completed, so only Moving Average forecasting is available. Reason: {arima_error}"

#     return {
#         "available": True,
#         "series_points": int(len(ts)),
#         "train_size": int(len(train)),
#         "test_size": int(len(test)),
#         "window": int(window),
#         "mae_ma": mae_ma,
#         "rmse_ma": rmse_ma,
#         "mae_arima": mae_arima,
#         "rmse_arima": rmse_arima,
#         "trend_plot": encode_plot(fig1),
#         "forecast_plot": encode_plot(fig2),
#         "conclusion": conclusion,
#     }


# FORECASTING_VIEW = build_forecasting_view()


# @app.route("/open-powerbi")
# def open_powerbi():
#     return send_file(POWER_BI_PATH, as_attachment=True, download_name=os.path.basename(POWER_BI_PATH))


# @app.route("/", methods=["GET", "POST"])
# def home():
#     active_tab = request.values.get("active_tab", "landing")

#     selected_columns = request.values.getlist("selected_columns")
#     selected_columns = [column for column in selected_columns if column in CLEAN_DF.columns]
#     if not selected_columns:
#         selected_columns = DISPLAY_COLUMNS

#     dataset_action = request.values.get("dataset_action", "view")
#     dataset_mode = request.values.get("dataset_mode", "raw")
#     if dataset_action == "reset":
#         selected_columns = DISPLAY_COLUMNS
#         dataset_mode = "raw"
#     elif dataset_action == "clean":
#         dataset_mode = "cleaned"
#         active_tab = "dataset-explorer"

#     current_df = CLEAN_DF if dataset_mode == "cleaned" else RAW_DF
#     preview_columns = [column for column in selected_columns if column in current_df.columns]
#     if not preview_columns:
#         preview_columns = DISPLAY_COLUMNS

#     eda_focus = request.values.get("eda_focus", "univariate")
#     summary_columns = request.values.getlist("summary_columns")
#     summary_columns = [column for column in summary_columns if column in NUMERIC_COLUMNS]
#     if not summary_columns:
#         summary_columns = SUMMARY_DEFAULT_COLUMNS
#     show_summary = request.values.get("show_summary") == "1"

#     hypothesis_test = request.values.get("hypothesis_test", "t_test")

#     prediction_result = None
#     if request.method == "POST" and request.form.get("form_name") == "prediction":
#         active_tab = "prediction"
#         prediction_result = build_prediction_result(request.form)

#     eda_view = build_eda_view(eda_focus, summary_columns, show_summary)
#     hypothesis_view = build_hypothesis_view(hypothesis_test)

#     context = {
#         "active_tab": active_tab,
#         "power_bi_url": "/open-powerbi",
#         "dataset_mode": dataset_mode,
#         "available_columns": CLEAN_DF.columns.tolist(),
#         "numeric_columns": NUMERIC_COLUMNS,
#         "selected_columns": preview_columns,
#         "dataset_preview": get_preview(current_df, preview_columns),
#         "dataset_headers": preview_columns,
#         "cleaning": CLEANING_RESULT,
#         "eda_focus": eda_focus,
#         "eda_view": eda_view,
#         "summary_columns": summary_columns,
#         "show_summary": show_summary,
#         "hypothesis_test": hypothesis_test,
#         "hypothesis_view": hypothesis_view,
#         "prediction_fields": PREDICTION_FORM_FIELDS,
#         "prediction_defaults": {
#             field: round(float(CLEAN_DF[field].median()), 3) if field in CLEAN_DF.columns else 0
#             for field in PREDICTION_FORM_FIELDS
#         },
#         "prediction_result": prediction_result,
#         "model_metrics": MODEL_METRICS,
#         "forecasting": FORECASTING_VIEW,
#         "overview": {
#             "rows": int(CLEAN_DF.shape[0]),
#             "columns": int(CLEAN_DF.shape[1]),
#             "avg_threat": round(float(CLEAN_DF["threat_score"].mean()), 3) if "threat_score" in CLEAN_DF.columns else None,
#             "total_activity": round(float(CLEAN_DF["total_activity"].sum()), 2) if "total_activity" in CLEAN_DF.columns else None,
#             "malicious_rate": round(float(CLEAN_DF[TARGET_COLUMN].mean()) * 100, 2) if TARGET_COLUMN in CLEAN_DF.columns else None,
#         },
#     }
#     return render_template("index.html", **context)


# if __name__ == "__main__":
#     app.run(debug=True)




"""
Insider Threat Detection — Flask Application
"""
import os
import base64
import io
from typing import Dict, List, Optional

import matplotlib
import plotly.express as px
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

try:
    import pickle
except ImportError:
    pickle = None

try:
    import seaborn as sns
except ImportError:
    sns = None

try:
    from scipy.stats import chi2_contingency, f_oneway, ttest_ind
except ImportError:
    chi2_contingency = f_oneway = ttest_ind = None

try:
    from statsmodels.tsa.arima.model import ARIMA
except ImportError:
    ARIMA = None


# ── App setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "feature_engineered_balanced.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

TARGET_COLUMN = "is_malicious"
CORE_PREDICTION_FIELDS = [
    "total_activity", "off_hours_ratio", "burn_ratio",
    "movement_anomaly", "employee_risk", "activity_per_entry", #"threat_score",
]

# ── Load & clean data ──────────────────────────────────────────────────────────
RAW_DF = pd.read_csv(DATASET_PATH)

def clean_dataset(df: pd.DataFrame) -> Dict:
    cleaned = df.copy()
    missing_before = int(cleaned.isna().sum().sum())
    duplicates_before = int(cleaned.duplicated().sum())

    for col in cleaned.columns:
        if cleaned[col].isna().sum() == 0:
            continue
        if pd.api.types.is_numeric_dtype(cleaned[col]):
            cleaned[col].fillna(cleaned[col].median(), inplace=True)
        else:
            mode = cleaned[col].mode(dropna=True)
            cleaned[col].fillna(mode.iloc[0] if not mode.empty else "Unknown", inplace=True)

    cleaned = cleaned.drop_duplicates().copy()
    for col in cleaned.columns:
        if cleaned[col].dtype == bool:
            cleaned[col] = cleaned[col].astype(int)

    return {
        "df": cleaned,
        "steps": [
            {"title": "Remove Null Values", "detail": f"Missing values reduced from {missing_before} to {int(cleaned.isna().sum().sum())}."},
            {"title": "Remove Duplicates", "detail": f"Duplicate rows reduced from {duplicates_before} to {int(cleaned.duplicated().sum())}."},
            {"title": "Normalize Data Types", "detail": "Boolean indicators converted to numeric flags."},
        ],
        "missing_before": missing_before,
        "missing_after": int(cleaned.isna().sum().sum()),
        "duplicates_before": duplicates_before,
        "duplicates_after": int(cleaned.duplicated().sum()),
    }

CLEANING_RESULT = clean_dataset(RAW_DF)
CLEAN_DF = CLEANING_RESULT["df"]
NUMERIC_COLUMNS = CLEAN_DF.select_dtypes(include=[np.number]).columns.tolist()
DISPLAY_COLUMNS = [c for c in NUMERIC_COLUMNS if c != TARGET_COLUMN][:10]
SUMMARY_DEFAULT_COLUMNS = [c for c in ["threat_score", "total_activity", "off_hours_ratio", "movement_anomaly"] if c in CLEAN_DF.columns]


# ── Load model ─────────────────────────────────────────────────────────────────
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

MODEL = load_model()
MODEL_FEATURES = list(getattr(MODEL, "feature_names_in_", CORE_PREDICTION_FIELDS)) if MODEL else CORE_PREDICTION_FIELDS
PREDICTION_FORM_FIELDS = [f for f in CORE_PREDICTION_FIELDS if f in CLEAN_DF.columns]


# ── Plot helpers ───────────────────────────────────────────────────────────────
def encode_plot(fig) -> str:
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def _theme():
    plt.style.use("dark_background")
    plt.rcParams.update({
        "axes.facecolor": "#0e1318",
        "figure.facecolor": "#0e1318",
        "axes.edgecolor": "#1e2a36",
        "axes.labelcolor": "#94a3b8",
        "xtick.color": "#64748b",
        "ytick.color": "#64748b",
        "grid.color": "#1e2a36",
        "text.color": "#e2e8f0",
    })

def make_histogram(series: pd.Series, title: str, color: str = "#e84545") -> str:
    _theme()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(series.dropna(), bins=30, color=color, edgecolor="#090c10", alpha=0.85)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel(series.name.replace("_", " ").title())
    ax.set_ylabel("Frequency")
    return encode_plot(fig)

def make_scatter(df: pd.DataFrame, x_col: str, y_col: str, hue_col: Optional[str] = None) -> str:
    _theme()
    fig, ax = plt.subplots(figsize=(8, 4))
    if sns and hue_col and hue_col in df.columns:
        sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue_col, palette=["#00d4aa", "#e84545"], alpha=0.6, ax=ax)
    else:
        ax.scatter(df[x_col], df[y_col], color="#f7931a", alpha=0.4, s=10)
    ax.set_title(f"{x_col.replace('_',' ').title()} vs {y_col.replace('_',' ').title()}", fontsize=14, fontweight="bold", pad=14)
    return encode_plot(fig)

def make_heatmap(df: pd.DataFrame, columns: List[str], title: str) -> str:
    _theme()
    fig, ax = plt.subplots(figsize=(8, 5))
    corr = df[columns].corr(numeric_only=True)
    if sns:
        sns.heatmap(corr, cmap="RdYlGn", annot=True, fmt=".2f", ax=ax, linewidths=0.5, linecolor="#0e1318")
    else:
        im = ax.imshow(corr, cmap="RdYlGn")
        fig.colorbar(im, ax=ax)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=14)
    return encode_plot(fig)

def make_bar(values: pd.Series, title: str, color: str = "#e84545") -> str:
    _theme()
    fig, ax = plt.subplots(figsize=(8, 4))
    values.plot(kind="bar", color=color, ax=ax, edgecolor="#090c10")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=14)
    ax.set_ylabel("Value")
    ax.tick_params(axis="x", rotation=35)
    return encode_plot(fig)

def make_boxplot(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> str:
    _theme()
    fig, ax = plt.subplots(figsize=(8, 4))
    if sns:
        sns.boxplot(data=df, x=x_col, y=y_col, palette=["#00d4aa", "#e84545"], ax=ax)
    else:
        grouped = [g[y_col].dropna().values for _, g in df.groupby(x_col)]
        ax.boxplot(grouped)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=14)
    return encode_plot(fig)

def compute_outliers(series: pd.Series) -> Dict:
    s = series.dropna()
    if s.empty:
        return {"count": 0, "examples": [], "bounds": None}
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    out = s[(s < lo) | (s > hi)]
    return {"count": int(out.shape[0]), "examples": [round(v, 3) for v in out.head(6).tolist()], "bounds": (round(lo, 3), round(hi, 3))}


# ── EDA builder ────────────────────────────────────────────────────────────────
def build_eda_view(focus: str, summary_columns: List[str], show_summary: bool) -> Dict:
    d: Dict = {"focus": focus}
    if focus == "univariate":
        col = "threat_score" if "threat_score" in CLEAN_DF.columns else NUMERIC_COLUMNS[0]
        d["title"] = "Univariate Analysis"
        d["description"] = f"Distribution of {col.replace('_', ' ')}."
        d["plot"] = make_histogram(CLEAN_DF[col], f"{col.replace('_',' ').title()} Distribution")
    elif focus == "bivariate":
        x, y = ("off_hours_ratio" if "off_hours_ratio" in CLEAN_DF.columns else NUMERIC_COLUMNS[0],
                 "threat_score" if "threat_score" in CLEAN_DF.columns else NUMERIC_COLUMNS[min(1, len(NUMERIC_COLUMNS)-1)])
        d["title"] = "Bivariate Analysis"
        d["description"] = f"Relationship between {x} and {y}, colored by threat class."
        d["plot"] = make_scatter(CLEAN_DF, x, y, TARGET_COLUMN)
    elif focus == "multivariate":
        cols = [c for c in SUMMARY_DEFAULT_COLUMNS if c in CLEAN_DF.columns][:4]
        if TARGET_COLUMN in CLEAN_DF.columns:
            cols.append(TARGET_COLUMN)
        cols = list(dict.fromkeys(cols))[:6]
        d["title"] = "Multivariate Analysis"
        d["description"] = "Correlation heatmap across key engineered features."
        d["plot"] = make_heatmap(CLEAN_DF, cols, "Feature Correlation Matrix")
    else:
        target_corr = CLEAN_DF.corr(numeric_only=True)[TARGET_COLUMN].drop(TARGET_COLUMN).abs().sort_values(ascending=False).head(6)
        d["title"] = "Insights"
        d["description"] = "Strongest predictive signals ranked by absolute correlation with the malicious target."
        d["plot"] = make_bar(target_corr, "Top Signals — Correlation with Malicious Behaviour", "#e84545")
        d["insights"] = [
            f"Mean threat score: {round(float(CLEAN_DF['threat_score'].mean()), 3)}" if "threat_score" in CLEAN_DF.columns else "Threat score N/A.",
            f"Malicious class share: {round(float(CLEAN_DF[TARGET_COLUMN].mean()) * 100, 2)}%",
            f"Most correlated signal: {target_corr.index[0].replace('_',' ')} (r={round(float(target_corr.iloc[0]), 3)})" if not target_corr.empty else "",
        ]
    if show_summary and summary_columns:
        num_summary = CLEAN_DF[summary_columns].describe().round(3).reset_index()
        d["summary_table"] = num_summary.to_dict(orient="records")
        d["summary_headers"] = num_summary.columns.tolist()
        d["summary_plot"] = make_heatmap(CLEAN_DF, summary_columns[:6], "Summary Correlation")
    return d


# ── Hypothesis builder ─────────────────────────────────────────────────────────
def build_hypothesis_view(test_name: str) -> Dict:
    if not all([chi2_contingency, f_oneway, ttest_ind]):
        return {"title": "Hypothesis Testing", "description": "SciPy required.", "result": None, "plot": None, "outliers": None}

    if test_name == "chi_square":
        feat = "late_exit_flag" if "late_exit_flag" in CLEAN_DF.columns else NUMERIC_COLUMNS[0]
        ct = pd.crosstab(CLEAN_DF[feat], CLEAN_DF[TARGET_COLUMN])
        stat, p, _, _ = chi2_contingency(ct)
        out = compute_outliers(CLEAN_DF["movement_anomaly"] if "movement_anomaly" in CLEAN_DF.columns else CLEAN_DF[NUMERIC_COLUMNS[0]])
        return {"title": "Chi-Square Test",
                "description": f"Association between {feat} and {TARGET_COLUMN}. χ²={round(float(stat),4)}, p={round(float(p),4)}.",
                "result": "Reject the null hypothesis." if p < 0.05 else "Fail to reject the null hypothesis.",
                "plot": make_bar(ct.sum(axis=1), f"{feat.replace('_',' ').title()} Category Count", "#7c3aed"),
                "outliers": out}

    if test_name == "anova":
        metric = "threat_score" if "threat_score" in CLEAN_DF.columns else NUMERIC_COLUMNS[0]
        group_col = "employee_risk" if "employee_risk" in CLEAN_DF.columns else TARGET_COLUMN
        groups = [g[metric].dropna() for _, g in CLEAN_DF.groupby(group_col) if len(g[metric].dropna()) > 1]
        stat, p = f_oneway(*groups)
        fdf = CLEAN_DF[[group_col, metric]].copy()
        return {"title": "ANOVA",
                "description": f"Comparing {metric} across {group_col} groups. F={round(float(stat),4)}, p={round(float(p),4)}.",
                "result": "Reject the null hypothesis." if p < 0.05 else "Fail to reject the null hypothesis.",
                "plot": make_boxplot(fdf, group_col, metric, f"{metric.replace('_',' ').title()} by {group_col.replace('_',' ').title()}"),
                "outliers": compute_outliers(fdf[metric])}

    # default: t-test
    metric = "off_hours_ratio" if "off_hours_ratio" in CLEAN_DF.columns else NUMERIC_COLUMNS[0]
    g0 = CLEAN_DF[CLEAN_DF[TARGET_COLUMN] == 0][metric]
    g1 = CLEAN_DF[CLEAN_DF[TARGET_COLUMN] == 1][metric]
    stat, p = ttest_ind(g0, g1, equal_var=False, nan_policy="omit")
    pdf = CLEAN_DF[[TARGET_COLUMN, metric]].copy()
    return {"title": "T-Test",
            "description": f"Comparing {metric} between normal and malicious groups. t={round(float(stat),4)}, p={round(float(p),4)}.",
            "result": "Reject the null hypothesis." if p < 0.05 else "Fail to reject the null hypothesis.",
            "plot": make_boxplot(pdf, TARGET_COLUMN, metric, f"{metric.replace('_',' ').title()} by Class"),
            "outliers": compute_outliers(pdf[metric])}


# ── Model evaluation ───────────────────────────────────────────────────────────
def evaluate_model() -> Dict:
    if MODEL is None or TARGET_COLUMN not in CLEAN_DF.columns:
        return {"available": False, "message": "Model not available."}
    feat_cols = [c for c in MODEL_FEATURES if c in CLEAN_DF.columns]
    if not feat_cols:
        return {"available": False, "message": "Feature mismatch."}
    try:
        X, y = CLEAN_DF[feat_cols], CLEAN_DF[TARGET_COLUMN]
        _, Xt, _, yt = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() > 1 else None)
        yp = MODEL.predict(Xt)
        cm = confusion_matrix(yt, yp)
        _theme()
        fig, ax = plt.subplots(figsize=(5, 4))
        if sns:
            sns.heatmap(cm, annot=True, fmt="d", cmap="Reds", cbar=False, ax=ax)
        else:
            im = ax.imshow(cm, cmap="Reds"); fig.colorbar(im, ax=ax)
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax.text(j, i, str(cm[i, j]), ha="center", va="center")
        ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold")
        ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
        return {"available": True,
                "accuracy": round(float(accuracy_score(yt, yp)), 4),
                "precision": round(float(precision_score(yt, yp, zero_division=0)), 4),
                "recall": round(float(recall_score(yt, yp, zero_division=0)), 4),
                "f1_score": round(float(f1_score(yt, yp, zero_division=0)), 4),
                "plot": encode_plot(fig)}
    except Exception as e:
        return {"available": False, "message": str(e)}


# ── Prediction ─────────────────────────────────────────────────────────────────
def build_prediction_result(form_values: Dict) -> Optional[Dict]:
    if MODEL is None:
        return None
    medians = CLEAN_DF.median(numeric_only=True)
    payload = {f: float(medians.get(f, 0.0)) for f in MODEL_FEATURES}
    user_snap = {}
    for field in PREDICTION_FORM_FIELDS:
        raw = str(form_values.get(field, "")).strip()
        payload[field] = float(raw) if raw else float(medians.get(field, 0.0))
        user_snap[field] = payload[field]

    frame = pd.DataFrame([payload])
    prediction = int(MODEL.predict(frame)[0])
    prob = None
    if hasattr(MODEL, "predict_proba"):
        try:
            prob = float(MODEL.predict_proba(frame)[0][1])
        except Exception:
            pass

    drivers = sorted(
        [(f, user_snap[f] - float(medians.get(f, 0))) for f in PREDICTION_FORM_FIELDS if abs(user_snap[f] - float(medians.get(f, 0))) > 0],
        key=lambda x: abs(x[1]), reverse=True
    )
    outcome = "Malicious / High Risk" if prediction == 1 else "Normal / Lower Risk"
    parts = [f"The model predicts: {outcome}."]
    if prob is not None:
        parts.append(f"Estimated threat probability: {round(prob * 100, 2)}%.")
    if drivers:
        top = ", ".join(f"{f.replace('_',' ')} ({'above' if d > 0 else 'below'} baseline)" for f, d in drivers[:3])
        parts.append(f"Main drivers: {top}.")

    return {"prediction": prediction, "outcome": outcome, "probability": prob,
            "explanation": " ".join(parts), "inputs": user_snap}


# ── Forecasting ────────────────────────────────────────────────────────────────
def build_forecasting_view() -> Dict:
    if "trip_day_number" not in CLEAN_DF.columns or "threat_score" not in CLEAN_DF.columns:
        return {"available": False, "message": "Requires trip_day_number and threat_score columns."}
    ts = CLEAN_DF.sort_values("trip_day_number").groupby("trip_day_number")["threat_score"].mean()
    if len(ts) < 8:
        return {"available": False, "message": "Not enough time points for forecasting."}

    split = int(len(ts) * 0.8)
    train, test = ts.iloc[:split], ts.iloc[split:]
    window = min(5, max(2, len(train) // 8))
    ma_level = float(train.rolling(window).mean().dropna().iloc[-1])
    forecast_ma = np.repeat(ma_level, len(test))

    arima_forecast = arima_error = None
    if ARIMA:
        try:
            arima_forecast = np.asarray(ARIMA(train, order=(1,1,1)).fit().forecast(steps=len(test)))
        except Exception as e:
            arima_error = str(e)
    else:
        arima_error = "statsmodels not installed."

    mae_ma = round(float(np.mean(np.abs(test.values - forecast_ma))), 4)
    rmse_ma = round(float(np.sqrt(np.mean((test.values - forecast_ma)**2))), 4)
    mae_arima = rmse_arima = None
    if arima_forecast is not None:
        mae_arima = round(float(np.mean(np.abs(test.values - arima_forecast))), 4)
        rmse_arima = round(float(np.sqrt(np.mean((test.values - arima_forecast)**2))), 4)

    _theme()
    fig1, ax1 = plt.subplots(figsize=(9, 4))
    ax1.plot(ts.index, ts.values, color="#e2e8f0", lw=1.5, label="Threat Score")
    ax1.plot(ts.index, ts.rolling(window).mean(), color="#f7931a", lw=2, label="Rolling Mean")
    ax1.set_title("Trend & Seasonality", fontsize=14, fontweight="bold"); ax1.legend()

    fig2, ax2 = plt.subplots(figsize=(9, 4))
    ax2.plot(test.index, test.values, label="Actual", color="#e2e8f0", lw=2)
    ax2.plot(test.index, forecast_ma, label="Moving Average", color="#00d4aa", lw=2)
    if arima_forecast is not None:
        ax2.plot(test.index, arima_forecast, label="ARIMA", color="#e84545", lw=2)
    ax2.set_title("Forecast vs Actual", fontsize=14, fontweight="bold"); ax2.legend()

    conclusion = "ARIMA and Moving Average forecasts generated."
    if rmse_arima is not None:
        conclusion = f"{'ARIMA' if rmse_arima < rmse_ma else 'Moving Average'} performs better on the test set (lower RMSE)."
    elif arima_error:
        conclusion = f"Only Moving Average forecast available. ARIMA skipped: {arima_error}"

    return {"available": True, "series_points": int(len(ts)), "train_size": int(len(train)),
            "test_size": int(len(test)), "window": int(window),
            "mae_ma": mae_ma, "rmse_ma": rmse_ma, "mae_arima": mae_arima, "rmse_arima": rmse_arima,
            "trend_plot": encode_plot(fig1), "forecast_plot": encode_plot(fig2), "conclusion": conclusion}


# ── Pre-compute ────────────────────────────────────────────────────────────────
MODEL_METRICS = evaluate_model()
FORECASTING_VIEW = build_forecasting_view()

OVERVIEW = {
    "rows": int(CLEAN_DF.shape[0]),
    "columns": int(CLEAN_DF.shape[1]),
    "avg_threat": round(float(CLEAN_DF["threat_score"].mean()), 3) if "threat_score" in CLEAN_DF.columns else None,
    "total_activity": round(float(CLEAN_DF["total_activity"].sum()), 2) if "total_activity" in CLEAN_DF.columns else None,
    "malicious_rate": round(float(CLEAN_DF[TARGET_COLUMN].mean()) * 100, 2) if TARGET_COLUMN in CLEAN_DF.columns else None,
}


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def home():
    focus = request.values.get("eda_focus", "univariate")
    summary_cols = [c for c in request.values.getlist("summary_columns") if c in NUMERIC_COLUMNS] or SUMMARY_DEFAULT_COLUMNS
    show_summary = request.values.get("show_summary") == "1"
    hypothesis_test = request.values.get("hypothesis_test", "t_test")
    selected_cols = [c for c in request.values.getlist("selected_columns") if c in CLEAN_DF.columns] or DISPLAY_COLUMNS
    preview_cols = [c for c in selected_cols if c in CLEAN_DF.columns] or DISPLAY_COLUMNS

    prediction_result = None
    active_tab = request.values.get("active_tab", "overview")
    if request.method == "POST" and request.form.get("form_name") == "prediction":
        active_tab = "prediction"
        prediction_result = build_prediction_result(request.form)

    eda_view = build_eda_view(focus, summary_cols, show_summary)
    hypothesis_view = build_hypothesis_view(hypothesis_test)
    preview_df = CLEAN_DF[preview_cols].head(15).replace({np.nan: None})

    context = {
        "active_tab": active_tab,
        "overview": OVERVIEW,
        "available_columns": CLEAN_DF.columns.tolist(),
        "numeric_columns": NUMERIC_COLUMNS,
        "selected_columns": preview_cols,
        "dataset_headers": preview_cols,
        "dataset_preview": preview_df.to_dict(orient="records"),
        "cleaning": CLEANING_RESULT,
        "eda_focus": focus,
        "eda_view": eda_view,
        "summary_columns": summary_cols,
        "show_summary": show_summary,
        "hypothesis_test": hypothesis_test,
        "hypothesis_view": hypothesis_view,
        "prediction_fields": PREDICTION_FORM_FIELDS,
        "prediction_defaults": {f: round(float(CLEAN_DF[f].median()), 3) if f in CLEAN_DF.columns else 0 for f in PREDICTION_FORM_FIELDS},
        "prediction_result": prediction_result,
        "model_metrics": MODEL_METRICS,
        "forecasting": FORECASTING_VIEW,
    }
    return render_template("index.html", **context)


@app.route("/api/eda")
def api_eda():
    focus = request.args.get("focus", "univariate")
    view = build_eda_view(focus, SUMMARY_DEFAULT_COLUMNS, False)
    return jsonify({"title": view.get("title"), "description": view.get("description"),
                    "plot_html": f'<img src="data:image/png;base64,{view["plot"]}" style="width:100%" />' if view.get("plot") else ""})


@app.route("/api/hypothesis")
def api_hypothesis():
    test = request.args.get("test", "t_test")
    view = build_hypothesis_view(test)
    if view.get("outliers") and view["outliers"].get("bounds"):
        view["outliers"]["bounds"] = list(view["outliers"]["bounds"])
    return jsonify(view)


@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(force=True) or {}
    result = build_prediction_result(data)
    if result is None:
        return jsonify({"error": "Model not available"}), 503
    return jsonify(result)


@app.route("/api/dataset")
def api_dataset():
    cols = request.args.getlist("col")
    cols = [c for c in cols if c in CLEAN_DF.columns][:10] or DISPLAY_COLUMNS
    rows = CLEAN_DF[cols].head(20).replace({np.nan: None}).to_dict(orient="records")
    return jsonify({"columns": cols, "rows": rows})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)