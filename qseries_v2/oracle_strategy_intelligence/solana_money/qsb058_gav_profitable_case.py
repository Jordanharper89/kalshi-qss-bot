from __future__ import annotations
import hashlib,json,time
from pathlib import Path

TOKEN_PREFIX="GavQxkBXLg"
DIRECTION="PUMP_TO_METEORA"
OBSERVED_POINTS=(
    {"start_sol":0.005,"net_sol":0.000429809,"bps":859.62},
    {"start_sol":0.010,"net_sol":0.000859233,"bps":859.23},
    {"start_sol":0.025,"net_sol":0.002145190,"bps":858.08},
    {"start_sol":0.050,"net_sol":0.004280742,"bps":856.15},
)
TAPE="runtime_state/solana_opportunities/universal_trade_tape/multidex_universal_economic_tape.json"
OUT="runtime_state/qseries/qsb058_gav_profitable_case/report.json"

def _sha(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def replay_observed():
    rows=[]
    for p in OBSERVED_POINTS:
        start=float(p["start_sol"]);net=float(p["net_sol"])
        end=start+net
        bps=net/start*10000.0
        rows.append({
            "start_sol":start,"end_sol":end,"net_sol":net,
            "logged_bps":float(p["bps"]),"replay_bps":bps,
            "bps_delta":bps-float(p["bps"]),
            "profitable":net>0,
        })
    return rows

def resolve_case(root):
    p=Path(root)/TAPE
    if not p.is_file():
        return {"resolved":False,"reason":"TAPE_MISSING"}
    try:j=json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:return {"resolved":False,"reason":"TAPE_INVALID","error":str(e)}
    rows=j.get("exact_rows") or j.get("rows") or []
    hits={}
    for r in rows:
        tok=str(r.get("token_address") or r.get("token_mint") or "")
        if not tok.startswith(TOKEN_PREFIX):continue
        pool=str(r.get("market_address") or r.get("pool") or "")
        if not pool:continue
        slot=int(r.get("slot") or 0)
        cur=hits.get(tok)
        if cur is None or slot>cur["slot"]:
            hits[tok]={"token":tok,"pump_pool":pool,"slot":slot}
    if len(hits)!=1:
        return {"resolved":False,"reason":"TOKEN_PREFIX_MATCH_COUNT","count":len(hits),
                "matches":sorted(hits)}
    return {"resolved":True,**next(iter(hits.values()))}

def current_binding(root):
    case=resolve_case(root)
    if not case.get("resolved"):return case
    token=case["token"]
    try:
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
        meta=c.discover_dlmm(token)
        snap=c.build_token_snapshot(token,case["pump_pool"])
        return {
            **case,
            "meteora_pool":meta["address"],
            "token_x":meta["token_x"],"token_y":meta["token_y"],
            "pump_base_reserve":int(snap["pump_base_reserve"]),
            "pump_quote_reserve":int(snap["pump_quote_reserve"]),
            "current_binding_ok":True,
        }
    except Exception as e:
        return {**case,"current_binding_ok":False,
                "binding_error":type(e).__name__+": "+str(e)}

def build_report(root):
    replay=replay_observed()
    binding=current_binding(root)
    profitable=all(x["profitable"] for x in replay)
    monotonic=all(replay[i]["net_sol"]<replay[i+1]["net_sol"] for i in range(len(replay)-1))
    bps_band=max(x["replay_bps"] for x in replay)-min(x["replay_bps"] for x in replay)
    report={
        "revision":"QSB_058_GAV_PROFITABLE_CASE_FREEZE_REPLAY_V1",
        "case_id":"GavQxkBXLg_PUMP_TO_METEORA_20260925",
        "token_prefix":TOKEN_PREFIX,
        "direction":DIRECTION,
        "source":"physically_observed_QSB055_runtime_output",
        "observed_points":list(OBSERVED_POINTS),
        "replay":replay,
        "four_of_four_profitable":profitable,
        "net_profit_monotonic_with_size":monotonic,
        "replay_bps_band":bps_band,
        "binding":binding,
        "historical_observation_hash":_sha(list(OBSERVED_POINTS)),
        "execution_authority":False,
        "real_money_moved":False,
        "next_required_boundary":"QSB_059_PUMP_TO_METEORA_NATIVE_ATOMIC_COMPOSER_FROM_FROZEN_GAV_CASE",
        "written_unix":time.time(),
    }
    out=Path(root)/OUT
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    return report,out

def main(root=None):
    root=Path(root or Path.cwd())
    r,p=build_report(root)
    print("[QSB-058] GAV PROFITABLE CASE FREEZE + REPLAY",flush=True)
    for x in r["replay"]:
        print("[REPLAY] start=%.3f end=%.9f net=%+.9f SOL bps=%+.2f profitable=%s"%(
            x["start_sol"],x["end_sol"],x["net_sol"],x["replay_bps"],x["profitable"]),flush=True)
    b=r["binding"]
    if b.get("resolved"):
        print("[CASE] token=%s pump=%s meteora=%s current_binding_ok=%s"%(
            b.get("token"),b.get("pump_pool"),b.get("meteora_pool"),b.get("current_binding_ok")),flush=True)
    else:
        print("[CASE] token_prefix=%s unresolved=%s"%(TOKEN_PREFIX,b.get("reason")),flush=True)
    print("[PROOF] four_of_four_profitable=%s monotonic=%s bps_band=%.2f"%(
        r["four_of_four_profitable"],r["net_profit_monotonic_with_size"],r["replay_bps_band"]),flush=True)
    print("[NEXT] "+r["next_required_boundary"],flush=True)
    print("[REPORT] "+str(p),flush=True)
    print("[MODE] execution_authority=FALSE real_money_moved=FALSE",flush=True)
    return r

if __name__=="__main__":
    main()
