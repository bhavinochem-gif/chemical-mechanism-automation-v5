import json, os, re

def load_database(path=None):
    path = path or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'named_reactions.json')
    with open(path, encoding='utf-8') as f: return json.load(f)

def identify_named_reactions(step, db):
    text = ' '.join([str(step.get('transformation','')), str(step.get('reaction_class','')), str(step.get('conditions_text','')), ' '.join(map(str, step.get('reagents',[]) or []))]).lower()
    results=[]
    for rxn in db:
        aliases = rxn.get('aliases', []) or []
        hits=[a for a in aliases if a.lower() in text]
        reagent_hits=[r for r in rxn.get('reagents',[]) or [] if r.lower() in text]
        score=min(100, len(hits)*45 + len(reagent_hits)*15)
        if score: results.append({'name':rxn.get('name','Unknown'),'score':score,'evidence':hits+reagent_hits,'description':rxn.get('description','')})
    return sorted(results,key=lambda x:x['score'],reverse=True)[:5]
