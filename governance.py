"""
Lightweight responsible-AI guardrails for the generator. Fully rule-based:
scans generated text for quantified claims that should be human-checked
before a proposal goes out, and attaches a disclaimer for internal review.
"""

import re

DISCLAIMER = (
    "This proposal was drafted by a rule-based generator from the information provided. "
    "All figures are estimates pending discovery, and any case-study statistics are from a "
    "past engagement, not a guarantee for this client. Please review before sending."
)

# Numeric claims are only risky where they read as promises/results about THIS
# client's business (percent changes, savings figures) rather than the fixed
# pricing table (which is scanned separately and is expected to have %'s).
RISKY_PATTERNS = [
    r"\b\d{1,3}%",  # any bare percentage in prose — usually a case-study stat needing attribution
    r"(?:save|saves|saving|cut|cuts|cutting|reduce|reduced|reducing)\s+"
    r"(?:roughly\s+|about\s+|approximately\s+)?\$?\d+",
]


def scan_for_risky_claims(text):
    """Returns a list of short excerpts around each unverified quantified claim found,
    deduplicated by the matched number so overlapping patterns don't double-report."""
    seen_spans = set()
    flags = []
    for pattern in RISKY_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            # Skip if this match sits inside a span we've already flagged
            if any(abs(m.start() - s) < 20 for s in seen_spans):
                continue
            seen_spans.add(m.start())
            excerpt = text[max(0, m.start() - 40):m.end() + 15].strip()
            excerpt = " ".join(excerpt.split())  # collapse whitespace/newlines
            flags.append(excerpt)
    return flags
