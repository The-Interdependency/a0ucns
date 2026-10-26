# ratios: loc_comments=157:22 imports_exports=6:7 calls_definitions=62:14
"""EDCM (Energy-Dissonance Circuit Model) computation engine.

Implements deterministic placeholder metrics from spec.md v1.0.2-S9:
- CM  (Constraint Mismatch)  — Jaccard-based
- DA  (Dissonance Accumulation) — sigmoid of feature weights
- DRIFT — cosine similarity to goal vector (keyword-based)
- DVG (Divergence) — entropy of topic distribution
- INT (Intensity) — weighted caps/punct/tempo features
- TBF (Turn Balance Fairness) — Gini coefficient on actor token shares
"""

import math
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Alert thresholds (80/20 rule, frozen v1.0.2)
ALERT_HIGH = 0.80
ALERT_LOW = 0.20


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def _gini(shares: List[float]) -> float:
    """Gini coefficient normalised to [0, 1]."""
    n = len(shares)
    if n <= 1:
        return 0.0
    total = sum(shares)
    if total == 0:
        return 0.0
    sorted_s = sorted(shares)
    numerator = sum((2 * (i + 1) - n - 1) * s for i, s in enumerate(sorted_s))
    return numerator / (n * total)


def _entropy(probs: List[float]) -> float:
    """Shannon entropy normalised to [0, 1]."""
    filtered = [p for p in probs if p > 0]
    if len(filtered) <= 1:
        return 0.0
    h = -sum(p * math.log2(p) for p in filtered)
    max_h = math.log2(len(filtered))
    return h / max_h if max_h > 0 else 0.0


def _cosine_sim(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Cosine similarity between two keyword vectors."""
    keys = set(a) | set(b)
    if not keys:
        return 1.0
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    mag_a = math.sqrt(sum(v ** 2 for v in a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _keyword_vector(text: str) -> Dict[str, float]:
    """Build a simple keyword frequency vector."""
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    counts = Counter(words)
    total = sum(counts.values()) or 1
    return {w: c / total for w, c in counts.items()}


# ---- Core metric functions ----

def compute_cm(declared_constraints: List[str], observed_text: str) -> Dict[str, Any]:
    """Constraint Mismatch: 1 - Jaccard(declared, observed keywords)."""
    declared_set = {c.lower().strip() for c in declared_constraints if c.strip()}
    observed_words = set(re.findall(r'\b[a-z]{3,}\b', observed_text.lower()))
    j = _jaccard(declared_set, observed_words & declared_set)
    value = _clamp01(1.0 - j)
    return {"value": round(value, 4), "range": [0, 1]}


def compute_da(turns: List[dict]) -> Dict[str, Any]:
    """Dissonance Accumulation: sigmoid of contradiction/retraction features."""
    contrad = 0
    retract = 0
    repeat_q = 0
    unresolved = 0

    for turn in turns:
        text = (turn.get("content") or "").lower()
        if any(m in text for m in ["actually", "i was wrong", "correction", "not what i meant"]):
            retract += 1
        if any(m in text for m in ["but you said", "that contradicts", "inconsistent"]):
            contrad += 1
        if text.endswith("?"):
            repeat_q += 1
        if any(m in text for m in ["unresolved", "still waiting", "no answer"]):
            unresolved += 1

    raw = 0.3 * contrad + 0.3 * retract + 0.2 * repeat_q + 0.2 * unresolved
    value = _clamp01(_sigmoid(raw - 2.0))
    return {"value": round(value, 4), "range": [0, 1]}


def compute_drift(goal_text: str, current_text: str) -> Dict[str, Any]:
    """Drift: 1 - cosine(goal_keywords, current_keywords). Deterministic keyword version."""
    g = _keyword_vector(goal_text)
    x = _keyword_vector(current_text)
    cos = _cosine_sim(g, x)
    value = _clamp01(1.0 - cos)
    return {"value": round(value, 4), "range": [0, 1]}


def compute_dvg(turns: List[dict], k: int = 5) -> Dict[str, Any]:
    """Divergence: entropy of simple topic distribution (word cluster proxy)."""
    all_text = " ".join((t.get("content") or "") for t in turns).lower()
    words = re.findall(r'\b[a-z]{4,}\b', all_text)
    if len(words) < 2:
        return {"value": 0.0, "range": [0, 1]}

    counts = Counter(words)
    top_k = counts.most_common(k)
    total = sum(c for _, c in top_k) or 1
    probs = [c / total for _, c in top_k]
    value = _clamp01(_entropy(probs))
    return {"value": round(value, 4), "range": [0, 1]}


def compute_int(turns: List[dict]) -> Dict[str, Any]:
    """Intensity / valence proxy."""
    caps_total = 0
    punct_total = 0
    char_total = 0
    short_interval = 0

    for i, turn in enumerate(turns):
        text = turn.get("content") or ""
        caps_total += sum(1 for c in text if c.isupper())
        punct_total += sum(1 for c in text if c in "!?...")
        char_total += len(text) or 1
        if i > 0 and len(text) < 20:
            short_interval += 1

    n = max(1, char_total)
    caps_ratio = caps_total / n
    punct_ratio = punct_total / n
    tempo = short_interval / max(1, len(turns))

    raw = 0.3 * caps_ratio * 10 + 0.3 * punct_ratio * 10 + 0.4 * tempo
    value = _clamp01(raw)
    return {"value": round(value, 4), "range": [0, 1]}


def compute_tbf(turns: List[dict]) -> Dict[str, Any]:
    """Turn-Balance Fairness: Gini on actor token shares."""
    actor_tokens: Dict[str, int] = {}
    for turn in turns:
        actor = turn.get("actor_id") or turn.get("model") or "unknown"
        tokens = len((turn.get("content") or "").split())
        actor_tokens[actor] = actor_tokens.get(actor, 0) + tokens

    shares = list(actor_tokens.values())
    value = _clamp01(_gini(shares))
    return {"value": round(value, 4), "range": [0, 1]}


def evaluate_edcm(
    turns: List[dict],
    goal_text: str = "",
    declared_constraints: Optional[List[str]] = None,
    window_w: int = 32,
) -> dict:
    """Run full EDCM evaluation, return EDCMBONE report."""
    windowed = turns[-window_w:]
    all_text = " ".join((t.get("content") or "") for t in windowed)

    metrics = {
        "CM": compute_cm(declared_constraints or [], all_text),
        "DA": compute_da(windowed),
        "DRIFT": compute_drift(goal_text, all_text),
        "DVG": compute_dvg(windowed),
        "INT": compute_int(windowed),
        "TBF": compute_tbf(windowed),
    }

    alerts = []
    for name, m in metrics.items():
        v = m["value"]
        if v >= ALERT_HIGH:
            alerts.append({
                "name": f"ALERT_{name}_HIGH",
                "severity": "high",
                "value": v,
                "threshold": ALERT_HIGH,
            })

    return {
        "thread_id": "",
        "used_context": {
            "window": {"type": "turns", "W": window_w},
            "retrieval": {"mode": "none", "sources": [], "top_k": 0},
        },
        "metrics": metrics,
        "alerts": alerts,
        "recommendations": [],
        "snapshot_id": f"snap_{uuid.uuid4().hex[:16]}",
    }
# ratios: loc_comments=157:22 imports_exports=6:7 calls_definitions=62:14
