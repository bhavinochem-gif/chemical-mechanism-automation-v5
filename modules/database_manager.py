from pathlib import Path
import json

class ChemistryDatabase:
    def __init__(self, data_dir="data"):
        self.datasets={}
        for p in sorted(Path(data_dir).glob("*.json")):
            try:self.datasets[p.stem]=json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:self.datasets[p.stem]={"_error":str(e)}
    def get(self,name,default=None): return self.datasets.get(name,default if default is not None else [])
    def records(self,name):
        d=self.get(name,[])
        if isinstance(d,list): return d
        out=[]
        if isinstance(d,dict):
            for k,v in d.items():
                if isinstance(v,dict): x=dict(v); x.setdefault("name",k); out.append(x)
                elif isinstance(v,list): out += [x for x in v if isinstance(x,dict)]
        return out
    def match(self,name,text):
        t=(text or "").lower(); hits=[]
        for r in self.records(name):
            vals=[]
            for k,v in r.items():
                if k.startswith("_"): continue
                vals += [str(x).lower() for x in v] if isinstance(v,list) else [str(v).lower()]
            score=sum(1 for x in vals if x and len(x)>2 and x in t)
            if score: q=dict(r); q["_score"]=score; hits.append(q)
        return sorted(hits,key=lambda x:x["_score"],reverse=True)
    def summary(self): return {k:len(self.records(k)) for k in self.datasets}
    def compact_context(self):
        names=["reaction_classes","mechanism_rules","reagents","catalysts","functional_group_transformations","named_reactions","stereochemistry_rules","impurity_formation_rules"]
        return "\n".join(f"{n}: {json.dumps(self.get(n,[]),ensure_ascii=False)[:900]}" for n in names)
