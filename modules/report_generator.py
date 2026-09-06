import json,io,pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet
def make_json(x):return json.dumps(x,indent=2,ensure_ascii=False).encode()
def make_csv(rows):return pd.DataFrame(rows).to_csv(index=False).encode()
def make_pdf(x):
    b=io.BytesIO(); d=SimpleDocTemplate(b,pagesize=A4); s=getSampleStyleSheet(); a=[Paragraph("Chemical Reaction Mechanism Automation V6.0.1",s["Title"]),Spacer(1,10)]
    for m in x.get("mechanisms",[]):a += [Paragraph(f"Step {m.get('step')}: {m.get('reaction_class')}",s["Heading2"]),Paragraph("Transformation: "+str(m.get("transformation","")),s["Normal"]),Paragraph("Mechanism: "+str(m.get("mechanism_summary","")),s["Normal"]),Paragraph(f"Confidence: {m.get('confidence',0):.0%}",s["Normal"]),Spacer(1,8)]
    d.build(a);return b.getvalue()
