import streamlit as st, pandas as pd
from modules.pdf_processor import process_document
from modules.ai_router import analyze_route
from modules.database_manager import ChemistryDatabase
from modules.ros_engine import normalize_ros,fallback_ros_from_document,validate_ros
from modules.mechanism_engine import generate_mechanism
from modules.report_generator import make_json,make_csv,make_pdf
st.set_page_config(page_title="Chemical Mechanism Automation V6.0.1",layout="wide")
st.title("🧪 Chemical Reaction Mechanism Automation V6.0.1")
@st.cache_resource
def db(): return ChemistryDatabase("data")
D=db()
with st.sidebar:
    provider=st.selectbox("AI provider",["auto","gemini","openrouter","groq","ollama","openai"])
    dpi=st.slider("PDF DPI",120,300,180,20)
    st.write("Knowledge-base datasets:",len(D.datasets))
f=st.file_uploader("Upload synthesis route PDF or image",type=["pdf","png","jpg","jpeg","webp"])
if f:
    raw=f.getvalue(); doc=process_document(raw,f.name,dpi)
    if doc["is_pdf"]: st.pdf(raw,height=600)
    else: st.image(raw,use_container_width=True)
    with st.expander("Extracted text"): st.text(doc["text"] or "No native text found.")
    if st.button("Extract / refresh ROS",type="primary"):
        try:a=analyze_route(doc["text"],doc["images"],provider,D.compact_context())
        except Exception as e:a={"steps":[],"warnings":[str(e)]}
        ros=normalize_ros(a.get("steps",[])) or fallback_ros_from_document(doc["text"],doc["page_count"])
        st.session_state["ros"]=ros
    ros=st.session_state.get("ros",[])
    if ros:
        st.subheader("ROS / Route Review")
        st.session_state["ros"]=st.data_editor(pd.DataFrame(ros),use_container_width=True,num_rows="dynamic").to_dict("records")
        w=validate_ros(st.session_state["ros"])
        if w:st.warning(" | ".join(w))
        if st.button("Generate mechanism analysis",type="primary"):
            st.session_state["mech"]=generate_mechanism(st.session_state["ros"],D)
        for m in st.session_state.get("mech",[]):
            with st.expander(f"Step {m['step']} — {m['reaction_class']}",expanded=True):
                st.write("Transformation:",m["transformation"]);st.write("Mechanism:",m["mechanism_summary"]);st.write("Named reactions:",", ".join(m["named_reactions"]) or "None");st.write("Reagents:",", ".join(m["recognized_reagents"]) or "None");st.write("Stereochemistry:",m["stereochemistry"]);st.write("Impurity/process:",m["impurity_notes"]);st.metric("Confidence",f"{m['confidence']:.0%}")
        if st.session_state.get("mech"):
            payload={"version":"6.0.1","filename":f.name,"ros":st.session_state["ros"],"mechanisms":st.session_state["mech"],"database_summary":D.summary()}
            c1,c2,c3=st.columns(3);c1.download_button("JSON",make_json(payload),"mechanism_report.json","application/json");c2.download_button("CSV",make_csv(st.session_state["ros"]),"route_ros.csv","text/csv");c3.download_button("PDF",make_pdf(payload),"mechanism_report.pdf","application/pdf")
else: st.info("Upload a synthesis route PDF or image.")
