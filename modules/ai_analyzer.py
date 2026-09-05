"""AI provider layer. Gemini is the V5.2 default; OpenAI remains optional."""
import base64, io, json, os

SCHEMA = {
    'type': 'object', 'properties': {
        'route_title': {'type': 'string'}, 'route_summary': {'type': 'string'},
        'steps': {'type': 'array', 'items': {'type': 'object', 'properties': {
            'step_number': {'type': 'integer'}, 'transformation': {'type': 'string'},
            'reactants_smiles': {'type': 'array', 'items': {'type': 'string'}},
            'products_smiles': {'type': 'array', 'items': {'type': 'string'}},
            'reagents': {'type': 'array', 'items': {'type': 'string'}},
            'solvent': {'type': 'string'}, 'temperature': {'type': 'string'}, 'time': {'type': 'string'},
            'pressure': {'type': 'string'}, 'yield': {'type': 'string'}, 'reaction_class': {'type': 'string'},
            'conditions_text': {'type': 'string'}, 'stereochemical_changes': {'type': 'string'},
            'confidence': {'type': 'string'}, 'uncertainty': {'type': 'string'}
        }, 'required': ['step_number','transformation','reactants_smiles','products_smiles','reagents','solvent','temperature','time','pressure','yield','reaction_class','conditions_text','stereochemical_changes','confidence','uncertainty']}}
    }, 'required': ['route_title','route_summary','steps']
}

PROMPT = '''You are a senior organic/process chemist analyzing a synthetic route image. Extract every reaction step in order. Separate substrates from reagents/solvents. Provide isomeric SMILES only when the drawn structure can be interpreted with reasonable confidence. If a structure is unreadable or ambiguous, return an empty SMILES array and explain the uncertainty. Preserve stereochemistry, salts and counterions where visible. Do not invent missing atoms or bonds. Describe the observed net transformation separately from mechanistic inference. Identify a reaction family, but do not force a named reaction when evidence is weak. Return only the requested JSON schema.'''

def _data_url(image):
    buf = io.BytesIO(); image.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')

def _gemini(pages, model, api_key, detail='high'):
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError('Gemini SDK missing. Add google-genai to requirements.txt.') from exc
    client = genai.Client(api_key=api_key)
    contents = [PROMPT]
    for page in pages:
        buf = io.BytesIO(); page['image'].save(buf, format='PNG')
        contents.append(types.Part.from_bytes(data=buf.getvalue(), mime_type='image/png'))
    config = types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=12000,
        response_mime_type='application/json',
        response_schema=SCHEMA,
    )
    try:
        response = client.models.generate_content(model=model, contents=contents, config=config)
    except Exception as exc:
        msg = str(exc)
        if '429' in msg or 'quota' in msg.lower() or 'resource_exhausted' in msg.lower():
            raise RuntimeError('Gemini free-tier quota/rate limit reached. Wait and retry, or switch AI_PROVIDER to openai.') from exc
        raise RuntimeError(f'Gemini API error: {msg}') from exc
    text = getattr(response, 'text', None)
    if not text: raise RuntimeError('Gemini returned no text response.')
    try: return json.loads(text)
    except json.JSONDecodeError as exc: raise RuntimeError('Gemini returned invalid JSON.') from exc

def _openai(pages, model, api_key, detail='high'):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError('OpenAI SDK missing.') from exc
    client = OpenAI(api_key=api_key)
    content = [{'type':'input_text','text':PROMPT}]
    for page in pages:
        content.append({'type':'input_image','image_url':_data_url(page['image']),'detail':detail})
    response = client.responses.create(model=model, input=[{'role':'user','content':content}], text={'format':{'type':'json_schema','name':'route_analysis','strict':True,'schema':SCHEMA}})
    text = getattr(response, 'output_text', None)
    if not text: raise RuntimeError('OpenAI returned no output_text.')
    return json.loads(text)

def analyze_route(pages, model=None, detail='high', api_key=None, provider=None):
    selected_provider = (provider or os.getenv('AI_PROVIDER', 'gemini')).lower()
    if selected_provider == 'gemini':
        key = api_key or os.getenv('GEMINI_API_KEY')
        if not key: raise RuntimeError('GEMINI_API_KEY is not set in Streamlit Secrets.')
        return _gemini(pages, model or os.getenv('GEMINI_MODEL', 'gemini-3.7-flash'), key, detail)
    if selected_provider == 'openai':
        key = api_key or os.getenv('OPENAI_API_KEY')
        if not key: raise RuntimeError('OPENAI_API_KEY is not set in Streamlit Secrets.')
        return _openai(pages, model or os.getenv('OPENAI_MODEL', 'gpt-5.6-luna'), key, detail)
    raise RuntimeError(f'Unsupported AI_PROVIDER: {selected_provider}. Use gemini or openai.')
