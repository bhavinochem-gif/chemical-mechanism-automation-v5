"""PDF report generation with lazy ReportLab import."""
import io

def reportlab_status():
    try:
        import reportlab
        return {"available": True, "version": getattr(reportlab, "Version", "unknown"), "error": None}
    except Exception as exc:
        return {"available": False, "version": None, "error": str(exc)}

def build_pdf(route):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import mm
    except Exception as exc:
        raise RuntimeError(
            "PDF generation is unavailable because ReportLab could not be imported. "
            "Check requirements.txt and redeploy the Streamlit app. Original error: " + str(exc)
        ) from exc

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Chemical Reaction Mechanism Automation — V5.2", styles["Title"]),
        Spacer(1, 8),
        Paragraph(str(route.get("route_title", "Synthetic Route")), styles["Heading2"]),
        Paragraph(str(route.get("route_summary", "")), styles["BodyText"]),
        Spacer(1, 10),
    ]

    for step in route.get("steps", []) or []:
        story.append(Paragraph(
            f"Step {step.get('step_number', '')}: {step.get('transformation', '')}",
            styles["Heading2"]
        ))
        story.append(Paragraph(
            f"Reaction class: {step.get('reaction_class', '')}", styles["BodyText"]
        ))
        reagents = step.get("reagents", []) or []
        if isinstance(reagents, str):
            reagents = [reagents]
        story.append(Paragraph(
            f"Reagents: {', '.join(map(str, reagents))}", styles["BodyText"]
        ))
        story.append(Paragraph(
            f"Conditions: {step.get('conditions_text', '')}", styles["BodyText"]
        ))

        mech = step.get("mechanism", {}) or {}
        for i, item in enumerate(mech.get("mechanism_steps", []) or [], 1):
            story.append(Paragraph(f"{i}. {item}", styles["BodyText"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Scientific disclaimer: structures, reaction classes, named reactions and mechanisms "
        "are AI-assisted interpretations and must be independently verified before use in "
        "development, regulatory, safety or manufacturing decisions.",
        styles["BodyText"]
    ))
    doc.build(story)
    return buf.getvalue()
