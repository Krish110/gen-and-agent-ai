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
    raw_chunks = [c.strip() for c in raw_chunks if len(c.strip()) > 15]

    # A lone "### heading" carries no answerable content on its own — merge it
    # into the block that follows so retrieval returns the heading + its content.
    merged = []
    i = 0
    while i < len(raw_chunks):
        chunk = raw_chunks[i]
        if chunk.startswith("### ") and i + 1 < len(raw_chunks):
            merged.append(chunk + "\n" + raw_chunks[i + 1])
            i += 2
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
