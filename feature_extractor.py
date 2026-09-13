"""
feature_extractor.py
---------------------
Extracts lexical, structural and statistical features from a raw URL
string for use by the phishing-detection models.

No network calls are required for the core feature set, so extraction
is fast enough to run synchronously inside a Flask request. An optional
network-based redirect check is included and fails silently (defaults
to 0) if the host cannot be reached, so the API keeps working offline.
"""

import re
import math
import socket
from collections import Counter
from urllib.parse import urlparse

try:
    import urllib.request
    _NETWORK_AVAILABLE = True
except ImportError:  # pragma: no cover
    _NETWORK_AVAILABLE = False

SUSPICIOUS_KEYWORDS = [
    "login", "signin", "verify", "update", "secure", "account", "banking",
    "confirm", "password", "credential", "wallet", "webscr", "ebayisapi",
    "paypal", "suspend", "unlock", "limited", "alert", "invoice", "billing",
    "security", "authenticate", "recover", "support", "helpdesk", "gift",
    "bonus", "click", "urgent", "verify-account", "reset", "authorize",
]

URL_SHORTENERS = [
    "bit.ly", "goo.gl", "tinyurl.com", "ow.ly", "t.co", "is.gd", "buff.ly",
    "adf.ly", "cutt.ly", "shorte.st", "bl.ink", "rebrand.ly", "rb.gy",
]

FEATURE_NAMES = [
    "url_length",
    "num_dots",
    "num_digits",
    "num_hyphens",
    "has_https",
    "has_at_symbol",
    "has_ip",
    "num_redirects",
    "num_subdomains",
    "suspicious_keyword_count",
    "url_entropy",
    "special_char_count",
    "num_slashes",
    "digit_ratio",
    "has_shortener",
]

IPV4_REGEX = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
IPV4_ANYWHERE_REGEX = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")
HEX_IP_REGEX = re.compile(r"0x[0-9a-fA-F]{2,}")


def _ensure_scheme(url: str) -> str:
    """Guarantee urlparse can find a netloc even for bare domains."""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        return "http://" + url
    return url


def shannon_entropy(s: str) -> float:
    """Standard Shannon entropy of the character distribution of s."""
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def count_subdomains(hostname: str) -> int:
    """Number of subdomain labels, ignoring the registrable domain + TLD."""
    if not hostname:
        return 0
    if IPV4_REGEX.match(hostname):
        return 0
    labels = hostname.split(".")
    # e.g. "a.b.example.co.uk" -> heuristically treat last 2 labels as domain+tld
    if len(labels) <= 2:
        return 0
    return max(0, len(labels) - 2)


def has_ip_address(hostname: str) -> int:
    if not hostname:
        return 0
    if IPV4_REGEX.match(hostname):
        return 1
    if HEX_IP_REGEX.search(hostname):
        return 1
    return 0


def count_redirects(url: str, timeout: float = 1.5) -> int:
    """
    Best-effort count of HTTP redirect hops. Returns 0 immediately if
    the network is unavailable or the host cannot be resolved, so this
    never blocks or breaks feature extraction offline.
    """
    if not _NETWORK_AVAILABLE:
        return 0
    try:
        parsed = urlparse(_ensure_scheme(url))
        socket.setdefaulttimeout(timeout)
        req = urllib.request.Request(url=parsed.geturl(), method="HEAD",
                                      headers={"User-Agent": "Mozilla/5.0"})
        redirects = 0
        current = req
        for _ in range(5):
            resp = urllib.request.urlopen(current, timeout=timeout)
            if resp.status in (301, 302, 303, 307, 308):
                redirects += 1
                location = resp.headers.get("Location")
                if not location:
                    break
                current = urllib.request.Request(url=location, method="HEAD",
                                                   headers={"User-Agent": "Mozilla/5.0"})
            else:
                break
        return redirects
    except Exception:
        return 0


def extract_features(url: str, check_live_redirects: bool = False) -> dict:
    """
    Extract the full feature vector for a single URL.
    Returns a dict keyed by FEATURE_NAMES (order preserved).
    """
    raw_url = url.strip()
    parsed = urlparse(_ensure_scheme(raw_url))
    hostname = parsed.hostname or ""
    scheme = parsed.scheme or ""

    length = len(raw_url)
    digits = sum(c.isdigit() for c in raw_url)

    features = {
        "url_length": length,
        "num_dots": raw_url.count("."),
        "num_digits": digits,
        "num_hyphens": raw_url.count("-"),
        "has_https": 1 if scheme.lower() == "https" else 0,
        "has_at_symbol": 1 if "@" in raw_url else 0,
        "has_ip": has_ip_address(hostname) or (1 if IPV4_ANYWHERE_REGEX.search(raw_url) else 0),
        "num_redirects": count_redirects(raw_url) if check_live_redirects else 0,
        "num_subdomains": count_subdomains(hostname),
        "suspicious_keyword_count": sum(
            1 for kw in SUSPICIOUS_KEYWORDS if kw in raw_url.lower()
        ),
        "url_entropy": round(shannon_entropy(raw_url), 4),
        "special_char_count": sum(1 for c in raw_url if c in "!$%^&*()_+={}[]|\\;:\"'<>,?~`"),
        "num_slashes": raw_url.count("/"),
        "digit_ratio": round(digits / length, 4) if length else 0.0,
        "has_shortener": 1 if any(s in hostname for s in URL_SHORTENERS) else 0,
    }
    return features


def extract_feature_vector(url: str, check_live_redirects: bool = False) -> list:
    """Return the feature values as an ordered list matching FEATURE_NAMES."""
    feats = extract_features(url, check_live_redirects=check_live_redirects)
    return [feats[name] for name in FEATURE_NAMES]


def explain_features(features: dict) -> list:
    """
    Produce short, human-readable reasons based on the extracted feature
    values. Used by the API to justify a prediction (explainable-AI panel).
    """
    reasons = []

    if features["has_https"] == 0:
        reasons.append({"type": "risk", "text": "Connection is not secured with HTTPS."})
    else:
        reasons.append({"type": "safe", "text": "URL uses a secure HTTPS connection."})

    if features["has_ip"] == 1:
        reasons.append({"type": "risk", "text": "Hostname is a raw IP address instead of a domain name."})

    if features["has_at_symbol"] == 1:
        reasons.append({"type": "risk", "text": "URL contains an '@' symbol, often used to hide the real destination."})

    if features["num_subdomains"] >= 3:
        reasons.append({"type": "risk", "text": f"Unusually deep subdomain nesting ({features['num_subdomains']} levels)."})

    if features["suspicious_keyword_count"] >= 2:
        reasons.append({"type": "risk", "text": f"Contains {features['suspicious_keyword_count']} phishing-associated keywords (e.g. 'verify', 'login', 'secure')."})
    elif features["suspicious_keyword_count"] == 1:
        reasons.append({"type": "risk", "text": "Contains at least one phishing-associated keyword."})

    if features["url_length"] > 75:
        reasons.append({"type": "risk", "text": f"Excessively long URL ({features['url_length']} characters)."})

    if features["url_entropy"] > 4.3:
        reasons.append({"type": "risk", "text": "High character randomness detected, typical of auto-generated phishing links."})

    if features["has_shortener"] == 1:
        reasons.append({"type": "risk", "text": "Uses a known URL-shortening service, which can mask the true destination."})

    if features["num_hyphens"] >= 4:
        reasons.append({"type": "risk", "text": f"Excessive hyphen usage ({features['num_hyphens']}) often seen in typosquatted domains."})

    if features["special_char_count"] >= 5:
        reasons.append({"type": "risk", "text": "High number of special characters detected."})

    if len(reasons) <= 1:
        reasons.append({"type": "safe", "text": "No major structural red flags detected in the URL."})

    return reasons
