from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import json,os

from qseries_v2.oracle_continuous_reasoning.ocr_011_reasoning_cursor_state import load_reasoning_cursor,save_reasoning_cursor,advance_reasoning_cursor
from qseries_v2.oracle_continuous_reasoning.ocr_012_incremental_observation_selection import read_new_canonical_observations,cursor_values_from_last_row
from qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join import join_rows_to_umd_context
from qseries_v2.oracle_continuous_reasoning.ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations
from qseries_v2.oracle_continuous_reasoning.ocr_009_intelligence_state_projection import project_reasoning_results
from .olf_001_learned_state_snapshot import materialize_learned_feedback_snapshot
from .olf_007_cross_market_learning_index import materialize_cross_market_learning_index
from .olf_009_generalized_learning_context import build_generalized_learning_context

OLF_010_BUILD_ID="OLF-010"
OLF_010_REVISION="OLF_010_CROSS_MARKET_REASONING_RUNTIME_V1"
ATTESTATION_NAME="oracle_cross_market_learning_reasoning_attestation.json"

@dataclass(frozen=True)
class CrossMarketReasoningCycleSummary:
    rows_read:int
    markets_reasoned:int
    learning_contexts:int
    exact_contexts:int
    generalized_contexts:int
    calibrated_contexts:int
    learner_state_hash:str
    idle:bool
    execution_authority:bool=False

def _attest(root,payload):
    path=Path(root)/"runtime_state"/ATTESTATION_NAME
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def _contexts_for_reasoning(root,reasoning):
    contexts=tuple(build_generalized_learning_context(root,x.market_ticker) for x in reasoning)
    hashes={x.learner_state_hash for x in contexts if x.learner_state_hash}
    if len(hashes)>1:raise RuntimeError("Inconsistent learner-state hashes in generalized reasoning context")
    return contexts,next(iter(hashes),"")

def run_cross_market_reasoning_cycle(root=None,limit=50,cursor_path=None,progress=print):
    root=Path(root or Path.cwd()).resolve()
    materialize_learned_feedback_snapshot(root)
    materialize_cross_market_learning_index(root)
    cp=Path(cursor_path or root/"runtime_state"/"ocr_reasoning_cursor.json")
    cursor=load_reasoning_cursor(cp)
    slice_=read_new_canonical_observations(root,cursor=cursor,limit=limit)
    if not slice_.rows:
        progress("[OLF-010 OCR] idle no_new_observations")
        return CrossMarketReasoningCycleSummary(0,0,0,0,0,0,"",True,False)
    aware=join_rows_to_umd_context(slice_.rows)
    if not aware:raise RuntimeError("No market identities recovered from new canonical observations")
    reasoning=reason_over_market_aware_observations(aware)
    projections=project_reasoning_results(reasoning)
    if len(projections)!=len(reasoning):raise RuntimeError("OIS projection count mismatch")
    contexts,state_hash=_contexts_for_reasoning(root,reasoning)
    consumed=sum(x.learning_context_consumed for x in contexts)
    exact=sum(x.relationship_type=="EXACT_TICKER" for x in contexts)
    generalized=sum(x.relationship_type=="SAME_KALSHI_SERIES" for x in contexts)
    calibrated=sum(x.calibration_applied for x in contexts)

    order_column,order_value,observation_id=cursor_values_from_last_row(slice_)
    save_reasoning_cursor(cp,advance_reasoning_cursor(cursor,order_column,order_value,observation_id,len(slice_.rows)))
    _attest(root,{
        "revision":OLF_010_REVISION,"learner_state_hash":state_hash,
        "rows_read":len(slice_.rows),"markets_reasoned":len(reasoning),
        "learning_contexts":consumed,"exact_contexts":exact,
        "generalized_contexts":generalized,"calibrated_contexts":calibrated,
        "contexts":[asdict(x) for x in contexts],"execution_authority":False,
    })
    progress(f"[OLF-010 OCR] rows={len(slice_.rows)} markets_reasoned={len(reasoning)} learning_context={consumed} exact={exact} generalized={generalized} calibrated={calibrated}")
    progress(f"[OLF-010 OCR] learner_state_hash={state_hash}")
    return CrossMarketReasoningCycleSummary(len(slice_.rows),len(reasoning),consumed,exact,generalized,calibrated,state_hash,False,False)

def proof_recent_generalization(root=None,limit=100):
    from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations
    root=Path(root or Path.cwd()).resolve()
    materialize_learned_feedback_snapshot(root);materialize_cross_market_learning_index(root)
    rows=read_latest_canonical_observations(root,limit=limit).rows
    aware=join_rows_to_umd_context(rows)
    reasoning=reason_over_market_aware_observations(aware)
    contexts,state_hash=_contexts_for_reasoning(root,reasoning)
    matches=tuple(x for x in contexts if x.learning_context_consumed)
    generalized=tuple(x for x in matches if x.relationship_type=="SAME_KALSHI_SERIES")
    return reasoning,matches,generalized,state_hash

def verify_olf_010_cross_market_reasoning_runtime():
    return OLF_010_BUILD_ID=="OLF-010" and callable(run_cross_market_reasoning_cycle)
