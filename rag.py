"""
Lightweight local RAG layer — TF-IDF retrieval over a small library of case
studies / past proposals. No embeddings API, no external calls: retrieval
happens entirely with scikit-learn's TfidfVectorizer + cosine similarity.
"""

import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DEFAULT_CASE_STUDIES = [
    {
        "title": "E-commerce support automation cut response time 70%",
        "industry": "E-commerce",
        "snippet": "A mid-size online retailer reduced average support response time from 18 hours to "
                   "under 3 hours after automating order-status and return queries, cutting repetitive "
                   "ticket volume by roughly 55%.",
    },
    {
        "title": "Marketing agency reporting automation saved 12 hrs/week",
        "industry": "Marketing / Digital Agency",
        "snippet": "A digital marketing agency automated client reporting across campaigns, saving the "
                   "team approximately 12 hours per week previously spent compiling manual reports.",
    },
    {
        "title": "Healthcare scheduling reminders reduced no-shows 30%",
        "industry": "Healthcare",
        "snippet": "A multi-location clinic reduced appointment no-shows by roughly 30% after introducing "
                   "automated reminders and rebooking workflows.",
    },
    {
        "title": "Finance onboarding automation cut processing time in half",
        "industry": "Finance / Banking",
        "snippet": "A regional lender cut client onboarding processing time roughly in half by automating "
                   "document verification and reconciliation steps, while keeping a full audit trail.",
    },
    {
        "title": "SaaS onboarding redesign lifted activation 25%",
        "industry": "SaaS / Technology",
        "snippet": "A SaaS company redesigned its onboarding flow and automated first-week check-ins, "
                   "lifting 30-day activation rates by about 25%.",
    },
    {
        "title": "Retail inventory dashboard cut stockouts 40%",
        "industry": "Retail",
        "snippet": "A retail chain unified inventory data into a single dashboard, cutting stockout "
                   "incidents by about 40% during peak season.",
    },
    {
        "title": "Manufacturing vendor workflow cut delays by a third",
        "industry": "Manufacturing",
        "snippet": "A manufacturer automated vendor coordination and quality reporting, cutting "
                   "supply-chain-related delays by roughly a third within one quarter.",
    },
    {
        "title": "Education admissions automation freed up staff time",
        "industry": "Education",
        "snippet": "An education institution automated admissions document processing and applicant "
                   "communication, freeing an estimated 10+ staff hours per week during peak season.",
    },
]

STORE_PATH = os.path.join(os.path.dirname(__file__), "case_studies.json")


class CaseStudyStore:
    """In-memory + on-disk store of case studies, retrieved via TF-IDF similarity."""

    def __init__(self):
        self.items = list(DEFAULT_CASE_STUDIES)
        self._custom = self._load_custom()
        self.items.extend(self._custom)

    def _load_custom(self):
        if os.path.exists(STORE_PATH):
            try:
                with open(STORE_PATH, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def add(self, title, industry, snippet):
        item = {"title": title, "industry": industry, "snippet": snippet}
        self._custom.append(item)
        self.items.append(item)
        with open(STORE_PATH, "w") as f:
            json.dump(self._custom, f, indent=2)

    def retrieve(self, query, industry=None, top_k=1):
        """Returns the best-matching case study dict, or None if the store is empty."""
        if not self.items:
            return None
        pool = [i for i in self.items if i["industry"] == industry] or self.items
        corpus = [f"{i['title']} {i['snippet']}" for i in pool] + [query]
        try:
            vec = TfidfVectorizer(stop_words="english").fit_transform(corpus)
        except ValueError:
            return pool[0]
        sims = cosine_similarity(vec[-1], vec[:-1]).flatten()
        best_idx = int(sims.argmax())
        return pool[best_idx]

    def all_items(self):
        return self.items
