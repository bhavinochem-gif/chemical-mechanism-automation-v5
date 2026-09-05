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


def render_mechanism_scheme(
    analysis,
):

    steps = analysis.get(
        "steps",
        [],
    )

    if not steps:
        return None

    width = 1500
    height = max(
        450,
        170 * len(steps),
    )

    image = Image.new(
        "RGB",
        (width, height),
        "white",
    )

    draw = ImageDraw.Draw(
        image
    )

    title_font = _font(28)
    body_font = _font(20)

    draw.text(
        (40, 20),
        "Proposed Reaction Mechanism",
        fill="black",
        font=title_font,
    )

    y = 90

    for step in steps:

        number = step.get(
            "step_number",
            "?",
        )

        transformation = str(
            step.get(
                "transformation",
                "",
            )
        )

        mechanism_class = str(
            step.get(
                "mechanistic_class",
                "",
            )
        )

        draw.rounded_rectangle(
            (50, y, 520, y + 90),
            radius=15,
            outline="black",
            width=2,
        )

        draw.text(
            (70, y + 15),
            f"Step {number}",
            fill="black",
            font=body_font,
        )

        draw.text(
            (70, y + 48),
            transformation[:48],
            fill="black",
            font=body_font,
        )

        draw.line(
            (550, y + 45, 700, y + 45),
            fill="black",
            width=3,
        )

        draw.polygon(
            [
                (700, y + 45),
                (680, y + 35),
                (680, y + 55),
            ],
            fill="black",
        )

        draw.rounded_rectangle(
            (730, y, 1430, y + 90),
            radius=15,
            outline="black",
            width=2,
        )

        draw.text(
            (750, y + 15),
            "Mechanism",
            fill="black",
            font=body_font,
        )

        draw.text(
            (750, y + 48),
            mechanism_class[:65],
            fill="black",
            font=body_font,
        )

        y += 150

    output = io.BytesIO()

    image.save(
        output,
        format="PNG",
    )

    return output.getvalue()
