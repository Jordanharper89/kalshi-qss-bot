from __future__ import annotations
import json
from pathlib import Path
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_059a_state_aligned_replay_eligibility.json")
TARGETS=("RAYDIUM_CLMM","ORCA","ORCA_WHIRLPOOL")

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def family(d):
    return str(d.get("venue") or d.get("family") or d.get("venue_name") or "").upper()

def state_evidence(d):
    keys=set(d)
    direct=any(k in keys for k in ("sqrt_price_x64","sqrt_price","liquidity","tick_current","tick_current_index"))
    pre=any(k in keys for k in ("pre_state","pretrade_state","pre_trade_state","pool_state_before","state_before"))
    slot=any(k in keys for k in ("slot","pre_slot","observed_slot","block_slot"))
    return direct or pre,slot

def build(root):
    root=Path(root);rows=[];files=0
    rs=root/"runtime_state"
    for p in rs.rglob("*.json") if rs.exists() else []:
        try:o=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        files+=1
        for d in walk(o):
            fam=family(d)
            if not any(t in fam for t in TARGETS):continue
            if not all(k in d for k in ("pool","input_mint","output_mint")):continue
            has_state,has_slot=state_evidence(d)
            rows.append({"source":str(p.relative_to(root)),"family":fam,"pool":d.get("pool"),
                         "signature":d.get("signature"),"input_amount":d.get("input_amount"),
                         "output_amount":d.get("output_amount"),"state_aligned":bool(has_state and has_slot),
                         "has_state":has_state,"has_slot":has_slot})
    cl=[r for r in rows if "RAYDIUM_CLMM" in r["family"]]
    oc=[r for r in rows if "ORCA" in r["family"]]
    payload={"revision":"QARB_059A","files_scanned":files,"economic_rows":len(rows),
             "raydium_clmm_rows":len(cl),"orca_rows":len(oc),
             "raydium_state_aligned":sum(1 for r in cl if r["state_aligned"]),
             "orca_state_aligned":sum(1 for r in oc if r["state_aligned"]),
             "historical_replay_safe":bool(cl and oc and all(r["state_aligned"] for r in cl+oc)),
             "rows":rows[:200],
             "next":"HISTORICAL_REPLAY" if bool(cl and oc and all(r["state_aligned"] for r in cl+oc))
                    else "LIVE_SHADOW_VALIDATION_REQUIRED",
             "execution_authority":False,"paper_only":True}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-059A] STATE-ALIGNED REPLAY ELIGIBILITY AUDIT")
    print("[ROWS] total=%d clmm=%d orca=%d"%(p["economic_rows"],p["raydium_clmm_rows"],p["orca_rows"]))
    print("[STATE_ALIGNED] clmm=%d orca=%d"%(p["raydium_state_aligned"],p["orca_state_aligned"]))
    print("[HISTORICAL_REPLAY_SAFE]",p["historical_replay_safe"])
    print("[NEXT]",p["next"]);print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
