import base64
import json
import os
import time
from typing import Any, Dict, List

# ---------------------------------------------------------
# Optional SDK imports
# ---------------------------------------------------------

try:
    from google import genai
    GEMINI_AVAILABLE = True
except Exception:
    genai = None
    GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OpenAI = None
    OPENAI_AVAILABLE = False


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DEFAULT_MODELS = {
    "gemini": "gemini-3.6-flash",
    "openrouter": "openrouter/free",
    "groq": "qwen/qwen3.6-27b",
    "ollama": "gemma3:12b",
    "openai": "gpt-5.6-luna",
}


def get_secret(
    name: str,
    default: str = "",
) -> str:

    try:

        import streamlit as st

        value = st.secrets.get(
            name,
            default,
        )

        if value:
            return str(value)

    except Exception:
        pass

    return os.getenv(
        name,
        default,
    )


# ---------------------------------------------------------
# JSON schema
# ---------------------------------------------------------

SCHEMA = {
    "type": "object",
    "properties": {

        "route_summary": {
            "type": "string"
        },

        "overall_confidence": {
            "type": "number"
        },

        "starting_materials": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "final_products": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "steps": {
            "type": "array",
            "items": {

                "type": "object",

                "properties": {

                    "step_number": {
                        "type": "integer"
                    },

                    "reactants": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },

                    "products": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },

                    "reagents": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },

                    "conditions": {
                        "type": "string"
                    },

                    "transformation": {
                        "type": "string"
                    },

                    "mechanistic_class": {
                        "type": "string"
                    },

                    "confidence": {
                        "type": "number"
                    },

                    "reactant_smiles": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },

                    "product_smiles": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },

                    "intermediates": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },

                    "electron_flow": {
                        "type": "string"
                    },

                    "notes": {
                        "type": "string"
                    },
                },

                "required": [
                    "step_number",
                    "reactants",
                    "products",
                    "reagents",
                    "conditions",
                    "transformation",
                    "mechanistic_class",
                    "confidence",
                ],
            },
        },
    },

    "required": [
        "route_summary",
        "overall_confidence",
        "starting_materials",
        "final_products",
        "steps",
    ],
}


# ---------------------------------------------------------
# Prompt
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are an expert synthetic organic chemist and reaction mechanism analyst.

Analyze the supplied synthetic route PDF/image and accompanying text.

Your tasks are:

1. Identify every discrete synthetic transformation.
2. Identify reactants and products.
3. Extract reagents, catalysts, solvents and conditions.
4. Infer the most probable reaction class.
5. Identify named reactions where justified.
6. Propose a chemically reasonable mechanism.
7. Identify likely intermediates.
8. Provide probable electron-flow description.
9. Extract SMILES when structures are visually identifiable.
10. Never invent a structure if the image is unclear.
11. Clearly distinguish observed information from inferred information.
12. Assign confidence values between 0 and 1.

Important:
- Do not claim certainty where the structure is ambiguous.
- Preserve stereochemistry when visible.
- Do not silently change molecular structures.
- Prefer chemically conservative interpretation.
- For each step, explain the transformation at the molecular level.
"""


# ---------------------------------------------------------
# Input construction
# ---------------------------------------------------------

def build_prompt(
    text: str,
) -> str:

    return f"""
{SYSTEM_PROMPT}

DOCUMENT TEXT:

{text[:30000]}

Return ONLY JSON conforming to the supplied schema.
"""


def image_to_part(
    image: Any,
) -> Dict[str, Any]:

    if isinstance(image, dict):

        data = image.get("data")

        if data is None:

            raw = image.get("bytes")

            if raw is not None:
                data = base64.b64encode(
                    raw
                ).decode("utf-8")

        mime = image.get(
            "mime_type",
            "image/png",
        )

        return {
            "type": "image",
            "mime_type": mime,
            "data": data,
        }

    if isinstance(image, bytes):

        return {
            "type": "image",
            "mime_type": "image/png",
            "data": base64.b64encode(
                image
            ).decode("utf-8"),
        }

    return None


# ---------------------------------------------------------
# Gemini Interactions API
# ---------------------------------------------------------

def call_gemini(
    text: str,
    images: List[Any],
    model: str,
) -> Dict[str, Any]:

    if not GEMINI_AVAILABLE:

        raise RuntimeError(
            "google-genai package is not installed."
        )

    api_key = get_secret(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(
        api_key=api_key
    )

    input_parts = [
        {
            "type": "text",
            "text": build_prompt(text),
        }
    ]

    for image in images[:8]:

        part = image_to_part(
            image
        )

        if part and part.get("data"):

            input_parts.append(
                part
            )

    interaction = client.interactions.create(

        model=model,

        input=input_parts,

        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": SCHEMA,
        },
    )

    output = getattr(
        interaction,
        "output_text",
        None,
    )

    if not output:

        raise RuntimeError(
            "Gemini returned no output text."
        )

    return json.loads(
        output
    )


# ---------------------------------------------------------
# OpenAI-compatible providers
# ---------------------------------------------------------

def call_openai_compatible(
    provider: str,
    text: str,
    images: List[Any],
    model: str,
) -> Dict[str, Any]:

    if not OPENAI_AVAILABLE:

        raise RuntimeError(
            "openai package is not installed."
        )

    if provider == "openrouter":

        api_key = get_secret(
            "OPENROUTER_API_KEY"
        )

        base_url = (
            "https://openrouter.ai/api/v1"
        )

    elif provider == "groq":

        api_key = get_secret(
            "GROQ_API_KEY"
        )

        base_url = (
            "https://api.groq.com/openai/v1"
        )

    elif provider == "ollama":

        api_key = (
            get_secret(
                "OLLAMA_API_KEY",
                "ollama",
            )
            or "ollama"
        )

        base_url = get_secret(
            "OLLAMA_BASE_URL",
            "http://localhost:11434/v1",
        )

    elif provider == "openai":

        api_key = get_secret(
            "OPENAI_API_KEY"
        )

        base_url = None

    else:

        raise ValueError(
            f"Unsupported provider: {provider}"
        )

    if not api_key:

        raise RuntimeError(
            f"{provider} API key is not configured."
        )

    kwargs = {
        "api_key": api_key
    }

    if base_url:
        kwargs["base_url"] = base_url

    client = OpenAI(
        **kwargs
    )

    user_content = [
        {
            "type": "text",
            "text": build_prompt(text),
        }
    ]

    for image in images[:8]:

        part = image_to_part(
            image
        )

        if not part:
            continue

        user_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url":
                        "data:"
                        + part["mime_type"]
                        + ";base64,"
                        + part["data"]
                },
            }
        )

    response = client.chat.completions.create(

        model=model,

        messages=[
            {
                "role": "system",
                "content":
                    SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content":
                    user_content,
            },
        ],

        temperature=0.1,

        response_format={
            "type": "json_object"
        },
    )

    content = response.choices[0].message.content

    if not content:

        raise RuntimeError(
            f"{provider} returned empty response."
        )

    return json.loads(
        content
    )


# ---------------------------------------------------------
# Provider dispatcher
# ---------------------------------------------------------

def call_provider(
    provider: str,
    text: str,
    images: List[Any],
) -> Dict[str, Any]:

    model = get_secret(
        provider.upper() + "_MODEL",
        DEFAULT_MODELS[provider],
    )

    if provider == "gemini":

        return call_gemini(
            text=text,
            images=images,
            model=model,
        )

    return call_openai_compatible(
        provider=provider,
        text=text,
        images=images,
        model=model,
    )


# ---------------------------------------------------------
# Provider order
# ---------------------------------------------------------

def provider_order(
    selected: str,
) -> List[str]:

    mapping = {
        "Gemini": ["gemini"],
        "OpenRouter": ["openrouter"],
        "Groq": ["groq"],
        "Ollama": ["ollama"],
        "OpenAI": ["openai"],
    }

    if selected in mapping:
        return mapping[selected]

    raw = get_secret(
        "AI_FALLBACK_ORDER",
        "gemini,openrouter,groq,ollama,openai",
    )

    return [
        x.strip().lower()
        for x in raw.split(",")
        if x.strip()
    ]


# ---------------------------------------------------------
# Main analysis
# ---------------------------------------------------------

def analyze_route(
    text: str,
    images: List[Any],
    provider: str = "Automatic",
) -> Dict[str, Any]:

    providers = provider_order(
        provider
    )

    errors = []

    for current_provider in providers:

        if current_provider not in DEFAULT_MODELS:
            continue

        for attempt in range(3):

            try:

                analysis = call_provider(
                    provider=current_provider,
                    text=text,
                    images=images,
                )

                return {
                    "success": True,
                    "provider":
                        current_provider,
                    "model":
                        get_secret(
                            current_provider.upper()
                            + "_MODEL",
                            DEFAULT_MODELS[
                                current_provider
                            ],
                        ),
                    "analysis":
                        analysis,
                    "diagnostics":
                        errors,
                }

            except Exception as exc:

                msg = (
                    f"{current_provider} "
                    f"attempt {attempt + 1}: "
                    f"{exc}"
                )

                errors.append(
                    msg
                )

                # Do not wait unnecessarily
                # for obvious configuration errors.
                text_error = str(
                    exc
                ).lower()

                if any(
                    x in text_error
                    for x in [
                        "api key",
                        "not configured",
                        "authentication",
                        "unauthorized",
                        "404",
                    ]
                ):
                    break

                time.sleep(
                    1.5 * (attempt + 1)
                )

    return {
        "success": False,
        "error":
            "All configured AI providers failed.",
        "diagnostics":
            errors,
    }


# ---------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------

def get_provider_status():

    result = {}

    for provider in DEFAULT_MODELS:

        key_name = (
            provider.upper()
            + "_API_KEY"
        )

        if provider == "ollama":

            enabled = get_secret(
                "OLLAMA_ENABLED",
                "false",
            ).lower() == "true"

        else:

            enabled = bool(
                get_secret(
                    key_name,
                    "",
                )
            )

        result[provider] = {
            "configured": enabled,
            "model":
                get_secret(
                    provider.upper()
                    + "_MODEL",
                    DEFAULT_MODELS[
                        provider
                    ],
                ),
        }

    return result
