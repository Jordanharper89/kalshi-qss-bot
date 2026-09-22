from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

OLR_016_BUILD_ID="OLR-016"
OLR_016_REVISION="OLR_016_PRODUCTION_LEARNED_STATE_ADAPTER_V1"

@dataclass(frozen=True)
class ProductionLearnedStateSnapshot:
    source_state_path:str
    source_ledger_path:str
    cycles:int
    outcomes_learned:int
    applied_through_sequence:int
    learner_state_hash:str
    ledger_records:int
    learned_records:int
    learned_market_counts:tuple
    read_only:bool=True

def _read_json(path):
    p=Path(path)
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))

def load_production_learned_state(root=None):
    root=Path(root or Path.cwd()).resolve()
    state_path=root/"runtime_state"/"oracle_learning_runtime_state.json"
    ledger_path=root/"runtime_state"/"oracle_learning_event_ledger.json"
    state=_read_json(state_path)
    ledger=_read_json(ledger_path)

    ocl=state.get("ocl_state") if isinstance(state,dict) else {}
    if not isinstance(ocl,dict):ocl={}
    counts={}
    learned=0
    if isinstance(ledger,dict):
        for rec in ledger.values():
            if not isinstance(rec,dict):continue
            if str(rec.get("status") or "")!="learned":continue
            learned+=1
            ticker=str(rec.get("ticker") or "")
            if ticker:counts[ticker]=counts.get(ticker,0)+1

    return ProductionLearnedStateSnapshot(
        str(state_path.relative_to(root)),
        str(ledger_path.relative_to(root)),
        int(state.get("cycles",0)) if isinstance(state,dict) else 0,
        int(state.get("outcomes_learned",0)) if isinstance(state,dict) else 0,
        int(ocl.get("applied_through_sequence",0)),
        str(ocl.get("state_hash") or ""),
        len(ledger) if isinstance(ledger,dict) else 0,
        learned,
        tuple(sorted(counts.items())),
        True,
    )

def verify_olr_016_production_learned_state_adapter():
    x=load_production_learned_state(Path("__olr_missing_root__"))
    return x.read_only and x.cycles==0 and x.ledger_records==0
