import streamlit as st
import pandas as pd
import plotly.express as px

from templates import INDUSTRY_INSIGHTS, CURRENCY_SYMBOLS
from docx_export import build_docx
from rag import CaseStudyStore
from agents import run_pipeline
from proposal_log import log_proposal, load_log
from qa import answer_question
from design import CUSTOM_CSS, HERO_HTML, FOOTER_HTML, section_label

st.set_page_config(page_title="AI Sales Proposal Generator", page_icon="\U0001F4C4", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(HERO_HTML, unsafe_allow_html=True)

PLOTLY_DARK = dict(
    template="plotly_dark",
    paper_bgcolor="#141826",
    plot_bgcolor="#141826",
    font=dict(family="Inter, sans-serif", color="#e9ebf1"),
    margin=dict(l=10, r=10, t=40, b=10),
)
ACCENT_SCALE = ["#f46b6b", "#f5a623", "#3ecf8e"]

if "store" not in st.session_state:
    st.session_state["store"] = CaseStudyStore()

tab_generate, tab_library, tab_dashboard = st.tabs(
    ["\U0001F4DD  Generate Proposal", "\U0001F4DA  Case Study Library", "\U0001F4CA  Sent Proposals Dashboard"]
)

# ---------------------------------------------------------------------------
# TAB 1 — Generate
# ---------------------------------------------------------------------------
with tab_generate:
    with st.form("proposal_form"):
        st.markdown(section_label("Your Company"), unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        sender_company = c1.text_input("Your company name*", "Acme Solutions")
        sender_name = c2.text_input("Your name*", "")
        sender_email = c3.text_input("Your email*", "")

        st.markdown(section_label("Client & Project"), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        client_company = c1.text_input("Client company name*", "")
        client_contact = c2.text_input("Client contact person", "")

        project_title = st.text_input("Project title*", "", placeholder="e.g. Customer Support Automation")
        industry = st.selectbox("Client industry*", list(INDUSTRY_INSIGHTS.keys()))
        requirements = st.text_area(
            "Customer requirements / problem description*", "", height=120,
            placeholder="Describe what the client told you they need...",
        )
        objectives = st.text_area("Business objectives (one per line, optional)", "", height=80)
        deliverables = st.text_area("Key deliverables (one per line, optional)", "", height=80)

        st.markdown(section_label("Commercials"), unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        currency = c1.selectbox("Currency", list(CURRENCY_SYMBOLS.keys()))
        budget = c2.number_input("Budget", min_value=0, value=10000, step=500)
        timeline_weeks = c3.number_input("Timeline (weeks)", min_value=1, value=6, step=1)
        team_size = st.number_input("Team size (optional, 0 = not specified)", min_value=0, value=0, step=1)

        submitted = st.form_submit_button("\u2728 Run Agent Pipeline", type="primary")

    if submitted:
        required = {
            "Your company name": sender_company, "Your name": sender_name, "Your email": sender_email,
            "Client company name": client_company, "Project title": project_title,
            "Customer requirements": requirements,
        }
        missing = [k for k, v in required.items() if not v.strip()]
        if missing:
            st.error(f"Please fill in: {', '.join(missing)}")
        else:
            data = {
                "sender_company": sender_company, "sender_name": sender_name, "sender_email": sender_email,
                "client_company": client_company, "client_contact": client_contact or "there",
                "project_title": project_title, "industry": industry, "requirements": requirements,
                "objectives": objectives, "deliverables": deliverables, "currency": currency,
                "budget": float(budget), "timeline_weeks": int(timeline_weeks),
                "team_size": int(team_size) if team_size else None,
            }
            with st.spinner("Running agent pipeline..."):
                result = run_pipeline(data, st.session_state["store"])
            st.session_state["result"] = result

    if "result" in st.session_state:
        result = st.session_state["result"]

        with st.expander("\U0001F50E  Agent Pipeline Trace", expanded=False):
            for step in result["trace"]:
                st.markdown(f"**{step['agent']}** — {step['action']}  \n"
                            f"<span style='color:#9aa0b4;font-size:13px'>{step['details']}</span>",
                            unsafe_allow_html=True)

        if result["case_study"]:
            st.info(f"\U0001F4CE Case study matched via local RAG: **{result['case_study']['title']}**")

        tone_tabs = st.tabs([f"  {t}  " for t in result["variants"].keys()])
        for tone, tab in zip(result["variants"].keys(), tone_tabs):
            variant = result["variants"][tone]
            gen = variant["generated"]
            data = variant["data"]

            with tab:
                with st.container(border=True):
                    st.markdown(section_label("Quality Scores"), unsafe_allow_html=True)
                    score_cols = st.columns(5)
                    score_cols[0].metric("Overall", f"{variant['scores']['overall']}")
                    score_cols[1].metric("Specificity", f"{variant['scores']['specificity']}")
                    score_cols[2].metric("Clarity", f"{variant['scores']['clarity']}")
                    score_cols[3].metric("Tone", f"{variant['scores']['tone']}")
                    score_cols[4].metric("Pricing", f"{variant['scores']['pricing_consistency']}")

                    if variant["flags"]:
                        with st.expander(f"\u26a0\ufe0f {len(variant['flags'])} quantified claim(s) flagged for review"):
                            for f in variant["flags"]:
                                st.warning(f"\u2026{f}\u2026")

                st.write("")
                content_tabs = st.tabs(["Executive Summary", "Full Proposal", "Pricing", "Follow-Up Email", "Follow-Up Strategy"])
                with content_tabs[0]:
                    st.markdown(gen["executive_summary"])
                with content_tabs[1]:
                    st.markdown(gen["proposal_body"])
                with content_tabs[2]:
                    st.markdown(gen["pricing_md"])
                with content_tabs[3]:
                    st.text_area(f"Draft email ({tone})", gen["followup_email"], height=260, key=f"email_{tone}")
                with content_tabs[4]:
                    st.markdown(gen["followup_strategy_md"])

                st.caption(f"\u2139\ufe0f {result['disclaimer']}")
                approved = st.checkbox(
                    "I've reviewed this draft and approve it for sending to the client",
                    key=f"approved_{tone}",
                )

                dl_col, log_col = st.columns(2)
                with dl_col:
                    if approved:
                        docx_buf = build_docx(data, gen)
                        st.download_button(
                            f"\u2b07\ufe0f Download {tone} Proposal (.docx)", data=docx_buf,
                            file_name=f"Proposal_{data['client_company'].replace(' ', '_')}_{tone}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"dl_{tone}",
                        )
                    else:
                        st.caption("Approve the draft above to unlock the download.")
                with log_col:
                    if approved and st.button(f"\U0001F4CB Log as Sent ({tone})", key=f"log_{tone}"):
                        log_proposal(data, gen["pricing_tier"], tone, variant["scores"]["overall"])
                        st.success("Logged — see the Dashboard tab.")

        st.markdown(section_label("Ask About This Proposal"), unsafe_allow_html=True)
        st.caption("Extractive Q&A over the generated content — retrieves the matching section, no LLM call.")
        q_tone = st.selectbox("Which variant to ask about?", list(result["variants"].keys()), key="qa_tone")
        question = st.text_input("Ask a question (e.g. 'what's included in the price?')", key="qa_input")
        if question:
            answer = answer_question(result["variants"][q_tone]["generated"], question)
            with st.container(border=True):
                st.markdown(f"**Answer:**\n\n{answer}")

# ---------------------------------------------------------------------------
# TAB 2 — Case Study Library
# ---------------------------------------------------------------------------
with tab_library:
    st.markdown(section_label("Add a Case Study"), unsafe_allow_html=True)
    st.caption(
        "Retrieved automatically via local TF-IDF similarity (no API) and inserted into proposals as "
        "social proof. Add your own past wins so future proposals cite real results."
    )
    store = st.session_state["store"]
    with st.form("add_case_study"):
        c1, c2 = st.columns(2)
        cs_title = c1.text_input("Title (short, e.g. 'Retail chatbot cut tickets 40%')")
        cs_industry = c2.selectbox("Industry", list(INDUSTRY_INSIGHTS.keys()), key="cs_industry")
        cs_snippet = st.text_area("Snippet (1-2 sentences describing the result)", height=80)
        add_submitted = st.form_submit_button("\u2795 Add Case Study")
        if add_submitted:
            if cs_title.strip() and cs_snippet.strip():
                store.add(cs_title.strip(), cs_industry, cs_snippet.strip())
                st.success("Added — it will be considered on the next proposal generation.")
            else:
                st.error("Please fill in both the title and the snippet.")

    st.markdown(section_label("Current Library"), unsafe_allow_html=True)
    by_industry = {}
    for item in store.all_items():
        by_industry.setdefault(item["industry"], []).append(item)

    for industry_name, items in by_industry.items():
        with st.container(border=True):
            st.markdown(f"**{industry_name}**")
            for item in items:
                st.markdown(f"- **{item['title']}** — {item['snippet']}")

# ---------------------------------------------------------------------------
# TAB 3 — Dashboard
# ---------------------------------------------------------------------------
with tab_dashboard:
    rows = load_log()
    if not rows:
        st.info("No proposals logged yet. Approve and log a proposal from the Generate tab to see it here.")
    else:
        df = pd.DataFrame(rows)
        df["budget"] = pd.to_numeric(df["budget"], errors="coerce")
        df["overall_score"] = pd.to_numeric(df["overall_score"], errors="coerce")

        st.markdown(section_label("Overview"), unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Proposals Logged", len(df))
        c2.metric("Total Pipeline Value", f"{df['budget'].sum():,.0f}")
        c3.metric("Avg. Quality Score", f"{df['overall_score'].mean():.0f}")

        st.markdown(section_label("Breakdown"), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            tier_counts = df["tier"].value_counts().reset_index()
            tier_counts.columns = ["Tier", "Count"]
            fig = px.bar(tier_counts, x="Tier", y="Count", title="By Tier", color="Tier",
                         color_discrete_sequence=["#3ecf8e", "#7c9eff", "#f5a623"])
            fig.update_layout(**PLOTLY_DARK, showlegend=False)
            st.plotly_chart(fig, width='stretch')
        with c2:
            outcome_counts = df["outcome"].value_counts().reset_index()
            outcome_counts.columns = ["Outcome", "Count"]
            fig = px.pie(outcome_counts, names="Outcome", values="Count", title="By Outcome", hole=0.55,
                         color_discrete_sequence=["#3ecf8e", "#f5a623", "#f46b6b", "#7c9eff"])
            fig.update_layout(**PLOTLY_DARK)
            st.plotly_chart(fig, width='stretch')

        industry_counts = df["industry"].value_counts().reset_index()
        industry_counts.columns = ["Industry", "Count"]
        fig = px.bar(industry_counts, x="Count", y="Industry", orientation="h", title="By Industry",
                     color="Count", color_continuous_scale=["#141826", "#3ecf8e"])
        fig.update_layout(**PLOTLY_DARK, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, width='stretch')

        st.markdown(section_label("Proposal Log"), unsafe_allow_html=True)
        with st.container(border=True):
            st.dataframe(
                df[["date", "client_company", "industry", "tier", "budget", "tone", "overall_score", "outcome"]],
                width='stretch', hide_index=True,
            )

st.markdown(FOOTER_HTML, unsafe_allow_html=True)
