import io
from PIL import Image, ImageDraw, ImageFont
from rdkit import Chem
from rdkit.Chem import Draw

def render_cascade(route):
    steps=route.get('steps',[]); w=max(900,360*max(1,len(steps))); h=340
    canvas=Image.new('RGB',(w,h),'white'); d=ImageDraw.Draw(canvas)
    try: font=ImageFont.truetype('DejaVuSans.ttf',18)
    except: font=ImageFont.load_default()
    x=10
    for i,step in enumerate(steps):
        smis=(step.get('products_smiles') or step.get('reactants_smiles') or [])
        smi=smis[0] if smis else ''
        mol=Chem.MolFromSmiles(smi) if smi else None
        if mol:
            img=Draw.MolToImage(mol,size=(320,230)); canvas.paste(img,(x,45))
        d.text((x,15),f"Step {step.get('step_number',i+1)}",fill='black',font=font)
        if i < len(steps)-1:
            y=165; d.line((x+325,y,x+350,y),fill='black',width=3); d.polygon([(x+350,y),(x+340,y-7),(x+340,y+7)],fill='black')
        x+=360
    out=io.BytesIO(); canvas.save(out,format='PNG'); return out.getvalue()

