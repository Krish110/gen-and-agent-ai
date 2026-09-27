import streamlit as st
from templates import INDUSTRY_INSIGHTS, CURRENCY_SYMBOLS, generate_all
from docx_export import build_docx

st.set_page_config(page_title="AI Sales Proposal Generator", page_icon="\U0001F4C4", layout="wide")

st.title("\U0001F4C4 AI Sales Proposal Generator")
st.caption(
    "Rule-based prototype — fill in customer requirements and generate a full proposal, "
    "executive summary, pricing assumptions, and a follow-up email + strategy. No API key required."
)

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
        "Customer requirements / problem description*",
        "",
        height=120,
        placeholder="Describe what the client told you they need...",
    )
    objectives = st.text_area(
        "Business objectives (one per line, optional — defaults will be used if blank)",
        "",
        height=80,
    )
    deliverables = st.text_area(
        "Key deliverables (one per line, optional — defaults will be used if blank)",
        "",
        height=80,
    )

    st.subheader("Commercials")
    c1, c2, c3 = st.columns(3)
    currency = c1.selectbox("Currency", list(CURRENCY_SYMBOLS.keys()))
    budget = c2.number_input("Budget", min_value=0, value=10000, step=500)
    timeline_weeks = c3.number_input("Timeline (weeks)", min_value=1, value=6, step=1)
    team_size = st.number_input("Team size (optional, 0 = not specified)", min_value=0, value=0, step=1)

    submitted = st.form_submit_button("Generate Proposal", type="primary")

if submitted:
    required = {
        "Your company name": sender_company,
        "Your name": sender_name,
        "Your email": sender_email,
        "Client company name": client_company,
        "Project title": project_title,
        "Customer requirements": requirements,
    }
    missing = [k for k, v in required.items() if not v.strip()]
    if missing:
        st.error(f"Please fill in: {', '.join(missing)}")
    else:
        data = {
            "sender_company": sender_company,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "client_company": client_company,
            "client_contact": client_contact or "there",
            "project_title": project_title,
            "industry": industry,
            "requirements": requirements,
            "objectives": objectives,
            "deliverables": deliverables,
            "currency": currency,
            "budget": float(budget),
            "timeline_weeks": int(timeline_weeks),
            "team_size": int(team_size) if team_size else None,
        }
        st.session_state["data"] = data
        st.session_state["generated"] = generate_all(data)

if "generated" in st.session_state:
    data = st.session_state["data"]
    gen = st.session_state["generated"]

    st.success(f"Proposal generated — recommended tier: **{gen['pricing_tier']}**")

    tabs = st.tabs(["Executive Summary", "Full Proposal", "Pricing", "Follow-Up Email", "Follow-Up Strategy"])

    with tabs[0]:
        st.markdown(gen["executive_summary"])

    with tabs[1]:
        st.markdown(gen["proposal_body"])

    with tabs[2]:
        st.markdown(gen["pricing_md"])

    with tabs[3]:
        st.text_area("Draft email (copy or edit as needed)", gen["followup_email"], height=280)

    with tabs[4]:
        st.markdown(gen["followup_strategy_md"])

    st.divider()
    docx_buf = build_docx(data, gen)
    st.download_button(
        "\u2b07\ufe0f Download Full Proposal (.docx)",
        data=docx_buf,
        file_name=f"Proposal_{data['client_company'].replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
