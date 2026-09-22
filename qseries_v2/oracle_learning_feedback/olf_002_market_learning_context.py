from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

from .olf_001_learned_state_snapshot import SNAPSHOT_NAME
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import (
    load_production_learned_state,
)
from qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import (
    load_live_feedback_snapshot,
)
from qseries_v2.oracle_learning_runtime.olr_039_bounded_learning_consumption_envelope import (
    build_bounded_learning_consumption,
)

OLF_002_BUILD_ID="OLF-002"
OLF_002_REVISION="OLF_002_MARKET_LEARNING_CONTEXT_READ_MODEL_V1"

@dataclass(frozen=True)
class MarketLearningContext:
    market_ticker:str
    learner_state_hash:str
    learned_records:int
    experience_weight:float
    feedback_eligible:bool
    calibration_available:bool
    bounded_adjustment:float
    calibration_reason:str
    advisory_only:bool=True
    execution_authority:bool=False

def _read_snapshot(root):
    path=Path(root)/"runtime_state"/SNAPSHOT_NAME
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def load_market_learning_context(root=None,market_ticker=""):
    root=Path(root or Path.cwd()).resolve()
    ticker=str(market_ticker or "")
    snapshot=_read_snapshot(root)
    current=load_production_learned_state(root)
    snap_hash=str(snapshot.get("learner_state_hash") or "")
    if snap_hash!=current.learner_state_hash:
        raise RuntimeError("Learned-feedback snapshot is stale relative to current learner state")

    by_market={
        str(x.get("market_ticker") or ""):x
        for x in snapshot.get("markets",[])
        if isinstance(x,dict)
    }
    row=by_market.get(ticker,{})
    learned_records=int(row.get("learned_records",0))
    experience_weight=float(row.get("experience_weight",0.0))
    feedback_eligible=bool(row.get("feedback_eligible",False))

    live=load_live_feedback_snapshot(root)
    calibration=live.get(ticker)
    if calibration is None:
        return MarketLearningContext(
            ticker,snap_hash,learned_records,experience_weight,feedback_eligible,
            False,0.0,"no_mature_calibration_feedback",True,False
        )

    bounded=build_bounded_learning_consumption(calibration)
    return MarketLearningContext(
        ticker,snap_hash,learned_records,experience_weight,feedback_eligible,
        bool(bounded.available),float(bounded.bounded_adjustment),
        str(bounded.reason),True,False
    )

def verify_olf_002_market_learning_context_read_model():
    return OLF_002_BUILD_ID=="OLF-002" and callable(load_market_learning_context)
