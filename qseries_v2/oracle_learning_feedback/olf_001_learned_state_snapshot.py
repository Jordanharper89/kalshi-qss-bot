from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import json,os

from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import (
    load_production_learned_state,
)
from qseries_v2.oracle_learning_runtime.olr_017_market_feedback_resolver import (
    resolve_market_feedback,
)
from qseries_v2.oracle_learning_runtime.olr_018_scientific_reasoning_feedback_envelope import (
    build_scientific_reasoning_feedback_envelope,
)

OLF_001_BUILD_ID="OLF-001"
OLF_001_REVISION="OLF_001_DURABLE_LEARNED_STATE_SNAPSHOT_BRIDGE_V1"
SNAPSHOT_NAME="oracle_reasoning_feedback_snapshot.json"

@dataclass(frozen=True)
class LearnedFeedbackSnapshotSummary:
    learner_state_hash:str
    outcomes_learned:int
    learned_records:int
    markets:int
    snapshot_path:str
    execution_authority:bool=False

def build_snapshot_payload(root=None):
    root=Path(root or Path.cwd()).resolve()
    state=load_production_learned_state(root)
    markets=[]
    for ticker,count in state.learned_market_counts:
        resolution=resolve_market_feedback(state,ticker)
        envelope=build_scientific_reasoning_feedback_envelope(resolution)
        markets.append(asdict(envelope))
    return {
        "revision":OLF_001_REVISION,
        "learner_state_hash":state.learner_state_hash,
        "learning_cycles":state.cycles,
        "outcomes_learned":state.outcomes_learned,
        "applied_through_sequence":state.applied_through_sequence,
        "learned_records":state.learned_records,
        "markets":markets,
        "execution_authority":False,
    }

def materialize_learned_feedback_snapshot(root=None,output_path=None):
    root=Path(root or Path.cwd()).resolve()
    payload=build_snapshot_payload(root)
    path=Path(output_path or root/"runtime_state"/SNAPSHOT_NAME)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(
        json.dumps(payload,sort_keys=True,separators=(",",":")),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(tmp,path)
    return LearnedFeedbackSnapshotSummary(
        str(payload["learner_state_hash"]),
        int(payload["outcomes_learned"]),
        int(payload["learned_records"]),
        len(payload["markets"]),
        str(path.relative_to(root)),
        False,
    )

def verify_snapshot_matches_current_learner(root=None):
    root=Path(root or Path.cwd()).resolve()
    path=root/"runtime_state"/SNAPSHOT_NAME
    if not path.is_file():
        return False
    payload=json.loads(path.read_text(encoding="utf-8"))
    state=load_production_learned_state(root)
    return (
        str(payload.get("learner_state_hash") or "")==state.learner_state_hash
        and int(payload.get("outcomes_learned",0))==state.outcomes_learned
        and int(payload.get("learned_records",0))==state.learned_records
        and payload.get("execution_authority") is False
    )

def verify_olf_001_durable_learned_state_snapshot_bridge():
    return OLF_001_BUILD_ID=="OLF-001" and callable(materialize_learned_feedback_snapshot)
