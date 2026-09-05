import io
from pathlib import Path

import fitz
from PIL import Image


def process_uploaded_file(
    file_bytes: bytes,
    filename: str,
):

    suffix = Path(
        filename
    ).suffix.lower()

    images = []
    pages = []

    if suffix == ".pdf":

        document = fitz.open(
            stream=file_bytes,
            filetype="pdf",
        )

        for page_number, page in enumerate(
            document
        ):

            text = page.get_text(
                "text"
            )

            pages.append(
                {
                    "page": page_number + 1,
                    "text": text or "",
                }
            )

            pix = page.get_pixmap(
                matrix=fitz.Matrix(
                    1.7,
                    1.7,
                ),
                alpha=False,
            )

            png_bytes = pix.tobytes(
                "png"
            )

            images.append(
                {
                    "page": page_number + 1,
                    "data": png_bytes,
                    "mime_type":
                        "image/png",
                }
            )

        document.close()

    else:

        image = Image.open(
            io.BytesIO(
                file_bytes
            )
        )

        image.load()

        output = io.BytesIO()

        image.convert(
            "RGB"
        ).save(
            output,
            format="PNG",
        )

        images.append(
            {
                "page": 1,
                "data":
                    output.getvalue(),
                "mime_type":
                    "image/png",
            }
        )

        pages.append(
            {
                "page": 1,
                "text":
                    "Image-based reaction scheme."
            }
        )

    return {
        "pages": pages,
        "images": images,
    }


def get_text_from_pages(
    processed,
):

    lines = []

    for page in processed.get(
        "pages",
        [],
    ):

        lines.append(
            f"--- PAGE {page['page']} ---"
        )

        lines.append(
            page.get(
                "text",
                "",
            )
        )

    return "\n".join(
        lines
    )
