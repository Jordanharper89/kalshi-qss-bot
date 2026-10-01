from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_cpmm_mriya_bridge as bridge

EXECUTION_AUTHORITY=False
READ_ONLY=True
CAPTURE=Path("runtime_state/qseries/qarb_clean_bot/mriya_dex_instruction_accounts.json")
CANON=Path("runtime_state/qseries/qarb_clean_bot/raydium_cpmm_canonical_live_descriptors.json")
UNIVERSAL=Path("runtime_state/solana_opportunities/universal_trade_tape/raydium_exact_instruction_pool_roles.json")
LEDGER=Path("runtime_state/qseries/qarb_clean_bot/mriya_cpmm_identity_ledger.json")
CPMM_PROGRAM=bridge.CPMM_PROGRAM
POOL_I=3;VA_I=6;VB_I=7;MA_I=10;MB_I=11

def _rows(x):
    if isinstance(x,list): return x
    if isinstance(x,dict):
        for k in ("rows","records","instructions","descriptors"):
            if isinstance(x.get(k),list): return x[k]
    return []

def _load(p):
    p=Path(p)
    if not p.is_file(): return []
    try:return _rows(json.loads(p.read_text(encoding="utf-8")))
    except Exception:return []

def _pk(x):
    if isinstance(x,str):return x
    if isinstance(x,dict):return x.get("pubkey") or x.get("address") or x.get("key")
    return None

def _descriptor_from_row(r):
    # Already-normalized descriptor
    if all(r.get(k) for k in ("pool","token_a","token_b","vault_a","vault_b")):
        return {"venue":"RAYDIUM_CPMM","pool":r["pool"],"token_a":r["token_a"],"token_b":r["token_b"],
                "vault_a":r["vault_a"],"vault_b":r["vault_b"],
                "fee_numerator":int(r.get("fee_numerator") or 25),
                "fee_denominator":int(r.get("fee_denominator") or 10000),
                "source_signature":r.get("source_signature") or r.get("signature"),
                "source_slot":r.get("slot"),"execution_authority":False}
    venue=str(r.get("venue") or "").upper()
    pid=str(r.get("program_id") or "")
    if venue!="RAYDIUM_CPMM" and pid!=CPMM_PROGRAM:return None
    a=[_pk(x) for x in (r.get("accounts") or [])]
    if len(a)<=MB_I:return None
    pool,va,vb,ma,mb=a[POOL_I],a[VA_I],a[VB_I],a[MA_I],a[MB_I]
    if not all((pool,va,vb,ma,mb)):return None
    if len({pool,va,vb,ma,mb})<5:return None
    return {"venue":"RAYDIUM_CPMM","pool":pool,"token_a":ma,"token_b":mb,
            "vault_a":va,"vault_b":vb,"fee_numerator":25,"fee_denominator":10000,
            "source_signature":r.get("signature"),"source_slot":r.get("slot"),
            "execution_authority":False}

def refresh(root=Path.cwd()):
    root=Path(root)
    sources=[("ledger",root/LEDGER),("canonical",root/CANON),("capture",root/CAPTURE),("universal",root/UNIVERSAL)]
    found={}
    source_counts={}
    for name,p in sources:
        n=0
        for r in _load(p):
            d=_descriptor_from_row(r)
            if not d:continue
            old=found.get(d["pool"])
            if old is None or int(d.get("source_slot") or -1)>=int(old.get("source_slot") or -1):
                found[d["pool"]]=d
            n+=1
        source_counts[name]=n
    payload={"revision":"QARB_051C","rows":sorted(found.values(),key=lambda x:x["pool"]),
             "descriptor_count":len(found),"source_counts":source_counts,
             "read_only":True,"execution_authority":False}
    p=root/LEDGER;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def discover(root=Path.cwd()):
    p=refresh(root)
    return [bridge.LivePool(r["pool"],r["token_a"],r["token_b"],r["vault_a"],r["vault_b"],
                            int(r["fee_numerator"]),int(r["fee_denominator"])) for r in p["rows"]]

def main():
    p=refresh(Path.cwd())
    print("[QARB-051C] ROLLING CPMM IDENTITY LEDGER")
    print("[SOURCE_COUNTS]",json.dumps(p["source_counts"],sort_keys=True))
    print("[DESCRIPTOR_COUNT]",p["descriptor_count"])
    for r in p["rows"]:
        print("[IDENTITY] pool=%s token_a=%s token_b=%s vault_a=%s vault_b=%s slot=%s"%(
          r["pool"][:12],r["token_a"][:12],r["token_b"][:12],r["vault_a"][:12],r["vault_b"][:12],r.get("source_slot")))
    print("[REPORT]",LEDGER)
    print("[MODE] READ_ONLY=True execution_authority=FALSE")

if __name__=="__main__":main()
