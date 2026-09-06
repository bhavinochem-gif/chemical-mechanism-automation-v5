import os,json,re,base64
SCHEMA={"type":"object","properties":{"steps":{"type":"array","items":{"type":"object","properties":{k:{"type":"string"} for k in ["starting_material","reagents","solvent","temperature","time","product","yield","reaction","notes"]}|{"step":{"type":"integer"}},"required":["step","starting_material","reagents","solvent","temperature","time","product","yield","reaction","notes"]}},"warnings":{"type":"array","items":{"type":"string"}}},"required":["steps","warnings"]}
def sec(k,d=""):
    try:
        import streamlit as st
        return st.secrets.get(k,os.getenv(k,d))
    except:return os.getenv(k,d)
def clean(x):
    if isinstance(x,dict):return x
    x=re.sub(r"^```json|```$","",x.strip(),flags=re.I).strip(); a=x.find("{"); b=x.rfind("}")
    return json.loads(x[a:b+1] if a>=0 and b>a else x)
def prompt(text,ctx):
    return f"""Extract every synthesis step from this chemistry route. Never invent unreadable information; use 'Not legible'. Return ONLY JSON matching the requested schema.\nDOCUMENT:\n{text[:18000]}\nKNOWLEDGE BASE:\n{ctx[:7000]}"""
def gemini(p,imgs,model):
    from google import genai
    from google.genai import types
    c=genai.Client(api_key=sec("GEMINI_API_KEY")); parts=[p]
    for im in imgs[:8]: parts.append(types.Part.from_bytes(data=base64.b64decode(im["data"]),mime_type=im["mime_type"]))
    x=c.interactions.create(model=model,input=parts,response_format={"type":"text","mime_type":"application/json","schema":SCHEMA})
    o=getattr(x,"output",None); s="".join(getattr(z,"text",str(z)) for z in o) if isinstance(o,list) else (getattr(o,"text",None) or str(o))
    return clean(s)
def compat(url,key,model,p,imgs):
    from openai import OpenAI
    c=OpenAI(api_key=key,base_url=url); content=[{"type":"text","text":p}]
    for im in imgs[:8]:content.append({"type":"image_url","image_url":{"url":f"data:{im['mime_type']};base64,{im['data']}"}})
    r=c.chat.completions.create(model=model,messages=[{"role":"user","content":content}],temperature=.1,response_format={"type":"json_object"})
    return clean(r.choices[0].message.content)
def analyze_route(text,images,provider="auto",database_context=""):
    order=[provider] if provider!="auto" else [x.strip() for x in sec("AI_FALLBACK_ORDER","gemini,openrouter,groq,ollama,openai").split(",")]
    p=prompt(text,database_context); errors=[]
    for x in order:
        try:
            if x=="gemini":return gemini(p,images,sec("GEMINI_MODEL","gemini-3.6-flash"))
            if x=="openrouter":return compat("https://openrouter.ai/api/v1",sec("OPENROUTER_API_KEY"),sec("OPENROUTER_MODEL","openrouter/free"),p,images)
            if x=="groq":return compat("https://api.groq.com/openai/v1",sec("GROQ_API_KEY"),sec("GROQ_MODEL","qwen/qwen3.6-27b"),p,images)
            if x=="ollama" and sec("OLLAMA_ENABLED","false").lower()=="true":return compat(sec("OLLAMA_BASE_URL","http://localhost:11434/v1"),"ollama",sec("OLLAMA_MODEL","gemma3:12b"),p,images)
            if x=="openai":return compat("https://api.openai.com/v1",sec("OPENAI_API_KEY"),sec("OPENAI_MODEL","gpt-5.6-luna"),p,images)
        except Exception as e:errors.append(f"{x}: {e}")
    raise RuntimeError("All providers failed: "+" | ".join(errors))
