import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors

def build_pdf_report(route, source_name='route'):
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=12*mm,leftMargin=12*mm,topMargin=12*mm,bottomMargin=12*mm)
    styles=getSampleStyleSheet(); small=ParagraphStyle('small',parent=styles['BodyText'],fontSize=8,leading=10)
    story=[Paragraph('Chemical Reaction Mechanism Automation — Version 5',styles['Title']),Paragraph(f'Source: {source_name}',small),Spacer(1,8),Paragraph(route.get('route_title','Synthetic route'),styles['Heading2']),Paragraph(route.get('route_summary',''),styles['BodyText']),Spacer(1,10)]
    if route.get('cascade_image'):
        story += [Paragraph('Structure Cascade',styles['Heading2']),Image(io.BytesIO(route['cascade_image']),width=180*mm,height=60*mm),Spacer(1,8)]
    for step in route.get('steps',[]):
        story += [PageBreak(),Paragraph(f"Step {step.get('step_number')}: {step.get('transformation','')}",styles['Heading2'])]
        data=[["Field","Value"],["Reaction class",step.get('reaction_class','')],["Reagents",', '.join(step.get('reagents',[]))],["Solvent",step.get('solvent','')],["Temperature",step.get('temperature','')],["Time",step.get('time','')],["Yield",step.get('yield','')],["Confidence",step.get('confidence','')]]
        t=Table([[Paragraph(str(a),small),Paragraph(str(b),small)] for a,b in data],colWidths=[38*mm,145*mm]); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.3,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey)])); story += [t,Spacer(1,8)]
        story += [Paragraph('Named reaction candidates',styles['Heading3'])]
        for c in step.get('named_reactions',[]): story.append(Paragraph(f"{c['name']} — {c['score']:.0%} — {c['reason']}",small))
        mech=step.get('mechanism',{}); story += [Spacer(1,5),Paragraph('Proposed mechanism',styles['Heading3']),Paragraph(mech.get('overview',''),small)]
        for i,e in enumerate(mech.get('events',[]),1): story.append(Paragraph(f"{i}. {e.get('title')}: {e.get('description')}",small))
        if step.get('mechanism_image'): story += [Spacer(1,6),Image(io.BytesIO(step['mechanism_image']),width=180*mm,height=55*mm)]
        story += [Spacer(1,8),Paragraph('Scientific note: mechanism and structures are AI-assisted proposals and must be reviewed against the original experimental record, analytical data and chemically validated atom mapping before use in a regulated document.',small)]
    doc.build(story); return buf.getvalue()

