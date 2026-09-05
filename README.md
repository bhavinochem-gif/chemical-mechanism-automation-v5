# Chemical Reaction Mechanism Automation V5.2

Streamlit application for AI-assisted analysis of multistep synthetic-route PDFs/images.

## V5.2 changes
- Gemini is the default AI provider.
- OpenAI remains an optional provider.
- Uses the current `google-genai` Python SDK.
- Gemini multimodal input supports route images and structured JSON output.
- RDKit drawing imports remain lazy to avoid `rdMolDraw2D` startup failures.
- PDF and JSON reports are downloadable.

Google currently documents a Gemini API free tier with free input/output tokens for eligible models, subject to published rate limits. See Google's pricing and rate-limit documentation before production use.

## Streamlit Secrets
```toml
AI_PROVIDER = "gemini"
GEMINI_API_KEY = "your_gemini_api_key"
GEMINI_MODEL = "gemini-3.7-flash"

# Optional:
OPENAI_API_KEY = "your_openai_api_key"
OPENAI_MODEL = "gpt-5.6-luna"
```

Never commit API keys to GitHub.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Scientific limitation
AI-generated structures, reaction classes, named reactions and mechanisms are proposals. Verify structures, stereochemistry, atom mapping and mechanisms independently before development, regulatory, safety or manufacturing use.
