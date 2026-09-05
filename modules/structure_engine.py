"""RDKit structure utilities. Drawing is intentionally lazy-loaded."""
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

def describe_smiles(smiles):
    if not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
    except Exception as exc:
        return {'smiles': smiles, 'valid': False, 'error': str(exc)}
    if mol is None:
        return {'smiles': smiles, 'valid': False}
    try:
        Chem.AssignStereochemistry(mol, cleanIt=True, force=True)
        return {
            'smiles': smiles,
            'valid': True,
            'canonical_smiles': Chem.MolToSmiles(mol, isomericSmiles=True),
            'formula': rdMolDescriptors.CalcMolFormula(mol),
            'mw': round(Descriptors.MolWt(mol), 4),
            'formal_charge': Chem.GetFormalCharge(mol),
            'heavy_atoms': mol.GetNumHeavyAtoms(),
            'stereocenters': len(Chem.FindMolChiralCenters(mol, includeUnassigned=True)),
        }
    except Exception as exc:
        return {'smiles': smiles, 'valid': False, 'error': str(exc)}

def enrich_step(step):
    reactants = step.get('reactants_smiles', []) or []
    products = step.get('products_smiles', []) or []
    step['reactant_details'] = [describe_smiles(s) for s in reactants]
    step['product_details'] = [describe_smiles(s) for s in products]
    step['invalid_smiles'] = [
        d['smiles'] for d in step['reactant_details'] + step['product_details']
        if d and not d.get('valid', False)
    ]
    step['atom_mapping_note'] = 'Exact atom mapping is not claimed in V5.2. Reaction-center and electron-flow statements are proposals unless independently verified.'
    return step
