"""
Report generation: HTML (Jinja2) and PDF (ReportLab).

ReportLab is used for PDF rather than converting HTML with an external
binary like wkhtmltopdf -- ReportLab is pure Python with no system
dependency, which matters for deploying on Render's free tier where we
can't guarantee external binaries are installed.
"""

from __future__ import annotations

import io
import re
from datetime import datetime
from pathlib import Path

import markdown as markdown_lib
from jinja2 import Environment, FileSystemLoader
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from modules.cleaner import CleaningLog
from modules.ml_readiness import MLReadinessResult
from modules.profiler import DatasetProfile
from modules.quality import QualityScore

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_TIER_COLORS = {
    "excellent": colors.HexColor("#2e7d32"),
    "good": colors.HexColor("#558b2f"),
    "fair": colors.HexColor("#f9a825"),
    "poor": colors.HexColor("#c62828"),
}

_SEVERITY_COLORS = {
    "high": colors.HexColor("#c62828"),
    "medium": colors.HexColor("#f9a825"),
    "low": colors.HexColor("#558b2f"),
}


def _score_tier(score: float) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "good"
    if score >= 60:
        return "fair"
    return "poor"


# ---------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------

def _render_markdown(text: str | None) -> str | None:
    """Convert AI-generated markdown (bullets, bold) to real HTML.
    Without this, text like '- **age and income**' renders as literal
    asterisks and dashes instead of an actual formatted list."""
    if text is None:
        return None
    return markdown_lib.markdown(text)


def generate_html_report(
    profile: DatasetProfile,
    quality: QualityScore,
    log: CleaningLog,
    filename: str,
    executive_summary: str | None = None,
    business_insights: str | None = None,
    ml_readiness: MLReadinessResult | None = None,
) -> str:
    """Render the full report to an HTML string. AI sections are
    optional -- the report is fully usable without them."""
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))
    template = env.get_template("report.html")

    return template.render(
        report_title="Data Intelligence Report",
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        filename=filename,
        profile=profile,
        quality=quality,
        quality_tier=_score_tier(quality.overall_score),
        cleaning_actions=log.actions,
        executive_summary=_render_markdown(executive_summary),
        business_insights=_render_markdown(business_insights),
        ml_readiness=ml_readiness,
        ml_readiness_tier=_score_tier(ml_readiness.readiness_score) if ml_readiness else None,
    )


# ---------------------------------------------------------------------
# PDF report
# ---------------------------------------------------------------------

def _markdown_inline_to_reportlab(text: str) -> str:
    """Convert a line of markdown to ReportLab's Paragraph mini-markup
    (a small XML-like subset supporting <b>, <i>, etc. -- NOT full
    HTML). Only handles **bold**, which is the one markdown feature our
    AI prompts actually ask the model to use."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def _markdown_block_to_flowables(text: str, styles) -> list:
    """Split AI-generated markdown text into ReportLab flowables:
    '- ' lines become a bulleted list, everything else becomes plain
    paragraphs. Mirrors _render_markdown()'s job but targets ReportLab's
    flowable model instead of HTML."""
    flowables = []
    bullet_items = []

    def _flush_bullets():
        if bullet_items:
            flowables.append(
                ListFlowable(
                    [ListItem(Paragraph(item, styles["Normal"])) for item in bullet_items],
                    bulletType="bullet",
                    leftIndent=18,
                )
            )
            bullet_items.clear()

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        converted = _markdown_inline_to_reportlab(line)
        if line.startswith("- ") or line.startswith("* "):
            bullet_items.append(converted[2:])
        else:
            _flush_bullets()
            flowables.append(Paragraph(converted, styles["Normal"]))
            flowables.append(Spacer(1, 6))

    _flush_bullets()
    return flowables


def _score_badge_table(score: float, label: str, styles) -> Table:
    tier = _score_tier(score)
    cell_style = ParagraphStyle(
        "Badge", parent=styles["Normal"], textColor=colors.white,
        fontSize=16, fontName="Helvetica-Bold", alignment=1,
    )
    t = Table(
        [[Paragraph(f"{score}%", cell_style)]],
        colWidths=[1.3 * inch], rowHeights=[0.4 * inch],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _TIER_COLORS[tier]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    return t


def generate_pdf_report(
    profile: DatasetProfile,
    quality: QualityScore,
    log: CleaningLog,
    filename: str,
    executive_summary: str | None = None,
    business_insights: str | None = None,
    ml_readiness: MLReadinessResult | None = None,
) -> bytes:
    """Build the same report as generate_html_report(), as PDF bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=colors.HexColor("#1a1a1a"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#4C78A8"), spaceBefore=18)
    meta = ParagraphStyle("Meta", parent=styles["Normal"], textColor=colors.HexColor("#666666"), fontSize=9)

    story = []
    story.append(Paragraph("Data Intelligence Report", h1))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} &middot; Source file: {filename}", meta
    ))
    story.append(Spacer(1, 16))

    # --- Overview ---
    story.append(Paragraph("Overview", h2))
    overview_rows = [
        ["Rows", str(profile.n_rows)],
        ["Columns", str(profile.n_columns)],
        ["Memory usage", f"{profile.memory_usage_mb} MB"],
        ["Numeric columns", ", ".join(profile.numerical_columns) or "—"],
        ["Categorical columns", ", ".join(profile.categorical_columns) or "—"],
    ]
    _kv_table_style = TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])
    overview_table = Table(overview_rows, colWidths=[1.8 * inch, 4.5 * inch])
    overview_table.setStyle(_kv_table_style)
    story.append(overview_table)

    # --- Data Quality ---
    story.append(Paragraph("Data Quality", h2))
    story.append(_score_badge_table(quality.overall_score, "quality", styles))
    story.append(Spacer(1, 8))
    quality_rows = [
        ["Completeness", f"{quality.completeness_score}%"],
        ["Duplicate score", f"{quality.duplicate_score}%"],
        ["Consistency", f"{quality.consistency_score}%"],
        ["Validity", f"{quality.validity_score}%"],
    ]
    quality_table = Table(quality_rows, colWidths=[1.8 * inch, 4.5 * inch])
    quality_table.setStyle(_kv_table_style)
    story.append(quality_table)

    # --- Cleaning Log ---
    story.append(Paragraph("Cleaning Log", h2))
    if log.actions:
        header = ["Column", "Issue", "Method", "Rows"]
        rows = [header] + [
            [a.column, a.issue, a.method, str(a.rows_affected)] for a in log.actions
        ]
        cleaning_table = Table(rows, colWidths=[1.1 * inch, 1.6 * inch, 2.2 * inch, 0.8 * inch])
        cleaning_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f5")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(cleaning_table)
    else:
        story.append(Paragraph("No cleaning actions were necessary — the dataset was already clean.", styles["Normal"]))

    # --- AI sections ---
    if executive_summary:
        story.append(Paragraph("Executive Summary", h2))
        story.extend(_markdown_block_to_flowables(executive_summary, styles))

    if business_insights:
        story.append(Paragraph("Business Insights", h2))
        story.extend(_markdown_block_to_flowables(business_insights, styles))

    # --- ML Readiness ---
    if ml_readiness:
        story.append(Paragraph("ML Readiness", h2))
        story.append(_score_badge_table(ml_readiness.readiness_score, "readiness", styles))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Inferred task: <b>{ml_readiness.inferred_task}</b>", styles["Normal"]))
        story.append(Spacer(1, 8))
        for issue in ml_readiness.issues:
            issue_style = ParagraphStyle(
                "Issue", parent=styles["Normal"], borderColor=_SEVERITY_COLORS[issue.severity],
                borderWidth=0, leftIndent=10, spaceBefore=4, spaceAfter=4,
            )
            story.append(Paragraph(
                f"<b>{issue.category}</b> ({issue.severity}) — {issue.description}", issue_style
            ))

    doc.build(story)
    return buffer.getvalue()
