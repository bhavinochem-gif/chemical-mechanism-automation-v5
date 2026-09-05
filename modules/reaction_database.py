import json, os, re

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'named_reactions.json')

def load_database():
    with open(DB, encoding='utf-8') as f: return json.load(f)

def identify_named_reactions(step, top_n=5):
    text = ' '.join([
        step.get('transformation',''), step.get('reaction_class',''), step.get('conditions_text',''),
        ' '.join(step.get('reagents', [])), step.get('solvent','')
    ]).lower()
    results=[]
    for rxn in load_database():
        score=0.0; reasons=[]
        for term in rxn.get('aliases', []):
            if term.lower() in text: score += 0.45; reasons.append(f'alias: {term}')
        for term in rxn.get('reagent_patterns', []):
            if term.lower() in text: score += 0.18; reasons.append(f'reagent: {term}')
        for term in rxn.get('condition_patterns', []):
            if term.lower() in text: score += 0.10; reasons.append(f'condition: {term}')
        for term in rxn.get('class_patterns', []):
            if term.lower() in text: score += 0.22; reasons.append(f'class: {term}')
        if score:
            results.append({'name': rxn['name'], 'score': min(score, 1.0), 'reason': '; '.join(reasons), 'family': rxn.get('family','')})
    results.sort(key=lambda x:x['score'], reverse=True)
    return results[:top_n]

