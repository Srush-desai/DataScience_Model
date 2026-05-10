from __future__ import annotations

import argparse
import os
import sys
from typing import List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CORE_PREDICTION_FIELDS = [
    "total_activity",
    "off_hours_ratio",
    "burn_ratio",
    "movement_anomaly",
    "employee_risk",
    "activity_per_entry",
]


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Insider Threat model (RandomForest).")
    parser.add_argument(
        "--dataset",
        default=os.path.join(BASE_DIR, "feature_engineered_balanced.csv"),
        help="Path to training CSV.",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(BASE_DIR, "model.pkl"),
        help="Where to write the trained model.",
    )
    parser.add_argument("--target", default="is_malicious", help="Target column name.")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio.")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed.")
    parser.add_argument("--n-estimators", type=int, default=200, help="Number of trees.")
    parser.add_argument(
        "--all-features",
        action="store_true",
        help="Train on all columns except target (default: core feature subset).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        import pandas as pd  # type: ignore
    except Exception:
        _die("Missing dependency: pandas. Install with: python -m pip install -r requirements.txt")

    try:
        from sklearn.ensemble import RandomForestClassifier  # type: ignore
        from sklearn.metrics import accuracy_score  # type: ignore
        from sklearn.model_selection import train_test_split  # type: ignore
    except Exception:
        _die(
            "Missing dependency: scikit-learn. Install with: python -m pip install -r requirements.txt"
        )

    joblib = None
    try:
        import joblib as _joblib  # type: ignore

        joblib = _joblib
    except Exception:
        joblib = None

    if not os.path.exists(args.dataset):
        _die(f"Dataset not found: {args.dataset}")

    df = pd.read_csv(args.dataset)
    if args.target not in df.columns:
        _die(f"Target column '{args.target}' not found in dataset.")

    if args.all_features:
        feature_columns: List[str] = [c for c in df.columns if c != args.target]
    else:
        feature_columns = [c for c in CORE_PREDICTION_FIELDS if c in df.columns]
        missing = [c for c in CORE_PREDICTION_FIELDS if c not in df.columns]
        if missing:
            print(f"Warning: missing core features in dataset: {missing}", file=sys.stderr)
        if not feature_columns:
            _die(
                "No core features found in dataset. Re-run with --all-features to train on all columns."
            )

    X = df[feature_columns]
    y = df[args.target]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y if y.nunique(dropna=True) > 1 else None,
    )

    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        random_state=args.random_state,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    if joblib is not None:
        joblib.dump(model, args.output, compress=3)
        saver = "joblib"
    else:
        import pickle

        with open(args.output, "wb") as f:
            pickle.dump(model, f)
        saver = "pickle"

    print(f"Model trained successfully. accuracy={acc:.4f}")
    print(f"Saved: {args.output} ({saver})")
    preview = feature_columns[:20]
    print(
        f"Features used ({len(feature_columns)}): {preview}{'...' if len(feature_columns) > 20 else ''}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

