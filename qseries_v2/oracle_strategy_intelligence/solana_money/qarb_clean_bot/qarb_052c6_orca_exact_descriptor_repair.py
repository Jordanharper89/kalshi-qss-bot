from __future__ import annotations
import json
from pathlib import Path

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052c6_orca_exact_descriptor_repair.json")

def jload(p):
    try:return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:return None
def rows(o):
    if isinstance(o,list):return o
    if isinstance(o,dict):
        for k in ("rows","records","items"):
            if isinstance(o.get(k),list):return o[k]
    return []

def source(root):
    root=Path(root)
    exact=[]
    for p in (root/"runtime_state").rglob("*.json"):
        o=jload(p)
        if isinstance(o,dict) and str(o.get("revision") or "").upper()=="USLS_083B":
            exact.extend(rows(o))
    return exact

def build(root):
    out=[]
    for r in source(root):
        pool=r.get("pool");ta=r.get("input_mint");tb=r.get("output_mint")
        va=r.get("vault_a");vb=r.get("vault_b")
        if all(isinstance(x,str) and x for x in (pool,ta,tb,va,vb)):
            out.append({"pool":pool,"token_a":ta,"token_b":tb,"vault_a":va,"vault_b":vb,
                        "signature":r.get("signature"),"direction":r.get("direction"),
                        "decoder_state":r.get("decoder_state"),"execution_authority":False})
    uniq={r["pool"]:r for r in out}
    return list(uniq.values())

def main():
    root=Path.cwd();d=build(root)
    payload={"revision":"QARB_052C6","descriptor_count":len(d),"descriptors":d,
             "hot_provider_bound":False,
             "next_boundary":"ORCA_WHIRLPOOL_LIVE_STATE_PLUS_LOCAL_QUOTE_PROVIDER",
             "execution_authority":False}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[QARB-052C6] ORCA EXACT DESCRIPTOR REPAIR")
    print("[ORCA_DESCRIPTORS]",len(d))
    for r in d: print("[ORCA_DESCRIPTOR]",r["pool"][:12],r["token_a"][:12],r["token_b"][:12],r["vault_a"][:12],r["vault_b"][:12])
    if d: print("[PASS] USLS-083B exact vault/mint economics repaired Orca descriptor pavement")
    else: print("[HOLD] USLS-083B artifact unavailable or empty")
    print("[HOT_PROVIDER_BOUND]",False)
    print("[NEXT]",payload["next_boundary"])
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
