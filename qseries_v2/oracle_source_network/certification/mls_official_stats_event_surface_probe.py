
import json,re,urllib.request
BASE="https://stats-api.mlssoccer.com"
SEASONS_URI=BASE+"/competitions/MLS-COM-000001/seasons"

def _get(uri,timeout=8.0):
    req=urllib.request.Request(uri,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
    return raw,json.loads(raw.decode("utf-8"))

def _walk(obj,path="$",depth=0):
    if depth>8:return
    if isinstance(obj,dict):
        yield path,obj
        for k,v in obj.items(): yield from _walk(v,f"{path}.{k}",depth+1)
    elif isinstance(obj,list):
        for i,v in enumerate(obj[:80]): yield from _walk(v,f"{path}[{i}]",depth+1)

def discover_2026_season(root):
    candidates=[]
    for path,d in _walk(root):
        text=json.dumps(d,ensure_ascii=False)[:2000]
        if "2026" not in text: continue
        for k,v in d.items():
            if isinstance(v,str) and ("SEA" in v.upper() or "season" in k.lower()):
                candidates.append((path,k,v))
    # Current 2026 MLS season id observed in public MLS API consumers.
    for _,_,v in candidates:
        if v=="MLS-SEA-0001KA": return v
    for _,_,v in candidates:
        if isinstance(v,str) and v.startswith("MLS-SEA-"): return v
    return None

def probe_surface(timeout=8.0):
    sraw,sroot=_get(SEASONS_URI,timeout)
    sid=discover_2026_season(sroot)
    if not sid: return {"season_bytes":len(sraw),"season_id":None,"matches_uri":None,"match_bytes":0,"sample_paths":[]}
    muri=BASE+f"/matches/seasons/{sid}"
    mraw,mroot=_get(muri,timeout)
    rows=[]
    for path,d in _walk(mroot):
        keys=tuple(str(k) for k in d.keys())
        low=" ".join(k.lower() for k in keys)
        if any(x in low for x in ("match","home","away","date","score","status","club")):
            scalars=tuple(f"{k}={repr(v)[:100]}" for k,v in d.items() if isinstance(v,(str,int,float,bool)) or v is None)[:25]
            rows.append((path,keys[:40],scalars))
        if len(rows)>=12: break
    return {"season_bytes":len(sraw),"season_id":sid,"matches_uri":muri,"match_bytes":len(mraw),"sample_paths":rows}
