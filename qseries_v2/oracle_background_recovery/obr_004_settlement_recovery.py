from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
import json

from .obr_003_state_recovery import recover_gap_market_states
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get

OBR_004_BUILD_ID="OBR-004"
OBR_004_REVISION="OBR_004_BACKGROUND_SETTLEMENT_RECONCILIATION_V1"
RESULTS="oracle_background_recovery_results.jsonl"

def _dt(v):
    if not v:return None
    try:
        x=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
    except Exception:return None

def recover_gap_settlements(root,gap,progress=print):
    root=Path(root).resolve()
    start=_dt(gap["gap_start"]);end=_dt(gap["gap_end"])
    creds=load_kalshi_credentials(root=root)
    cursor=None;pages=scanned=found=0
    out=root/"runtime_state"/RESULTS
    while True:
        params={"limit":1000,"status":"settled"}
        if cursor:params["cursor"]=cursor
        r=kalshi_rest_get(creds,"/markets",params,20)
        body=r.body or {};markets=tuple(body.get("markets",()))
        cursor=body.get("cursor");pages+=1;scanned+=len(markets)
        for raw in markets:
            ts=_dt(raw.get("settlement_ts") or raw.get("settled_ts") or raw.get("settled_time"))
            if ts is None or not(start<=ts<=end):continue
            with out.open("a",encoding="utf-8",newline="\n") as f:
                f.write(json.dumps({"gap_id":gap["gap_id"],"ticker":raw.get("ticker"),"kind":"SETTLEMENT","status":"RECOVERED","settlement_ts":str(ts),"result":raw.get("result"),"evidence_status":"NO_LIVE_EVIDENCE_DURING_GAP"},sort_keys=True,separators=(",",":"),default=str)+"\n")
            found+=1
        if progress:
            progress(f"[OBR SETTLEMENT] page={pages} scanned={scanned} found_in_gap={found} cursor={'YES' if cursor else 'NONE'}")
        if not cursor:break
    return {"settlement_pages":pages,"settlement_markets_scanned":scanned,"settlements_recovered":found}

def verify_obr_004_background_settlement_reconciliation():
    return OBR_004_BUILD_ID=="OBR-004" and callable(recover_gap_settlements)
