TEMPLATES = {
    'substitution': [
        ('Nucleophile approach', 'The nucleophile approaches the electrophilic center while the leaving-group bond is polarized.', 'Nu: → C; C–LG → LG'),
        ('Leaving-group departure', 'Bond cleavage gives the substituted product and the leaving group.', 'C–LG → LG⁻/LG'),
        ('Product formation', 'The new sigma bond is established; proton transfer may occur depending on the medium.', 'Nu–C bond formation')],
    'elimination': [
        ('Base activation', 'A base removes a beta hydrogen anti/periplanar to the leaving group where geometrically possible.', 'Base: → H; C–H → C=C'),
        ('Leaving-group departure', 'The leaving group departs as the pi bond forms.', 'C–LG → LG'),
        ('Alkene formation', 'The alkene product is formed, with regioselectivity governed by substrate and conditions.', 'C–C → C=C')],
    'reduction': [
        ('Hydride/proton delivery', 'A reducing reagent delivers hydride, hydrogen or an equivalent reducing species to the electrophilic center.', 'Reducing species → electrophilic carbon'),
        ('Intermediate protonation', 'The resulting anion/metal-bound intermediate is protonated or otherwise quenched.', 'Intermediate → product')],
    'oxidation': [
        ('Activation', 'The substrate is activated by the oxidant or catalytic cycle.', 'Substrate → activated intermediate'),
        ('Oxidation event', 'A net oxidation changes the oxidation state or introduces additional unsaturation/heteroatom bonding.', 'Electron transfer/atom transfer'),
        ('Product release', 'The oxidized product is released and the reagent-derived species is regenerated or quenched.', 'Product formation')]
}

def _family(step):
    text=(step.get('reaction_class','')+' '+step.get('transformation','')).lower()
    for k in TEMPLATES:
        if k in text: return k
    if any(x in text for x in ['substitut','sn1','sn2','alkylation']): return 'substitution'
    if any(x in text for x in ['elimin','dehydro']): return 'elimination'
    if any(x in text for x in ['reduction','hydrogenation','hydrogenolysis']): return 'reduction'
    if any(x in text for x in ['oxidation','oxidative']): return 'oxidation'
    return None

def build_mechanism(step):
    named=step.get('named_reactions', [])
    family=_family(step)
    if named: overview=f"Proposed mechanism consistent with {named[0]['name']} ({named[0]['score']:.0%} database score)."
    else: overview='Proposed mechanism based on the extracted reaction family and conditions; not an experimentally verified atom-mapped mechanism.'
    events=[]
    for title,desc,flow in TEMPLATES.get(family, [
        ('Reaction-center activation','Identify the electrophile, nucleophile, leaving group or redox partner implied by the transformation.','Use validated atom mapping before assigning exact arrows.'),
        ('Bond reorganization','The proposed pathway proceeds through the minimum chemically reasonable bond-making/bond-breaking sequence.','Exact curved-arrow placement requires verified atom mapping.'),
        ('Work-up/product formation','Proton transfers, salt formation and work-up steps are applied as appropriate.','Quench/proton-transfer events depend on conditions.')
    ]): events.append({'title':title,'description':desc,'electron_flow':flow})
    return {'overview':overview, 'events':events, 'status':'PROPOSED'}

