from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_033_mriya_live_token_venue_matrix as mx

SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_crossvenue_priority.json")
MATRIX=Path("runtime_state/qseries/qarb_clean_bot/mriya_live_token_venue_matrix.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_exact_pump_meteora_bindings.json")
MAX_BIND=4

def retry(fn,*a,attempts=5):
    err=None
    for i in range(attempts):
        try:return fn(*a)
        except Exception as e:
            err=e;time.sleep(.20*(i+1))
    raise err

def resolve():
    if not SRC.is_file():raise SystemExit("[FAIL] run QARB-035 first")
    if not MATRIX.is_file():raise SystemExit("[FAIL] run QARB-033 first")
    pri=json.loads(SRC.read_text(encoding="utf-8"))
    mat={x["mint"]:x for x in json.loads(MATRIX.read_text(encoding="utf-8")).get("rows",[])}
    rows=[];fails=[]
    targets=[x for x in pri.get("rows",[]) if x.get("preferred_pump_meteora")][:MAX_BIND]
    for t in targets:
        token=t["mint"];m=mat.get(token) or {};pumps=(m.get("venues") or {}).get("PUMP_SWAP") or []
        verified=None
        for c in pumps:
            addr=c["address"]
            try:
                raw,_=retry(pd.c.account,addr);d=pd.c.decode_pump_pool(raw)
                if d.get("quote_mint")==pd.c.WSOL and d.get("base_mint")==token:
                    verified={"address":addr,"decode":d};break
            except Exception as e:pass
        if verified is None:
            fails.append({"token":token,"reason":"NO_VERIFIED_PUMPSWAP_POOL"});continue
        try:
            meta=retry(pd.c.discover_dlmm,token)
            if token not in (meta.get("token_x"),meta.get("token_y")) or pd.c.WSOL not in (meta.get("token_x"),meta.get("token_y")):
                raise RuntimeError("DLMM_NOT_WSOL_TOKEN_PAIR")
            rows.append({"token":token,"pump_pool":verified["address"],"meteora_meta":meta,
                         "priority_score":t.get("score"),"activity":t.get("activity")})
        except Exception as e:
            fails.append({"token":token,"reason":type(e).__name__+":"+str(e)})
    payload={"requested":len(targets),"bound":len(rows),"rows":rows,"failures":fails,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    print("[QARB-036] MRIYA EXACT PUMPSWAP + METEORA BINDING")
    r=resolve();print("[RESULT] requested=%d bound=%d failures=%d"%(r["requested"],r["bound"],len(r["failures"])))
    for x in r["rows"]:
        print("[EXACT_BIND] token=%s pump=%s meteora=%s activity=%s"%(
            x["token"][:12],x["pump_pool"],x["meteora_meta"]["address"],x.get("activity")))
    for x in r["failures"]:print("[BIND_FAIL]",x["token"][:12],x["reason"])
    print("[REPORT]",OUT);print("[MODE] READ_ONLY=True execution_authority=FALSE")
