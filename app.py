import json
import traceback
from pathlib import Path

import streamlit as st

APP_VERSION = "5.3.1"

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------
# Safe imports
# ---------------------------------------------------------

IMPORT_ERRORS = []

try:
    from modules.pdf_processor import (
        process_uploaded_file,
        get_text_from_pages,
    )
except Exception as e:
    IMPORT_ERRORS.append(f"pdf_processor: {e}")

try:
    from modules.ai_analyzer import (
        analyze_route,
        get_provider_status,
    )
except Exception as e:
    IMPORT_ERRORS.append(f"ai_analyzer: {e}")

try:
    from modules.structure_engine import (
        enrich_structures,
    )
except Exception as e:
    IMPORT_ERRORS.append(f"structure_engine: {e}")

try:
    from modules.reaction_database import (
        identify_named_reactions,
    )
except Exception as e:
    IMPORT_ERRORS.append(f"reaction_database: {e}")

try:
    from modules.mechanism_engine import (
        build_mechanism_report,
    )
except Exception as e:
    IMPORT_ERRORS.append(f"mechanism_engine: {e}")

try:
    from modules.mechanism_renderer import (
        render_mechanism_scheme,
    )
except Exception as e:
    IMPORT_ERRORS.append(f"mechanism_renderer: {e}")

try:
    from modules.cascade_renderer import (
        render_cascade,
    )
except Exception as e:
    IMPORT_ERRORS.append(f"cascade_renderer: {e}")

try:
    from modules.report_generator import (
        build_pdf,
        reportlab_status,
    )
except Exception as e:
    IMPORT_ERRORS.append(f"report_generator: {e}")


# ---------------------------------------------------------
# Page
# ---------------------------------------------------------

st.set_page_config(
    page_title="Chemical Reaction Mechanism Automation",
    page_icon="⚗️",
    layout="wide",
)

st.title("⚗️ Chemical Reaction Mechanism Automation")
st.caption(f"Version {APP_VERSION}")

st.markdown(
    """
Upload a **synthetic route PDF, reaction scheme image, or experimental
reaction document** and the application will attempt to identify:

- starting materials
- products
- reagents
- solvents
- catalysts
- reaction conditions
- reaction transformations
- named reactions
- probable mechanisms
- intermediates
- structure cascade
- molecular formula / MW where structures are available
"""
)


# ---------------------------------------------------------
# Secrets
# ---------------------------------------------------------

def secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        return value if value is not None else default
    except Exception:
        return default


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("⚙️ Configuration")

    provider_options = [
        "Automatic",
        "Gemini",
        "OpenRouter",
        "Groq",
        "Ollama",
        "OpenAI",
    ]

    selected_provider = st.selectbox(
        "AI Provider",
        provider_options,
        index=0,
    )

    fallback_order = secret(
        "AI_FALLBACK_ORDER",
        "gemini,openrouter,groq,ollama,openai",
    )

    st.caption(
        f"Fallback order: `{fallback_order}`"
    )

    st.divider()

    st.subheader("Models")

    st.code(
        f"""
Gemini      : {secret("GEMINI_MODEL", "gemini-3.6-flash")}
OpenRouter  : {secret("OPENROUTER_MODEL", "openrouter/free")}
Groq        : {secret("GROQ_MODEL", "qwen/qwen3.6-27b")}
Ollama      : {secret("OLLAMA_MODEL", "gemma3:12b")}
OpenAI      : {secret("OPENAI_MODEL", "gpt-5.6-luna")}
""",
        language="text",
    )

    st.divider()

    if IMPORT_ERRORS:
        st.error("Import problems detected")
        for err in IMPORT_ERRORS:
            st.code(err)

    if "reportlab_status" in globals():
        try:
            st.caption(reportlab_status())
        except Exception:
            pass


# ---------------------------------------------------------
# Upload
# ---------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload synthetic route PDF or image",
    type=[
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "webp",
        "tif",
        "tiff",
    ],
)

if uploaded_file is None:

    st.info(
        "Upload a PDF or reaction-scheme image to begin."
    )

    with st.expander("Example workflow"):
        st.write(
            """
            1. Upload route PDF/image
            2. Extract reaction scheme and text
            3. AI identifies transformations
            4. Structures are validated using RDKit
            5. Named reactions are searched
            6. Mechanism is proposed
            7. Reaction cascade is generated
            8. Download JSON/PDF report
            """
        )

    st.stop()


# ---------------------------------------------------------
# Process file
# ---------------------------------------------------------

st.success(
    f"Uploaded: {uploaded_file.name}"
)

if st.button(
    "🔬 Analyze Synthetic Route",
    type="primary",
    use_container_width=True,
):

    try:

        with st.spinner("Reading uploaded document..."):

            file_bytes = uploaded_file.getvalue()

            processed = process_uploaded_file(
                file_bytes=file_bytes,
                filename=uploaded_file.name,
            )

        st.subheader("Document extraction")

        extracted_text = get_text_from_pages(processed)

        with st.expander(
            "View extracted text",
            expanded=False,
        ):
            st.text_area(
                "Extracted text",
                extracted_text,
                height=250,
            )

        with st.spinner(
            "Analyzing chemistry with AI..."
        ):

            result = analyze_route(
                text=extracted_text,
                images=processed.get("images", []),
                provider=selected_provider,
            )

        if not result.get("success"):

            st.error(
                "Analysis failed: "
                + str(result.get("error", "Unknown error"))
            )

            if result.get("diagnostics"):
                with st.expander("Diagnostics"):
                    st.json(result["diagnostics"])

            st.stop()

        analysis = result["analysis"]

        st.success(
            f"Analysis completed using "
            f"{result.get('provider', 'unknown')} "
            f"/ {result.get('model', 'unknown')}"
        )

        # -------------------------------------------------
        # Structures
        # -------------------------------------------------

        with st.spinner(
            "Validating chemical structures..."
        ):

            analysis = enrich_structures(
                analysis
            )

        # -------------------------------------------------
        # Named reactions
        # -------------------------------------------------

        with st.spinner(
            "Searching named reaction database..."
        ):

            named_reactions = identify_named_reactions(
                analysis
            )

        analysis["named_reactions"] = named_reactions

        # -------------------------------------------------
        # Mechanism
        # -------------------------------------------------

        with st.spinner(
            "Building proposed reaction mechanisms..."
        ):

            mechanism = build_mechanism_report(
                analysis
            )

        analysis["mechanism_report"] = mechanism

        # -------------------------------------------------
        # Display summary
        # -------------------------------------------------

        st.header("1. Route Summary")

        st.write(
            analysis.get(
                "route_summary",
                "No route summary generated.",
            )
        )

        # -------------------------------------------------
        # Steps
        # -------------------------------------------------

        st.header("2. Reaction Steps")

        steps = analysis.get("steps", [])

        if not steps:

            st.warning(
                "No discrete reaction steps were detected."
            )

        for step in steps:

            step_no = step.get(
                "step_number",
                "?",
            )

            title = step.get(
                "transformation",
                "Reaction step",
            )

            with st.expander(
                f"Step {step_no}: {title}",
                expanded=True,
            ):

                c1, c2 = st.columns(2)

                with c1:

                    st.markdown("### Reactants")

                    for item in step.get(
                        "reactants",
                        [],
                    ):
                        st.write(
                            "• "
                            + str(item)
                        )

                    st.markdown("### Reagents")

                    for item in step.get(
                        "reagents",
                        [],
                    ):
                        st.write(
                            "• "
                            + str(item)
                        )

                with c2:

                    st.markdown("### Products")

                    for item in step.get(
                        "products",
                        [],
                    ):
                        st.write(
                            "• "
                            + str(item)
                        )

                    st.markdown("### Conditions")

                    st.write(
                        step.get(
                            "conditions",
                            "",
                        )
                    )

                st.markdown("### Transformation")

                st.write(
                    step.get(
                        "transformation",
                        "",
                    )
                )

                if step.get("mechanistic_class"):
                    st.markdown(
                        "**Mechanistic class:** "
                        + str(
                            step["mechanistic_class"]
                        )
                    )

                if step.get("confidence") is not None:

                    st.progress(
                        max(
                            0.0,
                            min(
                                1.0,
                                float(
                                    step["confidence"]
                                ),
                            ),
                        )
                    )

        # -------------------------------------------------
        # Named reactions
        # -------------------------------------------------

        st.header("3. Named Reactions")

        if named_reactions:

            for nr in named_reactions:

                st.markdown(
                    f"### {nr.get('name', 'Unknown')}"
                )

                st.write(
                    nr.get(
                        "reason",
                        "",
                    )
                )

                if nr.get("confidence") is not None:

                    st.write(
                        "Confidence: "
                        + str(
                            nr["confidence"]
                        )
                    )

        else:

            st.info(
                "No strong named-reaction match found."
            )

        # -------------------------------------------------
        # Mechanism
        # -------------------------------------------------

        st.header("4. Proposed Mechanism")

        mechanism_steps = mechanism.get(
            "steps",
            [],
        )

        for item in mechanism_steps:

            st.markdown(
                f"**{item.get('number', '')}. "
                f"{item.get('title', '')}**"
            )

            st.write(
                item.get(
                    "description",
                    "",
                )
            )

            if item.get("electron_flow"):
                st.markdown(
                    "**Electron flow:** "
                    + item["electron_flow"]
                )

            if item.get("intermediate"):
                st.markdown(
                    "**Intermediate:** "
                    + item["intermediate"]
                )

        # -------------------------------------------------
        # Mechanism image
        # -------------------------------------------------

        try:

            scheme = render_mechanism_scheme(
                analysis
            )

            if scheme:

                st.header(
                    "5. Mechanism Scheme"
                )

                st.image(
                    scheme,
                    use_container_width=True,
                )

        except Exception as e:

            st.warning(
                "Mechanism rendering unavailable: "
                + str(e)
            )

        # -------------------------------------------------
        # Cascade
        # -------------------------------------------------

        try:

            cascade = render_cascade(
                analysis
            )

            if cascade:

                st.header(
                    "6. Reaction Cascade"
                )

                st.image(
                    cascade,
                    use_container_width=True,
                )

        except Exception as e:

            st.warning(
                "Cascade rendering unavailable: "
                + str(e)
            )

        # -------------------------------------------------
        # Raw JSON
        # -------------------------------------------------

        st.header("7. Complete Analysis JSON")

        json_text = json.dumps(
            analysis,
            indent=2,
            ensure_ascii=False,
        )

        st.download_button(
            "⬇️ Download JSON Report",
            data=json_text,
            file_name="reaction_mechanism_report.json",
            mime="application/json",
            use_container_width=True,
        )

        # -------------------------------------------------
        # PDF
        # -------------------------------------------------

        try:

            pdf_bytes = build_pdf(
                analysis
            )

            if pdf_bytes:

                st.download_button(
                    "⬇️ Download PDF Report",
                    data=pdf_bytes,
                    file_name="reaction_mechanism_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        except Exception as e:

            st.warning(
                "PDF generation unavailable: "
                + str(e)
            )

        # -------------------------------------------------
        # Diagnostics
        # -------------------------------------------------

        with st.expander(
            "AI Provider Diagnostics"
        ):

            try:

                st.json(
                    get_provider_status()
                )

            except Exception as e:

                st.write(
                    str(e)
                )

    except Exception as e:

        st.error(
            "Unexpected application error:"
        )

        st.code(
            traceback.format_exc()
        )
