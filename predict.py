"""
predict.py
----------
Loads the persisted model + scaler + metadata once, then exposes
`predict_url()` for app.py (and for standalone CLI use).
"""

import json
import os

import joblib
import numpy as np
import pandas as pd

from feature_extractor import extract_features, explain_features, FEATURE_NAMES

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, "models")

_model = None
_scaler = None
_metadata = None


class ModelNotTrainedError(RuntimeError):
    pass


def _load():
    global _model, _scaler, _metadata
    model_path = os.path.join(MODELS_DIR, "best_model.pkl")
    scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
    meta_path = os.path.join(MODELS_DIR, "metadata.json")

    if not (os.path.exists(model_path) and os.path.exists(scaler_path)):
        raise ModelNotTrainedError(
            "No trained model found. Run `python generate_dataset.py` "
            "then `python train_model.py` before starting the server."
        )

    _model = joblib.load(model_path)
    _scaler = joblib.load(scaler_path)
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            _metadata = json.load(f)
    else:
        _metadata = {}


def get_metadata() -> dict:
    if _metadata is None:
        _load()
    return _metadata


def threat_level(confidence: float, label: str) -> str:
    if label == "safe":
        return "Low"
    if confidence >= 0.85:
        return "Critical"
    if confidence >= 0.65:
        return "High"
    if confidence >= 0.45:
        return "Medium"
    return "Low"


def predict_url(url: str, check_live_redirects: bool = False) -> dict:
    """
    Full pipeline for a single URL: extract features -> scale -> predict.
    Returns a JSON-serialisable dict ready for the API / dashboard.
    """
    if _model is None or _scaler is None:
        _load()

    features = extract_features(url, check_live_redirects=check_live_redirects)
    vector = pd.DataFrame([[features[name] for name in FEATURE_NAMES]], columns=FEATURE_NAMES)
    scaled = _scaler.transform(vector)

    pred = int(_model.predict(scaled)[0])
    label = "phishing" if pred == 1 else "safe"

    if hasattr(_model, "predict_proba"):
        proba = _model.predict_proba(scaled)[0]
        confidence = float(proba[pred])
        safe_prob, phishing_prob = float(proba[0]), float(proba[1])
    else:
        confidence = 1.0
        safe_prob, phishing_prob = (1.0, 0.0) if label == "safe" else (0.0, 1.0)

    reasons = explain_features(features)

    return {
        "url": url,
        "prediction": "Phishing" if label == "phishing" else "Safe",
        "label": label,
        "confidence": round(confidence * 100, 2),
        "probability": {
            "safe": round(safe_prob * 100, 2),
            "phishing": round(phishing_prob * 100, 2),
        },
        "threat_level": threat_level(confidence, label),
        "features": features,
        "reasons": reasons,
        "model_used": get_metadata().get("best_model", "Unknown"),
    }


if __name__ == "__main__":
    import sys
    test_url = sys.argv[1] if len(sys.argv) > 1 else "http://192.168.1.1/paypal-secure-login/verify.php"
    result = predict_url(test_url)
    print(json.dumps(result, indent=2))
