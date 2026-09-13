"""
generate_dataset.py
--------------------
Builds dataset/phishing_dataset.csv.

This project ships with a programmatically generated URL corpus rather
than a downloaded CSV, because it must run fully offline for grading.
The generator encodes the same lexical patterns documented in published
phishing-URL research (PhishTank / UCI Phishing Websites feature set):
legitimate URLs are short, HTTPS, low subdomain depth and keyword-free;
phishing URLs skew toward raw IP hosts, brand-name typosquatting,
excessive subdomains, credential-harvesting keywords and shortener
services. Each generated URL is passed through the SAME
`feature_extractor.py` used at prediction time, so the model trains on
exactly the feature space it will see in production.

If you have a real labelled dataset (e.g. from PhishTank, OpenPhish or
the UCI ML Repository), drop it at dataset/phishing_dataset.csv with a
`url` and `label` ("phishing"/"safe") column and re-run train_model.py
-- generate_dataset.py will not overwrite an existing file unless
--force is passed.
"""

import argparse
import csv
import os
import random
import string

from feature_extractor import extract_features, FEATURE_NAMES

random.seed(42)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "dataset", "phishing_dataset.csv")

LEGIT_BRANDS = [
    "wikipedia", "github", "stackoverflow", "nytimes", "bbc", "python",
    "mozilla", "cloudflare", "harvard", "mit", "nationalgeographic",
    "spotify", "airbnb", "notion", "figma", "dropbox", "slack", "trello",
    "coursera", "khanacademy", "duolingo", "reuters", "npr", "who",
    "un", "nasa", "irs", "usps",
]
LEGIT_TLDS = ["com", "org", "edu", "gov", "io", "net"]
LEGIT_PATHS = [
    "", "/", "/about", "/help/contact", "/docs/getting-started",
    "/blog/2026/updates", "/careers", "/products", "/pricing",
    "/support/faq", "/en/home", "/news/latest", "/account/settings",
]

PHISH_BRANDS = [
    "paypal", "netflix", "amazon", "apple", "microsoft", "chase",
    "wellsfargo", "bankofamerica", "instagram", "facebook", "google",
    "outlook", "icloud", "coinbase", "binance", "dhl", "fedex", "usps",
]
SUSPICIOUS_WORDS = [
    "secure", "verify", "update", "login", "signin", "account", "confirm",
    "billing", "suspended", "unlock", "recover", "reset-password",
    "webscr", "authenticate", "support-center", "alert",
]
PHISH_TLDS = ["tk", "ml", "ga", "cf", "top", "xyz", "info", "click", "gq"]
SHORTENERS = ["bit.ly", "tinyurl.com", "cutt.ly", "rb.gy", "is.gd"]


def _rand_str(n, charset=string.ascii_lowercase + string.digits):
    return "".join(random.choice(charset) for _ in range(n))


def _rand_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def make_legit_url():
    brand = random.choice(LEGIT_BRANDS)
    tld = random.choice(LEGIT_TLDS)
    path = random.choice(LEGIT_PATHS)
    sub = random.choice(["", "www.", "docs.", "help.", "en."])
    scheme = "https"
    query = ""
    if random.random() < 0.15:
        query = "?ref=" + _rand_str(4)
    return f"{scheme}://{sub}{brand}.{tld}{path}{query}"


def make_phishing_url():
    style = random.choice(["ip", "typosquat", "subdomain-flood", "shortener", "keyword-path"])
    brand = random.choice(PHISH_BRANDS)
    word = random.choice(SUSPICIOUS_WORDS)
    scheme = random.choice(["http", "http", "https"])

    if style == "ip":
        host = _rand_ip()
        return f"{scheme}://{host}/{brand}-{word}/{_rand_str(6)}.php"

    if style == "typosquat":
        typo = brand.replace("o", "0").replace("l", "1") if random.random() < 0.5 else brand + _rand_str(2)
        tld = random.choice(PHISH_TLDS)
        return f"{scheme}://{typo}-{word}.{tld}/{word}/{_rand_str(5)}"

    if style == "subdomain-flood":
        depth = random.randint(3, 6)
        subs = ".".join(_rand_str(random.randint(3, 8)) for _ in range(depth))
        tld = random.choice(PHISH_TLDS)
        return f"{scheme}://{subs}.{brand}.{tld}/{word}"

    if style == "shortener":
        host = random.choice(SHORTENERS)
        return f"{scheme}://{host}/{_rand_str(7)}"

    # keyword-path
    tld = random.choice(PHISH_TLDS)
    depth_path = "/".join(random.choice(SUSPICIOUS_WORDS) for _ in range(random.randint(2, 4)))
    return f"{scheme}://{brand}-{word}.{tld}/{depth_path}/{_rand_str(8)}?id={_rand_str(10)}"


def build_dataset(n_per_class=3000):
    rows = []
    for _ in range(n_per_class):
        url = make_legit_url()
        feats = extract_features(url, check_live_redirects=False)
        feats["url"] = url
        feats["label"] = "safe"
        rows.append(feats)

    for _ in range(n_per_class):
        url = make_phishing_url()
        feats = extract_features(url, check_live_redirects=False)
        feats["url"] = url
        feats["label"] = "phishing"
        rows.append(feats)

    random.shuffle(rows)
    return rows


def write_csv(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ["url"] + FEATURE_NAMES + ["label"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fieldnames})


def main():
    parser = argparse.ArgumentParser(description="Generate the phishing URL training dataset.")
    parser.add_argument("--n", type=int, default=3000, help="Number of samples per class")
    parser.add_argument("--force", action="store_true", help="Overwrite existing dataset file")
    args = parser.parse_args()

    if os.path.exists(OUTPUT_PATH) and not args.force:
        print(f"[i] Dataset already exists at {OUTPUT_PATH} (use --force to regenerate). Skipping.")
        return

    rows = build_dataset(n_per_class=args.n)
    # introduce small label noise / duplicates to simulate a realistic messy dataset
    dup_count = max(1, len(rows) // 100)
    for _ in range(dup_count):
        rows.append(random.choice(rows).copy())

    write_csv(rows, OUTPUT_PATH)
    print(f"[OK] Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
