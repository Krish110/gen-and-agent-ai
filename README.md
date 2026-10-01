# AI Sales Proposal Generator (Prototype)

A **fully offline, no-API-key** multi-agent Streamlit app that turns customer requirements into a
complete, reviewed sales proposal package: proposal, executive summary, pricing, follow-up email,
and follow-up strategy — plus retrieval-augmented case studies, a heuristic evaluation layer,
responsible-AI guardrails, and a sent-proposals dashboard.

Nothing here calls an external LLM or embeddings API. Every "agent" and the RAG layer run on
local, deterministic logic (rules, regex, and scikit-learn's TF-IDF), so there's no key to manage,
no rate limit, and no cost.

## What it generates
- **Executive Summary** & **Full Proposal** — tailored to the client's industry, in your choice of
  **Formal** or **Consultative** tone (both are generated side by side for comparison)
- **Pricing** — a tiered budget breakdown (Starter / Growth / Enterprise) with itemized phase
  allocation, adjusted with a note when the requirements signal urgency or complexity
- **Follow-Up Email** — ready-to-send draft, tone-matched
- **Follow-Up Strategy** — a 5-touchpoint schedule with real calendar dates
- **One-click .docx export**, gated behind a human-approval checkbox

## Design

The app has a custom visual identity, not Streamlit's default look: a dark theme with a
green/blue accent gradient (`.streamlit/config.toml`), the Inter/Sora font pairing, a gradient
hero banner with feature pills, card-based sections (`st.container(border=True)`), styled
tabs/buttons/inputs, and Plotly dark-themed charts on the dashboard (tier bar chart, outcome
donut, industry breakdown). All of this lives in `design.py` (CSS + hero/footer markup) so
`app.py` stays focused on logic. To restyle, edit the CSS variables at the top of `design.py`
(`--accent`, `--bg`, etc.) — everything else derives from those tokens.

## Architecture — a rule-based multi-agent pipeline

```
RequirementsAgent → PricingAgent → RAGAgent → WriterAgent → ReviewerAgent
```

- **RequirementsAgent** (`agents.py`) — parses the freeform requirements text for urgency/complexity
  signals using keyword rules.
- **PricingAgent** — reviews those signals against the stated budget and leaves a note for the rep
  (e.g. "complexity detected — weight Discovery higher").
- **RAGAgent** (`rag.py`) — retrieves the most relevant case study from a local library using
  **TF-IDF + cosine similarity** (scikit-learn), no embeddings API. You can add your own case
  studies from the "Case Study Library" tab; they're saved to `case_studies.json` and considered
  on every future run.
- **WriterAgent** — drafts the proposal content in the requested tone, splicing in the retrieved
  case study as an attributed "Proven Results" section.
- **ReviewerAgent** — runs two independent checks before anything is shown as ready to send:
  - **`evaluation.py`** — a heuristic scorer (0-100) for specificity (does the draft actually use
    the client's own wording?), clarity (sentence length), tone (jargon density), and pricing
    consistency. This stands in for "LLM-as-judge" without needing a model call.
  - **`governance.py`** — scans for unverified quantified claims (e.g. a case-study percentage)
    and flags them for human review; attaches a disclaimer. A proposal can't be downloaded until
    the user checks "I've reviewed this draft."

The full agent trace (what each step did and why) is shown in an expander in the app — this is
the "Prompt Workflow / Agent Pipeline" artifact for a capstone writeup.

## Extras
- **Q&A over the proposal** (`qa.py`) — extractive question-answering: TF-IDF similarity finds the
  matching section of the *already-generated* text and returns it verbatim. No generation, so no
  hallucination risk — useful for "what's included in the price?"-style questions from a rep or
  client.
- **Sent Proposals Dashboard** (`proposal_log.py` + the Dashboard tab) — logs every approved
  proposal to a local CSV (client, industry, tier, budget, tone, quality score, outcome) and
  charts pipeline value, tier/industry mix, and win/loss outcome.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Files
- `app.py` — Streamlit UI: form → agent pipeline → tone tabs → evaluation/flags → docx download → Q&A → dashboard
- `design.py` — custom CSS, hero banner, footer (the visual identity — see "Design" above)
- `.streamlit/config.toml` — dark theme + accent color (commit this folder, it's not hidden from git)
- `agents.py` — the multi-agent pipeline orchestration (`run_pipeline`)
- `templates.py` — tone-aware content generation engine + industry knowledge base + pricing logic
- `rag.py` — local TF-IDF case-study retrieval store (persists custom entries to `case_studies.json`)
- `evaluation.py` — heuristic (non-LLM) proposal scoring
- `governance.py` — risky-claim scanner + disclaimer text
- `proposal_log.py` — local CSV logging for the dashboard (`proposal_log.csv`)
- `qa.py` — extractive Q&A over generated proposal text
- `docx_export.py` — renders the generated sections into a downloadable Word document
- `requirements.txt` — `streamlit`, `python-docx`, `scikit-learn`, `pandas`

`case_studies.json` and `proposal_log.csv` are created automatically on first use (git-ignore them
if you don't want sample data committed).

## Extending it
- Add more industries to `INDUSTRY_INSIGHTS` in `templates.py`.
- Adjust `PHASE_ALLOCATION` / `TIER_RULES` in `templates.py` to change pricing logic.
- Add more keyword rules to `URGENCY_KEYWORDS` / `COMPLEXITY_KEYWORDS` in `agents.py`.
- If you later want to add an LLM call (optional, not required), the natural seam is inside
  `WriterAgent.run()` in `agents.py` — everything else (form, tabs, evaluation, docx export)
  stays the same.
