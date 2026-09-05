# Chemical Mechanism Automation V5

A Streamlit application for AI-assisted analysis of multistep organic/API synthesis routes from PDF or image files.

## V5 workflow

```text
Upload PDF/Image
      ↓
PDF page rendering
      ↓
Vision AI structure/reagent extraction
      ↓
SMILES validation + formula/MW/stereochemistry
      ↓
Reaction family + named-reaction candidate scoring
      ↓
Reaction-center / atom-mapping caveat
      ↓
Proposed mechanistic event sequence
      ↓
RDKit structure rendering + mechanism scheme
      ↓
Multistep structure cascade
      ↓
Professional PDF report + JSON
```

## Repository flow

```text
app.py
 ├── modules/pdf_processor.py
 ├── modules/ai_analyzer.py
 ├── modules/structure_engine.py
 ├── modules/reaction_database.py
 │    └── data/named_reactions.json
 ├── modules/mechanism_engine.py
 ├── modules/mechanism_renderer.py
 ├── modules/cascade_renderer.py
 └── modules/report_generator.py
```

## GitHub copy/paste setup

1. Create a new GitHub repository, for example `chemical-mechanism-automation-v5`.
2. Create the folders `modules`, `data`, `outputs`, and `temp`.
3. Copy each file from this repository into the same path in GitHub.
4. Add your secret as `OPENAI_API_KEY` in your deployment platform; never commit `.env`.
5. For Streamlit Cloud, deploy the repository and set the main file to `app.py`.
6. Install dependencies from `requirements.txt`.

## Local Windows test

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and add OPENAI_API_KEY
streamlit run app.py
```

## Important scientific limitation

V5 is an **AI-assisted proposed-mechanism system**. It does not claim that every extracted structure, atom mapping, reaction name, intermediate, or curved arrow is experimentally verified. Exact atom mapping and mechanistic arrows should be reviewed by a chemist before inclusion in GMP/regulatory documentation.

The named-reaction database is intentionally extensible rather than claiming to contain every named reaction ever published. Add entries to `data/named_reactions.json` without changing the core application.

## OpenAI API note

The application uses the Responses API with image inputs and structured JSON output. The current OpenAI documentation supports image input and Structured Outputs through the Responses API. See the official documentation for current model/API details.
