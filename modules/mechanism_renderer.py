"""RDKit/PIL rendering with lazy Draw import to avoid rdMolDraw2D startup failures."""
import io
from PIL import Image, ImageDraw, ImageFont
from rdkit import Chem

def _load_draw():
    try:
        from rdkit.Chem import Draw
        return Draw, None
    except Exception as exc:
        return None, str(exc)

def renderer_status():
    try:
        import rdkit
        version = getattr(rdkit, '__version__', 'unknown')
    except Exception as exc:
        return {'rdkit_available': False, 'drawing_available': False, 'error': str(exc)}
    draw, error = _load_draw()
    return {'rdkit_available': True, 'rdkit_version': version, 'drawing_available': draw is not None, 'drawing_error': error}

def _font(size=20):
    for path in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def _mol_img(smiles, size=(400, 260)):
    if not smiles:
        return None
    draw, _ = _load_draw()
    if draw is None:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return draw.MolToImage(mol, size=size)
    except Exception:
        return None

def render_structure(smiles, size=(500, 320)):
    img = _mol_img(smiles, size=size)
    if img is None:
        return None
    out = io.BytesIO(); img.save(out, format='PNG'); return out.getvalue()

def render_mechanism_scheme(step, arrows=True):
    reactants = list(step.get('reactants_smiles', []) or [])[:2]
    products = list(step.get('products_smiles', []) or [])[:2]
    molecules = [('Reactant', s) for s in reactants] + [('Product', s) for s in products]
    box_w = 430
    canvas = Image.new('RGB', (max(900, box_w * max(2, len(molecules))), 420), 'white')
    d = ImageDraw.Draw(canvas); font = _font(18)
    x = 10
    for idx, (label, smiles) in enumerate(molecules, 1):
        img = _mol_img(smiles, size=(box_w - 20, 250))
        d.text((x, 15), f'{label} {idx}', fill='black', font=font)
        if img:
            canvas.paste(img, (x, 55))
        else:
            d.text((x, 130), 'Structure drawing unavailable', fill='black', font=font)
            d.text((x, 160), (smiles or '')[:45], fill='black', font=_font(12))
        x += box_w
    if arrows and len(molecules) >= 2:
        y = 210; start = box_w - 35; end = min(canvas.width - 40, start + 140)
        d.line((start, y, end, y), fill='black', width=4)
        d.polygon([(end, y), (end - 18, y - 10), (end - 18, y + 10)], fill='black')
        d.text((start, y - 45), str(step.get('reaction_class', 'proposed transformation'))[:70], fill='black', font=_font(15))
    out = io.BytesIO(); canvas.save(out, format='PNG'); return out.getvalue()
