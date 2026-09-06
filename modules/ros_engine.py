FIELDS=["step","starting_material","reagents","solvent","temperature","time","product","yield","reaction","notes"]
def normalize_ros(rows):
    out=[]
    for i,r in enumerate(rows or [],1):
        if not isinstance(r,dict): continue
        x={k:str(r.get(k,"") or "").strip() for k in FIELDS}
        try:x["step"]=int(r.get("step") or i)
        except:x["step"]=i
        out.append(x)
    return out
def fallback_ros_from_document(text,page_count=1):
    return [{"step":i,"starting_material":"Not extracted — review route image","reagents":"Not extracted","solvent":"Not extracted","temperature":"Not extracted","time":"Not extracted","product":"Not extracted — review route image","yield":"Not extracted","reaction":"Document page / scheme requires review","notes":"Fallback row created because structured extraction was unavailable."} for i in range(1,max(1,page_count)+1)]
def validate_ros(rows):
    e=[]
    if not rows:return ["No route steps present."]
    for i,r in enumerate(rows,1):
        if not any(str(r.get(k,"")).strip() for k in ["starting_material","product","reaction"]):e.append(f"Row {i}: no transformation information.")
    return e
