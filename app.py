import json
import os
import streamlit as st

APP_NAME = "Chemical Reaction Mechanism Automation"
APP_VERSION = "5.3.0"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧪",
    layout="wide",
)

# ---------------------------------------------------------
# Safe imports
# ---------------------------------------------------------

IMPORT_ERRORS = {}

try:
    from modules.pdf_processor import extract_pages
except Exception as exc:
    extract_pages = None
    IMPORT_ERRORS["pdf_processor"] = str(exc)

try:
    from modules.ai_analyzer import analyze_route, provider_status
except Exception as exc:
    analyze_route = None
    provider_status = None
    IMPORT_ERRORS["ai_analyzer"] = str(exc)

try:
    from modules.structure_engine import enrich_step, describe_smiles
except Exception as exc:
    enrich_step = None
    describe_smiles = None
    IMPORT_ERRORS["structure_engine"] = str(exc)

try:
    from modules.reaction_database import identify_named_reactions
except Exception as exc:
    identify_named_reactions = None
    IMPORT_ERRORS["reaction_database"] = str(exc)

try:
    from modules.mechanism_engine import build_mechanism
except Exception as exc:
    build_mechanism = None
    IMPORT_ERRORS["mechanism_engine"] = str(exc)

try:
    from modules.mechanism_renderer import (
        render_mechanism_scheme,
        renderer_status,
    )
except Exception as exc:
    render_mechanism_scheme = None
    renderer_status = None
    IMPORT_ERRORS["mechanism_renderer"] = str(exc)

try:
    from modules.cascade_renderer import render_cascade
except Exception as exc:
    render_cascade = None
    IMPORT_ERRORS["cascade_renderer"] = str(exc)

try:
    from modules.report_generator import build_pdf
except Exception as exc:
    build_pdf = None
    IMPORT_ERRORS["report_generator"] = str(exc)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def get_secret(name, default=None):
    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass

    return os.getenv(name, default)


def get_bool_secret(name, default=False):
    value = get_secret(name, default)

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def json_safe(obj):
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if key in {
                "image",
                "png",
                "image_bytes",
                "scheme_png",
                "cascade_png",
            }:
                continue
            result[key] = json_safe(value)
        return result

    if isinstance(obj, list):
        return [json_safe(x) for x in obj]

    if isinstance(obj, bytes):
        return None

    return obj


def render_mol(smiles):
    try:
        from modules.structure_engine import describe_smiles
        from modules.mechanism_renderer import render_structure

        data = describe_smiles(smiles)

        if data and data.get("valid"):
            png = render_structure(smiles)

            if png:
                st.image(png, width=400)

            st.caption(
                f"Formula: {data.get('formula', 'N/A')} | "
                f"MW: {data.get('mw', 'N/A')} | "
                f"SMILES: {data.get('canonical_smiles', smiles)}"
            )
        else:
            st.warning(f"Invalid or unreadable SMILES: {smiles}")

    except Exception as exc:
        st.warning(f"Structure rendering unavailable: {exc}")


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("🧪 Chemical Reaction Mechanism Automation")

st.caption(
    f"Version {APP_VERSION} — Multistep synthetic-route analysis, "
    "structure validation, named reactions and proposed mechanisms"
)

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("AI Configuration")

    provider_options = [
        "Automatic",
        "Gemini",
        "OpenRouter",
        "Groq",
        "Ollama",
        "OpenAI",
    ]

    default_provider = get_secret("AI_PROVIDER", "auto")

    provider_map = {
        "auto": "Automatic",
        "automatic": "Automatic",
        "gemini": "Gemini",
        "openrouter": "OpenRouter",
        "groq": "Groq",
        "ollama": "Ollama",
        "openai": "OpenAI",
    }

    provider_default = provider_map.get(
        str(default_provider).lower(),
        "Automatic",
    )

    provider = st.selectbox(
        "AI Provider",
        provider_options,
        index=provider_options.index(provider_default),
    )

    provider_internal = provider.lower()

    if provider_internal == "automatic":
        provider_internal = "auto"

    model_defaults = {
        "gemini": get_secret(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        ),
        "openrouter": get_secret(
            "OPENROUTER_MODEL",
            "openrouter/free",
        ),
        "groq": get_secret(
            "GROQ_MODEL",
            "qwen/qwen3.6-27b",
        ),
        "ollama": get_secret(
            "OLLAMA_MODEL",
            "gemma3:12b",
        ),
        "openai": get_secret(
            "OPENAI_MODEL",
            "gpt-5.6-luna",
        ),
    }

    model = st.text_input(
        "Model",
        value=model_defaults.get(
            provider_internal,
            model_defaults["gemini"],
        ),
    )

    image_detail = st.selectbox(
        "Image detail",
        ["high", "auto", "low"],
        index=0,
    )

    st.divider()

    st.header("Analysis Options")

    render_arrows = st.checkbox(
        "Render mechanism arrows",
        value=True,
    )

    identify_names = st.checkbox(
        "Identify named reactions",
        value=True,
    )

    propose_mechanisms = st.checkbox(
        "Generate proposed mechanisms",
        value=True,
    )

    show_cascade = st.checkbox(
        "Generate structure cascade",
        value=True,
    )

    st.divider()

    st.caption(
        "V5.3 supports Gemini, OpenRouter, Groq, "
        "Ollama and OpenAI."
    )


# ---------------------------------------------------------
# API availability
# ---------------------------------------------------------

if provider_status:

    with st.expander("AI provider status"):

        try:
            statuses = provider_status()

            for name, info in statuses.items():

                available = info.get("available", False)

                if available:
                    st.success(
                        f"{name}: configured"
                    )
                else:
                    st.info(
                        f"{name}: not configured"
                    )

        except Exception as exc:
            st.warning(str(exc))


# ---------------------------------------------------------
# OpenAI/Gemini keys are NOT hard-coded
# ---------------------------------------------------------

if not any([
    get_secret("GEMINI_API_KEY"),
    get_secret("OPENROUTER_API_KEY"),
    get_secret("GROQ_API_KEY"),
    get_bool_secret("OLLAMA_ENABLED", False),
    get_secret("OPENAI_API_KEY"),
]):

    st.warning(
        "No AI provider is configured. "
        "Add at least one provider API key in Streamlit Secrets."
    )


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
        "tif",
        "tiff",
    ],
)


if uploaded_file:

    st.write(
        f"**File:** {uploaded_file.name}  "
        f"({uploaded_file.size / 1024:.1f} KB)"
    )

    if extract_pages is None:
        st.error(
            "PDF/image processor could not be loaded."
        )
        st.stop()

    try:

        pages = extract_pages(
            uploaded_file.getvalue(),
            uploaded_file.name,
        )

        st.success(
            f"Loaded {len(pages)} page(s)."
        )

        with st.expander("Preview uploaded route"):

            for page in pages:

                st.image(
                    page["image"],
                    caption=f"Page {page['page_number']}",
                    use_container_width=True,
                )

    except Exception as exc:

        st.error(
            f"Unable to read uploaded file: {exc}"
        )
        st.stop()


# ---------------------------------------------------------
# Analyze
# ---------------------------------------------------------

analyze_button = st.button(
    "🔬 Analyze Reaction Route",
    type="primary",
    use_container_width=True,
)


if analyze_button:

    if not uploaded_file:

        st.error(
            "Please upload a PDF or reaction-route image first."
        )
        st.stop()

    if analyze_route is None:

        st.error(
            "AI analyzer could not be loaded."
        )
        st.stop()

    if not pages:

        st.error(
            "No pages were extracted from the uploaded file."
        )
        st.stop()

    try:

        with st.status(
            "Analyzing synthetic route...",
            expanded=True,
        ):

            st.write(
                f"AI provider: **{provider}**"
            )

            st.write(
                "Extracting reaction structures and conditions..."
            )

            route = analyze_route(
                pages=pages,
                model=model,
                detail=image_detail,
                provider=provider_internal,
                fallback=(provider_internal == "auto"),
            )

            steps = route.get("steps", [])

            st.write(
                f"Detected **{len(steps)} reaction step(s)**."
            )

            # ---------------------------------------------
            # RDKit validation
            # ---------------------------------------------

            if enrich_step:

                st.write(
                    "Validating structures with RDKit..."
                )

                enriched_steps = []

                for step in steps:

                    try:
                        enriched_steps.append(
                            enrich_step(step)
                        )

                    except Exception as exc:

                        step["structure_validation_error"] = str(
                            exc
                        )

                        enriched_steps.append(step)

                route["steps"] = enriched_steps

            # ---------------------------------------------
            # Named reactions
            # ---------------------------------------------

            if identify_names and identify_named_reactions:

                st.write(
                    "Searching named-reaction database..."
                )

                for step in route.get("steps", []):

                    try:

                        step["named_reactions"] = (
                            identify_named_reactions(step)
                        )

                    except Exception as exc:

                        step["named_reactions"] = []

                        step["named_reaction_error"] = str(
                            exc
                        )

            # ---------------------------------------------
            # Mechanisms
            # ---------------------------------------------

            if propose_mechanisms and build_mechanism:

                st.write(
                    "Generating proposed reaction mechanisms..."
                )

                for step in route.get("steps", []):

                    try:

                        step["mechanism"] = build_mechanism(
                            step
                        )

                    except Exception as exc:

                        step["mechanism"] = {
                            "error": str(exc)
                        }

            # ---------------------------------------------
            # Reaction scheme rendering
            # ---------------------------------------------

            if render_mechanism_scheme:

                st.write(
                    "Rendering reaction schemes..."
                )

                for step in route.get("steps", []):

                    try:

                        step["scheme_png"] = (
                            render_mechanism_scheme(
                                step,
                                arrows=render_arrows,
                            )
                        )

                    except Exception as exc:

                        step["scheme_error"] = str(exc)

            # ---------------------------------------------
            # Structure cascade
            # ---------------------------------------------

            if show_cascade and render_cascade:

                st.write(
                    "Generating structure cascade..."
                )

                try:

                    route["cascade_png"] = render_cascade(
                        route
                    )

                except Exception as exc:

                    route["cascade_error"] = str(exc)

            route["analysis_metadata"] = {
                "application": APP_NAME,
                "version": APP_VERSION,
                "provider": provider_internal,
                "model": model,
            }

            st.session_state["route"] = route

            st.success(
                "Analysis completed."
            )

    except Exception as exc:

        st.error(
            f"Analysis failed: {exc}"
        )

        st.info(
            "If this is a temporary 429/503 provider error, "
            "try Automatic mode again. V5.3 supports provider fallback."
        )


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

route = st.session_state.get("route")


if route:

    st.divider()

    st.header("Analysis Results")

    tabs = st.tabs([
        "Route",
        "Structures",
        "Named Reactions",
        "Mechanisms",
        "Data",
        "Downloads",
        "Diagnostics",
    ])

    # -----------------------------------------------------
    # Route
    # -----------------------------------------------------

    with tabs[0]:

        st.subheader(
            route.get(
                "route_title",
                "Synthetic Route",
            )
        )

        st.write(
            route.get(
                "route_summary",
                "",
            )
        )

        for step in route.get("steps", []):

            with st.expander(
                f"Step {step.get('step_number', '?')}: "
                f"{step.get('transformation', '')}",
                expanded=True,
            ):

                col1, col2 = st.columns(2)

                with col1:

                    st.markdown(
                        "**Reaction class**"
                    )

                    st.write(
                        step.get(
                            "reaction_class",
                            "N/A",
                        )
                    )

                    st.markdown(
                        "**Reagents**"
                    )

                    reagents = step.get(
                        "reagents",
                        [],
                    )

                    if isinstance(reagents, list):
                        st.write(
                            ", ".join(reagents)
                        )
                    else:
                        st.write(reagents)

                    st.markdown(
                        "**Solvent**"
                    )

                    st.write(
                        step.get(
                            "solvent",
                            "N/A",
                        )
                    )

                with col2:

                    st.markdown(
                        "**Temperature**"
                    )

                    st.write(
                        step.get(
                            "temperature",
                            "N/A",
                        )
                    )

                    st.markdown(
                        "**Time**"
                    )

                    st.write(
                        step.get(
                            "time",
                            "N/A",
                        )
                    )

                    st.markdown(
                        "**Pressure**"
                    )

                    st.write(
                        step.get(
                            "pressure",
                            "N/A",
                        )
                    )

                    st.markdown(
                        "**Yield**"
                    )

                    st.write(
                        step.get(
                            "yield",
                            "N/A",
                        )
                    )

                st.markdown(
                    "**Stereochemical changes**"
                )

                st.write(
                    step.get(
                        "stereochemical_changes",
                        "N/A",
                    )
                )

                st.markdown(
                    "**Confidence / uncertainty**"
                )

                st.write(
                    step.get(
                        "confidence",
                        "N/A",
                    )
                )

                if step.get("uncertainty"):
                    st.warning(
                        step["uncertainty"]
                    )

                if step.get("scheme_png"):
                    st.image(
                        step["scheme_png"],
                        use_container_width=True,
                    )

    # -----------------------------------------------------
    # Structures
    # -----------------------------------------------------

    with tabs[1]:

        for step in route.get("steps", []):

            st.subheader(
                f"Step {step.get('step_number', '?')}"
            )

            reactants = step.get(
                "reactants_smiles",
                [],
            )

            products = step.get(
                "products_smiles",
                [],
            )

            col1, col2 = st.columns(2)

            with col1:

                st.markdown("### Reactants")

                if reactants:

                    for smi in reactants:
                        render_mol(smi)

                else:
                    st.info(
                        "No reliable reactant SMILES extracted."
                    )

            with col2:

                st.markdown("### Products")

                if products:

                    for smi in products:
                        render_mol(smi)

                else:
                    st.info(
                        "No reliable product SMILES extracted."
                    )

    # -----------------------------------------------------
    # Named reactions
    # -----------------------------------------------------

    with tabs[2]:

        for step in route.get("steps", []):

            st.subheader(
                f"Step {step.get('step_number', '?')}"
            )

            names = step.get(
                "named_reactions",
                [],
            )

            if not names:

                st.info(
                    "No strong named-reaction match."
                )

            else:

                for item in names:

                    if isinstance(item, dict):

                        name = item.get(
                            "name",
                            "Candidate",
                        )

                        score = item.get(
                            "score",
                            "",
                        )

                        explanation = item.get(
                            "explanation",
                            "",
                        )

                        st.markdown(
                            f"**{name}** — score: {score}"
                        )

                        if explanation:
                            st.write(
                                explanation
                            )

                    else:

                        st.write(item)

    # -----------------------------------------------------
    # Mechanisms
    # -----------------------------------------------------

    with tabs[3]:

        for step in route.get("steps", []):

            st.subheader(
                f"Step {step.get('step_number', '?')}"
            )

            mechanism = step.get(
                "mechanism"
            )

            if not mechanism:

                st.info(
                    "No mechanism generated."
                )
                continue

            if isinstance(mechanism, dict):

                for key, value in mechanism.items():

                    st.markdown(
                        f"**{key.replace('_', ' ').title()}**"
                    )

                    if isinstance(value, list):

                        for item in value:
                            st.write(
                                f"• {item}"
                            )

                    else:

                        st.write(value)

            else:

                st.write(mechanism)

    # -----------------------------------------------------
    # Data
    # -----------------------------------------------------

    with tabs[4]:

        st.json(
            json_safe(route)
        )

    # -----------------------------------------------------
    # Downloads
    # -----------------------------------------------------

    with tabs[5]:

        json_data = json.dumps(
            json_safe(route),
            indent=2,
            ensure_ascii=False,
        )

        st.download_button(
            "Download JSON Report",
            data=json_data,
            file_name="reaction_mechanism_analysis.json",
            mime="application/json",
        )

        if build_pdf:

            try:

                pdf_bytes = build_pdf(route)

                if pdf_bytes:

                    st.download_button(
                        "Download PDF Report",
                        data=pdf_bytes,
                        file_name="reaction_mechanism_analysis.pdf",
                        mime="application/pdf",
                    )

            except Exception as exc:

                st.error(
                    f"PDF report generation failed: {exc}"
                )

        else:

            st.warning(
                "PDF generator unavailable."
            )

        cascade = route.get(
            "cascade_png"
        )

        if cascade:

            st.download_button(
                "Download Structure Cascade PNG",
                data=cascade,
                file_name="structure_cascade.png",
                mime="image/png",
            )

    # -----------------------------------------------------
    # Diagnostics
    # -----------------------------------------------------

    with tabs[6]:

        st.subheader("Module status")

        if IMPORT_ERRORS:

            for module, error in IMPORT_ERRORS.items():

                st.error(
                    f"{module}: {error}"
                )

        else:

            st.success(
                "All application modules imported successfully."
            )

        if renderer_status:

            try:

                st.json(
                    renderer_status()
                )

            except Exception as exc:

                st.warning(
                    f"Renderer diagnostics unavailable: {exc}"
                )

        if provider_status:

            try:

                st.json(
                    provider_status()
                )

            except Exception as exc:

                st.warning(
                    f"Provider diagnostics unavailable: {exc}"
                )

        st.markdown("### Analysis metadata")

        st.json(
            route.get(
                "analysis_metadata",
                {},
            )
        )


# ---------------------------------------------------------
# Scientific disclaimer
# ---------------------------------------------------------

st.divider()

st.caption(
    "Scientific disclaimer: AI-generated structures, reaction assignments, "
    "atom mappings and mechanisms are proposed interpretations and must be "
    "independently verified by a qualified chemist using appropriate "
    "spectroscopic, analytical and literature evidence."
)
