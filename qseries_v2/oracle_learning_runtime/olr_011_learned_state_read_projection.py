from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass(frozen=True)
class LearnedStateProjection:
    market_ticker: str
    events_seen: int
    successes: int
    failures: int
    reliability: float
    calibration: float

def project_learned_state(path: str|Path, market_ticker: str) -> LearnedStateProjection:
    p=Path(path)
    if not p.exists():
        return LearnedStateProjection(market_ticker,0,0,0,0.5,0.5)
    rows=[]
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            obj=json.loads(line)
        except Exception:
            continue
        if str(obj.get("market_ticker") or obj.get("ticker") or "") == market_ticker:
            rows.append(obj)
    success=sum(1 for x in rows if x.get("outcome") in (True,1,"win","correct","success"))
    failure=sum(1 for x in rows if x.get("outcome") in (False,0,"loss","incorrect","failure"))
    decided=success+failure
    rel=(success/decided) if decided else 0.5
    cal=max(0.0,min(1.0,1.0-abs(rel-0.5)))
    return LearnedStateProjection(market_ticker,len(rows),success,failure,rel,cal)

def verify_olr_011_learned_state_read_projection():
    x=project_learned_state("__missing__","KXTEST")
    return x.market_ticker=="KXTEST" and x.events_seen==0 and x.reliability==0.5
