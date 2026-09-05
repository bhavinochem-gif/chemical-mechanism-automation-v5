import json
import os
import traceback
from datetime import datetime

import streamlit as st

APP_NAME = "Chemical Reaction Mechanism Automation"
APP_VERSION = "5.1.1"

st.set_page_config(page_title=f"{APP_NAME} V{APP_VERSION}", page_icon="⚗️", layout="wide")

# Safe/lazy module imports: one optional native dependency must not stop the whole app.
try:
    from modules.pdf_processor import extract_pages
    PDF_OK, PDF_ERR = True, ""
except Exception as e:
    PDF_OK, PDF_ERR = False, str(e)

try:
    from modules.ai_analyzer import analyze_route
    AI_OK, AI_ERR = True, ""
except Exception as e:
    AI_OK, AI_ERR = False, str(e)

try:
    from modules.structure_engine import enrich_step
    STRUCT_OK, STRUCT_ERR = True, ""
except Exception as e:
    STRUCT_OK, STRUCT_ERR = False, str(e)

try:
    from modules.reaction_database import identify_named_reactions
    RXN_OK, RXN_ERR = True, ""
except Exception as e:
    RXN_OK, RXN_ERR = False, str(e)

try:
    from modules.mechanism_engine import build_mechanism
    MECH_OK, MECH_ERR = True, ""
except Exception as e:
    MECH_OK, MECH_ERR = False, str(e)

try:
    from modules.mechanism_renderer import render_mechanism_scheme, renderer_status
    RENDER_OK, RENDER_ERR = True, ""
except Exception as e:
    RENDER_OK, RENDER_ERR = False, str(e)

try:
    from modules.cascade_renderer import render_cascade
    CASCADE_OK, CASCADE_ERR = True, ""
except Exception as e:
    CASCADE_OK, CASCADE_ERR = False, str(e)

try:
    from modules.report_generator import build_pdf_report
    REPORT_OK, REPORT_ERR = True, ""
except Exception as e:
    REPORT_OK, REPORT_ERR = False, str(e)


def get_secret(name: str, default=None):
    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


def json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items() if k not in {"image", "mechanism_image", "cascade_image"}}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    if isinstance(obj, bytes):
        return "<binary image omitted>"
    return obj


def render_mol(smiles):
    if not smiles or not RENDER_OK:
        return None
    try:
        from modules.mechanism_renderer import render_structure
        return render_structure(smiles)
    except Exception:
        return None


# ---------------- Sidebar ----------------
with st.sidebar:
    st.title("⚗️ Mechanism Automation")
    st.caption(f"Version {APP_VERSION}")
    st.divider()

    model = st.text_input("OpenAI model", value=get_secret("OPENAI_MODEL", "gpt-5.6-luna"))
    detail = st.selectbox("Image detail", ["high", "auto", "low"], index=0)
    render_arrows = st.checkbox("Render reaction arrows", True)
    named_rxn = st.checkbox("Identify named reactions", True)
    mechanisms = st.checkbox("Generate proposed mechanisms", True)
    cascade = st.checkbox("Generate structure cascade", True)
    debug = st.checkbox("Show technical diagnostics", False)

    st.divider()
    st.subheader("System")
    for label, ok in [
        ("PDF/image processor", PDF_OK),
        ("AI analyzer", AI_OK),
        ("Structure engine", STRUCT_OK),
        ("Reaction database", RXN_OK),
        ("Mechanism engine", MECH_OK),
        ("Mechanism renderer", RENDER_OK),
        ("Cascade renderer", CASCADE_OK),
        ("PDF report", REPORT_OK),
    ]:
        (st.success if ok else st.warning)(f"{label} {'✓' if ok else '—'}")


st.title("⚗️ Automated Chemical Reaction Mechanism Analysis")
st.markdown(
    "Upload a reaction scheme or synthesis-route PDF/image to extract structures, conditions, "
    "reaction classes, named-reaction candidates and proposed mechanisms."
)
st.info("Mechanistic output is an AI-assisted proposal. Verify structures, atom mapping, stereochemistry and mechanisms before scientific or regulated use.")

api_key = get_secret("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY is not configured. Add it in Streamlit Cloud → Manage app → Settings → Secrets.")
    st.code('OPENAI_API_KEY = "sk-..."\nOPENAI_MODEL = "gpt-5.6-luna"')
    st.stop()

uploaded = st.file_uploader(
    "Upload synthesis route PDF or image",
    type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
)

if uploaded is None:
    st.info("Upload a file to begin.")
    st.stop()

st.success(f"Uploaded: {uploaded.name} ({uploaded.size / 1024 / 1024:.2f} MB)")

if not PDF_OK:
    st.error(f"PDF/image processor failed to load: {PDF_ERR}")
    st.stop()

try:
    pages = extract_pages(uploaded.getvalue(), uploaded.name)
except Exception as e:
    st.error(f"Could not read the uploaded file: {e}")
    st.exception(e)
    st.stop()

st.success(f"Loaded {len(pages)} page(s).")

preview_cols = st.columns(min(3, max(1, len(pages))))
for i, page in enumerate(pages[:3]):
    with preview_cols[i]:
        st.image(page["image"], caption=f"Page {page.get('page_number', i + 1)}", use_container_width=True)

if st.button("🚀 Analyze complete route", type="primary", use_container_width=True):
    if not AI_OK:
        st.error(f"AI analyzer failed to load: {AI_ERR}")
        st.stop()

    progress = st.progress(0)
    status = st.empty()

    try:
        status.info("1/7 — Sending route images for structure/reaction extraction…")
        progress.progress(10)
        route = analyze_route(pages, model=model, detail=detail, api_key=api_key)

        if not isinstance(route, dict):
            raise RuntimeError("AI returned an unexpected result format.")

        steps = route.get("steps", [])
        if not isinstance(steps, list):
            steps = []
            route["steps"] = steps

        status.info("2/7 — Validating structures with RDKit…")
        progress.progress(30)
        for i, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                steps[i - 1] = {"step_number": i, "transformation": str(step), "reactants_smiles": [], "products_smiles": []}
                step = steps[i - 1]
            step["step_number"] = step.get("step_number", i)
            if STRUCT_OK:
                enrich_step(step)

        status.info("3/7 — Matching named-reaction candidates…")
        progress.progress(45)
        if named_rxn and RXN_OK:
            for step in steps:
                try:
                    step["named_reactions"] = identify_named_reactions(step)
                except Exception as e:
                    step["named_reactions"] = []
                    step["named_reaction_error"] = str(e)
        else:
            for step in steps:
                step["named_reactions"] = []

        status.info("4/7 — Building proposed mechanisms…")
        progress.progress(60)
        if mechanisms and MECH_OK:
            for step in steps:
                try:
                    step["mechanism"] = build_mechanism(step)
                except Exception as e:
                    step["mechanism"] = {"status": "ERROR", "overview": str(e), "events": []}
        else:
            for step in steps:
                step["mechanism"] = {"status": "NOT_REQUESTED", "overview": "Mechanism generation disabled.", "events": []}

        status.info("5/7 — Rendering reaction schemes…")
        progress.progress(75)
        if render_arrows and RENDER_OK:
            for step in steps:
                try:
                    step["mechanism_image"] = render_mechanism_scheme(step, arrows=True)
                except Exception as e:
                    step["mechanism_image"] = None
                    step["render_error"] = str(e)

        status.info("6/7 — Rendering structure cascade…")
        progress.progress(88)
        if cascade and CASCADE_OK:
            try:
                route["cascade_image"] = render_cascade(route)
            except Exception as e:
                route["cascade_image"] = None
                route["cascade_error"] = str(e)

        route["application"] = APP_NAME
        route["version"] = APP_VERSION
        route["source_file"] = uploaded.name
        route["analysis_timestamp"] = datetime.now().isoformat(timespec="seconds")
        route["scientific_status"] = "AI-assisted proposed interpretation"

        st.session_state.route = route
        st.session_state.source_name = uploaded.name

        status.success("7/7 — Analysis completed.")
        progress.progress(100)

    except Exception as e:
        status.error("Analysis failed.")
        st.error(f"{type(e).__name__}: {e}")
        with st.expander("Technical traceback"):
            st.code(traceback.format_exc())
        st.stop()


route = st.session_state.get("route")
if not route:
    st.stop()

steps = route.get("steps", [])

# ---------------- Results tabs ----------------
tabs = st.tabs(["Route", "Structures", "Named Reactions", "Mechanisms", "Data", "Downloads", "Diagnostics"])

with tabs[0]:
    st.header(route.get("route_title", "Synthetic route"))
    st.write(route.get("route_summary", ""))
    c1, c2, c3 = st.columns(3)
    c1.metric("Steps", len(steps))
    c2.metric("Source", st.session_state.get("source_name", "uploaded file"))
    c3.metric("Status", "Proposed / review required")

    for step in steps:
        st.subheader(f"Step {step.get('step_number', '?')}: {step.get('transformation', 'Transformation')}")
        st.write(step.get("conditions_text", ""))
        st.caption(f"Reaction class: {step.get('reaction_class', 'unknown')} | Confidence: {step.get('confidence', 'unknown')}")
        left, right = st.columns(2)
        with left:
            st.markdown("**Reactants**")
            for smi in step.get("reactants_smiles", []) or []:
                st.code(smi)
        with right:
            st.markdown("**Products**")
            for smi in step.get("products_smiles", []) or []:
                st.code(smi)
        st.divider()

with tabs[1]:
    st.header("Structure information")
    for step in steps:
        st.subheader(f"Step {step.get('step_number', '?')}")
        left, right = st.columns(2)
        with left:
            st.markdown("**Reactants**")
            for smi, details in zip(step.get("reactants_smiles", []) or [], step.get("reactant_details", []) or []):
                img = render_mol(smi)
                if img:
                    st.image(img, use_container_width=True)
                st.code(smi)
                if details:
                    st.json(details)
        with right:
            st.markdown("**Products**")
            for smi, details in zip(step.get("products_smiles", []) or [], step.get("product_details", []) or []):
                img = render_mol(smi)
                if img:
                    st.image(img, use_container_width=True)
                st.code(smi)
                if details:
                    st.json(details)

with tabs[2]:
    st.header("Named-reaction candidates")
    for step in steps:
        st.markdown(f"### Step {step.get('step_number', '?')}")
        candidates = step.get("named_reactions", []) or []
        if not candidates:
            st.info("No high-confidence database match.")
        for c in candidates:
            score = c.get("score", 0)
            st.markdown(f"**{c.get('name', 'Unknown')}** — {float(score):.0%}")
            st.write(c.get("reason", ""))

with tabs[3]:
    st.header("Proposed mechanisms")
    for step in steps:
        st.markdown(f"## Step {step.get('step_number', '?')}: {step.get('transformation', '')}")
        mech = step.get("mechanism", {}) or {}
        st.write(mech.get("overview", ""))
        for i, event in enumerate(mech.get("events", []) or [], 1):
            st.markdown(f"**{i}. {event.get('title', 'Mechanistic event')}**")
            st.write(event.get("description", ""))
            if event.get("electron_flow"):
                st.caption("Electron flow: " + event["electron_flow"])
        if step.get("mechanism_image"):
            st.image(step["mechanism_image"], use_container_width=True)
        st.warning("Exact atom mapping and curved-arrow placement should be chemically verified.")

with tabs[4]:
    st.json(json_safe(route))

with tabs[5]:
    st.header("Downloads")
    pdf_error = None
    if REPORT_OK:
        try:
            pdf_bytes = build_pdf_report(route, st.session_state.get("source_name", "route"))
            st.download_button("📄 Download PDF report", pdf_bytes, "chemical_mechanism_report_v5_1_1.pdf", "application/pdf", use_container_width=True)
        except Exception as e:
            pdf_error = str(e)
    if pdf_error:
        st.error(f"PDF generation failed: {pdf_error}")

    json_bytes = json.dumps(json_safe(route), indent=2, ensure_ascii=False, default=str).encode("utf-8")
    st.download_button("🧾 Download JSON analysis", json_bytes, "chemical_mechanism_analysis_v5_1_1.json", "application/json", use_container_width=True)

with tabs[6]:
    st.header("Diagnostics")
    st.write({
        "python_version": os.sys.version,
        "app_version": APP_VERSION,
        "api_key_detected": bool(api_key),
        "PDF_OK": PDF_OK,
        "AI_OK": AI_OK,
        "STRUCT_OK": STRUCT_OK,
        "RXN_OK": RXN_OK,
        "MECH_OK": MECH_OK,
        "RENDER_OK": RENDER_OK,
        "CASCADE_OK": CASCADE_OK,
        "REPORT_OK": REPORT_OK,
    })
    if RENDER_OK and renderer_status:
        try:
            st.json(renderer_status())
        except Exception as e:
            st.error(str(e))

st.divider()
st.caption("Scientific disclaimer: AI-assisted structures and mechanisms are proposals and require qualified chemical review before process-development, publication, regulatory or GMP use.")
