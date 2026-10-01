"""
Extractive Q&A over a generated proposal. Finds the most relevant existing
chunk of the proposal for a given question via TF-IDF similarity — it never
generates new text, only retrieves what's already there. No LLM call.
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _chunk(generated):
    full_text = "\n".join([
        generated["executive_summary"],
        generated["proposal_body"],
        generated["pricing_md"],
        generated["followup_strategy_md"],
    ])
    # Split on blank lines and before headings/bullets. Table rows (lines
    # starting with "|") have no blank line between them so they stay glued
    # together as one retrievable block instead of one chunk per row.
    raw_chunks = re.split(r"\n\s*\n|\n(?=### )|\n(?=- )", full_text)
    # Keep short section headings (e.g. "### 6. Timeline") even though they're
    # under the length floor — dropping them removes a section boundary and
    # lets unrelated bullet lists bleed into each other during grouping below.
    raw_chunks = [c.strip() for c in raw_chunks if len(c.strip()) > 15 or c.strip().startswith("### ")]

    # A lone heading/label carries no answerable content on its own — merge it
    # with everything that belongs to it: all following bullet lines (not just
    # one), or the next paragraph if there are no bullets. Covers "### Heading"
    # lines AND short bold labels like "**Pricing Assumptions:**".
    def _is_bare_label(chunk):
        if chunk.startswith("### "):
            return True
        stripped = chunk.strip("*").strip()
        return stripped.endswith(":") and len(stripped.split()) <= 6 and "\n" not in chunk

    def _is_bullet(chunk):
        return chunk.lstrip().startswith("- ")

    merged = []
    i = 0
    while i < len(raw_chunks):
        chunk = raw_chunks[i]
        if _is_bare_label(chunk) and i + 1 < len(raw_chunks):
            group = [chunk]
            j = i + 1
            while j < len(raw_chunks) and _is_bullet(raw_chunks[j]):
                group.append(raw_chunks[j])
                j += 1
            if len(group) == 1:  # no bullets followed — fall back to the next block
                group.append(raw_chunks[j])
                j += 1
            merged.append("\n".join(group))
            i = j
        else:
            merged.append(chunk)
            i += 1
    return merged


# Small local synonym map so plain TF-IDF (no stemming) still catches common
# phrasings like "price" vs "pricing" without calling an external model.
SYNONYMS = {
    "price": "price pricing cost budget",
    "cost": "cost price pricing budget",
    "pricing": "pricing price cost budget",
    "budget": "budget pricing cost",
    "deliverable": "deliverable deliverables scope",
    "deliverables": "deliverables deliverable scope",
    "timeline": "timeline week weeks schedule",
    "schedule": "schedule timeline week weeks",
    "email": "email follow-up followup",
}


def _expand_query(question):
    words = re.findall(r"[a-zA-Z']+", question.lower())
    expanded = [SYNONYMS.get(w, w) for w in words]
    return question + " " + " ".join(expanded)


def answer_question(generated, question):
    chunks = _chunk(generated)
    if not chunks:
        return "No content available yet — generate a proposal first."
    corpus = chunks + [_expand_query(question)]
    try:
        vec = TfidfVectorizer(stop_words="english").fit_transform(corpus)
    except ValueError:
        return "Couldn't match that question to the proposal content — try rephrasing."
    sims = cosine_similarity(vec[-1], vec[:-1]).flatten()
    best_idx = int(sims.argmax())
    if sims[best_idx] <= 0.05:
        return "That doesn't appear to be covered in this proposal — you may want to follow up directly."
    return chunks[best_idx]
