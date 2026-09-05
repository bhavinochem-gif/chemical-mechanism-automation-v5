import io, json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.units import mm

def build_pdf(route):
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=15*mm,leftMargin=15*mm,topMargin=15*mm,bottomMargin=15*mm)
    styles=getSampleStyleSheet(); story=[Paragraph('Chemical Reaction Mechanism Automation — V5.2',styles['Title']),Spacer(1,8)]
    story += [Paragraph(str(route.get('route_title','Synthetic Route')),styles['Heading2']),Paragraph(str(route.get('route_summary','')),styles['BodyText']),Spacer(1,10)]
    for step in route.get('steps',[]):
        story.append(Paragraph(f"Step {step.get('step_number','')}: {step.get('transformation','')}",styles['Heading2']))
        story.append(Paragraph(f"Reaction class: {step.get('reaction_class','')}",styles['BodyText']))
        story.append(Paragraph(f"Reagents: {', '.join(step.get('reagents',[]) or [])}",styles['BodyText']))
        story.append(Paragraph(f"Conditions: {step.get('conditions_text','')}",styles['BodyText']))
        mech=step.get('mechanism',{})
        for i,m in enumerate(mech.get('mechanism_steps',[]) or [],1): story.append(Paragraph(f"{i}. {m}",styles['BodyText']))
        story.append(Spacer(1,8))
    story.append(Paragraph('Scientific disclaimer: structures, reaction classes, named reactions and mechanisms are AI-assisted interpretations and must be independently verified before use in development, regulatory, safety or manufacturing decisions.',styles['BodyText']))
    doc.build(story); return buf.getvalue()
