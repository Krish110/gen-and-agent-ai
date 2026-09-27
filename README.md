# AI Sales Proposal Generator (Prototype)

A rule-based Streamlit app that turns customer requirements into a full sales proposal package — no LLM/API key required.

## What it generates
- **Executive Summary** — tailored to the client's industry and stated pain points
- **Full Proposal** — problem statement, objectives, proposed solution, scope/deliverables, timeline, team, terms
- **Pricing** — a tiered budget breakdown (Starter / Growth / Enterprise) with itemized phase allocation and pricing assumptions
- **Follow-Up Email** — a ready-to-send draft
- **Follow-Up Strategy** — a day-by-day touchpoint schedule
- **One-click .docx export** of the complete proposal

## How it works
All content is produced by deterministic template logic in `templates.py`:
- An **industry knowledge base** (`INDUSTRY_INSIGHTS`) supplies pain points, value props, and default deliverables per industry (E-commerce, Marketing, Healthcare, Finance, SaaS, Retail, Manufacturing, Education, Other).
- **Pricing** is allocated across six standard project phases as fixed percentages of the entered budget, with the tier (Starter/Growth/Enterprise) chosen by budget size.
- **Timeline** milestones are calculated as percentages of the total weeks entered.
- **Follow-up strategy** generates a 5-touchpoint schedule (Day 0/2/5/10/20) with real calendar dates.

No external API calls are made — everything runs offline once dependencies are installed.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Files
- `app.py` — Streamlit UI (form input → tabbed output → docx download)
- `templates.py` — rule-based content generation engine
- `docx_export.py` — renders the generated sections into a downloadable Word document
- `requirements.txt` — `streamlit`, `python-docx`

## Extending it
- Add more industries to `INDUSTRY_INSIGHTS` in `templates.py`.
- Adjust `PHASE_ALLOCATION` or `TIER_RULES` to change pricing logic.
- Swap in an LLM call inside `generate_all()` later if you want AI-generated (rather than template-based) prose — the rest of the app (form, tabs, docx export) doesn't need to change.
