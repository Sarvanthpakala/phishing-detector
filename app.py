"""
app.py
------
Flask backend for the Real-Time AI/ML-Based Phishing Detection and
Prevention System.

Routes
------
Pages:   /  /about  /scanner  /dashboard  /analytics  /contact
API:     POST /api/predict        -> single URL prediction
         GET  /api/history        -> recent prediction history
         GET  /api/metadata       -> model metrics / feature importance
         POST /api/contact        -> contact form (stored in-memory)
"""

import os
import time
import uuid
from collections import deque

from flask import Flask, jsonify, render_template, request

from predict import predict_url, get_metadata, ModelNotTrainedError

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# In-memory prediction history (most-recent-first). Fine for a single
# grading/demo instance; swap for a real DB in production.
HISTORY = deque(maxlen=200)


def _record_history(result: dict):
    HISTORY.appendleft({
        "id": str(uuid.uuid4())[:8],
        "url": result["url"],
        "prediction": result["prediction"],
        "confidence": result["confidence"],
        "threat_level": result["threat_level"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route("/")
def home():
    return render_template("index.html", active="home")


@app.route("/about")
def about():
    return render_template("about.html", active="about")


@app.route("/scanner")
def scanner():
    return render_template("scanner.html", active="scanner")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active="dashboard")


@app.route("/analytics")
def analytics():
    return render_template("analytics.html", active="analytics")


@app.route("/contact")
def contact():
    return render_template("contact.html", active="contact")


@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "Please provide a 'url' field."}), 400
    if len(url) > 2048:
        return jsonify({"error": "URL is too long."}), 400

    try:
        result = predict_url(url, check_live_redirects=False)
    except ModelNotTrainedError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 500

    _record_history(result)
    return jsonify(result), 200


@app.route("/api/history", methods=["GET"])
def api_history():
    limit = request.args.get("limit", default=20, type=int)
    return jsonify({"history": list(HISTORY)[:limit], "total": len(HISTORY)})


@app.route("/api/metadata", methods=["GET"])
def api_metadata():
    try:
        meta = get_metadata()
    except ModelNotTrainedError as e:
        return jsonify({"error": str(e)}), 503
    return jsonify(meta)


@app.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    if not (name and email and message):
        return jsonify({"error": "Name, email and message are all required."}), 400
    # Demo project: acknowledge receipt without persisting to disk/DB.
    return jsonify({"status": "received", "message": "Thanks — we'll get back to you shortly."}), 200


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
