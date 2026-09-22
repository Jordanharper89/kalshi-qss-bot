from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import json,os

from qseries_v2.oracle_continuous_reasoning.ocr_011_reasoning_cursor_state import load_reasoning_cursor,save_reasoning_cursor,advance_reasoning_cursor
from qseries_v2.oracle_continuous_reasoning.ocr_012_incremental_observation_selection import read_new_canonical_observations,cursor_values_from_last_row
from qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join import join_rows_to_umd_context
from qseries_v2.oracle_continuous_reasoning.ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations
from qseries_v2.oracle_continuous_reasoning.ocr_009_intelligence_state_projection import project_reasoning_results
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import load_production_learned_state
from .olf_011_learned_experience_profile import materialize_learned_experience_profiles
from .olf_012_historical_condition_context import materialize_historical_condition_context
from .olf_013_behavior_patterns import materialize_behavior_patterns
from .olf_014_condition_aware_experience import resolve_condition_aware_experience

OLF_015_BUILD_ID="OLF-015"
OLF_015_REVISION="OLF_015_CONDITION_AWARE_REASONING_RUNTIME_V1"
ATTESTATION_NAME="oracle_condition_aware_learning_reasoning_attestation.json"

@dataclass(frozen=True)
class ConditionAwareReasoningSummary:
    rows_read:int;markets_reasoned:int;condition_contexts:int;learner_state_hash:str;idle:bool;execution_authority:bool=False

def refresh_intelligence(root):
    a=materialize_learned_experience_profiles(root)
    b=materialize_historical_condition_context(root)
    c=materialize_behavior_patterns(root,3)
    hashes={a["learner_state_hash"],b["learner_state_hash"],c["learner_state_hash"]}
    if len(hashes)!=1:raise RuntimeError("Historical intelligence learner-state lineage mismatch")
    return next(iter(hashes))

def _resolve(root,aware,reasoning):
    by={}
    for x in aware:by.setdefault(x.market_ticker,[]).append(x)
    contexts=tuple(resolve_condition_aware_experience(root,r.market_ticker,tuple(by.get(r.market_ticker,()))) for r in reasoning)
    return contexts

def run_condition_aware_reasoning_cycle(root=None,limit=50,cursor_path=None,progress=print):
    root=Path(root or Path.cwd()).resolve();state_hash=refresh_intelligence(root)
    cp=Path(cursor_path or root/"runtime_state"/"ocr_reasoning_cursor.json");cursor=load_reasoning_cursor(cp)
    slice_=read_new_canonical_observations(root,cursor=cursor,limit=limit)
    if not slice_.rows:return ConditionAwareReasoningSummary(0,0,0,state_hash,True,False)
    aware=join_rows_to_umd_context(slice_.rows)
    if not aware:raise RuntimeError("No market identity resolved from canonical observations")
    reasoning=reason_over_market_aware_observations(aware);projections=project_reasoning_results(reasoning)
    if len(reasoning)!=len(projections):raise RuntimeError("OIS projection count mismatch")
    contexts=_resolve(root,aware,reasoning)
    consumed=sum(1 for x in contexts if x.available)
    hashes={x.learner_state_hash for x in contexts if x.learner_state_hash}
    if hashes and hashes!={state_hash}:raise RuntimeError("Condition context consumed stale learner state")
    order_column,order_value,observation_id=cursor_values_from_last_row(slice_)
    save_reasoning_cursor(cp,advance_reasoning_cursor(cursor,order_column,order_value,observation_id,len(slice_.rows)))
    path=root/"runtime_state"/ATTESTATION_NAME;payload={"revision":OLF_015_REVISION,"learner_state_hash":state_hash,"rows_read":len(slice_.rows),"markets_reasoned":len(reasoning),"condition_contexts":consumed,"contexts":[asdict(x) for x in contexts],"execution_authority":False}
    tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,path)
    progress(f"[OLF-015 OCR] rows={len(slice_.rows)} markets_reasoned={len(reasoning)} condition_context={consumed}")
    progress(f"[OLF-015 OCR] learner_state_hash={state_hash}")
    return ConditionAwareReasoningSummary(len(slice_.rows),len(reasoning),consumed,state_hash,False,False)

def proof_recent_condition_intelligence(root=None,limit=200):
    from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations
    root=Path(root or Path.cwd()).resolve();state_hash=refresh_intelligence(root)
    rows=read_latest_canonical_observations(root,limit=limit).rows;aware=join_rows_to_umd_context(rows);reasoning=reason_over_market_aware_observations(aware)
    contexts=_resolve(root,aware,reasoning);matches=tuple(x for x in contexts if x.available)
    return reasoning,matches,state_hash

def verify_olf_015_condition_aware_reasoning_runtime():
    return OLF_015_BUILD_ID=="OLF-015" and callable(run_condition_aware_reasoning_cycle)
