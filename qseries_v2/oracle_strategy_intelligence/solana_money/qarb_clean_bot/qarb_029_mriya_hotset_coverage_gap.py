from __future__ import annotations
import json
from pathlib import Path

SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_route_decode.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_hotset_coverage_gap.json")

def inspect(root):
    if not SRC.is_file(): raise SystemExit("[FAIL] run QARB-028 first: "+str(SRC))
    d=json.loads(SRC.read_text(encoding="utf-8"))
    hot=set(d.get("mint_counts") or {})
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
    p.m.pd.MAX_PAIRS=p.MAX_PAIRS
    state=p.m.prepare(Path(root))
    covered=set(state.get("eps") or {})
    pair_tokens={x.token for x in state.get("pairs",())}
    missing=sorted(hot-covered)
    rows=[]
    for m in sorted(hot):
        rows.append({"mint":m,"mriya_tx_count":int((d.get("mint_counts") or {}).get(m,0)),
                     "qarb_priced":m in covered,"pump_meteora_pair":m in pair_tokens})
    return {"mriya_hot_tokens":len(hot),"qarb_priced_tokens":len(covered),
            "hot_tokens_already_priced":len(hot&covered),"hot_tokens_missing":len(missing),
            "missing_mints":missing,"venue_counts":d.get("venue_counts") or {},
            "rows":rows,"execution_authority":False}

def run(root):
    r=inspect(root)
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(r,indent=2,sort_keys=True),encoding="utf-8")
    print("[QARB-029] MRIYA HOTSET VS QARB COVERAGE GAP")
    print("[COVERAGE] mriya_hot=%d qarb_priced=%d overlap=%d missing=%d"%(
        r["mriya_hot_tokens"],r["qarb_priced_tokens"],r["hot_tokens_already_priced"],r["hot_tokens_missing"]))
    print("[MRIYA_VENUES]",json.dumps(r["venue_counts"],sort_keys=True))
    for x in sorted(r["rows"],key=lambda z:(not z["qarb_priced"],-z["mriya_tx_count"]))[:30]:
        print("[HOTSET] token=%s tx=%d qarb_priced=%s pump_meteora=%s"%(
            x["mint"][:12],x["mriya_tx_count"],x["qarb_priced"],x["pump_meteora_pair"]))
    if r["missing_mints"]:
        print("[NEXT_BOUNDARY] expand live discovery/price adapters to missing Mriya hot tokens and venue families")
    else:
        print("[NEXT_BOUNDARY] coverage overlap exists; compare exact route economics instead of expanding blindly")
    print("[REPORT]",OUT)
    print("[MODE] READ_ONLY=True execution_authority=FALSE")
    return r
