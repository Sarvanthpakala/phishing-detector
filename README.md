# SENTRA — Real-Time AI/ML-Based Phishing Detection and Prevention System

SENTRA is a full-stack, AI/ML-powered phishing detection console. Paste any
URL and it extracts 15 lexical/structural features, scores it with the
best-performing of eight benchmarked machine-learning models, and returns a
verdict with a confidence score, threat level, and plain-English explanation
— all through a portfolio-quality dashboard UI.

---

## Features

- **Real-time URL scanning** — paste a link, get Safe/Phishing + confidence in under a second
- **Explainable AI output** — every verdict is backed by human-readable reasons, not just a score
- **8 ML algorithms benchmarked** — Logistic Regression, Decision Tree, Random Forest, KNN, SVM,
  Naive Bayes, XGBoost, LightGBM — best model auto-selected by F1 score
- **15 engineered features** — URL length, entropy, subdomain depth, keyword density, IP hosting,
  shortener detection, and more
- **Live analytics dashboard** — scan history, KPI cards, model comparison charts, confusion matrix
- **REST API** — `/api/predict`, `/api/history`, `/api/metadata`, `/api/contact`
- **Premium dark/light UI** — glassmorphism panels, animated threat gauge, particle background,
  scroll-reveal motion, fully responsive

---

## Tech Stack

| Layer          | Technology                                                         |
|----------------|---------------------------------------------------------------------|
| Backend        | Python, Flask                                                      |
| ML / Data      | NumPy, Pandas, Scikit-learn, XGBoost, LightGBM, Joblib, Matplotlib   |
| Frontend       | HTML5, CSS3 (custom, no framework), Vanilla JavaScript              |

---

## Project Structure

```
phishing-detector/
├── app.py                     # Flask application & REST API
├── feature_extractor.py       # URL -> 15-feature vector + explanations
├── generate_dataset.py        # Builds dataset/phishing_dataset.csv
├── train_model.py             # Trains & compares 8 models, saves the best
├── predict.py                 # Loads saved model and scores a URL
├── requirements.txt
├── README.md
├── dataset/
│   └── phishing_dataset.csv   # Generated training data
├── models/
│   ├── best_model.pkl         # Best model (Joblib)
│   ├── scaler.pkl             # Fitted StandardScaler
│   └── metadata.json          # Metrics, confusion matrix, feature importance
├── templates/
│   ├── base.html
│   ├── index.html             # Home
│   ├── about.html
│   ├── scanner.html           # Live URL scanner
│   ├── dashboard.html         # Scan history + KPIs
│   ├── analytics.html         # Model comparison + charts
│   ├── contact.html
│   └── 404.html
└── static/
    ├── css/style.css
    ├── js/{particles,main,scanner,dashboard,analytics}.js
    └── images/{model_comparison,feature_importance}.png
```

---

## Installation

```bash
git clone <this-repo>
cd phishing-detector
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> `xgboost` / `lightgbm` are optional. If either fails to install on your
> machine, delete it from `requirements.txt` — `train_model.py` detects
> their absence automatically and trains the remaining six models.

## Usage

```bash
# 1. Generate the training dataset (synthetic, offline-safe generator)
python generate_dataset.py

# 2. Train all 8 models and persist the best one
python train_model.py

# 3. Launch the web app
python app.py
```

Then open **http://localhost:5000** in your browser.

### Using your own dataset

Drop a real labelled CSV at `dataset/phishing_dataset.csv` with a `url` and
`label` (`safe`/`phishing`) column, then run:

```bash
python generate_dataset.py --force   # skip this if you already have real data
python train_model.py
```

### Calling the API directly

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "http://192.168.4.21/paypal-secure/verify.php"}'
```

```json
{
  "prediction": "Phishing",
  "confidence": 97.4,
  "threat_level": "Critical",
  "probability": { "safe": 2.6, "phishing": 97.4 },
  "reasons": [
    { "type": "risk", "text": "Hostname is a raw IP address instead of a domain name." },
    { "type": "risk", "text": "Connection is not secured with HTTPS." }
  ]
}
```

---

## Feature Set

| Feature                    | Description                                            |
|-----------------------------|--------------------------------------------------------|
| `url_length`                 | Total character length of the URL                      |
| `num_dots`                   | Count of `.` characters                                 |
| `num_digits`                 | Count of numeric characters                             |
| `num_hyphens`                | Count of `-` characters                                 |
| `has_https`                  | Whether the scheme is HTTPS                             |
| `has_at_symbol`               | Presence of `@` (used to obscure the real destination)  |
| `has_ip`                     | Whether the host is a raw IP address                    |
| `num_redirects`               | Detected HTTP redirect hops (best-effort, live checks only) |
| `num_subdomains`              | Subdomain nesting depth                                 |
| `suspicious_keyword_count`    | Count of phishing-associated keywords                   |
| `url_entropy`                 | Shannon entropy of the URL string                        |
| `special_char_count`          | Count of special characters                              |
| `num_slashes`                 | Count of `/` characters                                  |
| `digit_ratio`                 | Ratio of digits to total URL length                       |
| `has_shortener`               | Whether the host is a known URL-shortening service        |

---

## Model Training Pipeline

1. **Clean** — drop duplicates, impute missing values, normalize labels
2. **Split** — 80/20 stratified train/test split
3. **Scale** — `StandardScaler` fit on the training set
4. **Train** — 8 candidate classifiers trained on identical folds
5. **Evaluate** — accuracy, precision, recall, F1, ROC-AUC on the held-out test set
6. **Select** — highest-F1 model persisted with Joblib, alongside the scaler and metadata

---

## Screenshots

Run the app locally and visit `/`, `/scanner`, `/dashboard` and `/analytics` —
the scanner shows a live animated threat gauge, the dashboard tracks scan
history, and analytics renders full model-comparison charts.

---

## Future Improvements

- Persist scan history in a real database (PostgreSQL / SQLite) instead of in-memory storage
- Add a browser extension front-end that calls `/api/predict` on page load
- Incorporate WHOIS/domain-age and SSL-certificate-age as live features
- Add authentication for the dashboard in a multi-user deployment
- Periodic retraining pipeline against live threat-intelligence feeds

---

## License

MIT License — free to use, modify, and distribute for academic and
educational purposes.
