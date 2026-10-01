from __future__ import annotations
import json,time
from pathlib import Path
from solders.pubkey import Pubkey
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_043_continuous_mriya_token_discovery as d

SRC=d.STATE
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_dynamic_exact_bindings.json")
PUMP_PROGRAM=Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
AMM_PROGRAM=Pubkey.from_string("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
EXECUTION_AUTHORITY=False

def canonical_pump_pool(token):
    base=Pubkey.from_string(token);quote=Pubkey.from_string(c.WSOL)
    creator,_=Pubkey.find_program_address([b"pool-authority",bytes(base)],PUMP_PROGRAM)
    pool,_=Pubkey.find_program_address([b"pool",b"\x00\x00",bytes(creator),bytes(base),bytes(quote)],AMM_PROGRAM)
    return str(pool)

def verify(token):
    pump=canonical_pump_pool(token);raw,_=c.account(pump);pp=c.decode_pump_pool(raw)
    if pp.get("base_mint")!=token or pp.get("quote_mint")!=c.WSOL:raise RuntimeError("PUMP_EXACT_IDENTITY_FAIL")
    meta=c.discover_dlmm(token);xy={meta.get("token_x"),meta.get("token_y")}
    if token not in xy or c.WSOL not in xy:raise RuntimeError("DLMM_EXACT_IDENTITY_FAIL")
    c.account(meta["address"])
    return pump,meta

def bind(limit=16):
    if not SRC.is_file():raise SystemExit("[FAIL] run QARB-043 first")
    reg=json.loads(SRC.read_text(encoding="utf-8"));now=time.time()
    cached={}
    if OUT.is_file():
        try:cached={x["token"]:x for x in json.loads(OUT.read_text(encoding="utf-8")).get("rows",[])}
        except Exception:cached={}
    items=list((reg.get("tokens") or {}).items())
    items.sort(key=lambda kv:(-float(kv[1].get("last_seen_epoch",0)),-int(kv[1].get("touches",0))))
    rows=[];fails=[]
    for token,info in items[:int(limit)]:
        try:
            if token in cached:
                row=dict(cached[token]);row["first_seen_epoch"]=float(info["first_seen_epoch"])
                row["last_seen_epoch"]=float(info["last_seen_epoch"]);row["touches"]=int(info.get("touches",0))
                rows.append(row)
                print("[BIND_REUSE] token=%s pump=%s meteora=%s age_last=%.1fs"%(token[:12],row["pump_pool"][:12],row["meteora_meta"]["address"][:12],max(0,now-float(info["last_seen_epoch"]))),flush=True)
                continue
            pump,meta=verify(token)
            rows.append({"token":token,"pump_pool":pump,"meteora_meta":meta,
                         "first_seen_epoch":float(info["first_seen_epoch"]),"last_seen_epoch":float(info["last_seen_epoch"]),
                         "touches":int(info.get("touches",0)),"bound_epoch":now})
            print("[EXACT_BIND] token=%s pump=%s meteora=%s age_last=%.1fs"%(token[:12],pump[:12],meta["address"][:12],max(0,now-float(info["last_seen_epoch"]))),flush=True)
        except Exception as exc:
            fails.append({"token":token,"reason":type(exc).__name__+":"+str(exc)})
            print("[BIND_SKIP] token=%s %s:%s"%(token[:12],type(exc).__name__,str(exc)[:120]),flush=True)
    payload={"rows":rows,"failures":fails,"source_registry_updated_epoch":reg.get("updated_epoch"),"created_epoch":now,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--limit",type=int,default=16);a=ap.parse_args(argv)
    print("[QARB-044] DYNAMIC EXACT PUMPSWAP/METEORA BINDING")
    r=bind(a.limit);print("[RESULT] bound=%d failed=%d"%(len(r["rows"]),len(r["failures"])))
    print("[REPORT]",OUT);print("[MODE] READ_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
