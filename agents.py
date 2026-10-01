"""
Multi-agent style pipeline for the proposal generator — fully rule-based,
zero external API calls. Each 'agent' below is a small class with one
responsibility; a PipelineTrace records what each one did, so the flow can
be shown to the user as an audit trail (this doubles as the "Prompt
Workflow / Agent Pipeline" artifact for the capstone writeup).
"""

from templates import generate_all
from rag import CaseStudyStore
from evaluation import evaluate_proposal
from governance import scan_for_risky_claims, DISCLAIMER

URGENCY_KEYWORDS = ["urgent", "asap", "immediately", "critical", "right away", "as soon as possible"]
COMPLEXITY_KEYWORDS = ["integrate", "integration", "multiple systems", "legacy", "custom",
                       "compliance", "migrate", "migration", "several departments"]


class PipelineTrace:
    def __init__(self):
        self.steps = []

    def log(self, agent, action, details=""):
        self.steps.append({"agent": agent, "action": action, "details": details})


class RequirementsAgent:
    """Parses the freeform requirements text into structured signals (rule-based NLP)."""

    def run(self, data, trace: PipelineTrace):
        text = data["requirements"].lower()
        urgency = any(k in text for k in URGENCY_KEYWORDS)
        complexity = any(k in text for k in COMPLEXITY_KEYWORDS)
        word_count = len(text.split())
        signals = {
            "urgency": urgency,
            "complexity": complexity,
            "detail_level": "high" if word_count > 40 else "low",
        }
        trace.log(
            "RequirementsAgent", "Parsed requirements text",
            f"urgency={urgency}, complexity={complexity}, detail_level={signals['detail_level']}",
        )
        return signals


class PricingAgent:
    """Reviews budget vs. complexity/urgency signals and leaves a note for the sales rep."""

    def run(self, data, signals, trace: PipelineTrace):
        notes = []
        if signals["complexity"]:
            notes.append("Complexity signals detected in requirements — consider weighting "
                         "Discovery & Solution Architecture higher than the default split.")
        if signals["urgency"]:
            notes.append("Urgency language detected — confirm team availability before "
                         "committing to the proposed timeline.")
        note = " ".join(notes) if notes else "No complexity or urgency flags — standard allocation applies."
        trace.log("PricingAgent", "Evaluated pricing fit", note)
        return note


class RAGAgent:
    """Retrieves the most relevant case study for this client's industry/requirements."""

    def __init__(self, store: CaseStudyStore):
        self.store = store

    def run(self, data, trace: PipelineTrace):
        query = f"{data['industry']} {data['requirements']}"
        match = self.store.retrieve(query, industry=data["industry"])
        if match:
            trace.log("RAGAgent", "Retrieved supporting case study", match["title"])
        else:
            trace.log("RAGAgent", "No case study match found", "Falling back to generic industry value prop.")
        return match


class WriterAgent:
    """Generates the proposal content in the requested tone."""

    def run(self, data, tone, pricing_note, trace: PipelineTrace):
        generated = generate_all(data, tone=tone, pricing_note=pricing_note)
        trace.log(
            "WriterAgent", f"Drafted proposal content ({tone} tone)",
            "Executive summary, proposal body, pricing, follow-up email & strategy generated.",
        )
        return generated


class ReviewerAgent:
    """Scores the draft and flags anything needing human review before sending."""

    def run(self, data, generated, trace: PipelineTrace):
        scores = evaluate_proposal(data, generated)
        # Only scan the executive summary (it already embeds any case-study stat via
        # "For context: ...") — not the Terms section, which has legitimate % figures.
        flags = scan_for_risky_claims(generated["executive_summary"])
        trace.log(
            "ReviewerAgent", "Scored draft",
            f"overall={scores['overall']}/100, flags={len(flags)}",
        )
        return scores, flags


def run_pipeline(data, case_study_store, tones=("Formal", "Consultative")):
    """Runs the full multi-agent pipeline and returns everything the UI needs to render."""
    trace = PipelineTrace()
    requirements_agent = RequirementsAgent()
    pricing_agent = PricingAgent()
    rag_agent = RAGAgent(case_study_store)
    writer_agent = WriterAgent()
    reviewer_agent = ReviewerAgent()

    signals = requirements_agent.run(data, trace)
    pricing_note = pricing_agent.run(data, signals, trace)
    case_study = rag_agent.run(data, trace)

    variants = {}
    for tone in tones:
        tone_data = dict(data)
        if case_study:
            tone_data["case_study_snippet"] = case_study["snippet"]
            tone_data["case_study_title"] = case_study["title"]
        generated = writer_agent.run(tone_data, tone, pricing_note, trace)
        scores, flags = reviewer_agent.run(tone_data, generated, trace)
        variants[tone] = {"generated": generated, "scores": scores, "flags": flags, "data": tone_data}

    return {
        "signals": signals,
        "pricing_note": pricing_note,
        "case_study": case_study,
        "variants": variants,
        "trace": trace.steps,
        "disclaimer": DISCLAIMER,
    }
