import json, os
import streamlit as st
from modules.pdf_processor import extract_pages
from modules.ai_analyzer import analyze_route
from modules.structure_engine import enrich_step
from modules.reaction_database import load_database, identify_named_reactions
from modules.mechanism_engine import build_mechanism
from modules.mechanism_renderer import render_mechanism_scheme, render_structure, renderer_status
from modules.cascade_renderer import render_cascade
from modules.report_generator import build_pdf

APP_VERSION='5.2.0'
st.set_page_config(page_title='Chemical Reaction Mechanism Automation',layout='wide')

def secret(name, default=None):
    try:
        if name in st.secrets: return st.secrets[name]
    except Exception: pass
    return os.getenv(name, default)

def json_safe(obj):
    if isinstance(obj,dict): return {k:json_safe(v) for k,v in obj.items() if k not in {'image','image_bytes'}}
    if isinstance(obj,list): return [json_safe(v) for v in obj]
    return obj

st.title('Chemical Reaction Mechanism Automation')
st.caption(f'Version {APP_VERSION} — Gemini Free Tier default; OpenAI optional')

with st.sidebar:
    st.header('AI settings')
    provider=st.selectbox('AI provider',['gemini','openai'],index=0)
    if provider=='gemini':
        model=st.text_input('Gemini model', secret('GEMINI_MODEL','gemini-3.7-flash'))
        api_key=secret('GEMINI_API_KEY')
    else:
        model=st.text_input('OpenAI model', secret('OPENAI_MODEL','gpt-5.6-luna'))
        api_key=secret('OPENAI_API_KEY')
    detail=st.selectbox('Image detail',['high','auto','low'],index=0)
    render_arrows=st.checkbox('Render reaction arrows',True)
    named=st.checkbox('Identify named reactions',True)
    mechanisms=st.checkbox('Generate proposed mechanisms',True)
    cascade=st.checkbox('Generate structure cascade',True)
    diagnostics=st.checkbox('Technical diagnostics',False)

if provider=='gemini':
    if not api_key:
        st.info('Add GEMINI_API_KEY in Streamlit Secrets. Gemini Free Tier supports free input/output tokens within its published limits.')
else:
    if not api_key: st.warning('Add OPENAI_API_KEY in Streamlit Secrets.')

uploaded=st.file_uploader('Upload synthesis route PDF or image',type=['pdf','png','jpg','jpeg','tif','tiff'])
if uploaded:
    try:
        pages=extract_pages(uploaded.getvalue(),uploaded.name)
        st.success(f'{len(pages)} page(s) extracted.')
        with st.expander('Preview'):
            for p in pages: st.image(p['image'],caption=f"Page {p['page_number']}",use_container_width=True)
    except Exception as exc:
        st.error(f'File extraction failed: {exc}'); pages=[]
else: pages=[]

if st.button('Analyze synthesis route',type='primary',disabled=not pages):
    if not api_key:
        st.error(f'{provider.upper()} API key is missing. Add it to Streamlit Secrets.')
        st.stop()
    try:
        with st.spinner(f'Analyzing with {provider}...'):
            route=analyze_route(pages,model=model,detail=detail,api_key=api_key,provider=provider)
            db=load_database()
            for step in route.get('steps',[]):
                enrich_step(step)
                if named: step['named_reactions']=identify_named_reactions(step,db)
                if mechanisms: step['mechanism']=build_mechanism(step)
            route['_provider']=provider; route['_model']=model
            st.session_state.route=route
            st.session_state.route_pdf=build_pdf(route)
            st.success('Analysis completed.')
    except Exception as exc:
        st.error(f'Analysis failed: {exc}')

route=st.session_state.get('route')
if route:
    tabs=st.tabs(['Route','Structures','Named Reactions','Mechanisms','Data','Downloads','Diagnostics'])
    with tabs[0]:
        st.subheader(route.get('route_title','Synthetic Route')); st.write(route.get('route_summary',''))
        for s in route.get('steps',[]):
            st.markdown(f"### Step {s.get('step_number')}: {s.get('transformation')}")
            st.write(f"**Class:** {s.get('reaction_class','')}")
            st.write(f"**Reagents:** {', '.join(s.get('reagents',[]) or [])}")
            st.write(f"**Conditions:** {s.get('conditions_text','')}")
            st.write(f"**Confidence:** {s.get('confidence','')} — {s.get('uncertainty','')}")
    with tabs[1]:
        for s in route.get('steps',[]):
            st.markdown(f"**Step {s.get('step_number')}**")
            cols=st.columns(4)
            for i,smiles in enumerate((s.get('reactants_smiles',[]) or [])[:2]+(s.get('products_smiles',[]) or [])[:2]):
                with cols[i]:
                    st.code(smiles,language='text')
                    b=render_structure(smiles)
                    if b: st.image(b)
    with tabs[2]:
        for s in route.get('steps',[]):
            st.markdown(f"**Step {s.get('step_number')}**")
            st.json(s.get('named_reactions',[]))
    with tabs[3]:
        for s in route.get('steps',[]):
            st.markdown(f"**Step {s.get('step_number')}**")
            st.json(s.get('mechanism',{}))
            if render_arrows:
                st.image(render_mechanism_scheme(s,arrows=True),use_container_width=True)
    with tabs[4]:
        st.json(json_safe(route))
    with tabs[5]:
        if cascade:
            st.image(render_cascade(route),use_container_width=True)
        st.download_button('Download PDF report',data=st.session_state.route_pdf,file_name='chemical_reaction_mechanism_report_v5.2.pdf',mime='application/pdf')
        st.download_button('Download JSON report',data=json.dumps(json_safe(route),indent=2).encode(),file_name='chemical_reaction_mechanism_report_v5.2.json',mime='application/json')
    with tabs[6]:
        st.json({'provider':route.get('_provider'),'model':route.get('_model'),'renderer':renderer_status()})
        if diagnostics: st.write('RDKit and renderer diagnostics are shown above.')

st.divider()
st.caption('Scientific disclaimer: AI output is a proposed interpretation. Verify structures, stereochemistry, atom mapping, reaction mechanisms and conditions experimentally before scientific, quality, regulatory or manufacturing use.')
