import base64, io, json, os
from openai import OpenAI

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "route_title": {"type": "string"},
        "route_summary": {"type": "string"},
        "steps": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {
                "step_number": {"type": "integer"}, "transformation": {"type": "string"},
                "reactants_smiles": {"type": "array", "items": {"type": "string"}},
                "products_smiles": {"type": "array", "items": {"type": "string"}},
                "reagents": {"type": "array", "items": {"type": "string"}},
                "solvent": {"type": "string"}, "temperature": {"type": "string"},
                "time": {"type": "string"}, "pressure": {"type": "string"},
                "yield": {"type": "string"}, "reaction_class": {"type": "string"},
                "conditions_text": {"type": "string"}, "stereochemical_changes": {"type": "string"},
                "confidence": {"type": "string"}, "uncertainty": {"type": "string"}
            }, "required": ["step_number", "transformation", "reactants_smiles", "products_smiles", "reagents", "solvent", "temperature", "time", "pressure", "yield", "reaction_class", "conditions_text", "stereochemical_changes", "confidence", "uncertainty"]
        }}
    }, "required": ["route_title", "route_summary", "steps"]
}

def _data_url(image):
    buf = io.BytesIO(); image.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

def analyze_route(pages, model=None, detail='high'):
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('OPENAI_API_KEY is not set. Add it to Streamlit secrets or .env.')
    client = OpenAI(api_key=key)
    content = [{"type": "input_text", "text": """
You are a senior organic/process chemist. Analyze the uploaded synthesis-route page images.
Extract every synthetic step in order. Identify structures and provide valid isomeric SMILES only when
confidence is reasonable. Never invent a structure: if unreadable, return an empty SMILES array and
state uncertainty. Separate reagents from substrates/products. Preserve stereochemistry, salts and
counterions where visible. Describe the net transformation and reaction family. This output will be
used for a proposed mechanism, so distinguish observation from inference.
"""}]
    for p in pages:
        content.append({"type": "input_image", "image_url": _data_url(p['image']), "detail": detail})
    response = client.responses.create(
        model=model or os.getenv('OPENAI_MODEL', 'gpt-5.6-luna'),
        input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_schema", "name": "route_analysis", "strict": True, "schema": SCHEMA}}
    )
    return json.loads(response.output_text)
