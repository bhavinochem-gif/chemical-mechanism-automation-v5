from typing import Any, Dict

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    RDKIT_AVAILABLE = True
except Exception:
    Chem = None
    Descriptors = None
    RDKIT_AVAILABLE = False


def validate_smiles(
    smiles: str,
):

    if not RDKIT_AVAILABLE:
        return {
            "valid": False,
            "error":
                "RDKit unavailable.",
        }

    if not smiles:
        return {
            "valid": False,
            "error":
                "Empty SMILES.",
        }

    try:

        mol = Chem.MolFromSmiles(
            smiles
        )

        if mol is None:
            return {
                "valid": False,
                "error":
                    "Invalid SMILES.",
            }

        formula = ""

        try:

            from rdkit.Chem import rdMolDescriptors

            formula = (
                rdMolDescriptors
                .CalcMolFormula(mol)
            )

        except Exception:
            pass

        return {
            "valid": True,
            "canonical_smiles":
                Chem.MolToSmiles(
                    mol,
                    isomericSmiles=True,
                ),
            "formula":
                formula,
            "molecular_weight":
                round(
                    Descriptors.MolWt(
                        mol
                    ),
                    4,
                ),
            "heavy_atoms":
                mol.GetNumHeavyAtoms(),
        }

    except Exception as e:

        return {
            "valid": False,
            "error": str(e),
        }


def enrich_structures(
    analysis: Dict[str, Any],
):

    for step in analysis.get(
        "steps",
        [],
    ):

        reactant_info = []

        for smiles in step.get(
            "reactant_smiles",
            [],
        ):

            info = validate_smiles(
                smiles
            )

            info["input_smiles"] = smiles

            reactant_info.append(
                info
            )

        product_info = []

        for smiles in step.get(
            "product_smiles",
            [],
        ):

            info = validate_smiles(
                smiles
            )

            info["input_smiles"] = smiles

            product_info.append(
                info
            )

        step[
            "validated_reactants"
        ] = reactant_info

        step[
            "validated_products"
        ] = product_info

    return analysis
