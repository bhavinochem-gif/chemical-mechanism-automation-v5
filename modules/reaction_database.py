import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "named_reactions.json"
)


def load_database():

    if not DATA_FILE.exists():
        return []

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            return json.load(f)

    except Exception:
        return []


def identify_named_reactions(
    analysis,
):

    database = load_database()

    results = []

    for step in analysis.get(
        "steps",
        [],
    ):

        combined = " ".join(
            [
                str(
                    step.get(
                        "transformation",
                        "",
                    )
                ),
                str(
                    step.get(
                        "mechanistic_class",
                        "",
                    )
                ),
                " ".join(
                    map(
                        str,
                        step.get(
                            "reagents",
                            [],
                        ),
                    )
                ),
                str(
                    step.get(
                        "conditions",
                        "",
                    )
                ),
            ]
        ).lower()

        for reaction in database:

            keywords = [
                str(x).lower()
                for x in reaction.get(
                    "keywords",
                    [],
                )
            ]

            matches = [
                x
                for x in keywords
                if x in combined
            ]

            if matches:

                results.append(
                    {
                        "step_number":
                            step.get(
                                "step_number"
                            ),
                        "name":
                            reaction.get(
                                "name",
                                "Unknown",
                            ),
                        "reason":
                            (
                                "Keyword evidence: "
                                + ", ".join(
                                    matches
                                )
                            ),
                        "confidence":
                            min(
                                0.95,
                                0.50
                                + 0.10
                                * len(matches),
                            ),
                    }
                )

    return results
