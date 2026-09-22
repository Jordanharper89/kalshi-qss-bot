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
from .olf_016_outcome_attributed_experience import materialize_outcome_attributed_experience
from .olf_017_pattern_performance import materialize_pattern_performance
from .olf_018_pattern_stability import materialize_pattern_stability
from .olf_019_reliability_weighted_experience import resolve_reliability_weighted_experience

OLF_020_BUILD_ID="OLF-020"
OLF_020_REVISION="OLF_020_RELIABILITY_AWARE_REASONING_RUNTIME_V1"
ATTESTATION_NAME="oracle_reliability_aware_learning_reasoning_attestation.json"

@dataclass(frozen=True)
class ReliabilityAwareReasoningSummary:
    rows_read:int;markets_reasoned:int;reliable_contexts:int;rejected_contexts:int;learner_state_hash:str;idle:bool;execution_authority:bool=False

def refresh_reliability(root):
    a=materialize_outcome_attributed_experience(root)
    b=materialize_pattern_performance(root,3)
    c=materialize_pattern_stability(root)
    hashes={a["learner_state_hash"],b["learner_state_hash"],c["learner_state_hash"]}
    if len(hashes)!=1:raise RuntimeError("Pattern reliability learner-state lineage mismatch")
    return next(iter(hashes))

def _resolve(root,aware,reasoning):
    by={}
    for x in aware:by.setdefault(x.market_ticker,[]).append(x)
    return tuple(resolve_reliability_weighted_experience(root,r.market_ticker,tuple(by.get(r.market_ticker,()))) for r in reasoning)

def run_reliability_aware_reasoning_cycle(root=None,limit=50,cursor_path=None,progress=print):
    root=Path(root or Path.cwd()).resolve();state_hash=refresh_reliability(root)
    cp=Path(cursor_path or root/"runtime_state"/"ocr_reasoning_cursor.json");cursor=load_reasoning_cursor(cp)
    slice_=read_new_canonical_observations(root,cursor=cursor,limit=limit)
    if not slice_.rows:return ReliabilityAwareReasoningSummary(0,0,0,0,state_hash,True,False)
    aware=join_rows_to_umd_context(slice_.rows)
    if not aware:raise RuntimeError("No market identities resolved")
    reasoning=reason_over_market_aware_observations(aware);projections=project_reasoning_results(reasoning)
    if len(reasoning)!=len(projections):raise RuntimeError("OIS projection count mismatch")
    contexts=_resolve(root,aware,reasoning);reliable=sum(1 for x in contexts if x.available);rejected=sum(1 for x in contexts if x.pattern_id and not x.available)
    order_column,order_value,observation_id=cursor_values_from_last_row(slice_)
    save_reasoning_cursor(cp,advance_reasoning_cursor(cursor,order_column,order_value,observation_id,len(slice_.rows)))
    payload={"revision":OLF_020_REVISION,"learner_state_hash":state_hash,"rows_read":len(slice_.rows),"markets_reasoned":len(reasoning),"reliable_contexts":reliable,"rejected_contexts":rejected,"contexts":[asdict(x) for x in contexts],"execution_authority":False}
    path=root/"runtime_state"/ATTESTATION_NAME;tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,path)
    progress(f"[OLF-020 OCR] rows={len(slice_.rows)} markets_reasoned={len(reasoning)} reliable_context={reliable} rejected_context={rejected}")
    progress(f"[OLF-020 OCR] learner_state_hash={state_hash}")
    return ReliabilityAwareReasoningSummary(len(slice_.rows),len(reasoning),reliable,rejected,state_hash,False,False)

def proof_recent_reliability(root=None,limit=250):
    from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations
    root=Path(root or Path.cwd()).resolve();state_hash=refresh_reliability(root)
    rows=read_latest_canonical_observations(root,limit=limit).rows;aware=join_rows_to_umd_context(rows);reasoning=reason_over_market_aware_observations(aware);contexts=_resolve(root,aware,reasoning)
    return reasoning,tuple(x for x in contexts if x.available),tuple(x for x in contexts if x.pattern_id and not x.available),state_hash

def verify_olf_020_reliability_aware_reasoning_runtime():
    return OLF_020_BUILD_ID=="OLF-020" and callable(run_reliability_aware_reasoning_cycle)
