import io, json, os, zipfile
import streamlit as st
from dotenv import load_dotenv
from modules.pdf_processor import extract_pages
from modules.ai_analyzer import analyze_route
from modules.structure_engine import enrich_step
from modules.reaction_database import identify_named_reactions
from modules.mechanism_engine import build_mechanism
from modules.mechanism_renderer import render_mechanism_scheme
from modules.cascade_renderer import render_cascade
from modules.report_generator import build_pdf_report

load_dotenv()
st.set_page_config(page_title="Chemical Mechanism Automation V5", page_icon="⚗️", layout="wide")

st.title("⚗️ Chemical Reaction Mechanism Automation — Version 5")
st.caption("PDF/image → structure recognition → reaction-center analysis → named reaction → proposed mechanism → cascade → PDF")

with st.sidebar:
    st.header("Settings")
    model = st.text_input("AI model", value=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"))
    detail = st.selectbox("Image detail", ["high", "auto", "low"], index=0)
    render_arrows = st.checkbox("Render mechanism arrows", True)
    show_debug = st.checkbox("Show extracted JSON", False)
    st.info("API key is read from OPENAI_API_KEY. Do not commit .env or secrets to GitHub.")

uploaded = st.file_uploader("Upload synthesis route PDF or image", type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"])

if uploaded:
    raw = uploaded.getvalue()
    pages = extract_pages(raw, uploaded.name)
    st.success(f"Loaded {len(pages)} page(s).")
    cols = st.columns(min(3, len(pages)))
    for i, p in enumerate(pages[:3]):
        with cols[i]:
            st.image(p["image"], caption=f"Page {i+1}", use_container_width=True)

    if st.button("🚀 Analyze complete route", type="primary"):
        try:
            with st.spinner("AI is extracting structures, reagents and transformations..."):
                route = analyze_route(pages, model=model, detail=detail)
            for step in route.get("steps", []):
                enrich_step(step)
                step["named_reactions"] = identify_named_reactions(step)
                step["mechanism"] = build_mechanism(step)
                step["mechanism_image"] = render_mechanism_scheme(step, arrows=render_arrows)

            route["cascade_image"] = render_cascade(route)
            st.session_state["route"] = route
            st.session_state["source_name"] = uploaded.name
            st.success("Analysis completed.")
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            st.exception(exc)

route = st.session_state.get("route")
if route:
    tabs = st.tabs(["Route", "Structure cascade", "Named reactions", "Mechanisms", "Data", "Downloads"])

    with tabs[0]:
        st.subheader(route.get("route_title", "Synthetic route"))
        st.write(route.get("route_summary", ""))
        for step in route.get("steps", []):
            st.markdown(f"### Step {step.get('step_number', '?')}: {step.get('transformation', 'Transformation')}")
            st.write(step.get("conditions_text", ""))
            st.caption(f"AI confidence: {step.get('confidence', 'unknown')} | {step.get('uncertainty', '')}")
            c1, c2 = st.columns(2)
            with c1:
                st.write("Reactants")
                for s in step.get("reactants_smiles", []): st.code(s)
            with c2:
                st.write("Products")
                for s in step.get("products_smiles", []): st.code(s)
            st.divider()

    with tabs[1]:
        img = route.get("cascade_image")
        if img:
            st.image(img, use_container_width=True)

    with tabs[2]:
        for step in route.get("steps", []):
            st.markdown(f"**Step {step.get('step_number')}**")
            candidates = step.get("named_reactions", [])
            if not candidates:
                st.info("No high-confidence database match; inspect the reaction family and AI interpretation.")
            for c in candidates:
                st.write(f"**{c['name']}** — score {c['score']:.2f} — {c['reason']}")

    with tabs[3]:
        for step in route.get("steps", []):
            st.markdown(f"## Step {step.get('step_number')}: {step.get('transformation', '')}")
            mech = step.get("mechanism", {})
            st.write(mech.get("overview", ""))
            for i, item in enumerate(mech.get("events", []), 1):
                st.markdown(f"**{i}. {item.get('title', 'Mechanistic event')}**")
                st.write(item.get("description", ""))
                if item.get("electron_flow"): st.caption("Electron flow: " + item["electron_flow"])
            if step.get("mechanism_image"):
                st.image(step["mechanism_image"], use_container_width=True)

    with tabs[4]:
        if show_debug:
            st.json(route)
        else:
            st.json({k: v for k, v in route.items() if k not in {"cascade_image"}})

    with tabs[5]:
        pdf_bytes = build_pdf_report(route, st.session_state.get("source_name", "route"))
        st.download_button("📄 Download mechanism PDF", pdf_bytes, "mechanism_report_v5.pdf", "application/pdf")
        data = json.dumps(route, indent=2, default=str).encode()
        st.download_button("🧾 Download analysis JSON", data, "mechanism_analysis_v5.json", "application/json")

