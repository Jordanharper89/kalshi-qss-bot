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

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import meteora_damm_v2_live as live

OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052a5_damm_source_certified_bridge.json")

def account_value(x):
    if isinstance(x,str):return x
    if isinstance(x,dict):
        return sval(x,"pubkey","address","account","key")
def role_accounts(r):
    a=r.get("accounts")
    if isinstance(a,list):return [account_value(x) for x in a if account_value(x)]
    if isinstance(a,dict):return {k:account_value(v) for k,v in a.items() if account_value(v)}
    return a

def extract_role_descriptor(r):
    venue=str(r.get("venue") or r.get("family") or "").upper()
    if venue not in ("METEORA_DAMM","METEORA_DAMM_V2"): return None
    pool=sval(r,"pool","pool_id","pool_address")
    ta=sval(r,"token_a","mint_a","token_0","base_mint","input_mint")
    tb=sval(r,"token_b","mint_b","token_1","quote_mint","output_mint")
    va=sval(r,"vault_a","token_vault_a","vault_0","base_vault","input_vault")
    vb=sval(r,"vault_b","token_vault_b","vault_1","quote_vault","output_vault")
    roles=r.get("roles") or r.get("account_roles")
    if isinstance(roles,dict):
        pool=pool or sval(roles,"pool","pool_account")
        va=va or sval(roles,"vault_a","token_a_vault","source_vault","base_vault")
        vb=vb or sval(roles,"vault_b","token_b_vault","destination_vault","quote_vault")
        ta=ta or sval(roles,"token_a","mint_a","base_mint")
        tb=tb or sval(roles,"token_b","mint_b","quote_mint")
    return {"pool":pool,"token_a":ta,"token_b":tb,"vault_a":va,"vault_b":vb,
            "signature":sval(r,"signature"),"instruction_name":sval(r,"instruction_name")}

def build(root):
    root=Path(root);roles=[]
    for p,o in find_revision(root,"USLS_071"):
        roles += rows_of(o)
    econ=[]
    for p,o in find_revision(root,"USLS_072"):
        econ += rows_of(o)
    by_sig={}
    for r in econ:
        if str(r.get("venue") or "").upper() not in ("METEORA_DAMM","METEORA_DAMM_V2"):continue
        sig=sval(r,"signature")
        e=r.get("economics") if isinstance(r.get("economics"),dict) else r
        if sig: by_sig[sig]=(sval(e,"input_mint"),sval(e,"output_mint"),sval(r,"pool","pool_id"))
    descs=[]
    for r in roles:
        d=extract_role_descriptor(r)
        if not d:continue
        if d["signature"] in by_sig:
            im,om,pool=by_sig[d["signature"]]
            d["pool"]=d["pool"] or pool
            d["token_a"]=d["token_a"] or im
            d["token_b"]=d["token_b"] or om
        if all(d.get(k) for k in ("pool","token_a","token_b","vault_a","vault_b")):
            descs.append(d)
    uniq={d["pool"]:d for d in descs}
    hydrated=[];fail=[]
    for d in uniq.values():
        try:
            lp=live.LivePool(d["pool"],d["token_a"],d["token_b"],d["vault_a"],d["vault_b"],25,10000)
            live.hydrate(lp,c.account);hydrated.append(d)
        except Exception as e:fail.append({"pool":d["pool"],"error":type(e).__name__+":"+str(e)})
    payload={"revision":"QARB_052A5","role_rows":len(roles),"economic_rows":len(econ),
             "descriptor_count":len(uniq),"hydrated_count":len(hydrated),
             "descriptors":list(uniq.values()),"hydrated":hydrated,"failures":fail[:20],
             "execution_authority":False}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-052A5] DAMM SOURCE-CERTIFIED ROLE/ECONOMICS BRIDGE")
    print("[USLS071_ROLE_ROWS]",p["role_rows"]);print("[USLS072_ECONOMIC_ROWS]",p["economic_rows"])
    print("[DAMM_DESCRIPTORS]",p["descriptor_count"]);print("[DAMM_HYDRATED]",p["hydrated_count"])
    for d in p["hydrated"]:print("[DAMM_READY]",d["pool"][:12],d["token_a"][:12],d["token_b"][:12])
    if not p["hydrated_count"]:print("[HOLD] source-certified role rows still lack a complete live descriptor shape")
    print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
