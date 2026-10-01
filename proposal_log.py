"""
Local proposal log (CSV) — stands in for a CRM for this prototype. Powers
the "Business Impact" dashboard tab in the app.
"""

import os
import csv
from datetime import date

LOG_PATH = os.path.join(os.path.dirname(__file__), "proposal_log.csv")
FIELDS = ["date", "client_company", "industry", "tier", "budget", "currency", "tone", "overall_score", "outcome"]


def log_proposal(data, tier, tone, overall_score, outcome="Pending"):
    is_new = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "date": date.today().isoformat(),
            "client_company": data["client_company"],
            "industry": data["industry"],
            "tier": tier,
            "budget": data["budget"],
            "currency": data["currency"],
            "tone": tone,
            "overall_score": overall_score,
            "outcome": outcome,
        })


def load_log():
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r", newline="") as f:
        return list(csv.DictReader(f))


def update_outcome(row_index, outcome):
    rows = load_log()
    if 0 <= row_index < len(rows):
        rows[row_index]["outcome"] = outcome
        with open(LOG_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
