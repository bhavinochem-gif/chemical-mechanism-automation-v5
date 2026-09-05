"""Structure cascade renderer with lazy RDKit Draw import."""
import io
from PIL import Image, ImageDraw, ImageFont
from rdkit import Chem


def _load_draw():
    try:
        from rdkit.Chem import Draw
        return Draw
    except Exception:
        return None


def _font(size=18):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def render_cascade(route):
    steps = route.get("steps", []) or []
    draw = _load_draw()
    box_w, box_h = 360, 340
    canvas = Image.new("RGB", (max(900, box_w * max(1, len(steps))), box_h), "white")
    d = ImageDraw.Draw(canvas)
    font = _font(18)

    for i, step in enumerate(steps):
        smis = step.get("products_smiles") or step.get("reactants_smiles") or []
        smi = smis[0] if smis else ""
        x = i * box_w + 10
        d.text((x, 15), f"Step {step.get('step_number', i + 1)}", fill="black", font=font)
        if draw and smi:
            try:
                mol = Chem.MolFromSmiles(smi)
                if mol:
                    img = draw.MolToImage(mol, size=(320, 230))
                    canvas.paste(img, (x, 50))
                else:
                    d.text((x, 150), "Invalid SMILES", fill="black", font=font)
            except Exception:
                d.text((x, 150), "Structure drawing unavailable", fill="black", font=font)
        else:
            d.text((x, 140), "RDKit drawing unavailable", fill="black", font=font)
            if smi:
                d.text((x, 175), smi[:40], fill="black", font=_font(11))

        if i < len(steps) - 1:
            y = 175
            start = x + 325
            end = x + 350
            d.line((start, y, end, y), fill="black", width=3)
            d.polygon([(end, y), (end - 10, y - 7), (end - 10, y + 7)], fill="black")

    out = io.BytesIO()
    canvas.save(out, format="PNG")
    return out.getvalue()
