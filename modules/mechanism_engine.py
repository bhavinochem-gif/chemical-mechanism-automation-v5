def generate_mechanism(ros,db):
    out=[]
    for r in ros:
        t=" ".join(str(r.get(k,"")) for k in ["starting_material","reagents","solvent","temperature","product","reaction"]).lower()
        cls=db.match("reaction_classes",t); named=db.match("named_reactions",t); reag=db.match("reagents",t); cat=db.match("catalysts",t); fg=db.match("functional_group_transformations",t); st=db.match("stereochemistry_rules",t); imp=db.match("impurity_formation_rules",t); rules=db.match("mechanism_rules",t); haz=db.match("reaction_hazard_rules",t)
        c=.25+.1*sum(bool(x) for x in [cls,named,reag,cat,fg,rules]); c=min(.95,c)
        summary=cls[0].get("description","") if cls else "Structure-level confirmation is required for a unique mechanism."
        if "boc" in t and ("tfa" in t or "hcl" in t):summary="Acid-mediated Boc carbamate cleavage followed by amine salt formation."
        elif "h2" in t or "hydrogenation" in t:summary="Likely catalytic hydrogenation/reduction; exact bond changes require structure confirmation."
        out.append({"step":r.get("step"),"reaction_class":cls[0]["name"] if cls else "Unknown / review required","transformation":r.get("reaction",""),"mechanism_summary":summary,"named_reactions":[x.get("name","") for x in named[:5]],"recognized_reagents":[x.get("name","") for x in reag[:5]],"recognized_catalysts":[x.get("name","") for x in cat[:5]],"functional_groups":[x.get("name","") for x in fg[:5]],"stereochemistry":"; ".join(x.get("description","") for x in st[:3]) or "No specific rule matched.","impurity_notes":"; ".join(x.get("description","") for x in imp[:3]) or "No specific impurity rule matched.","confidence":c,"validation_warnings":(["Hazard-rule match present; perform process-specific assessment."] if haz else [])+([] if cls else ["Reaction class not confidently matched."])})
    return out
