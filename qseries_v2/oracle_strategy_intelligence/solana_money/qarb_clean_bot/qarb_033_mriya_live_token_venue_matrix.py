from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

CAND=Path("runtime_state/qseries/qarb_clean_bot/mriya_program_owned_pool_candidates.json")
LIVE=Path("runtime_state/qseries/qarb_clean_bot/mriya_pool_live_update_probe.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_live_token_venue_matrix.json")
WSOL="So11111111111111111111111111111111111111112"

def build():
    if not CAND.is_file():raise SystemExit("[FAIL] run QARB-031 first")
    if not LIVE.is_file():raise SystemExit("[FAIL] run QARB-032 first")
    c=json.loads(CAND.read_text(encoding="utf-8"))
    l=json.loads(LIVE.read_text(encoding="utf-8"))
    live={x["address"]:x for x in l.get("rows",[]) if x.get("live")}
    by=defaultdict(lambda:defaultdict(list))
    for x in c.get("rows",[]):
        if x["address"] not in live:continue
        for mint in x.get("mints") or []:
            if mint==WSOL:continue
            by[mint][x["program_name"]].append({
                "address":x["address"],"updates":int(live[x["address"]].get("updates",0)),
                "occurrences":int(x.get("occurrences",0))})
    rows=[]
    for mint,venues in by.items():
        vd={}
        for venue,items in venues.items():
            items=sorted(items,key=lambda z:(-z["updates"],-z["occurrences"],z["address"]))
            vd[venue]=items
        rows.append({"mint":mint,"venue_count":len(vd),"venues":vd,
                     "crossvenue_live":len(vd)>=2})
    rows.sort(key=lambda x:(not x["crossvenue_live"],-x["venue_count"],x["mint"]))
    payload={"tokens":len(rows),"crossvenue_live_tokens":sum(x["crossvenue_live"] for x in rows),
             "rows":rows,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    print("[QARB-033] MRIYA LIVE TOKEN/VENUE MATRIX")
    r=build()
    print("[RESULT] tokens=%d crossvenue_live=%d"%(r["tokens"],r["crossvenue_live_tokens"]))
    for x in r["rows"]:
        print("[TOKEN_MATRIX] token=%s venues=%s crossvenue=%s"%(
            x["mint"][:12],sorted(x["venues"]),x["crossvenue_live"]))
        for venue,items in x["venues"].items():
            top=items[0]
            print("  [VENUE] %s updates=%d hits=%d account=%s"%(
                venue,top["updates"],top["occurrences"],top["address"][:16]))
    print("[REPORT]",OUT)
    print("[MODE] READ_ONLY=True execution_authority=FALSE")
