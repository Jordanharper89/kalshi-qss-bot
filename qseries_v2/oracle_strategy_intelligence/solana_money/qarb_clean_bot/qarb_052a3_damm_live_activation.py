from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import meteora_damm_v2_live as live

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052a3_damm_live_activation.json")

ALIASES={
 "pool":("pool","pool_id","pool_address","amm_config_pool"),
 "token_a":("token_a","mint_a","token_0","mint_0","base_mint"),
 "token_b":("token_b","mint_b","token_1","mint_1","quote_mint"),
 "vault_a":("vault_a","token_vault_a","vault_0","base_vault"),
 "vault_b":("vault_b","token_vault_b","vault_1","quote_vault"),
}
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
def pick(d,n):
    for k in ALIASES[n]:
        v=d.get(k)
        if isinstance(v,str) and v:return v
    a=d.get("accounts")
    if isinstance(a,dict):
        for k in ALIASES[n]:
            v=a.get(k)
            if isinstance(v,str) and v:return v
def discover(root):
    found={}
    for p in (Path(root)/"runtime_state").rglob("*.json"):
        try:o=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        for d in walk(o):
            venue=str(d.get("venue") or d.get("venue_name") or d.get("family") or "").upper()
            if venue not in ("METEORA_DAMM","METEORA_DAMM_V2","DAMM","DAMM_V2"):continue
            vals={k:pick(d,k) for k in ALIASES}
            if all(vals.values()):
                try:
                    desc=live.LivePool(vals["pool"],vals["token_a"],vals["token_b"],vals["vault_a"],vals["vault_b"],
                                       int(d.get("fee_numerator") or 25),int(d.get("fee_denominator") or 10000))
                    found[vals["pool"]]=desc
                except Exception:pass
    return list(found.values())
def activate(root):
    desc=discover(root); ok=[];fail=[]
    for d in desc:
        try:
            s=live.hydrate(d,c.account)
            ok.append((d,s))
        except Exception as e: fail.append((d.pool,type(e).__name__+":"+str(e)))
    payload={"descriptors":len(desc),"hydrated":len(ok),"failures":fail[:20],
             "pools":[d.pool for d,_ in ok],"execution_authority":False}
    p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return payload
def main():
    p=activate(Path.cwd())
    print("[QARB-052A3] METEORA DAMM LIVE ACTIVATION")
    print("[DAMM_DESCRIPTORS]",p["descriptors"])
    print("[DAMM_HYDRATED]",p["hydrated"])
    if p["hydrated"]==0: print("[HOLD] no exact DAMM descriptor hydrated; graph remains unchanged")
    else: print("[PASS] existing DAMM hydrate/update/quote pavement physically activated")
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
