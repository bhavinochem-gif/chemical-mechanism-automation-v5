def build_mechanism_report(
    analysis,
):

    mechanism_steps = []

    for step in analysis.get(
        "steps",
        [],
    ):

        number = step.get(
            "step_number",
            len(mechanism_steps) + 1,
        )

        transformation = step.get(
            "transformation",
            "Unknown transformation",
        )

        mechanistic_class = step.get(
            "mechanistic_class",
            "",
        )

        reagents = ", ".join(
            map(
                str,
                step.get(
                    "reagents",
                    [],
                ),
            )
        )

        intermediates = step.get(
            "intermediates",
            [],
        )

        electron_flow = step.get(
            "electron_flow",
            "",
        )

        description = (
            f"The proposed transformation is "
            f"{transformation}. "
        )

        if mechanistic_class:

            description += (
                f"The reaction is classified as "
                f"{mechanistic_class}. "
            )

        if reagents:

            description += (
                f"Relevant reagents/conditions: "
                f"{reagents}."
            )

        mechanism_steps.append(
            {
                "number": number,
                "title": transformation,
                "description": description,
                "electron_flow":
                    electron_flow,
                "intermediate":
                    "; ".join(
                        map(
                            str,
                            intermediates,
                        )
                    ),
            }
        )

    return {
        "steps":
            mechanism_steps,
        "overall_note":
            (
                "Mechanisms are AI-generated "
                "chemical hypotheses and should "
                "be experimentally/structurally "
                "verified."
            ),
    }
