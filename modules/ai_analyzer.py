import base64
import io
import json
import os

from openai import OpenAI

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "route_title": {"type": "string"},
        "route_summary": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "step_number": {"type": "integer"},
                    "transformation": {"type": "string"},
                    "reactants_smiles": {"type": "array", "items": {"type": "string"}},
                    "products_smiles": {"type": "array", "items": {"type": "string"}},
                    "reagents": {"type": "array", "items": {"type": "string"}},
                    "solvent": {"type": "string"},
                    "temperature": {"type": "string"},
                    "time": {"type": "string"},
                    "pressure": {"type": "string"},
                    "yield": {"type": "string"},
                    "reaction_class": {"type": "string"},
                    "conditions_text": {"type": "string"},
                    "stereochemical_changes": {"type": "string"},
                    "confidence": {"type": "string"},
                    "uncertainty": {"type": "string"},
                },
                "required": [
                    "step_number", "transformation", "reactants_smiles", "products_smiles", "reagents",
                    "solvent", "temperature", "time", "pressure", "yield", "reaction_class",
                    "conditions_text", "stereochemical_changes", "confidence", "uncertainty"
                ],
            },
        },
    },
    "required": ["route_title", "route_summary", "steps"],
}


def _data_url(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def analyze_route(pages, model=None, detail="high", api_key=None):
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    client = OpenAI(api_key=key)

    prompt = """
You are a senior organic/process chemist analyzing a synthetic route image.
Extract every reaction step in order. Separate substrates from reagents/solvents.
Provide isomeric SMILES only when the drawn structure can be interpreted with reasonable confidence.
If a structure is unreadable or ambiguous, return an empty SMILES array and explain the uncertainty.
Preserve stereochemistry, salts and counterions where visible. Do not invent missing atoms or bonds.
Describe the observed net transformation separately from mechanistic inference. Identify a reaction family,
but do not force a named reaction when evidence is weak. Return only the requested JSON schema.
"""

    content = [{"type": "input_text", "text": prompt}]
    for page in pages:
        content.append({
            "type": "input_image",
            "image_url": _data_url(page["image"]),
            "detail": detail,
        })

    response = client.responses.create(
        model=selected_model,
        input=[{"role": "user", "content": content}],
        text={
            "format": {
                "type": "json_schema",
                "name": "route_analysis",
                "strict": True,
                "schema": SCHEMA,
            }
        },
    )

    text = getattr(response, "output_text", None)
    if not text:
        raise RuntimeError("OpenAI returned no output_text.")
    return json.loads(text)
