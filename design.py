"""
Visual design system for the Streamlit app: custom CSS (typography, cards,
buttons, tabs, metrics), a hero banner, and a footer. Kept separate from
app.py so the page logic isn't buried in markup.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=swap');

:root {
    --bg: #0b0d14;
    --bg-card: #141826;
    --bg-card-hover: #171c2c;
    --border: #262c40;
    --accent: #3ecf8e;
    --accent-soft: rgba(62, 207, 142, 0.12);
    --accent2: #7c9eff;
    --text: #e9ebf1;
    --text-dim: #9aa0b4;
    --danger: #f46b6b;
    --warn: #f5a623;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: var(--bg); }

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

h1, h2, h3 { font-family: 'Sora', 'Inter', sans-serif; letter-spacing: -0.01em; }
h2 { font-weight: 700 !important; margin-top: 0.3em !important; }
h3 { font-weight: 700 !important; color: var(--text); }

/* ---- Hero banner ---- */
.hero {
    background: linear-gradient(135deg, rgba(62,207,142,0.10) 0%, rgba(124,158,255,0.06) 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 22px;
}
.hero-title {
    font-family: 'Sora', sans-serif;
    font-size: 30px;
    font-weight: 800;
    background: linear-gradient(90deg, #3ecf8e 0%, #7c9eff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.hero-sub { color: var(--text-dim); font-size: 15px; margin-bottom: 14px; max-width: 760px; }
.pill-row { display: flex; flex-wrap: wrap; gap: 8px; }
.pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--bg-card); border: 1px solid var(--border);
    color: var(--text-dim); font-size: 12.5px; font-weight: 500;
    padding: 5px 12px; border-radius: 999px;
}

/* ---- Cards (st.container(border=True)) ---- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg-card);
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 6px 4px;
}

/* ---- Buttons ---- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    background: linear-gradient(90deg, #3ecf8e 0%, #34b57d 100%);
    color: #06140d;
    font-weight: 700;
    border: none;
    border-radius: 10px;
    padding: 0.55em 1.3em;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    box-shadow: 0 0 0 rgba(62,207,142,0);
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(62,207,142,0.25);
}
.stButton > button:disabled { opacity: 0.4; }

/* ---- Inputs ---- */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}

/* ---- Tabs ---- */
div[data-baseweb="tab-list"] {
    gap: 4px; background: var(--bg-card); padding: 5px; border-radius: 12px;
    border: 1px solid var(--border);
}
button[data-baseweb="tab"] {
    border-radius: 8px !important; font-weight: 600; color: var(--text-dim);
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: var(--accent-soft); color: var(--accent) !important;
}

/* ---- Metrics ---- */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 14px 8px 14px;
}
div[data-testid="stMetricLabel"] { color: var(--text-dim); font-size: 12.5px; }
div[data-testid="stMetricValue"] { color: var(--accent); font-weight: 800; }

/* ---- Alerts ---- */
div[data-testid="stAlert"] { border-radius: 12px; border: 1px solid var(--border); }

/* ---- Expander ---- */
details { border: 1px solid var(--border) !important; border-radius: 12px !important; background: var(--bg-card); }

/* ---- Dataframe ---- */
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }

/* ---- Section divider ---- */
.section-label {
    display: flex; align-items: center; gap: 10px;
    color: var(--text-dim); font-size: 13px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.06em;
    margin: 22px 0 10px 0;
}
.section-label::after { content: ""; flex: 1; height: 1px; background: var(--border); }

/* ---- Footer ---- */
.app-footer {
    text-align: center; color: var(--text-dim); font-size: 12.5px;
    padding: 28px 0 8px 0; border-top: 1px solid var(--border); margin-top: 32px;
}
.app-footer b { color: var(--text); }
</style>
"""

HERO_HTML = """
<div class="hero">
  <div class="hero-title">\U0001F4C4 AI Sales Proposal Generator</div>
  <div class="hero-sub">
    A rule-based multi-agent pipeline that turns customer requirements into a complete,
    reviewed proposal package — executive summary, pricing, case-study-backed value prop,
    follow-up email, and a follow-up strategy. Every step runs locally.
  </div>
  <div class="pill-row">
    <span class="pill">\U0001F512 No API key</span>
    <span class="pill">\U0001F9E9 Multi-agent pipeline</span>
    <span class="pill">\U0001F4DA Local RAG (TF-IDF)</span>
    <span class="pill">\U0001F6E1\uFE0F Governance checks</span>
    <span class="pill">\U0001F4CA Quality scoring</span>
  </div>
</div>
"""

FOOTER_HTML = """
<div class="app-footer">
  Built with a <b>rule-based multi-agent pipeline</b> — requirements parsing, pricing review,
  local case-study retrieval, drafting, and automated review all run offline, with no external
  API calls or model inference.
</div>
"""


def section_label(text):
    """Returns the HTML for a small uppercase section divider label."""
    return f'<div class="section-label">{text}</div>'
