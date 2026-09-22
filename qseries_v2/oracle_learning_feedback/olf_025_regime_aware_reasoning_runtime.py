from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import json,os
from qseries_v2.oracle_continuous_reasoning.ocr_011_reasoning_cursor_state import load_reasoning_cursor,save_reasoning_cursor,advance_reasoning_cursor
from qseries_v2.oracle_continuous_reasoning.ocr_012_incremental_observation_selection import read_new_canonical_observations,cursor_values_from_last_row
from qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join import join_rows_to_umd_context
from qseries_v2.oracle_continuous_reasoning.ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations
from qseries_v2.oracle_continuous_reasoning.ocr_009_intelligence_state_projection import project_reasoning_results
from .olf_021_experience_regimes import materialize_regime_segments
from .olf_022_regime_performance import materialize_regime_performance
from .olf_023_regime_recency import materialize_recency_weighted_regimes
from .olf_024_regime_aware_experience import select_regime_aware_experience

OLF_025_BUILD_ID="OLF-025";OLF_025_REVISION="OLF_025_REGIME_AWARE_REASONING_RUNTIME_V1";ATTESTATION_NAME="oracle_regime_aware_reasoning_attestation.json"
@dataclass(frozen=True)
class RegimeAwareReasoningSummary:
    rows_read:int;markets_reasoned:int;regime_contexts:int;rejected_contexts:int;learner_state_hash:str;idle:bool;execution_authority:bool=False
def refresh_regimes(root):
    a=materialize_regime_segments(root);b=materialize_regime_performance(root,2);c=materialize_recency_weighted_regimes(root,30.0,2);h={a["learner_state_hash"],b["learner_state_hash"],c["learner_state_hash"]}
    if len(h)!=1:raise RuntimeError("Regime learner-state lineage mismatch")
    return next(iter(h))
def _resolve(root,aware,reasoning):
    by={}
    for x in aware:by.setdefault(x.market_ticker,[]).append(x)
    return tuple(select_regime_aware_experience(root,r.market_ticker,tuple(by.get(r.market_ticker,()))) for r in reasoning)
def run_regime_aware_reasoning_cycle(root=None,limit=50,cursor_path=None,progress=print):
    root=Path(root or Path.cwd()).resolve();state_hash=refresh_regimes(root);cp=Path(cursor_path or root/"runtime_state"/"ocr_reasoning_cursor.json");cursor=load_reasoning_cursor(cp);s=read_new_canonical_observations(root,cursor=cursor,limit=limit)
    if not s.rows:return RegimeAwareReasoningSummary(0,0,0,0,state_hash,True,False)
    aware=join_rows_to_umd_context(s.rows)
    if not aware:raise RuntimeError("No market identities resolved")
    reasoning=reason_over_market_aware_observations(aware);projections=project_reasoning_results(reasoning)
    if len(reasoning)!=len(projections):raise RuntimeError("OIS projection count mismatch")
    ctx=_resolve(root,aware,reasoning);used=sum(x.available for x in ctx);rej=sum((not x.available) and bool(x.regime_id) for x in ctx)
    oc,ov,oid=cursor_values_from_last_row(s);save_reasoning_cursor(cp,advance_reasoning_cursor(cursor,oc,ov,oid,len(s.rows)))
    payload={"revision":OLF_025_REVISION,"learner_state_hash":state_hash,"rows_read":len(s.rows),"markets_reasoned":len(reasoning),"regime_contexts":used,"rejected_contexts":rej,"contexts":[asdict(x) for x in ctx],"execution_authority":False};path=root/"runtime_state"/ATTESTATION_NAME;tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,path)
    progress(f"[OLF-025 OCR] rows={len(s.rows)} markets_reasoned={len(reasoning)} regime_context={used} rejected={rej}");progress(f"[OLF-025 OCR] learner_state_hash={state_hash}")
    return RegimeAwareReasoningSummary(len(s.rows),len(reasoning),used,rej,state_hash,False,False)
def proof_recent_regimes(root=None,limit=250):
    from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations
    root=Path(root or Path.cwd()).resolve();h=refresh_regimes(root);rows=read_latest_canonical_observations(root,limit=limit).rows;aware=join_rows_to_umd_context(rows);reasoning=reason_over_market_aware_observations(aware);ctx=_resolve(root,aware,reasoning);return reasoning,tuple(x for x in ctx if x.available),tuple(x for x in ctx if (not x.available) and x.regime_id),h
def verify_olf_025_regime_aware_reasoning_runtime():return OLF_025_BUILD_ID=="OLF-025" and callable(run_regime_aware_reasoning_cycle)
