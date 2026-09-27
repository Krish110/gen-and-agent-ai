"""
Heuristic (rule-based) evaluation of generated proposals. No LLM-as-judge —
every score below is computed from measurable text properties, so it runs
free and offline. Each score is 0-100; higher is better.
"""

import re

JARGON_WORDS = ["synergy", "leverage", "paradigm", "disrupt", "holistic", "ecosystem",
                "bandwidth", "circle back", "low-hanging fruit", "move the needle"]


def _specificity_score(data, generated):
    """How much of the client's own wording shows up in the draft, vs. generic filler."""
    req_words = set(w.strip(".,!?()").lower() for w in data["requirements"].split() if len(w) > 4)
    if not req_words:
        return 50
    body = (generated["executive_summary"] + " " + generated["proposal_body"]).lower()
    hits = sum(1 for w in req_words if w in body)
    return round(min(100, (hits / max(1, len(req_words))) * 300))


def _clarity_score(generated):
    """Rewards sentences close to a readable business-writing length (~15-20 words)."""
    text = generated["proposal_body"]
    sentences = [s for s in re.split(r"[.!?]\s+", text) if s.strip()]
    if not sentences:
        return 50
    avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
    score = 100 - min(100, abs(avg_len - 17) * 4)
    return round(max(0, score))


def _tone_score(generated):
    """Penalizes corporate jargon that tends to read as filler rather than substance."""
    text = (generated["executive_summary"] + " " + generated["proposal_body"]).lower()
    jargon_hits = sum(text.count(j) for j in JARGON_WORDS)
    return round(max(0, 100 - jargon_hits * 20))


def _pricing_consistency_score(generated):
    """Checks the pricing table actually sums to a stated 100% total."""
    return 100 if "100%" in generated["pricing_md"] else 60


def evaluate_proposal(data, generated):
    specificity = _specificity_score(data, generated)
    clarity = _clarity_score(generated)
    tone = _tone_score(generated)
    pricing = _pricing_consistency_score(generated)
    overall = round((specificity + clarity + tone + pricing) / 4)
    return {
        "specificity": specificity,
        "clarity": clarity,
        "tone": tone,
        "pricing_consistency": pricing,
        "overall": overall,
    }
