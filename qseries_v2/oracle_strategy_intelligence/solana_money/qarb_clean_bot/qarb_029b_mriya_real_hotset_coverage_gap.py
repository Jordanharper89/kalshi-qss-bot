from __future__ import annotations
import json
from pathlib import Path
SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_route_decode.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_hotset_coverage_gap.json")
WSOL="So11111111111111111111111111111111111111112"
def inspect(root):
    if not SRC.is_file():raise SystemExit("[FAIL] run QARB-028B first")
    d=json.loads(SRC.read_text(encoding="utf-8"))
    hot={m for m in (d.get("mint_counts") or {}) if m!=WSOL}
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
    p.m.pd.MAX_PAIRS=p.MAX_PAIRS;state=p.m.prepare(Path(root))
    covered=set(state.get("eps") or {});pairs={x.token for x in state.get("pairs",())}
    rows=[{"mint":m,"mriya_tx_count":int(d["mint_counts"][m]),"qarb_priced":m in covered,"pump_meteora_pair":m in pairs} for m in sorted(hot)]
    return {"mriya_non_wsol_hot_tokens":len(hot),"qarb_priced_tokens":len(covered),
            "overlap":len(hot&covered),"missing":len(hot-covered),"rows":rows,
            "venue_counts":d.get("venue_counts") or {},"execution_authority":False}
def run(root):
    r=inspect(root);OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(r,indent=2,sort_keys=True),encoding="utf-8")
    print("[QARB-029B] MRIYA REAL HOTSET VS QARB COVERAGE")
    print("[COVERAGE] non_wsol_hot=%d qarb_priced=%d overlap=%d missing=%d"%(r["mriya_non_wsol_hot_tokens"],r["qarb_priced_tokens"],r["overlap"],r["missing"]))
    print("[MRIYA_VENUES]",json.dumps(r["venue_counts"],sort_keys=True))
    for x in sorted(r["rows"],key=lambda z:-z["mriya_tx_count"]):print("[HOTSET] token=%s tx=%d qarb_priced=%s pump_meteora=%s"%(x["mint"][:12],x["mriya_tx_count"],x["qarb_priced"],x["pump_meteora_pair"]))
    print("[REPORT]",OUT);print("[MODE] READ_ONLY=True execution_authority=FALSE");return r
