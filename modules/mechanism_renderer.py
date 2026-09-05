"""
V5.1 Mechanism Renderer
Robust RDKit rendering with graceful fallback.
"""

import io
import base64
from typing import Optional, Dict, Any

try:
    from rdkit import Chem
    RDKIT_AVAILABLE = True
except Exception as exc:
    Chem = None
    RDKIT_AVAILABLE = False
    RDKIT_ERROR = str(exc)


def _load_draw_module():
    """
    Load RDKit drawing only when actually required.

    This prevents an rdMolDraw2D problem from crashing
    the entire Streamlit application during startup.
    """
    try:
        from rdkit.Chem import Draw
        return Draw, None
    except Exception as exc:
        return None, str(exc)


def validate_smiles(smiles: str) -> bool:
    """Validate a SMILES string."""
    if not RDKIT_AVAILABLE:
        return False

    if not smiles:
        return False

    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False


def render_structure(
    smiles: str,
    width: int = 500,
    height: int = 300
) -> Optional[bytes]:
    """
    Render a molecule to PNG.

    Returns:
        PNG bytes or None if rendering is unavailable.
    """

    if not RDKIT_AVAILABLE:
        return None

    Draw, error = _load_draw_module()

    if Draw is None:
        return None

    try:
        mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            return None

        image = Draw.MolToImage(
            mol,
            size=(width, height)
        )

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")

        return buffer.getvalue()

    except Exception:
        return None


def render_mechanism_scheme(
    reactant_smiles: str,
    product_smiles: str,
    reagent_text: str = "",
    width: int = 900,
    height: int = 350
) -> Optional[bytes]:
    """
    Render a simple reaction scheme.

    The renderer intentionally fails gracefully if RDKit's
    drawing extension is unavailable.
    """

    if not RDKIT_AVAILABLE:
        return None

    Draw, error = _load_draw_module()

    if Draw is None:
        return None

    try:
        reactant = Chem.MolFromSmiles(reactant_smiles)
        product = Chem.MolFromSmiles(product_smiles)

        if reactant is None or product is None:
            return None

        from PIL import Image, ImageDraw, ImageFont

        left = Draw.MolToImage(
            reactant,
            size=(350, 280)
        )

        right = Draw.MolToImage(
            product,
            size=(350, 280)
        )

        canvas = Image.new(
            "RGB",
            (width, height),
            "white"
        )

        canvas.paste(
            left,
            (30, 40)
        )

        canvas.paste(
            right,
            (520, 40)
        )

        drawing = ImageDraw.Draw(canvas)

        # Reaction arrow
        y = 175

        drawing.line(
            (400, y, 500, y),
            fill="black",
            width=3
        )

        drawing.polygon(
            [
                (500, y),
                (485, y - 8),
                (485, y + 8)
            ],
            fill="black"
        )

        # Reagent text
        if reagent_text:
            try:
                font = ImageFont.load_default()

                drawing.text(
                    (400, 125),
                    reagent_text[:80],
                    fill="black",
                    font=font
                )
            except Exception:
                pass

        buffer = io.BytesIO()
        canvas.save(
            buffer,
            format="PNG"
        )

        return buffer.getvalue()

    except Exception:
        return None


def image_to_base64(image_bytes: bytes) -> str:
    """Convert image bytes to base64."""
    return base64.b64encode(
        image_bytes
    ).decode("utf-8")


def renderer_status() -> Dict[str, Any]:
    """Return renderer diagnostic information."""

    Draw, error = _load_draw_module()

    return {
        "rdkit_available": RDKIT_AVAILABLE,
        "drawing_available": Draw is not None,
        "error": error
    }
