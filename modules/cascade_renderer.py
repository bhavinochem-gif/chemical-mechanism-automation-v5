import io

from PIL import Image, ImageDraw, ImageFont


def _font(size=22):

    try:
        return ImageFont.truetype(
            "DejaVuSans.ttf",
            size,
        )
    except Exception:
        return ImageFont.load_default()


def render_cascade(
    analysis,
):

    steps = analysis.get(
        "steps",
        [],
    )

    if not steps:
        return None

    width = max(
        1200,
        330 * len(steps),
    )

    height = 420

    image = Image.new(
        "RGB",
        (width, height),
        "white",
    )

    draw = ImageDraw.Draw(
        image
    )

    title_font = _font(28)
    body_font = _font(18)

    draw.text(
        (30, 20),
        "Synthetic Reaction Cascade",
        fill="black",
        font=title_font,
    )

    x = 40

    for index, step in enumerate(
        steps
    ):

        step_no = step.get(
            "step_number",
            index + 1,
        )

        reactants = ", ".join(
            map(
                str,
                step.get(
                    "reactants",
                    [],
                ),
            )
        )

        products = ", ".join(
            map(
                str,
                step.get(
                    "products",
                    [],
                ),
            )
        )

        draw.rounded_rectangle(
            (
                x,
                100,
                x + 250,
                260,
            ),
            radius=15,
            outline="black",
            width=2,
        )

        draw.text(
            (x + 15, 115),
            f"Step {step_no}",
            fill="black",
            font=body_font,
        )

        draw.text(
            (x + 15, 150),
            "Reactants:",
            fill="black",
            font=body_font,
        )

        draw.text(
            (x + 15, 180),
            reactants[:25],
            fill="black",
            font=body_font,
        )

        draw.text(
            (x + 15, 215),
            "→ "
            + products[:25],
            fill="black",
            font=body_font,
        )

        if index < len(steps) - 1:

            draw.line(
                (
                    x + 260,
                    180,
                    x + 315,
                    180,
                ),
                fill="black",
                width=3,
            )

            draw.polygon(
                [
                    (x + 315, 180),
                    (x + 295, 170),
                    (x + 295, 190),
                ],
                fill="black",
            )

        x += 330

    output = io.BytesIO()

    image.save(
        output,
        format="PNG",
    )

    return output.getvalue()
