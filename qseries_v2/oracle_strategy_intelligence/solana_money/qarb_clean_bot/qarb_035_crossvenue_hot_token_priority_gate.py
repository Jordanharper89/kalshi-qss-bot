from __future__ import annotations
import json
from pathlib import Path
SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_live_token_venue_matrix.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_crossvenue_priority.json")

def rank():
    if not SRC.is_file():raise SystemExit("[FAIL] run QARB-033 first")
    d=json.loads(SRC.read_text(encoding="utf-8"));rows=[]
    for x in d.get("rows",[]):
        if not x.get("crossvenue_live"):continue
        activity=0;venues=[]
        for venue,items in x.get("venues",{}).items():
            venues.append(venue)
            activity+=max((int(i.get("updates",0)) for i in items),default=0)
        preferred=int("PUMP_SWAP" in venues and "METEORA_DLMM" in venues)
        ray=int(any(v.startswith("RAYDIUM") for v in venues))
        score=preferred*1_000_000+ray*100_000+len(venues)*10_000+activity
        rows.append({"mint":x["mint"],"venues":sorted(venues),"activity":activity,
                     "preferred_pump_meteora":bool(preferred),"has_raydium":bool(ray),"score":score})
    rows.sort(key=lambda z:(-z["score"],z["mint"]))
    payload={"candidates":len(rows),"rows":rows,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    print("[QARB-035] CROSS-VENUE HOT TOKEN PRIORITY GATE")
    r=rank();print("[CANDIDATES]",r["candidates"])
    for i,x in enumerate(r["rows"],1):
        print("[PRIORITY] rank=%d token=%s venues=%s activity=%d pump_meteora=%s raydium=%s"%(
            i,x["mint"][:12],x["venues"],x["activity"],x["preferred_pump_meteora"],x["has_raydium"]))
    if r["rows"]:print("[NEXT_BIND_TARGET]",r["rows"][0]["mint"],r["rows"][0]["venues"])
    print("[REPORT]",OUT);print("[MODE] READ_ONLY=True execution_authority=FALSE")
