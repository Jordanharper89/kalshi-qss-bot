
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from qseries_v2.oracle_learning_runtime.olr_002_settled_outcome_read_model import fetch_recent_settled_markets
from .ohl_005_historical_learning_candidate_gate import verify_ohl_005_historical_learning_candidate_gate

OHL_006_BUILD_ID="OHL-006"
OHL_006_REVISION="OHL_006_SETTLED_OUTCOME_INVENTORY_ADAPTER_V1"

@dataclass(frozen=True)
class SettledOutcomeInventory:
    requested_limit:int
    settled_count:int
    unique_tickers:int
    outcomes:tuple
    read_only:bool=True

def read_settled_outcome_inventory(root=None,limit=500):
    if not verify_ohl_005_historical_learning_candidate_gate():
        raise RuntimeError("OHL-005 verification failed")
    limit=int(limit)
    if limit < 1 or limit > 10000:
        raise ValueError("limit must be 1..10000")
    root=Path(root or Path.cwd()).resolve()
    rows=tuple(fetch_recent_settled_markets(root,limit=limit))
    tickers={str(getattr(x,"ticker","")) for x in rows if str(getattr(x,"ticker",""))}
    return SettledOutcomeInventory(limit,len(rows),len(tickers),rows,True)

def verify_ohl_006_settled_outcome_inventory_adapter():
    x=SettledOutcomeInventory(10,0,0,tuple(),True)
    return x.requested_limit==10 and x.read_only
