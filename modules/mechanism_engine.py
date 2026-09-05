def build_mechanism(step):
    cls=(step.get('reaction_class') or '').lower()
    templates=[]
    if 'substitution' in cls or 'sn2' in cls or 'sn1' in cls:
        templates=[
            'Identify the electrophilic carbon and leaving group.',
            'A nucleophile approaches the electrophilic center; bond formation and leaving-group departure are proposed.',
            'Product connectivity follows replacement of the leaving group.'
        ]
    elif 'elimination' in cls or 'dehydro' in cls:
        templates=['Identify the leaving group and adjacent beta-hydrogen.','Propose base-assisted beta-hydrogen removal with leaving-group departure.','Formation of the alkene is proposed.']
    elif 'reduction' in cls:
        templates=['Identify the reducible functional group.','Hydrogen/hydride or catalyst-mediated electron/proton transfer is proposed according to the stated conditions.','The reduced product is formed after proton/electron transfer.']
    elif 'oxidation' in cls:
        templates=['Identify the oxidized functional group.','Oxidant-mediated electron transfer and bond reorganization are proposed.','The oxidized product is formed after workup.']
    else:
        templates=['Reaction center: compare reactant and product connectivity.','Proposed bond breaking/forming events should be verified against the actual structures and conditions.','The product is the net result of the proposed transformation.']
    return {'reaction_class':step.get('reaction_class',''), 'mechanism_steps':templates, 'caveat':'Mechanism is an AI-assisted proposal, not experimental proof.', 'arrow_mapping':'Exact curved-arrow atom mapping is not claimed in V5.2.'}
