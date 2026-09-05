import io, math
from PIL import Image, ImageDraw, ImageFont
from rdkit import Chem
from rdkit.Chem import Draw

def _font(size=22):
    try: return ImageFont.truetype('DejaVuSans.ttf', size)
    except: return ImageFont.load_default()

def _mol_img(smiles, size=(420,260)):
    if not smiles: return None
    mol=Chem.MolFromSmiles(smiles)
    if mol is None: return None
    return Draw.MolToImage(mol, size=size)

def render_mechanism_scheme(step, arrows=True):
    react=step.get('reactants_smiles',[])[:2]; prod=step.get('products_smiles',[])[:2]
    imgs=[]
    for s in react: imgs.append(('Reactant', _mol_img(s)))
    for s in prod: imgs.append(('Product', _mol_img(s)))
    canvas=Image.new('RGB',(max(900,430*len(imgs)),420),'white'); d=ImageDraw.Draw(canvas)
    x=10
    for i,(label,img) in enumerate(imgs):
        if img:
            canvas.paste(img,(x,65)); d.text((x,20),f'{label} {i+1}',fill='black',font=_font(20))
            x += 430
    if len(imgs)>=2 and arrows:
        y=200; start=420; end=min(canvas.width-30,start+150)
        d.line((start,y,end,y),fill='black',width=4)
        d.polygon([(end,y),(end-18,y-10),(end-18,y+10)],fill='black')
        d.text((start+20,y-45),step.get('reaction_class','proposed transformation'),fill='black',font=_font(18))
    out=io.BytesIO(); canvas.save(out,format='PNG'); return out.getvalue()

