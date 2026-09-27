"""Builds a downloadable .docx version of the generated proposal."""

import io
import re
from datetime import date

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


def _add_markdown_table(doc, md_lines):
    rows = [l for l in md_lines if l.strip().startswith("|")]
    if not rows:
        return
    rows = [r for r in rows if not re.match(r"^\|[\s\-|]+\|$", r.strip())]
    data = [[c.strip().strip("*") for c in r.strip().strip("|").split("|")] for r in rows]
    if not data:
        return
    table = doc.add_table(rows=len(data), cols=len(data[0]))
    table.style = "Light Grid Accent 1"
    for i, row in enumerate(data):
        for j, cell in enumerate(row):
            table.cell(i, j).text = cell


def _add_inline_runs(paragraph, text):
    """Splits text on **bold** and *italic* markers and adds runs accordingly."""
    parts = re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        else:
            paragraph.add_run(part)


def _add_markdown_block(doc, text):
    """Very small markdown-ish renderer: handles #### headings, bullets, tables, inline bold."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            _add_markdown_table(doc, table_lines)
            continue
        if stripped.startswith("### "):
            doc.add_heading(stripped[4:], level=2)
        elif stripped.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            _add_inline_runs(p, stripped[2:])
        elif stripped == "":
            pass
        else:
            p = doc.add_paragraph()
            _add_inline_runs(p, stripped)
        i += 1


def build_docx(data, generated):
    doc = Document()

    # Title
    title = doc.add_heading(data["project_title"] or "Business Proposal", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub.add_run(f"Prepared for {data['client_company']}  |  {date.today().strftime('%B %d, %Y')}")
    sub_run.italic = True

    doc.add_paragraph(f"Prepared by: {data['sender_name']}, {data['sender_company']}")
    doc.add_paragraph(f"Contact: {data['sender_email']}")

    doc.add_page_break()

    doc.add_heading("Executive Summary", level=1)
    doc.add_paragraph(generated["executive_summary"])

    doc.add_heading("Proposal Details", level=1)
    _add_markdown_block(doc, generated["proposal_body"])

    doc.add_heading("Pricing", level=1)
    _add_markdown_block(doc, generated["pricing_md"])

    doc.add_heading("Follow-Up Strategy", level=1)
    _add_markdown_block(doc, generated["followup_strategy_md"])

    doc.add_heading("Follow-Up Email Draft", level=1)
    for line in generated["followup_email"].split("\n"):
        doc.add_paragraph(line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
