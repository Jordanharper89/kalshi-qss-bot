from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd

SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_exact_pump_meteora_bindings.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_priority_pair_hydration.json")
_ORIG_UNIVERSE=pd.engine.candidate_universe

def binding_universe(root):
    if not SRC.is_file():raise SystemExit("[FAIL] run QARB-036 first")
    d=json.loads(SRC.read_text(encoding="utf-8"))
    return [{"token":x["token"],"pump_pool":x["pump_pool"],"meteora_meta":x["meteora_meta"]} for x in d.get("rows",[])]

def hydrate(root):
    old=pd.engine.candidate_universe;oldmax=pd.MAX_PAIRS
    pd.engine.candidate_universe=binding_universe;pd.MAX_PAIRS=16
    try:pairs,landing=pd.prepare_pairs(Path(root))
    finally:pd.engine.candidate_universe=old;pd.MAX_PAIRS=oldmax
    rows=[]
    for p in pairs:
        quote=None;err=None
        try:quote=pd.best_local_route(p,landing)
        except Exception as e:err=type(e).__name__+":"+str(e)
        rows.append({"token":p.token,"pump_pool":p.pump_pool,"meteora_pool":p.meteora_pool,
                     "watched_accounts":p.watched_accounts(),"initial_best":quote,"quote_error":err})
    payload={"hydrated":len(pairs),"landing_lamports":landing,"rows":rows,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return pairs,landing,payload

def main():
    print("[QARB-037] MRIYA PRIORITY PAIR HYDRATION")
    pairs,landing,r=hydrate(Path.cwd());print("[RESULT] hydrated=%d landing_lamports=%d"%(len(pairs),landing))
    for x in r["rows"]:
        print("[HYDRATED_PAIR] token=%s accounts=%d pump=%s meteora=%s best=%s error=%s"%(
            x["token"][:12],len(x["watched_accounts"]),x["pump_pool"][:12],x["meteora_pool"][:12],
            x["initial_best"],x["quote_error"]))
    print("[REPORT]",OUT);print("[MODE] READ_ONLY=True execution_authority=FALSE")
