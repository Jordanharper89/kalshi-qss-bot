from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import json,os
from .olr_016_production_learned_state_adapter import load_production_learned_state
from .olr_017_market_feedback_resolver import resolve_market_feedback
from .olr_018_scientific_reasoning_feedback_envelope import build_scientific_reasoning_feedback_envelope

OLR_019_BUILD_ID="OLR-019"
OLR_019_REVISION="OLR_019_CONTINUOUS_FEEDBACK_SNAPSHOT_RUNTIME_V1"

@dataclass(frozen=True)
class FeedbackSnapshotSummary:
    markets:int
    learned_records:int
    snapshot_path:str
    read_only_upstream:bool=True
    execution_authority:bool=False

def materialize_feedback_snapshot(root=None,output_path=None):
    root=Path(root or Path.cwd()).resolve()
    state=load_production_learned_state(root)
    rows=[]
    for ticker,count in state.learned_market_counts:
        resolution=resolve_market_feedback(state,ticker)
        rows.append(asdict(build_scientific_reasoning_feedback_envelope(resolution)))
    payload={
        "revision":OLR_019_REVISION,
        "learner_state_hash":state.learner_state_hash,
        "outcomes_learned":state.outcomes_learned,
        "learned_records":state.learned_records,
        "markets":rows,
        "execution_authority":False,
    }
    path=Path(output_path or root/"runtime_state"/"oracle_reasoning_feedback_snapshot.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n")
    os.replace(tmp,path)
    return FeedbackSnapshotSummary(len(rows),state.learned_records,str(path.relative_to(root)),True,False)

def verify_olr_019_continuous_feedback_snapshot_runtime():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        x=materialize_feedback_snapshot(Path(d))
        return x.markets==0 and x.read_only_upstream and not x.execution_authority
