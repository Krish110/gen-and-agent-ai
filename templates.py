"""
Rule-based content generation engine for the AI Sales Proposal Generator.
No LLM / API calls — everything here is deterministic template logic
driven by the customer requirements the user fills into the Streamlit form.
"""

from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Industry knowledge base — pain points, value props, default deliverables
# ---------------------------------------------------------------------------
INDUSTRY_INSIGHTS = {
    "E-commerce": {
        "pain_point": "cart abandonment, inconsistent customer support response times, and fragmented marketing data",
        "value_prop": "streamline the customer journey and recover revenue that is currently being lost to friction and delay",
        "deliverables": ["Storefront/checkout audit & recommendations", "Customer support workflow setup",
                          "Marketing automation integration", "Performance dashboard"],
    },
    "Marketing / Digital Agency": {
        "pain_point": "manual reporting, slow campaign turnaround, and difficulty proving ROI to clients",
        "value_prop": "automate the repetitive parts of campaign management so the team can focus on strategy and creative",
        "deliverables": ["Campaign workflow automation", "Client reporting dashboard", "Content/creative pipeline setup",
                          "ROI tracking framework"],
    },
    "Healthcare": {
        "pain_point": "administrative overhead, appointment no-shows, and disconnected patient communication",
        "value_prop": "reduce administrative burden while keeping patient data handling compliant and secure",
        "deliverables": ["Patient communication workflow", "Scheduling & reminders system",
                          "Compliance-aligned data handling review", "Staff training materials"],
    },
    "Finance / Banking": {
        "pain_point": "manual reconciliation, slow client onboarding, and compliance reporting overhead",
        "value_prop": "cut manual processing time while strengthening auditability and regulatory alignment",
        "deliverables": ["Process automation for onboarding", "Reporting & audit trail setup",
                          "Risk/compliance checklist integration", "Staff enablement session"],
    },
    "SaaS / Technology": {
        "pain_point": "high customer churn, slow feature adoption, and support ticket backlog",
        "value_prop": "improve activation and retention through better onboarding and faster support resolution",
        "deliverables": ["Onboarding flow redesign", "Support automation setup", "Usage analytics dashboard",
                          "Churn-risk alerting"],
    },
    "Retail": {
        "pain_point": "inventory visibility gaps, inconsistent in-store/online experience, and slow promotions turnaround",
        "value_prop": "unify inventory and customer data so promotions and restocking decisions happen faster",
        "deliverables": ["Inventory visibility dashboard", "Omnichannel workflow setup", "Promotions calendar automation",
                          "Sales performance reporting"],
    },
    "Manufacturing": {
        "pain_point": "supply chain visibility gaps, manual quality reporting, and vendor coordination delays",
        "value_prop": "give the team real-time visibility into supply chain and quality data to cut delays",
        "deliverables": ["Vendor coordination workflow", "Quality reporting automation", "Supply chain dashboard",
                          "Process documentation"],
    },
    "Education": {
        "pain_point": "manual admissions processing, inconsistent student communication, and limited data on outcomes",
        "value_prop": "free up staff time from repetitive admin work and give leadership clearer outcome data",
        "deliverables": ["Admissions workflow automation", "Student communication system", "Outcomes dashboard",
                          "Staff training session"],
    },
    "Other": {
        "pain_point": "manual, repetitive processes that slow the team down and make reporting difficult",
        "value_prop": "streamline core workflows and give leadership clearer, faster visibility into performance",
        "deliverables": ["Process audit & recommendations", "Workflow automation setup", "Reporting dashboard",
                          "Team enablement session"],
    },
}

CURRENCY_SYMBOLS = {"USD ($)": "$", "INR (\u20b9)": "\u20b9", "EUR (\u20ac)": "\u20ac", "GBP (\u00a3)": "\u00a3"}

# ---------------------------------------------------------------------------
# Pricing tiers — allocation percentages across common project phases
# ---------------------------------------------------------------------------
PHASE_ALLOCATION = [
    ("Discovery & Strategy", 0.15),
    ("Design & Solution Architecture", 0.20),
    ("Build / Implementation", 0.40),
    ("Testing & Quality Assurance", 0.10),
    ("Deployment & Training", 0.10),
    ("Post-Launch Support (30 days)", 0.05),
]

TIER_RULES = [
    (0, 5000, "Starter"),
    (5000, 20000, "Growth"),
    (20000, float("inf"), "Enterprise"),
]


def _fmt_money(amount, symbol):
    return f"{symbol}{amount:,.0f}"


def pick_tier(budget):
    for lo, hi, name in TIER_RULES:
        if lo <= budget < hi:
            return name
    return "Enterprise"


def build_pricing_table(budget, symbol):
    tier = pick_tier(budget)
    rows = []
    for phase, pct in PHASE_ALLOCATION:
        rows.append((phase, pct, budget * pct))
    return tier, rows


def format_pricing_section(data):
    symbol = CURRENCY_SYMBOLS.get(data["currency"], "$")
    budget = data["budget"]
    tier, rows = build_pricing_table(budget, symbol)

    lines = []
    lines.append(f"**Recommended Tier: {tier}**\n")
    lines.append(
        f"Based on the stated budget of {_fmt_money(budget, symbol)}, this proposal assumes the "
        f"**{tier}** engagement tier. Allocation below is an estimate for planning purposes; a fixed "
        f"quote will follow scope sign-off.\n"
    )
    lines.append("| Phase | % of Budget | Estimated Amount |")
    lines.append("|---|---|---|")
    for phase, pct, amt in rows:
        lines.append(f"| {phase} | {pct*100:.0f}% | {_fmt_money(amt, symbol)} |")
    lines.append(f"| **Total** | **100%** | **{_fmt_money(budget, symbol)}** |")
    lines.append("")
    lines.append("**Pricing Assumptions:**")
    assumptions = [
        f"Estimate assumes a project timeline of {data['timeline_weeks']} weeks; scope changes may affect cost.",
        "Pricing excludes third-party licensing, API, or hosting costs unless explicitly listed above.",
        f"Team size assumed for delivery: {data['team_size']} people." if data.get("team_size") else
        "Team size to be confirmed during discovery.",
        "50% due at kickoff, 30% at midpoint milestone, 20% on final delivery (standard terms; negotiable).",
        "Estimate valid for 30 days from the date of this proposal.",
    ]
    for a in assumptions:
        lines.append(f"- {a}")
    return tier, "\n".join(lines)


def format_executive_summary(data):
    insight = INDUSTRY_INSIGHTS[data["industry"]]
    return (
        f"{data['client_company']} is looking to {data['project_title'].lower() if data['project_title'] else 'address a key operational challenge'}. "
        f"Organizations in {data['industry']} commonly face {insight['pain_point']}. "
        f"{data['sender_company']} proposes a solution designed to {insight['value_prop']}.\n\n"
        f"This proposal outlines our understanding of {data['client_company']}'s requirements, our proposed "
        f"approach, a delivery timeline of approximately {data['timeline_weeks']} weeks, and investment "
        f"details for your review."
    )


def format_proposal_body(data):
    insight = INDUSTRY_INSIGHTS[data["industry"]]
    objectives = [o.strip() for o in data["objectives"].splitlines() if o.strip()] or [
        "Improve operational efficiency", "Reduce manual effort", "Provide clearer visibility into performance"
    ]
    deliverables = [d.strip() for d in data["deliverables"].splitlines() if d.strip()] or insight["deliverables"]

    sections = []
    sections.append("### 1. Problem Statement")
    sections.append(
        f"{data['client_company']} has shared the following context:\n\n> {data['requirements']}\n\n"
        f"This is a common challenge in {data['industry']}, where teams often struggle with "
        f"{insight['pain_point']}."
    )

    sections.append("### 2. Business Objectives")
    sections.append("\n".join(f"- {o}" for o in objectives))

    sections.append("### 3. Proposed Solution")
    sections.append(
        f"{data['sender_company']} proposes a solution to {insight['value_prop']}. Our approach combines "
        f"a structured discovery phase with iterative delivery, so {data['client_company']} sees progress "
        f"early and can adjust direction before final rollout."
    )

    sections.append("### 4. Scope of Work & Deliverables")
    sections.append("\n".join(f"- {d}" for d in deliverables))

    sections.append("### 5. Timeline")
    sections.append(build_timeline_text(data["timeline_weeks"]))

    sections.append("### 6. Team & Engagement Model")
    team_line = (
        f"We propose a delivery team of {data['team_size']} people, working closely with your point of "
        f"contact, {data['client_contact']}."
        if data.get("team_size")
        else f"Team composition will be finalized during discovery in coordination with {data['client_contact']}."
    )
    sections.append(team_line)

    sections.append("### 7. Terms")
    sections.append(
        "- This proposal is valid for 30 days from the date below.\n"
        "- Payment terms: 50% at kickoff, 30% at midpoint milestone, 20% on final delivery.\n"
        "- Any changes to scope will be documented in a written change order before work proceeds."
    )
    return "\n\n".join(sections)


def build_timeline_text(weeks):
    try:
        weeks = int(weeks)
    except (TypeError, ValueError):
        weeks = 4
    milestones = [
        ("Discovery & Kickoff", max(1, round(weeks * 0.15))),
        ("Design & Planning", max(1, round(weeks * 0.20))),
        ("Build / Implementation", max(1, round(weeks * 0.40))),
        ("Testing & Refinement", max(1, round(weeks * 0.15))),
        ("Deployment & Handover", max(1, round(weeks * 0.10))),
    ]
    lines = []
    running = 0
    for name, dur in milestones:
        start = running + 1
        end = running + dur
        lines.append(f"- **Week {start}-{end}:** {name}")
        running = end
    return "\n".join(lines)


def format_followup_email(data):
    return (
        f"Subject: Proposal for {data['project_title'] or 'Your Project'} — {data['sender_company']}\n\n"
        f"Hi {data['client_contact'] or 'there'},\n\n"
        f"Thank you for the opportunity to put together this proposal for {data['client_company']}. "
        f"I've attached the full document, which covers our understanding of your requirements, the "
        f"proposed approach, timeline, and investment.\n\n"
        f"A few highlights:\n"
        f"- Delivery timeline: approximately {data['timeline_weeks']} weeks\n"
        f"- Investment: {CURRENCY_SYMBOLS.get(data['currency'], '$')}{data['budget']:,.0f} "
        f"(tiered breakdown enclosed)\n\n"
        f"I'd love to walk you through it — would you have 20 minutes this week or early next week? "
        f"Happy to work around your schedule.\n\n"
        f"Best regards,\n{data['sender_name']}\n{data['sender_company']}\n{data['sender_email']}"
    )


def format_followup_strategy(data):
    today = date.today()
    steps = [
        (0, "Send proposal", "Email the proposal with a short personal note referencing the conversation so far."),
        (2, "Confirm receipt", "Quick check-in to confirm the proposal arrived and answer any first questions."),
        (5, "Value follow-up", "Share a relevant case study, stat, or quick win related to their industry pain point."),
        (10, "Direct check-in", "Ask directly whether they need anything else to make a decision; offer a call."),
        (20, "Final nudge", "Note the 30-day validity window and offer to revisit scope/pricing if priorities shifted."),
    ]
    lines = ["| Day | Touchpoint | Purpose |", "|---|---|---|"]
    for offset, name, purpose in steps:
        d = today + timedelta(days=offset)
        lines.append(f"| Day {offset} ({d.strftime('%b %d')}) | {name} | {purpose} |")
    return "\n".join(lines)


def generate_all(data):
    """Returns a dict of all generated sections."""
    tier, pricing_md = format_pricing_section(data)
    return {
        "executive_summary": format_executive_summary(data),
        "proposal_body": format_proposal_body(data),
        "pricing_md": pricing_md,
        "pricing_tier": tier,
        "followup_email": format_followup_email(data),
        "followup_strategy_md": format_followup_strategy(data),
    }
