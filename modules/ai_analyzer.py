"""
V5.3 multi-provider AI analyzer.

Supported providers:
    - Gemini
    - OpenRouter
    - Groq
    - Ollama
    - OpenAI

Automatic mode:
    Gemini -> OpenRouter -> Groq -> Ollama -> OpenAI

Transient failures such as 429 and 503 trigger retry/fallback.
"""

import base64
import io
import json
import os
import time
from typing import Any, Dict, List

from openai import OpenAI

try:
    from google import genai
    from google.genai import types

    GEMINI_SDK_AVAILABLE = True

except Exception:
    genai = None
    types = None
    GEMINI_SDK_AVAILABLE = False


# ---------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "route_title": {
            "type": "string"
        },
        "route_summary": {
            "type": "string"
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "step_number": {
                        "type": "integer"
                    },
                    "transformation": {
                        "type": "string"
                    },
                    "reactants_smiles": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "products_smiles": {
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
                    "solvent": {
                        "type": "string"
                    },
                    "temperature": {
                        "type": "string"
                    },
                    "time": {
                        "type": "string"
                    },
                    "pressure": {
                        "type": "string"
                    },
                    "yield": {
                        "type": "string"
                    },
                    "reaction_class": {
                        "type": "string"
                    },
                    "conditions_text": {
                        "type": "string"
                    },
                    "stereochemical_changes": {
                        "type": "string"
                    },
                    "confidence": {
                        "type": "string"
                    },
                    "uncertainty": {
                        "type": "string"
                    },
                },
                "required": [
                    "step_number",
                    "transformation",
                    "reactants_smiles",
                    "products_smiles",
                    "reagents",
                    "solvent",
                    "temperature",
                    "time",
                    "pressure",
                    "yield",
                    "reaction_class",
                    "conditions_text",
                    "stereochemical_changes",
                    "confidence",
                    "uncertainty",
                ],
            },
        },
    },
    "required": [
        "route_title",
        "route_summary",
        "steps",
    ],
}


PROMPT = """
You are a senior organic and process chemist.

Analyze the uploaded synthetic route image(s).

Extract every reaction step in order.

For each step identify:

1. Reactants/substrates
2. Products
3. Reagents
4. Solvents
5. Temperature
6. Reaction time
7. Pressure
8. Yield
9. Net chemical transformation
10. Reaction class
11. Stereochemical changes
12. Confidence
13. Uncertainty

IMPORTANT STRUCTURE RULES:

- Provide SMILES only when the structure can be interpreted with reasonable confidence.
- Do not invent atoms, bonds or stereochemistry.
- Preserve stereochemistry when visible.
- Preserve salts/counterions when clearly visible.
- If the structure cannot be confidently interpreted, return an empty SMILES array.
- Explain the uncertainty.
- Separate observed transformation from mechanistic inference.
- Do not force a named reaction when evidence is weak.

Return only the requested structured JSON.
"""


# ---------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------

def _secret(name: str, default=None):

    try:

        import streamlit as st

        value = st.secrets.get(name)

        if value:
            return value

    except Exception:
        pass

    return os.getenv(name, default)


def _bool_value(value):

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


# ---------------------------------------------------------
# Provider status
# ---------------------------------------------------------

def provider_status():

    return {
        "gemini": {
            "available": bool(
                _secret("GEMINI_API_KEY")
            ),
            "sdk_available": GEMINI_SDK_AVAILABLE,
            "model": _secret(
                "GEMINI_MODEL",
                "gemini-2.5-flash",
            ),
        },
        "openrouter": {
            "available": bool(
                _secret("OPENROUTER_API_KEY")
            ),
            "model": _secret(
                "OPENROUTER_MODEL",
                "openrouter/free",
            ),
        },
        "groq": {
            "available": bool(
                _secret("GROQ_API_KEY")
            ),
            "model": _secret(
                "GROQ_MODEL",
                "qwen/qwen3.6-27b",
            ),
        },
        "ollama": {
            "available": _bool_value(
                _secret(
                    "OLLAMA_ENABLED",
                    False,
                )
            ),
            "model": _secret(
                "OLLAMA_MODEL",
                "gemma3:12b",
            ),
        },
        "openai": {
            "available": bool(
                _secret("OPENAI_API_KEY")
            ),
            "model": _secret(
                "OPENAI_MODEL",
                "gpt-5.6-luna",
            ),
        },
    }


# ---------------------------------------------------------
# Image conversion
# ---------------------------------------------------------

def _image_bytes(image):

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()


def _data_url(image):

    data = _image_bytes(image)

    return (
        "data:image/png;base64,"
        + base64.b64encode(data).decode("ascii")
    )


# ---------------------------------------------------------
# Retry classification
# ---------------------------------------------------------

def _is_retryable_error(exc):

    text = str(exc).lower()

    retry_terms = [
        "429",
        "503",
        "500",
        "502",
        "504",
        "unavailable",
        "resource_exhausted",
        "rate limit",
        "rate_limit",
        "temporarily",
        "timeout",
        "deadline",
        "overloaded",
        "high demand",
    ]

    return any(
        term in text
        for term in retry_terms
    )


def _retry_delay(attempt):

    # 2, 4, 8 seconds
    return min(
        2 ** attempt,
        12,
    )


# ---------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------

def _parse_json(text):

    if not text:

        raise RuntimeError(
            "AI provider returned empty output."
        )

    text = text.strip()

    try:
        return json.loads(text)

    except Exception:
        pass

    # Remove Markdown JSON fencing
    if text.startswith("```"):

        lines = text.splitlines()

        if len(lines) >= 3:

            cleaned = "\n".join(
                lines[1:-1]
            )

            try:
                return json.loads(cleaned)

            except Exception:
                pass

    raise RuntimeError(
        "AI provider returned output that could not "
        "be parsed as JSON."
    )


# ---------------------------------------------------------
# Gemini
# ---------------------------------------------------------

def _analyze_gemini(
    pages,
    model,
    detail,
):

    if not GEMINI_SDK_AVAILABLE:

        raise RuntimeError(
            "google-genai package is not installed."
        )

    api_key = _secret(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(
        api_key=api_key
    )

    contents = [
        PROMPT
    ]

    for page in pages:

        contents.append(
            types.Part.from_bytes(
                data=_image_bytes(
                    page["image"]
                ),
                mime_type="image/png",
            )
        )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=SCHEMA,
        ),
    )

    return _parse_json(
        response.text
    )


# ---------------------------------------------------------
# OpenAI-compatible multimodal provider
# ---------------------------------------------------------

def _analyze_openai_compatible(
    api_key,
    base_url,
    model,
    pages,
):

    if not api_key:

        raise RuntimeError(
            "API key is not configured."
        )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    content = [
        {
            "type": "text",
            "text": PROMPT,
        }
    ]

    for page in pages:

        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": _data_url(
                        page["image"]
                    )
                },
            }
        )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        temperature=0,
        response_format={
            "type": "json_object"
        },
    )

    text = response.choices[0].message.content

    return _parse_json(text)


# ---------------------------------------------------------
# OpenRouter
# ---------------------------------------------------------

def _analyze_openrouter(
    pages,
    model,
    detail,
):

    return _analyze_openai_compatible(
        api_key=_secret(
            "OPENROUTER_API_KEY"
        ),
        base_url="https://openrouter.ai/api/v1",
        model=model,
        pages=pages,
    )


# ---------------------------------------------------------
# Groq
# ---------------------------------------------------------

def _analyze_groq(
    pages,
    model,
    detail,
):

    return _analyze_openai_compatible(
        api_key=_secret(
            "GROQ_API_KEY"
        ),
        base_url="https://api.groq.com/openai/v1",
        model=model,
        pages=pages,
    )


# ---------------------------------------------------------
# Ollama
# ---------------------------------------------------------

def _analyze_ollama(
    pages,
    model,
    detail,
):

    if not _bool_value(
        _secret(
            "OLLAMA_ENABLED",
            False,
        )
    ):

        raise RuntimeError(
            "Ollama is disabled."
        )

    return _analyze_openai_compatible(
        api_key="ollama",
        base_url=_secret(
            "OLLAMA_BASE_URL",
            "http://localhost:11434/v1",
        ),
        model=model,
        pages=pages,
    )


# ---------------------------------------------------------
# OpenAI
# ---------------------------------------------------------

def _analyze_openai(
    pages,
    model,
    detail,
):

    return _analyze_openai_compatible(
        api_key=_secret(
            "OPENAI_API_KEY"
        ),
        base_url="https://api.openai.com/v1",
        model=model,
        pages=pages,
    )


# ---------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------

def _provider_models():

    return {
        "gemini": _secret(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        ),
        "openrouter": _secret(
            "OPENROUTER_MODEL",
            "openrouter/free",
        ),
        "groq": _secret(
            "GROQ_MODEL",
            "qwen/qwen3.6-27b",
        ),
        "ollama": _secret(
            "OLLAMA_MODEL",
            "gemma3:12b",
        ),
        "openai": _secret(
            "OPENAI_MODEL",
            "gpt-5.6-luna",
        ),
    }


def _fallback_order():

    value = _secret(
        "AI_FALLBACK_ORDER",
        "gemini,openrouter,groq,ollama,openai",
    )

    return [
        x.strip().lower()
        for x in str(value).split(",")
        if x.strip()
    ]


# ---------------------------------------------------------
# Main analysis
# ---------------------------------------------------------

def analyze_route(
    pages,
    model=None,
    detail="high",
    provider="auto",
    fallback=True,
):

    if not pages:

        raise RuntimeError(
            "No reaction-route pages supplied."
        )

    provider = (
        provider or "auto"
    ).lower().strip()

    models = _provider_models()

    if provider == "auto":

        providers = _fallback_order()

    else:

        providers = [
            provider
        ]

    # If a manually selected provider has a model
    # supplied by the Streamlit UI, use it.
    if provider != "auto" and model:

        models[provider] = model

    errors = []

    for provider_name in providers:

        if provider_name not in models:

            continue

        selected_model = models[
            provider_name
        ]

        # -------------------------------------------------
        # Check provider availability
        # -------------------------------------------------

        status = provider_status().get(
            provider_name,
            {},
        )

        if not status.get(
            "available",
            False,
        ):

            errors.append(
                f"{provider_name}: not configured"
            )

            continue

        # -------------------------------------------------
        # Retry provider
        # -------------------------------------------------

        for attempt in range(3):

            try:

                if provider_name == "gemini":

                    return _analyze_gemini(
                        pages,
                        selected_model,
                        detail,
                    )

                if provider_name == "openrouter":

                    return _analyze_openrouter(
                        pages,
                        selected_model,
                        detail,
                    )

                if provider_name == "groq":

                    return _analyze_groq(
                        pages,
                        selected_model,
                        detail,
                    )

                if provider_name == "ollama":

                    return _analyze_ollama(
                        pages,
                        selected_model,
                        detail,
                    )

                if provider_name == "openai":

                    return _analyze_openai(
                        pages,
                        selected_model,
                        detail,
                    )

                raise RuntimeError(
                    f"Unknown provider: {provider_name}"
                )

            except Exception as exc:

                errors.append(
                    f"{provider_name} "
                    f"({selected_model}) "
                    f"attempt {attempt + 1}: "
                    f"{exc}"
                )

                if not _is_retryable_error(
                    exc
                ):

                    break

                if attempt < 2:

                    time.sleep(
                        _retry_delay(attempt)
                    )

        # -------------------------------------------------
        # Fallback
        # -------------------------------------------------

        if not fallback:

            break

    raise RuntimeError(
        "All configured AI providers failed.\n\n"
        + "\n".join(
            errors
        )
    )
