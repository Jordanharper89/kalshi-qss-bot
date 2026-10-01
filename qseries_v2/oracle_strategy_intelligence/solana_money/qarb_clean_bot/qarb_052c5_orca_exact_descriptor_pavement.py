from __future__ import annotations
import json
from pathlib import Path

EXECUTION_AUTHORITY=False
PAPER_ONLY=True

def jload(p):
    try:return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:return None

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def rows_of(o):
    if isinstance(o,list):return o
    if isinstance(o,dict):
        for k in ("rows","records","roles","descriptors","items"):
            if isinstance(o.get(k),list):return o[k]
    return []

def find_revision(root,revision):
    out=[]
    for p in (Path(root)/"runtime_state").rglob("*.json"):
        o=jload(p)
        if isinstance(o,dict) and str(o.get("revision") or "").upper()==revision.upper():
            out.append((p,o))
    return out

def sval(d,*names):
    for n in names:
        v=d.get(n)
        if isinstance(v,str) and v:return v
    return None

OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052c5_orca_exact_descriptor_pavement.json")
def build(root):
    root=Path(root);ir=[];er=[]
    for p,o in find_revision(root,"USLS_067"): ir += rows_of(o)
    for p,o in find_revision(root,"USLS_072"): er += rows_of(o)
    ir=[r for r in ir if str(r.get("venue") or "").upper()=="ORCA"]
    er=[r for r in er if str(r.get("venue") or "").upper()=="ORCA"]
    ep={}
    for r in er:
        e=r.get("economics") if isinstance(r.get("economics"),dict) else r
        pool=sval(r,"pool","pool_id");im=sval(e,"input_mint");om=sval(e,"output_mint")
        if pool and im and om: ep.setdefault(pool,set()).update((im,om))
    desc=[]
    for r in ir:
        pool=sval(r,"pool","pool_id")
        acc=r.get("accounts") if isinstance(r.get("accounts"),list) else []
        m=sorted(ep.get(pool,set()))
        if pool and len(m)==2 and acc:
            desc.append({"pool":pool,"token_a":m[0],"token_b":m[1],"watched_accounts":acc,
                         "signature":sval(r,"signature"),"execution_authority":False})
    uniq={d["pool"]:d for d in desc}
    payload={"revision":"QARB_052C5","exact_instruction_rows":len(ir),"economic_rows":len(er),
             "descriptor_count":len(uniq),"descriptors":list(uniq.values()),
             "hot_provider_bound":False,
             "hold_reason":"LOCAL_ORCA_MATH_PROVIDER_REQUIRED; HTTP_QUOTER_NOT_ADMISSIBLE_ON_HOT_PATH",
             "execution_authority":False}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8");return payload
def main():
    p=build(Path.cwd())
    print("[QARB-052C5] ORCA EXACT DESCRIPTOR PAVEMENT")
    print("[ORCA_DESCRIPTORS]",p["descriptor_count"])
    for d in p["descriptors"]:print("[ORCA_DESCRIPTOR]",d["pool"][:12],d["token_a"][:12],d["token_b"][:12],"accounts="+str(len(d["watched_accounts"])))
    print("[HOT_PROVIDER_BOUND]",p["hot_provider_bound"])
    print("[HOLD_REASON]",p["hold_reason"])
    print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
