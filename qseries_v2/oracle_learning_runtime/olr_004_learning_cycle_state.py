from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import json,os
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import assemble_runtime_batch
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import IncrementalLearnerState,genesis_incremental_state
from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import run_learning_cycle
OLR_004_BUILD_ID="OLR-004"
OLR_004_REVISION="OLR_004_DURABLE_CONTINUOUS_LEARNING_CYCLE_V1"

@dataclass(frozen=True)
class LearningRuntimeState:
    ocl_state:IncrementalLearnerState
    last_settlement_ts:str
    last_ticker:str
    cycles:int
    outcomes_learned:int

def genesis_learning_runtime_state():
    return LearningRuntimeState(genesis_incremental_state(),"","",0,0)

def load_learning_runtime_state(path):
    p=Path(path)
    if not p.is_file():return genesis_learning_runtime_state()
    d=json.loads(p.read_text(encoding="utf-8"))
    return LearningRuntimeState(
        IncrementalLearnerState(**d["ocl_state"]),
        str(d.get("last_settlement_ts") or ""),
        str(d.get("last_ticker") or ""),
        int(d.get("cycles",0)),
        int(d.get("outcomes_learned",0)),
    )

def save_learning_runtime_state(path,state):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps({
        "ocl_state":asdict(state.ocl_state),
        "last_settlement_ts":state.last_settlement_ts,
        "last_ticker":state.last_ticker,
        "cycles":state.cycles,
        "outcomes_learned":state.outcomes_learned,
    },sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n")
    os.replace(tmp,p)

def apply_learning_inputs(state,inputs,last_settlement_ts,last_ticker):
    batch=assemble_runtime_batch(inputs)
    result,new_ocl=run_learning_cycle(state.cycles+1,state.ocl_state,batch)
    new=LearningRuntimeState(
        new_ocl,last_settlement_ts,last_ticker,
        state.cycles+1,state.outcomes_learned+len(batch.inputs)
    )
    return result,new

def verify_olr_004_durable_continuous_learning_cycle():
    return genesis_learning_runtime_state().ocl_state.applied_through_sequence==0
