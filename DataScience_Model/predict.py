from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _to_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def load_model(model_path: str) -> Any:
    if not os.path.exists(model_path):
        _die(f"Model not found: {model_path}")

    errors: List[str] = []
    try:
        import joblib  # type: ignore

        return joblib.load(model_path)
    except Exception as exc:
        errors.append(f"joblib: {exc}")

    try:
        import pickle

        with open(model_path, "rb") as f:
            return pickle.load(f)
    except Exception as exc:
        errors.append(f"pickle: {exc}")

    _die("Failed to load model. " + "; ".join(errors))
    raise AssertionError("unreachable")


def parse_payload(args: argparse.Namespace) -> Dict[str, Any]:
    if args.json is not None:
        try:
            payload = json.loads(args.json)
        except json.JSONDecodeError as exc:
            _die(f"--json is not valid JSON: {exc}")
        if not isinstance(payload, dict):
            _die("--json must be a JSON object (dictionary).")
        return payload

    if args.json_file is not None:
        if not os.path.exists(args.json_file):
            _die(f"JSON file not found: {args.json_file}")
        with open(args.json_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if not isinstance(payload, dict):
            _die("--json-file must contain a JSON object (dictionary).")
        return payload

    _die("Provide either --json or --json-file.")
    raise AssertionError("unreachable")


def infer_features(model: Any, payload: Dict[str, Any]) -> List[str]:
    names = getattr(model, "feature_names_in_", None)
    if names is not None:
        return [str(name) for name in names]
    return sorted(payload.keys())


def predict(model: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import numpy as np  # type: ignore
    except Exception:
        np = None

    features = infer_features(model, payload)
    row = [_to_float(payload.get(feature, 0)) for feature in features]
    X = [row] if np is None else np.asarray([row], dtype=float)

    pred = int(model.predict(X)[0])
    probability = None
    if hasattr(model, "predict_proba"):
        try:
            probability = float(model.predict_proba(X)[0][1])
        except Exception:
            probability = None

    return {
        "prediction": pred,
        "probability": probability,
        "outcome": "Malicious" if pred == 1 else "Normal",
        "features_used": features,
        "inputs": {k: _to_float(payload.get(k, 0)) for k in features},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single prediction using model.pkl")
    parser.add_argument(
        "--model",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl"),
        help="Path to model.pkl",
    )
    parser.add_argument("--json", help="JSON string with feature values.")
    parser.add_argument("--json-file", help="Path to JSON file with feature values.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = parse_payload(args)
    model = load_model(args.model)
    result = predict(model, payload)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

