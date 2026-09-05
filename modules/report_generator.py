import io


def reportlab_status():

    try:

        import reportlab

        return (
            "ReportLab available: "
            + str(
                reportlab.Version
            )
        )

    except Exception:

        return (
            "ReportLab unavailable."
        )


def build_pdf(
    analysis,
):

    try:

        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.enums import TA_CENTER
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            PageBreak,
        )

    except Exception as e:

        raise RuntimeError(
            "ReportLab is not available: "
            + str(e)
        )

    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title = styles["Title"]
    title.alignment = TA_CENTER

    heading = styles["Heading2"]
    body = styles["BodyText"]

    story = []

    story.append(
        Paragraph(
            "Chemical Reaction Mechanism Report",
            title,
        )
    )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "<b>Route Summary</b>",
            heading,
        )
    )

    summary = str(
        analysis.get(
            "route_summary",
            "",
        )
    )

    story.append(
        Paragraph(
            summary.replace(
                "&",
                "&amp;",
            ),
            body,
        )
    )

    story.append(
        Spacer(1, 15)
    )

    for step in analysis.get(
        "steps",
        [],
    ):

        story.append(
            Paragraph(
                f"Step {step.get('step_number', '')}: "
                f"{step.get('transformation', '')}",
                heading,
            )
        )

        fields = [
            (
                "Reactants",
                step.get(
                    "reactants",
                    [],
                ),
            ),
            (
                "Products",
                step.get(
                    "products",
                    [],
                ),
            ),
            (
                "Reagents",
                step.get(
                    "reagents",
                    [],
                ),
            ),
            (
                "Conditions",
                step.get(
                    "conditions",
                    "",
                ),
            ),
            (
                "Mechanistic class",
                step.get(
                    "mechanistic_class",
                    "",
                ),
            ),
            (
                "Electron flow",
                step.get(
                    "electron_flow",
                    "",
                ),
            ),
        ]

        for label, value in fields:

            if isinstance(
                value,
                list,
            ):

                value = ", ".join(
                    map(
                        str,
                        value,
                    )
                )

            story.append(
                Paragraph(
                    f"<b>{label}:</b> "
                    f"{str(value).replace('&', '&amp;')}",
                    body,
                )
            )

            story.append(
                Spacer(1, 5)
            )

        story.append(
            Spacer(1, 10)
        )

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Named Reactions",
            heading,
        )
    )

    for item in analysis.get(
        "named_reactions",
        [],
    ):

        story.append(
            Paragraph(
                f"<b>{item.get('name', '')}</b>",
                body,
            )
        )

        story.append(
            Paragraph(
                str(
                    item.get(
                        "reason",
                        "",
                    )
                ),
                body,
            )
        )

        story.append(
            Spacer(1, 8)
        )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "Important: Mechanistic assignments are "
            "AI-generated hypotheses and require "
            "scientific verification.",
            body,
        )
    )

    document.build(
        story
    )

    return output.getvalue()
