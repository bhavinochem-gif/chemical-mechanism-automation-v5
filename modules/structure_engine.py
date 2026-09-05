from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

def describe_smiles(smiles):
    if not smiles: return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None: return {"smiles": smiles, "valid": False}
    Chem.AssignStereochemistry(mol, cleanIt=True, force=True)
    return {
        "smiles": smiles, "valid": True,
        "canonical_smiles": Chem.MolToSmiles(mol, isomericSmiles=True),
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "mw": round(Descriptors.MolWt(mol), 4),
        "formal_charge": Chem.GetFormalCharge(mol),
        "heavy_atoms": mol.GetNumHeavyAtoms(),
        "stereocenters": len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))
    }

def enrich_step(step):
    step['reactant_details'] = [describe_smiles(s) for s in step.get('reactants_smiles', [])]
    step['product_details'] = [describe_smiles(s) for s in step.get('products_smiles', [])]
    step['invalid_smiles'] = [d['smiles'] for d in step['reactant_details'] + step['product_details'] if d and not d['valid']]
    step['atom_mapping_note'] = 'V5 uses structure identity and graph comparison only; exact atom mapping requires a dedicated mapper or manually verified mapping.'
    return step

