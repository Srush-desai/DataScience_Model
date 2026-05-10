"""
Insider Threat Detection — Flask Application

Designed to be "error-less":
- Starts even when optional dependencies are missing.
- Shows clear messages for missing deps / model load issues / dataset issues.
- Avoids model feature-mismatch by using the model's `feature_names_in_` when available.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    from flask import Flask, jsonify, render_template, request
except Exception:
    print(
        "Missing dependency: flask. Install with: python -m pip install -r requirements.txt",
        file=sys.stderr,
    )
    raise SystemExit(2)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "feature_engineered_balanced.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

TARGET_COLUMN = "is_malicious"
CORE_PREDICTION_FIELDS = [
    "total_activity",
    "off_hours_ratio",
    "burn_ratio",
    "movement_anomaly",
    "employee_risk",
    "activity_per_entry",
]

missing_required: List[str] = []
missing_optional: List[str] = []

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
    missing_required.append("numpy")

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None
    missing_optional.append("pandas")

try:
    import plotly.express as px
except Exception:  # pragma: no cover
    px = None
    missing_optional.append("plotly")

try:
    from scipy.stats import f_oneway, ttest_ind
except Exception:  # pragma: no cover
    f_oneway = None
    ttest_ind = None
    missing_optional.append("scipy")

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None

try:
    import pickle
except Exception:  # pragma: no cover
    pickle = None


app = Flask(__name__)


def _to_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def load_dataset() -> Tuple[Optional["pd.DataFrame"], Dict[str, Any]]:
    if pd is None:
        return None, {
            "available": False,
            "message": "Dataset view disabled (missing dependency: pandas).",
        }
    if not os.path.exists(DATASET_PATH):
        return None, {
            "available": False,
            "message": f"Dataset file not found: {DATASET_PATH}",
        }
    try:
        raw_df = pd.read_csv(DATASET_PATH)
    except Exception as exc:  # pragma: no cover
        return None, {"available": False, "message": f"Failed to read dataset: {exc}"}

    cleaned = raw_df.copy()

    # Ensure unique column names (Plotly + correlation matrices require it)
    duplicate_cols = cleaned.columns[cleaned.columns.duplicated()].tolist()
    renamed_columns = 0
    if duplicate_cols:
        seen: Dict[str, int] = {}
        new_cols: List[str] = []
        for col in cleaned.columns.tolist():
            key = str(col)
            if key not in seen:
                seen[key] = 1
                new_cols.append(key)
                continue
            seen[key] += 1
            renamed_columns += 1
            new_cols.append(f"{key}__{seen[key]}")
        cleaned.columns = new_cols

    missing_before = int(cleaned.isna().sum().sum())
    duplicates_before = int(cleaned.duplicated().sum())

    for column in cleaned.columns:
        if cleaned[column].isna().sum() == 0:
            continue
        if pd.api.types.is_numeric_dtype(cleaned[column]):
            cleaned[column] = cleaned[column].fillna(cleaned[column].median())
        else:
            cleaned[column] = cleaned[column].fillna("Unknown")

    cleaned = cleaned.drop_duplicates().copy()

    duplicates_after = int(cleaned.duplicated().sum())
    missing_after = int(cleaned.isna().sum().sum())

    return cleaned, {
        "available": True,
        "steps": [
            {
                "title": "Remove Null Values",
                "detail": f"Missing values reduced from {missing_before} to {missing_after}.",
            },
            {
                "title": "Remove Duplicates",
                "detail": f"Duplicate rows reduced from {duplicates_before} to {duplicates_after}.",
            },
            *(
                [
                    {
                        "title": "Fix Duplicate Columns",
                        "detail": f"Renamed {renamed_columns} duplicate column(s) to be unique (example: {duplicate_cols[0]} -> {duplicate_cols[0]}__2).",
                    }
                ]
                if renamed_columns
                else []
            ),
        ],
        "missing_before": missing_before,
        "missing_after": missing_after,
        "duplicates_before": duplicates_before,
        "duplicates_after": duplicates_after,
    }


def load_model() -> Tuple[Optional[Any], Dict[str, Any]]:
    if not os.path.exists(MODEL_PATH):
        return None, {"available": False, "message": f"Model file not found: {MODEL_PATH}"}

    errors: List[str] = []
    if joblib is not None:
        try:
            return joblib.load(MODEL_PATH), {"available": True, "message": "Loaded via joblib."}
        except Exception as exc:
            errors.append(f"joblib: {exc}")

    if pickle is not None:
        try:
            with open(MODEL_PATH, "rb") as f:
                return pickle.load(f), {"available": True, "message": "Loaded via pickle."}
        except Exception as exc:
            errors.append(f"pickle: {exc}")

    detail = "; ".join(errors) if errors else "No loader available (install joblib)."
    return None, {"available": False, "message": f"Failed to load model. {detail}"}


def infer_model_features(model: Any) -> List[str]:
    names = getattr(model, "feature_names_in_", None)
    if names is not None:
        return [str(name) for name in names]
    return CORE_PREDICTION_FIELDS[:]


DATASET_DF, CLEANING_INFO = load_dataset()
MODEL, MODEL_INFO = load_model()

MODEL_FEATURES = infer_model_features(MODEL) if MODEL is not None else CORE_PREDICTION_FIELDS[:]
FORM_FIELDS = [f for f in CORE_PREDICTION_FIELDS if f in MODEL_FEATURES]
if not FORM_FIELDS:
    FORM_FIELDS = MODEL_FEATURES[: min(10, len(MODEL_FEATURES))]

_MODEL_METRICS_CACHE: Optional[Dict[str, Any]] = None
_FORECASTING_CACHE: Optional[Dict[str, Any]] = None


def _format_p_value(p_value: Any) -> str:
    try:
        p = float(p_value)
    except Exception:
        return "p = N/A"
    if p < 0.0001:
        return "p < 0.0001"
    return f"p = {p:.4f}"


def compute_outliers_iqr(series: Any) -> Dict[str, Any]:
    if pd is None:
        return {"count": 0, "bounds": None, "examples": []}
    try:
        s = pd.Series(series).dropna()
    except Exception:
        return {"count": 0, "bounds": None, "examples": []}

    if s.empty:
        return {"count": 0, "bounds": None, "examples": []}

    try:
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        iqr = q3 - q1
        lo = q1 - 1.5 * iqr
        hi = q3 + 1.5 * iqr
        outliers = s[(s < lo) | (s > hi)]
        examples = outliers.head(6).tolist()
        examples_out: List[Any] = []
        for v in examples:
            try:
                examples_out.append(round(float(v), 3))
            except Exception:
                examples_out.append(v)
        return {
            "count": int(outliers.shape[0]),
            "bounds": (round(lo, 3), round(hi, 3)),
            "examples": examples_out,
        }
    except Exception:
        return {"count": 0, "bounds": None, "examples": []}


def _plotly_disabled(reason: str) -> str:
    return f"<p class='muted'>EDA/plot disabled ({reason}).</p>"


def _plotly_html(fig: Any) -> str:
    """
    Render Plotly figures in environments without internet access by embedding plotly.js inline.
    """
    try:
        return fig.to_html(full_html=False, include_plotlyjs="inline")
    except TypeError:
        return fig.to_html(full_html=False)


def _make_unique_names(names: List[Any]) -> List[str]:
    seen: Dict[str, int] = {}
    out: List[str] = []
    for name in names:
        key = str(name)
        if key not in seen:
            seen[key] = 1
            out.append(key)
            continue
        seen[key] += 1
        out.append(f"{key}__{seen[key]}")
    return out


def make_histogram_html(series: Any, *, title: str = "Distribution") -> str:
    if px is None:
        return _plotly_disabled("missing dependency: plotly")
    try:
        fig = px.histogram(
            series,
            x=getattr(series, "name", "value"),
            nbins=30,
            template="plotly_dark",
            title=title,
        )
        return _plotly_html(fig)
    except Exception as exc:  # pragma: no cover
        return f"<p class='muted'>EDA plot unavailable: {exc}</p>"


def build_eda_view(focus: str, summary_columns: List[str], show_summary: bool) -> Dict[str, Any]:
    if DATASET_DF is None:
        return {
            "title": "EDA",
            "description": CLEANING_INFO.get("message", "Dataset not available."),
            "plot": f"<p class='muted'>{CLEANING_INFO.get('message', 'Dataset not available.')}</p>",
            "summary_table": None,
            "summary_headers": None,
            "summary_graph_html": None,
            "summary_plot_html": None,
        }

    numeric_columns = DATASET_DF.select_dtypes(include="number").columns.tolist()
    numeric_columns = [c for c in numeric_columns if c != TARGET_COLUMN]
    if not numeric_columns:
        return {
            "title": "EDA",
            "description": "No numeric columns available for analysis.",
            "plot": "<p class='muted'>No numeric columns available.</p>",
            "summary_table": None,
            "summary_headers": None,
            "summary_graph_html": None,
            "summary_plot_html": None,
        }

    focus = (focus or "univariate").lower()
    if focus not in {"univariate", "bivariate", "multivariate", "insights"}:
        focus = "univariate"

    metric = "threat_score" if "threat_score" in DATASET_DF.columns else numeric_columns[0]
    x_default = "off_hours_ratio" if "off_hours_ratio" in DATASET_DF.columns else numeric_columns[0]

    plot_html: str
    insights: Optional[List[str]] = None

    if px is None:
        plot_html = _plotly_disabled("missing dependency: plotly")
    else:
        try:
            if focus == "univariate":
                plot_html = make_histogram_html(DATASET_DF[metric], title=f"Distribution of {metric}")
            elif focus == "bivariate":
                y_col = metric
                if TARGET_COLUMN in DATASET_DF.columns:
                    fig = px.scatter(
                        DATASET_DF,
                        x=x_default,
                        y=y_col,
                        color=TARGET_COLUMN,
                        template="plotly_dark",
                        title=f"{y_col} vs {x_default} (colored by {TARGET_COLUMN})",
                    )
                else:
                    fig = px.scatter(
                        DATASET_DF,
                        x=x_default,
                        y=y_col,
                        template="plotly_dark",
                        title=f"{y_col} vs {x_default}",
                    )
                plot_html = _plotly_html(fig)
            elif focus == "multivariate":
                cols = []
                for candidate in ["total_activity", "off_hours_ratio", "burn_ratio", "movement_anomaly", metric]:
                    if candidate in DATASET_DF.columns:
                        cols.append(candidate)
                cols = list(dict.fromkeys(cols))
                cols = (cols + numeric_columns)[: min(8, len(numeric_columns))]
                corr = DATASET_DF[cols].corr(numeric_only=True)
                # Plotly requires unique axis labels; guard against duplicate source columns.
                corr.columns = _make_unique_names(list(corr.columns))
                corr.index = _make_unique_names(list(corr.index))
                fig = px.imshow(
                    corr,
                    text_auto=True,
                    template="plotly_dark",
                    title="Correlation Heatmap (selected numeric features)",
                )
                plot_html = _plotly_html(fig)
            else:
                corr_all = DATASET_DF.corr(numeric_only=True)
                if TARGET_COLUMN in corr_all.columns:
                    target_corr = (
                        corr_all[TARGET_COLUMN]
                        .drop(TARGET_COLUMN, errors="ignore")
                        .abs()
                        .sort_values(ascending=False)
                        .head(8)
                    )
                    fig = px.bar(
                        target_corr.reset_index(),
                        x="index",
                        y=TARGET_COLUMN,
                        template="plotly_dark",
                        title=f"Top signals by |correlation| with {TARGET_COLUMN}",
                        labels={"index": "Feature", TARGET_COLUMN: "|corr|"},
                    )
                    plot_html = _plotly_html(fig)
                    insights = []
                    try:
                        insights.append(f"Dataset rows: {int(DATASET_DF.shape[0])}, columns: {int(DATASET_DF.shape[1])}.")
                    except Exception:
                        pass
                    if metric in DATASET_DF.columns:
                        insights.append(f"Average {metric}: {round(float(DATASET_DF[metric].mean()), 3)}.")
                    insights.append(
                        f"Malicious rate: {round(float(DATASET_DF[TARGET_COLUMN].mean()) * 100, 2)}%."
                    )
                    if not target_corr.empty:
                        insights.append(
                            f"Strongest signal: {str(target_corr.index[0])} (|corr|={round(float(target_corr.iloc[0]), 3)})."
                        )
                else:
                    plot_html = "<p class='muted'>Insights unavailable (target column missing for correlation).</p>"
                    insights = [
                        "Insights are based on correlation with the target label.",
                        f"Target column missing: {TARGET_COLUMN}.",
                    ]
        except Exception as exc:
            plot_html = f"<p class='muted'>EDA plot unavailable: {exc}</p>"

    view: Dict[str, Any] = {
        "title": {
            "univariate": "Univariate Analysis",
            "bivariate": "Bivariate Analysis",
            "multivariate": "Multivariate Analysis",
            "insights": "Insights",
        }[focus],
        "description": {
            "univariate": f"Distribution of {metric}.",
            "bivariate": f"Relationship between {x_default} and {metric}.",
            "multivariate": "How numeric features move together (correlation).",
            "insights": "Simple takeaways for non-technical readers.",
        }[focus],
        "plot": plot_html,
        "insights": insights,
        "summary_table": None,
        "summary_headers": None,
        "summary_graph_html": None,
        "summary_plot_html": None,
    }

    if show_summary and summary_columns and pd is not None:
        cols = [c for c in summary_columns if c in DATASET_DF.columns]
        cols = [c for c in cols if c != TARGET_COLUMN]
        if cols:
            try:
                summary_df = DATASET_DF[cols].describe().round(3).reset_index()
                view["summary_table"] = summary_df.to_dict(orient="records")
                view["summary_headers"] = summary_df.columns.tolist()

                if px is not None:
                    corr = DATASET_DF[cols[:8]].corr(numeric_only=True)
                    corr.columns = _make_unique_names(list(corr.columns))
                    corr.index = _make_unique_names(list(corr.index))
                    view["summary_plot_html"] = px.imshow(
                        corr, text_auto=True, template="plotly_dark", title="Summary Correlation Heatmap"
                    )
                    view["summary_plot_html"] = _plotly_html(view["summary_plot_html"])

                    means = DATASET_DF[cols[:8]].mean(numeric_only=True).sort_values(ascending=False)
                    view["summary_graph_html"] = px.bar(
                        means.reset_index(),
                        x="index",
                        y=0,
                        template="plotly_dark",
                        title="Average values (selected features)",
                        labels={"index": "Feature", 0: "Mean"},
                    )
                    view["summary_graph_html"] = _plotly_html(view["summary_graph_html"])
            except Exception:
                pass

    return view


def build_hypothesis_view(test_name: str) -> Dict[str, Any]:
    def empty_outliers() -> Dict[str, Any]:
        return {"count": 0, "bounds": None, "examples": []}

    if DATASET_DF is None:
        return {
            "title": "Hypothesis Testing",
            "description": "Dataset not available.",
            "result": "Not available",
            "outliers": empty_outliers(),
            "plot_html": None,
        }
    if ttest_ind is None or f_oneway is None:
        return {
            "title": "Hypothesis Testing",
            "description": "Missing dependency: scipy.",
            "result": "Not available",
            "outliers": empty_outliers(),
            "plot_html": None,
        }

    numeric_columns = DATASET_DF.select_dtypes(include="number").columns.tolist()
    if not numeric_columns or TARGET_COLUMN not in DATASET_DF.columns:
        return {
            "title": "Hypothesis Testing",
            "description": "Not enough numeric data.",
            "result": "Not available",
            "outliers": empty_outliers(),
            "plot_html": None,
        }

    alpha = 0.05
    metric = "threat_score" if "threat_score" in numeric_columns else numeric_columns[0]
    outliers = compute_outliers_iqr(DATASET_DF[metric])

    plot_html = None
    if px is not None:
        try:
            plot_html = px.box(
                DATASET_DF,
                x=TARGET_COLUMN,
                y=metric,
                template="plotly_dark",
                title=f"{metric} by {TARGET_COLUMN}",
            )
            plot_html = _plotly_html(plot_html)
        except Exception:
            plot_html = None

    if test_name == "anova":
        # Prefer a real multi-category feature for ANOVA (otherwise it becomes equivalent to the binary t-test view)
        candidate_features: List[str] = []
        for c in ["employee_risk", "employee_department", "employee_classification"]:
            if c in DATASET_DF.columns:
                candidate_features.append(c)
        # Fall back to any non-numeric column with >= 3 categories
        if pd is not None:
            for c in DATASET_DF.columns:
                if c in candidate_features or c == TARGET_COLUMN:
                    continue
                try:
                    if not pd.api.types.is_numeric_dtype(DATASET_DF[c]):
                        if int(DATASET_DF[c].nunique(dropna=True)) >= 3:
                            candidate_features.append(c)
                except Exception:
                    continue

        anova_feature = candidate_features[0] if candidate_features else None
        if anova_feature is None:
            return {
                "title": "ANOVA",
                "description": "No suitable multi-category feature found for ANOVA.",
                "result": "Not available",
                "outliers": outliers,
                "plot_html": plot_html,
            }

        groups = []
        for _, g in DATASET_DF.groupby(anova_feature):
            values = g[metric].dropna()
            if values.shape[0] >= 2:
                groups.append(values)
        if len(groups) < 2:
            return {
                "title": "ANOVA",
                "description": "Not enough data per category to run ANOVA.",
                "result": "Not available",
                "outliers": outliers,
                "plot_html": plot_html,
            }

        stat, p = f_oneway(*groups)
        decision = "Reject H0" if float(p) < alpha else "Fail to reject H0"
        why = (
            f"{decision} because {_format_p_value(p)} is {'<' if float(p) < alpha else '≥'} {alpha}."
        )

        anova_plot_html = plot_html
        if px is not None:
            try:
                fig = px.box(
                    DATASET_DF,
                    x=anova_feature,
                    y=metric,
                    template="plotly_dark",
                    title=f"{metric} by {anova_feature}",
                )
                anova_plot_html = _plotly_html(fig)
            except Exception:
                anova_plot_html = plot_html

        return {
            "title": "ANOVA",
            "description": f"H0: the mean of {metric} is equal across categories of {anova_feature}. "
            f"(ANOVA compares between-group vs within-group variance to test mean differences.) "
            f"Test: F = {round(float(stat), 4)}, {_format_p_value(p)}, α = {alpha}.",
            "result": why,
            "outliers": outliers,
            "plot_html": anova_plot_html,
            "p_value": float(p),
        }

    g0 = DATASET_DF[DATASET_DF[TARGET_COLUMN] == 0][metric].dropna()
    g1 = DATASET_DF[DATASET_DF[TARGET_COLUMN] == 1][metric].dropna()
    if len(g0) == 0 or len(g1) == 0:
        return {
            "title": "T-Test",
            "description": "Not enough data",
            "result": "Not available",
            "outliers": outliers,
            "plot_html": plot_html,
        }

    stat, p = ttest_ind(g0, g1, equal_var=False, nan_policy="omit")
    decision = "Reject H0" if float(p) < alpha else "Fail to reject H0"
    why = f"{decision} because {_format_p_value(p)} is {'<' if float(p) < alpha else '≥'} {alpha}."
    return {
        "title": "T-Test",
        "description": f"H0: the mean of {metric} is equal for {TARGET_COLUMN}=0 vs {TARGET_COLUMN}=1. "
        f"Test (Welch): t = {round(float(stat), 4)}, {_format_p_value(p)}, α = {alpha}.",
        "result": why,
        "outliers": outliers,
        "plot_html": plot_html,
        "p_value": float(p),
    }


def build_chi_square_view() -> Dict[str, Any]:
    def empty_outliers() -> Dict[str, Any]:
        return {"count": 0, "bounds": None, "examples": []}

    if DATASET_DF is None:
        return {
            "title": "Chi-Square",
            "description": "Dataset not available.",
            "result": "Not available",
            "outliers": empty_outliers(),
            "plot_html": None,
        }

    chi2_contingency = None
    try:
        from scipy.stats import chi2_contingency as _chi2_contingency  # type: ignore

        chi2_contingency = _chi2_contingency
    except Exception:
        chi2_contingency = None

    if chi2_contingency is None:
        return {
            "title": "Chi-Square",
            "description": "Missing dependency: scipy.",
            "result": "Not available",
            "outliers": empty_outliers(),
            "plot_html": None,
        }

    if TARGET_COLUMN not in DATASET_DF.columns:
        return {
            "title": "Chi-Square",
            "description": f"Target column not found: {TARGET_COLUMN}",
            "result": "Not available",
            "outliers": empty_outliers(),
            "plot_html": None,
        }

    candidate_columns = [
        c
        for c in ["entry_during_weekend", "late_exit_flag", "is_contractor", "has_foreign_citizenship"]
        if c in DATASET_DF.columns
    ]
    if not candidate_columns:
        return {
            "title": "Chi-Square",
            "description": "No suitable categorical/binary feature found for Chi-Square test.",
            "result": "Not available",
            "outliers": empty_outliers(),
            "plot_html": None,
        }

    feature = candidate_columns[0]
    contingency = DATASET_DF.groupby([feature, TARGET_COLUMN]).size().unstack(fill_value=0)
    chi2, p, dof, _expected = chi2_contingency(contingency.values)

    plot_html = None
    if px is not None:
        try:
            fig = px.imshow(
                contingency,
                text_auto=True,
                title=f"Contingency: {feature} vs {TARGET_COLUMN}",
                template="plotly_dark",
            )
            plot_html = _plotly_html(fig)
        except Exception:
            plot_html = None

    alpha = 0.05
    decision = "Reject H0" if float(p) < alpha else "Fail to reject H0"
    why = f"{decision} because {_format_p_value(p)} is {'<' if float(p) < alpha else '≥'} {alpha}."

    # Outliers: show for a common risk-like numeric metric if present
    out_metric = None
    for candidate in ["threat_score", "off_hours_ratio", "movement_anomaly", "total_activity"]:
        if candidate in DATASET_DF.columns:
            out_metric = candidate
            break
    outliers = compute_outliers_iqr(DATASET_DF[out_metric]) if out_metric else empty_outliers()

    return {
        "title": "Chi-Square",
        "description": f"H0: {feature} and {TARGET_COLUMN} are independent. "
        f"Test: χ² = {round(float(chi2), 4)}, dof = {int(dof)}, {_format_p_value(p)}, α = {alpha}.",
        "result": why,
        "outliers": outliers,
        "plot_html": plot_html,
        "p_value": float(p),
        "chi2": float(chi2),
    }


def compute_model_metrics() -> Dict[str, Any]:
    global _MODEL_METRICS_CACHE
    if _MODEL_METRICS_CACHE is not None:
        return _MODEL_METRICS_CACHE

    if MODEL is None:
        _MODEL_METRICS_CACHE = {"available": False, "message": MODEL_INFO.get("message", "Model not loaded.")}
        return _MODEL_METRICS_CACHE
    if DATASET_DF is None:
        _MODEL_METRICS_CACHE = {"available": False, "message": CLEANING_INFO.get("message", "Dataset not available.")}
        return _MODEL_METRICS_CACHE
    if pd is None or np is None:
        _MODEL_METRICS_CACHE = {"available": False, "message": "Missing dependencies: pandas/numpy."}
        return _MODEL_METRICS_CACHE
    if TARGET_COLUMN not in DATASET_DF.columns:
        _MODEL_METRICS_CACHE = {"available": False, "message": f"Target column not found: {TARGET_COLUMN}"}
        return _MODEL_METRICS_CACHE

    try:
        from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, accuracy_score  # type: ignore
        from sklearn.model_selection import train_test_split  # type: ignore
    except Exception:
        _MODEL_METRICS_CACHE = {"available": False, "message": "Missing dependency: scikit-learn."}
        return _MODEL_METRICS_CACHE

    df = DATASET_DF
    X_full = df.reindex(columns=MODEL_FEATURES, fill_value=0.0)
    y_full = df[TARGET_COLUMN]

    if len(df) > 5000:
        X_full = X_full.sample(n=5000, random_state=42)
        y_full = y_full.loc[X_full.index]

    X_train, X_test, y_train, y_test = train_test_split(
        X_full,
        y_full,
        test_size=0.2,
        random_state=42,
        stratify=y_full if y_full.nunique(dropna=True) > 1 else None,
    )
    try:
        y_pred = MODEL.predict(X_test)
    except Exception as exc:
        _MODEL_METRICS_CACHE = {"available": False, "message": f"Model prediction failed: {exc}"}
        return _MODEL_METRICS_CACHE

    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    if px is None:
        plot_html = "<p class='muted'>Confusion matrix plot disabled (missing dependency: plotly).</p>"
    else:
        try:
            fig = px.imshow(
                cm,
                text_auto=True,
                template="plotly_dark",
                title="Confusion Matrix",
                labels={"x": "Predicted", "y": "Actual", "color": "Count"},
            )
            fig.update_xaxes(tickmode="array", tickvals=[0, 1], ticktext=["Normal", "Malicious"])
            fig.update_yaxes(tickmode="array", tickvals=[0, 1], ticktext=["Normal", "Malicious"])
            plot_html = _plotly_html(fig)
        except Exception:
            plot_html = "<p class='muted'>Confusion matrix plot unavailable.</p>"

    _MODEL_METRICS_CACHE = {
        "available": True,
        "message": "OK",
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "plot_html": plot_html,
        "plot": None,
    }
    return _MODEL_METRICS_CACHE


def compute_forecasting() -> Dict[str, Any]:
    global _FORECASTING_CACHE
    if _FORECASTING_CACHE is not None:
        return _FORECASTING_CACHE

    if DATASET_DF is None:
        _FORECASTING_CACHE = {"available": False, "message": CLEANING_INFO.get("message", "Dataset not available.")}
        return _FORECASTING_CACHE
    if pd is None:
        _FORECASTING_CACHE = {"available": False, "message": "Missing dependency: pandas."}
        return _FORECASTING_CACHE

    if "trip_day_number" not in DATASET_DF.columns:
        _FORECASTING_CACHE = {
            "available": False,
            "message": "No time-like column found (expected: trip_day_number).",
        }
        return _FORECASTING_CACHE

    # Prefer a meaningful continuous signal if available
    if "threat_score" in DATASET_DF.columns:
        value_col = "threat_score"
    elif "total_activity" in DATASET_DF.columns:
        value_col = "total_activity"
    else:
        value_col = TARGET_COLUMN
    if value_col not in DATASET_DF.columns:
        _FORECASTING_CACHE = {"available": False, "message": "No series column available for forecasting."}
        return _FORECASTING_CACHE

    series = (
        DATASET_DF.groupby("trip_day_number")[value_col]
        .mean()
        .sort_index()
        .astype(float)
    )
    series_points = int(series.shape[0])
    if series_points < 10:
        _FORECASTING_CACHE = {"available": False, "message": "Not enough points for forecasting."}
        return _FORECASTING_CACHE

    split = max(2, int(series_points * 0.2))
    train = series.iloc[:-split]
    test = series.iloc[-split:]

    # Simple baseline: last rolling-mean value
    window = max(2, min(7, int(max(3, train.shape[0] // 8))))
    ma_train = train.rolling(window=window, min_periods=1).mean()
    last_ma = float(ma_train.iloc[-1])
    ma_forecast = pd.Series([last_ma] * len(test), index=test.index)

    mae_ma = float((test - ma_forecast).abs().mean())
    rmse_ma = float((((test - ma_forecast) ** 2).mean()) ** 0.5)

    arima_forecast = None
    mae_arima = None
    rmse_arima = None
    arima_available = False
    arima_message = None
    try:
        from statsmodels.tsa.arima.model import ARIMA  # type: ignore

        arima_available = True
        try:
            order = (1, 1, 1)
            fit = ARIMA(train, order=order).fit()
            arima_forecast = fit.forecast(steps=len(test))
            arima_forecast.index = test.index
            mae_arima = float((test - arima_forecast).abs().mean())
            rmse_arima = float((((test - arima_forecast) ** 2).mean()) ** 0.5)
        except Exception as exc:
            arima_message = f"ARIMA failed: {exc}"
            arima_forecast = None
            mae_arima = None
            rmse_arima = None
    except Exception:
        arima_available = False

    if px is None:
        trend_plot_html = "<p class='muted'>Forecast plots disabled (missing dependency: plotly).</p>"
        forecast_plot_html = "<p class='muted'>Forecast plots disabled (missing dependency: plotly).</p>"
    else:
        try:
            trend_df = pd.DataFrame({"trip_day_number": series.index, "value": series.values})
            trend_plot_html = px.line(
                trend_df,
                x="trip_day_number",
                y="value",
                template="plotly_dark",
                title=f"Trend: mean({value_col}) over trip_day_number",
            )
            trend_plot_html = _plotly_html(trend_plot_html)

            fc_df = pd.DataFrame(
                {
                    "trip_day_number": test.index,
                    "actual": test.values,
                    "ma_forecast": ma_forecast.values,
                    "arima_forecast": arima_forecast.values if arima_forecast is not None else None,
                }
            )
            y_cols = ["actual", "ma_forecast"]
            if arima_forecast is not None:
                y_cols.append("arima_forecast")

            fig = px.line(
                fc_df,
                x="trip_day_number",
                y=y_cols,
                template="plotly_dark",
                title="Forecast Comparison (MA vs ARIMA)",
            )
            forecast_plot_html = _plotly_html(fig)
        except Exception:
            trend_plot_html = "<p class='muted'>Trend plot unavailable.</p>"
            forecast_plot_html = "<p class='muted'>Forecast plot unavailable.</p>"

    conclusion_parts: List[str] = [
        f"Forecast target: mean({value_col}) by trip_day_number.",
        f"Baseline Moving Average (window={window}) RMSE={round(rmse_ma,4)}.",
    ]
    if arima_available:
        if arima_message is not None:
            conclusion_parts.append(f"ARIMA skipped: {arima_message}")
        elif arima_forecast is None or rmse_arima is None:
            conclusion_parts.append("ARIMA could not be computed for this series.")
        else:
            conclusion_parts.append(f"ARIMA RMSE={round(float(rmse_arima),4)}.")
            best = "ARIMA" if float(rmse_arima) < rmse_ma else "Moving Average"
            conclusion_parts.append(f"Better on the test split (lower RMSE): {best}.")
    else:
        conclusion_parts.append("ARIMA unavailable (install statsmodels).")

    conclusion = " ".join(conclusion_parts)

    _FORECASTING_CACHE = {
        "available": True,
        "message": "OK",
        "series_points": series_points,
        "train_size": int(train.shape[0]),
        "test_size": int(test.shape[0]),
        "window": window,
        "mae_ma": round(mae_ma, 4),
        "rmse_ma": round(rmse_ma, 4),
        "mae_arima": round(mae_arima, 4) if mae_arima is not None else None,
        "rmse_arima": round(rmse_arima, 4) if rmse_arima is not None else None,
        "trend_plot_html": trend_plot_html,
        "forecast_plot_html": forecast_plot_html,
        "trend_plot": None,
        "forecast_plot": None,
        "conclusion": conclusion,
    }
    return _FORECASTING_CACHE


def build_prediction_result(values: Dict[str, Any]) -> Dict[str, Any]:
    if MODEL is None:
        return {
            "prediction": 0,
            "probability": None,
            "outcome": "Model Not Loaded",
            "explanation": MODEL_INFO.get("message", "Model file missing or incompatible."),
            "inputs": {f: _to_float(values.get(f, 0)) for f in FORM_FIELDS},
        }

    row = [_to_float(values.get(feature, 0)) for feature in MODEL_FEATURES]
    X = [row] if np is None else np.asarray([row], dtype=float)

    try:
        pred = int(MODEL.predict(X)[0])
        probability = None
        if hasattr(MODEL, "predict_proba"):
            try:
                probability = float(MODEL.predict_proba(X)[0][1])
            except Exception:
                probability = None
        return {
            "prediction": pred,
            "probability": probability,
            "outcome": "Malicious" if pred == 1 else "Normal",
            "explanation": "Prediction generated successfully.",
            "inputs": {f: _to_float(values.get(f, 0)) for f in FORM_FIELDS},
        }
    except Exception as exc:
        return {
            "prediction": 0,
            "probability": None,
            "outcome": "Prediction Error",
            "explanation": str(exc),
            "inputs": {f: _to_float(values.get(f, 0)) for f in FORM_FIELDS},
        }


@app.route("/", methods=["GET", "POST"])
def home():
    prediction_result = None
    if request.method == "POST":
        prediction_result = build_prediction_result(request.form.to_dict())

    active_tab = request.values.get("active_tab", request.args.get("active_tab", "landing"))
    hypothesis_test = request.args.get("hypothesis_test", "t_test")
    eda_focus = request.args.get("eda_focus", request.values.get("eda_focus", "univariate"))
    show_summary = str(request.args.get("show_summary", request.values.get("show_summary", ""))).strip() in {
        "1",
        "true",
        "True",
        "yes",
        "on",
    }
    summary_columns = request.args.getlist("summary_columns")

    if DATASET_DF is not None:
        numeric_columns = DATASET_DF.select_dtypes(include="number").columns.tolist()
        display_columns = [c for c in numeric_columns if c != TARGET_COLUMN][:10]
        metric_col = (
            "threat_score"
            if "threat_score" in numeric_columns
            else (numeric_columns[0] if numeric_columns else None)
        )

        avg_metric = round(float(DATASET_DF[metric_col].mean()), 3) if metric_col else 0.0
        malicious_rate = (
            round(float(DATASET_DF[TARGET_COLUMN].mean()) * 100, 2)
            if TARGET_COLUMN in DATASET_DF.columns
            else 0.0
        )

        dataset_preview = (
            DATASET_DF[display_columns].head(10).to_dict(orient="records") if display_columns else []
        )
    else:
        numeric_columns = []
        display_columns = []
        avg_metric = 0.0
        malicious_rate = 0.0
        dataset_preview = []

    eda_view = build_eda_view(eda_focus, summary_columns, show_summary)

    context = {
        "active_tab": active_tab,
        "overview": {
            "rows": int(DATASET_DF.shape[0]) if DATASET_DF is not None else 0,
            "columns": int(DATASET_DF.shape[1]) if DATASET_DF is not None else 0,
            "avg_threat": avg_metric,
            "malicious_rate": malicious_rate,
        },
        "available_columns": DATASET_DF.columns.tolist() if DATASET_DF is not None else [],
        "selected_columns": display_columns,
        "dataset_headers": display_columns,
        "dataset_preview": dataset_preview,
        "dataset_mode": "cleaned" if CLEANING_INFO.get("available") else "raw",
        "cleaning": CLEANING_INFO,
        "eda_focus": eda_focus,
        "eda_view": eda_view,
        "numeric_columns": numeric_columns,
        "summary_columns": summary_columns,
        "show_summary": show_summary,
        "hypothesis_test": hypothesis_test,
        "hypothesis_view": (
            build_chi_square_view()
            if hypothesis_test == "chi_square"
            else build_hypothesis_view("anova" if hypothesis_test == "anova" else "t_test")
        ),
        "prediction_fields": FORM_FIELDS,
        "prediction_defaults": {f: 0 for f in FORM_FIELDS},
        "prediction_result": prediction_result,
        "model_metrics": compute_model_metrics(),
        "forecasting": compute_forecasting(),
        "power_bi_url": "#",
        "dependency_status": {
            "missing_required": missing_required,
            "missing_optional": missing_optional,
        },
    }
    return render_template("index.html", **context)


@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(force=True) or {}
    result = build_prediction_result(data)
    return jsonify(result)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "ok": True,
            "model": MODEL_INFO,
            "dataset": CLEANING_INFO if isinstance(CLEANING_INFO, dict) else {},
            "missing_required": missing_required,
            "missing_optional": missing_optional,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
