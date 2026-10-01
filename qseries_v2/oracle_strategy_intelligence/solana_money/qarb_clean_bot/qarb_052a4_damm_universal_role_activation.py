from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import meteora_damm_v2_live as live

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052a4_damm_universal_role_activation.json")

ALIASES={
 "pool":("pool","pool_id","pool_address","amm_config_pool"),
 "token_a":("token_a","mint_a","token_0","mint_0","base_mint","input_mint"),
 "token_b":("token_b","mint_b","token_1","mint_1","quote_mint","output_mint"),
 "vault_a":("vault_a","token_vault_a","vault_0","base_vault","input_vault"),
 "vault_b":("vault_b","token_vault_b","vault_1","quote_vault","output_vault"),
}
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
def pick(d,key):
    for k in ALIASES[key]:
        v=d.get(k)
        if isinstance(v,str) and v:return v
    a=d.get("accounts")
    if isinstance(a,dict):
        for k in ALIASES[key]:
            v=a.get(k)
            if isinstance(v,str) and v:return v
    e=d.get("economics")
    if isinstance(e,dict):
        for k in ALIASES[key]:
            v=e.get(k)
            if isinstance(v,str) and v:return v
def discover(root):
    root=Path(root)
    found={};sources={}
    tape=root/"runtime_state/solana_opportunities/universal_trade_tape"
    files=list(tape.rglob("*.json")) if tape.exists() else []
    for p in files:
        try:o=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        for d in walk(o):
            venue=str(d.get("venue") or d.get("family") or d.get("venue_name") or "").upper()
            if venue not in ("METEORA_DAMM","METEORA_DAMM_V2"):continue
            vals={k:pick(d,k) for k in ALIASES}
            if not all(vals.values()):continue
            fee_n=int(d.get("fee_numerator") or 25); fee_d=int(d.get("fee_denominator") or 10000)
            try:desc=live.LivePool(vals["pool"],vals["token_a"],vals["token_b"],vals["vault_a"],vals["vault_b"],fee_n,fee_d)
            except Exception:continue
            found[vals["pool"]]=desc;sources[vals["pool"]]=str(p.relative_to(root))
    return list(found.values()),sources
def main():
    root=Path.cwd();desc,sources=discover(root);ok=[];fail=[]
    for d in desc:
        try:s=live.hydrate(d,c.account);ok.append(d.pool)
        except Exception as e:fail.append({"pool":d.pool,"error":type(e).__name__+":"+str(e)})
    payload={"descriptors":len(desc),"hydrated":len(ok),"pools":ok,"sources":sources,"failures":fail[:20],"execution_authority":False}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[QARB-052A4] DAMM UNIVERSAL ROLE ACTIVATION")
    print("[DAMM_DESCRIPTORS]",len(desc));print("[DAMM_HYDRATED]",len(ok))
    for pool in ok: print("[DAMM_READY]",pool)
    if not ok: print("[HOLD] universal tape has no fully normalized DAMM pool+mint+vault descriptor yet")
    print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
