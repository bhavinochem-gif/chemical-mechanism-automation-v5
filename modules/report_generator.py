import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle


def _safe_text(value):
    if isinstance(value, list):
        return ", ".join(str(x) for x in value)
    if isinstance(value, dict):
        return str(value)
    return str(value or "")


def _add_image(story, image_bytes, max_w=175 * mm, max_h=70 * mm):
    if not image_bytes:
        return
    try:
        from PIL import Image as PILImage
        img = PILImage.open(io.BytesIO(image_bytes))
        w, h = img.size
        scale = min(max_w / w, max_h / h)
        story.append(Image(io.BytesIO(image_bytes), width=w * scale, height=h * scale))
    except Exception:
        pass


def build_pdf_report(route, source_name="route"):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=12 * mm, leftMargin=12 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small_v5", parent=styles["BodyText"], fontSize=8.5, leading=11)
    story = [
        Paragraph("Chemical Reaction Mechanism Automation — V5.1.1", styles["Title"]),
        Paragraph(f"Source: {_safe_text(source_name)}", small),
        Spacer(1, 6),
        Paragraph(_safe_text(route.get("route_title", "Synthetic route")), styles["Heading2"]),
        Paragraph(_safe_text(route.get("route_summary", "")), styles["BodyText"]),
        Spacer(1, 8),
    ]

    _add_image(story, route.get("cascade_image"), max_w=175 * mm, max_h=65 * mm)

    for n, step in enumerate(route.get("steps", []) or [], 1):
        story.append(PageBreak())
        story.append(Paragraph(f"Step {step.get('step_number', n)}: {_safe_text(step.get('transformation', 'Transformation'))}", styles["Heading2"]))
        data = [
            ["Field", "Value"],
            ["Reaction class", _safe_text(step.get("reaction_class"))],
            ["Reactants", _safe_text(step.get("reactants_smiles"))],
            ["Products", _safe_text(step.get("products_smiles"))],
            ["Reagents", _safe_text(step.get("reagents"))],
            ["Solvent", _safe_text(step.get("solvent"))],
            ["Temperature", _safe_text(step.get("temperature"))],
            ["Time", _safe_text(step.get("time"))],
            ["Pressure", _safe_text(step.get("pressure"))],
            ["Yield", _safe_text(step.get("yield"))],
            ["Confidence", _safe_text(step.get("confidence"))],
        ]
        table = Table([[Paragraph(_safe_text(a), small), Paragraph(_safe_text(b), small)] for a, b in data], colWidths=[38 * mm, 145 * mm])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story += [table, Spacer(1, 7)]

        story.append(Paragraph("Named reaction candidates", styles["Heading3"]))
        candidates = step.get("named_reactions", []) or []
        if candidates:
            for c in candidates:
                story.append(Paragraph(
                    f"{_safe_text(c.get('name'))} — {float(c.get('score', 0)):.0%} — {_safe_text(c.get('reason'))}", small
                ))
        else:
            story.append(Paragraph("No high-confidence database match.", small))

        mech = step.get("mechanism", {}) or {}
        story += [Spacer(1, 5), Paragraph("Proposed mechanism", styles["Heading3"]), Paragraph(_safe_text(mech.get("overview", "")), small)]
        for i, event in enumerate(mech.get("events", []) or [], 1):
            story.append(Paragraph(f"{i}. {_safe_text(event.get('title'))}: {_safe_text(event.get('description'))}", small))

        _add_image(story, step.get("mechanism_image"), max_w=175 * mm, max_h=70 * mm)
        story += [Spacer(1, 8), Paragraph(
            "Scientific note: structures, named reactions and mechanisms are AI-assisted proposals. "
            "Verify against the original scheme, experimental record, analytical data and chemically validated atom mapping before regulated use.", small
        )]

    doc.build(story)
    return buf.getvalue()
