import streamlit as st
import pandas as pd

from templates import INDUSTRY_INSIGHTS, CURRENCY_SYMBOLS
from docx_export import build_docx
from rag import CaseStudyStore
from agents import run_pipeline
from proposal_log import log_proposal, load_log
from qa import answer_question

st.set_page_config(page_title="AI Sales Proposal Generator", page_icon="\U0001F4C4", layout="wide")

if "store" not in st.session_state:
    st.session_state["store"] = CaseStudyStore()

st.title("\U0001F4C4 AI Sales Proposal Generator")
st.caption(
    "Rule-based multi-agent prototype — no API key required. Requirements parsing, pricing review, "
    "case-study retrieval, drafting, and quality review all run locally."
)

tab_generate, tab_library, tab_dashboard = st.tabs(
    ["\U0001F4DD Generate Proposal", "\U0001F4DA Case Study Library", "\U0001F4CA Sent Proposals Dashboard"]
)

# ---------------------------------------------------------------------------
# TAB 1 — Generate
# ---------------------------------------------------------------------------
with tab_generate:
    with st.form("proposal_form"):
        st.subheader("Your Company")
        c1, c2, c3 = st.columns(3)
        sender_company = c1.text_input("Your company name*", "Acme Solutions")
        sender_name = c2.text_input("Your name*", "")
        sender_email = c3.text_input("Your email*", "")

        st.subheader("Client & Project")
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

        st.subheader("Commercials")
        c1, c2, c3 = st.columns(3)
        currency = c1.selectbox("Currency", list(CURRENCY_SYMBOLS.keys()))
        budget = c2.number_input("Budget", min_value=0, value=10000, step=500)
        timeline_weeks = c3.number_input("Timeline (weeks)", min_value=1, value=6, step=1)
        team_size = st.number_input("Team size (optional, 0 = not specified)", min_value=0, value=0, step=1)

        submitted = st.form_submit_button("Run Agent Pipeline", type="primary")

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
            st.session_state["approved"] = {}

    if "result" in st.session_state:
        result = st.session_state["result"]

        with st.expander("\U0001F50E Agent Pipeline Trace", expanded=False):
            for step in result["trace"]:
                st.markdown(f"**{step['agent']}** — {step['action']}  \n*{step['details']}*")

        if result["case_study"]:
            st.info(f"\U0001F4CE Case study matched via local RAG: **{result['case_study']['title']}**")

        tone_tabs = st.tabs(list(result["variants"].keys()))
        for tone, tab in zip(result["variants"].keys(), tone_tabs):
            variant = result["variants"][tone]
            gen = variant["generated"]
            data = variant["data"]

            with tab:
                score_cols = st.columns(5)
                score_cols[0].metric("Overall", f"{variant['scores']['overall']}/100")
                score_cols[1].metric("Specificity", f"{variant['scores']['specificity']}/100")
                score_cols[2].metric("Clarity", f"{variant['scores']['clarity']}/100")
                score_cols[3].metric("Tone", f"{variant['scores']['tone']}/100")
                score_cols[4].metric("Pricing consistency", f"{variant['scores']['pricing_consistency']}/100")

                if variant["flags"]:
                    with st.expander(f"\u26a0\ufe0f {len(variant['flags'])} quantified claim(s) flagged for review", expanded=False):
                        for f in variant["flags"]:
                            st.warning(f"\u2026{f}\u2026")

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
                approved_key = f"approved_{tone}"
                approved = st.checkbox(
                    "I've reviewed this draft and approve it for sending to the client",
                    key=approved_key,
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

        st.divider()
        st.subheader("\U0001F4AC Ask About This Proposal")
        st.caption("Extractive Q&A over the generated content — retrieves the matching section, no LLM call.")
        q_tone = st.selectbox("Which variant to ask about?", list(result["variants"].keys()), key="qa_tone")
        question = st.text_input("Ask a question (e.g. 'what's included in the price?')", key="qa_input")
        if question:
            answer = answer_question(result["variants"][q_tone]["generated"], question)
            st.markdown(f"**Answer:** {answer}")

# ---------------------------------------------------------------------------
# TAB 2 — Case Study Library
# ---------------------------------------------------------------------------
with tab_library:
    st.subheader("Case Study Library")
    st.caption(
        "These are retrieved automatically (via local TF-IDF similarity, no API) and inserted into "
        "proposals as social proof. Add your own past wins so future proposals cite real results."
    )
    store = st.session_state["store"]
    with st.form("add_case_study"):
        c1, c2 = st.columns(2)
        cs_title = c1.text_input("Title (short, e.g. 'Retail chatbot cut tickets 40%')")
        cs_industry = c2.selectbox("Industry", list(INDUSTRY_INSIGHTS.keys()), key="cs_industry")
        cs_snippet = st.text_area("Snippet (1-2 sentences describing the result)", height=80)
        add_submitted = st.form_submit_button("Add Case Study")
        if add_submitted:
            if cs_title.strip() and cs_snippet.strip():
                store.add(cs_title.strip(), cs_industry, cs_snippet.strip())
                st.success("Added — it will be considered on the next proposal generation.")
            else:
                st.error("Please fill in both the title and the snippet.")

    st.markdown("#### Current library")
    for item in store.all_items():
        st.markdown(f"- **[{item['industry']}]** {item['title']} — {item['snippet']}")

# ---------------------------------------------------------------------------
# TAB 3 — Dashboard
# ---------------------------------------------------------------------------
with tab_dashboard:
    st.subheader("Sent Proposals Dashboard")
    rows = load_log()
    if not rows:
        st.info("No proposals logged yet. Approve and log a proposal from the Generate tab to see it here.")
    else:
        df = pd.DataFrame(rows)
        df["budget"] = pd.to_numeric(df["budget"], errors="coerce")
        df["overall_score"] = pd.to_numeric(df["overall_score"], errors="coerce")

        c1, c2, c3 = st.columns(3)
        c1.metric("Proposals logged", len(df))
        c2.metric("Total pipeline value", f"{df['budget'].sum():,.0f}")
        c3.metric("Avg. quality score", f"{df['overall_score'].mean():.0f}/100")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**By tier**")
            st.bar_chart(df["tier"].value_counts())
        with c2:
            st.markdown("**By industry**")
            st.bar_chart(df["industry"].value_counts())

        st.markdown("**Update outcomes**")
        st.dataframe(df[["date", "client_company", "industry", "tier", "budget", "tone", "overall_score", "outcome"]],
                     use_container_width=True)

        st.markdown("**By outcome**")
        st.bar_chart(df["outcome"].value_counts())
