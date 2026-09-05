# ============================================================
# CHEMICAL MECHANISM AUTOMATION
# VERSION 5.1
# app.py
# ============================================================

import os
import json
import traceback
from datetime import datetime

import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Chemical Mechanism Automation V5.1",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# APPLICATION INFORMATION
# ============================================================

APP_NAME = "Chemical Mechanism Automation"
APP_VERSION = "5.1"

SUPPORTED_FILE_TYPES = [
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "tif",
    "tiff",
]


# ============================================================
# SAFE MODULE IMPORTS
# ============================================================

# PDF PROCESSOR
try:
    from modules.pdf_processor import process_uploaded_file

    PDF_PROCESSOR_OK = True
    PDF_PROCESSOR_ERROR = None

except Exception as e:
    PDF_PROCESSOR_OK = False
    PDF_PROCESSOR_ERROR = str(e)


# AI ANALYZER
try:
    from modules.ai_analyzer import analyze_reaction_route

    AI_ANALYZER_OK = True
    AI_ANALYZER_ERROR = None

except Exception as e:
    AI_ANALYZER_OK = False
    AI_ANALYZER_ERROR = str(e)


# STRUCTURE ENGINE
try:
    from modules.structure_engine import analyze_structure

    STRUCTURE_ENGINE_OK = True
    STRUCTURE_ENGINE_ERROR = None

except Exception as e:
    STRUCTURE_ENGINE_OK = False
    STRUCTURE_ENGINE_ERROR = str(e)


# REACTION DATABASE
try:
    from modules.reaction_database import identify_named_reactions

    REACTION_DATABASE_OK = True
    REACTION_DATABASE_ERROR = None

except Exception as e:
    REACTION_DATABASE_OK = False
    REACTION_DATABASE_ERROR = str(e)


# MECHANISM ENGINE
try:
    from modules.mechanism_engine import generate_mechanism

    MECHANISM_ENGINE_OK = True
    MECHANISM_ENGINE_ERROR = None

except Exception as e:
    MECHANISM_ENGINE_OK = False
    MECHANISM_ENGINE_ERROR = str(e)


# MECHANISM RENDERER
try:
    from modules.mechanism_renderer import (
        render_mechanism_scheme,
        render_structure,
        renderer_status,
    )

    MECHANISM_RENDERER_OK = True
    MECHANISM_RENDERER_ERROR = None

except Exception as e:
    MECHANISM_RENDERER_OK = False
    MECHANISM_RENDERER_ERROR = str(e)


# CASCADE RENDERER
try:
    from modules.cascade_renderer import render_structure_cascade

    CASCADE_RENDERER_OK = True
    CASCADE_RENDERER_ERROR = None

except Exception as e:
    CASCADE_RENDERER_OK = False
    CASCADE_RENDERER_ERROR = str(e)


# REPORT GENERATOR
try:
    from modules.report_generator import generate_pdf_report

    REPORT_GENERATOR_OK = True
    REPORT_GENERATOR_ERROR = None

except Exception as e:
    REPORT_GENERATOR_OK = False
    REPORT_GENERATOR_ERROR = str(e)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_api_key():
    """
    Read OpenAI API key from Streamlit secrets or environment.
    """

    # Streamlit Cloud
    try:
        if "OPENAI_API_KEY" in st.secrets:
            key = st.secrets["OPENAI_API_KEY"]

            if key:
                return str(key)

    except Exception:
        pass

    # Local environment
    key = os.getenv("OPENAI_API_KEY")

    if key:
        return str(key)

    return None


# ------------------------------------------------------------
# SAFE VALUE
# ------------------------------------------------------------

def get_value(data, *keys, default=None):
    """
    Return first available value from dictionary.
    """

    if not isinstance(data, dict):
        return default

    for key in keys:

        if key in data:

            value = data[key]

            if value is not None:
                return value

    return default


# ------------------------------------------------------------
# SAFE JSON
# ------------------------------------------------------------

def make_json_safe(value):
    """
    Convert data into JSON serializable format.
    """

    if value is None:
        return None

    if isinstance(value, dict):

        return {
            str(k): make_json_safe(v)
            for k, v in value.items()
        }

    if isinstance(value, list):

        return [
            make_json_safe(v)
            for v in value
        ]

    if isinstance(value, tuple):

        return [
            make_json_safe(v)
            for v in value
        ]

    if isinstance(value, bytes):

        return (
            f"<binary image data: "
            f"{len(value)} bytes>"
        )

    try:
        json.dumps(value)
        return value

    except Exception:
        return str(value)


# ------------------------------------------------------------
# NORMALIZE ROUTE
# ------------------------------------------------------------

def get_steps(route_data):
    """
    Extract reaction steps from different possible AI formats.
    """

    if route_data is None:
        return []

    if isinstance(route_data, list):
        return route_data

    if isinstance(route_data, dict):

        if isinstance(
            route_data.get("steps"),
            list
        ):
            return route_data["steps"]

        if isinstance(
            route_data.get("reactions"),
            list
        ):
            return route_data["reactions"]

        if isinstance(
            route_data.get("reaction_steps"),
            list
        ):
            return route_data["reaction_steps"]

    return []


# ------------------------------------------------------------
# TEXT CONVERSION
# ------------------------------------------------------------

def value_to_text(value):
    """
    Convert lists/dictionaries to readable text.
    """

    if value is None:
        return ""

    if isinstance(value, list):

        return ", ".join(
            str(x) for x in value
        )

    if isinstance(value, dict):

        return "; ".join(
            f"{k}: {v}"
            for k, v in value.items()
        )

    return str(value)


# ------------------------------------------------------------
# STRUCTURE ANALYSIS
# ------------------------------------------------------------

def analyze_smiles(smiles):

    if not smiles:
        return None

    if not STRUCTURE_ENGINE_OK:
        return None

    try:

        return analyze_structure(
            smiles
        )

    except Exception:

        return None


# ------------------------------------------------------------
# STRUCTURE IMAGE
# ------------------------------------------------------------

def get_structure_image(smiles):

    if not smiles:
        return None

    if not MECHANISM_RENDERER_OK:
        return None

    try:

        return render_structure(
            smiles
        )

    except Exception:

        return None


# ------------------------------------------------------------
# RENDER REACTION
# ------------------------------------------------------------

def get_reaction_image(
    reactant_smiles,
    product_smiles,
    reagent_text=""
):

    if not reactant_smiles:
        return None

    if not product_smiles:
        return None

    if not MECHANISM_RENDERER_OK:
        return None

    try:

        return render_mechanism_scheme(
            reactant_smiles,
            product_smiles,
            reagent_text,
        )

    except Exception:

        return None


# ============================================================
# SESSION STATE
# ============================================================

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if "uploaded_filename" not in st.session_state:
    st.session_state["uploaded_filename"] = None

if "analysis_complete" not in st.session_state:
    st.session_state["analysis_complete"] = False


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("⚗️ Mechanism AI")

    st.markdown(
        f"**Version {APP_VERSION}**"
    )

    st.divider()

    st.subheader("Analysis Options")

    identify_names = st.checkbox(
        "Named reaction identification",
        value=True,
    )

    mechanism_option = st.checkbox(
        "Generate proposed mechanism",
        value=True,
    )

    render_option = st.checkbox(
        "Render reaction schemes",
        value=True,
    )

    cascade_option = st.checkbox(
        "Generate structure cascade",
        value=True,
    )

    st.divider()

    st.subheader("System Status")

    if PDF_PROCESSOR_OK:
        st.success("PDF processor ✓")
    else:
        st.error("PDF processor ✗")

    if AI_ANALYZER_OK:
        st.success("AI analyzer ✓")
    else:
        st.error("AI analyzer ✗")

    if STRUCTURE_ENGINE_OK:
        st.success("Structure engine ✓")
    else:
        st.error("Structure engine ✗")

    if REACTION_DATABASE_OK:
        st.success("Reaction database ✓")
    else:
        st.warning("Reaction database")

    if MECHANISM_ENGINE_OK:
        st.success("Mechanism engine ✓")
    else:
        st.warning("Mechanism engine")

    if MECHANISM_RENDERER_OK:
        st.success("Mechanism renderer ✓")
    else:
        st.warning("Mechanism renderer")

    if CASCADE_RENDERER_OK:
        st.success("Cascade renderer ✓")
    else:
        st.warning("Cascade renderer")

    if REPORT_GENERATOR_OK:
        st.success("PDF generator ✓")
    else:
        st.warning("PDF generator")

    st.divider()

    api_key = get_api_key()

    if api_key:
        st.success(
            "OpenAI API key detected ✓"
        )
    else:
        st.warning(
            "OpenAI API key not detected"
        )


# ============================================================
# HEADER
# ============================================================

st.title(
    "⚗️ Automated Chemical Reaction Mechanism Analysis"
)

st.markdown(
    """
### AI-assisted multistep chemical synthesis analysis

Upload a **reaction PDF or chemical reaction image** to analyze:

**Structure → Reaction → Named Reaction → Reaction Center →
Mechanism → Intermediate Cascade → PDF Report**
"""
)

st.info(
    """
**Scientific disclaimer:** The structures, atom assignments,
reaction mechanisms, named-reaction classifications and
stereochemical interpretations generated by this application
are AI-assisted/proposed results. They must be reviewed by a
qualified chemist before use in process development, analytical
investigation, regulatory documentation, GMP documentation,
publication or other scientific decision-making.
"""
)


# ============================================================
# UPLOAD SECTION
# ============================================================

st.header("1️⃣ Upload Reaction Route")

uploaded_file = st.file_uploader(
    "Select PDF or reaction image",
    type=SUPPORTED_FILE_TYPES,
    help=(
        "Upload a synthesis route, reaction scheme, "
        "patent reaction image, or chemical reaction PDF."
    ),
)


if uploaded_file is not None:

    st.success(
        f"File selected: {uploaded_file.name}"
    )

    file_size = uploaded_file.size / (
        1024 * 1024
    )

    st.caption(
        f"File size: {file_size:.2f} MB"
    )


# ============================================================
# API KEY CHECK
# ============================================================

if uploaded_file is not None:

    if not api_key:

        st.error(
            """
###
