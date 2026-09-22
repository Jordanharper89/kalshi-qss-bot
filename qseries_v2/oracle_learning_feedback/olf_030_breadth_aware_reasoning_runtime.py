from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import json,os
from qseries_v2.oracle_continuous_reasoning.ocr_011_reasoning_cursor_state import load_reasoning_cursor,save_reasoning_cursor,advance_reasoning_cursor
from qseries_v2.oracle_continuous_reasoning.ocr_012_incremental_observation_selection import read_new_canonical_observations,cursor_values_from_last_row
from qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join import join_rows_to_umd_context
from qseries_v2.oracle_continuous_reasoning.ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations
from qseries_v2.oracle_continuous_reasoning.ocr_009_intelligence_state_projection import project_reasoning_results
from .olf_026_learning_coverage_atlas import materialize_learning_coverage_atlas
from .olf_027_series_learning_gaps import materialize_series_learning_gaps
from .olf_028_series_maturity import materialize_series_maturity
from .olf_029_breadth_aware_experience import select_breadth_aware_experience

OLF_030_BUILD_ID="OLF-030";OLF_030_REVISION="OLF_030_BREADTH_AWARE_REASONING_RUNTIME_V1";ATTESTATION_NAME="oracle_learning_breadth_reasoning_attestation.json"

def _orh007_atomic_json(path,payload,max_attempts=8):
    import uuid,time
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"));last=None
    for attempt in range(1,int(max_attempts)+1):
        tmp=p.with_name(p.name+f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_text(raw,encoding="utf-8",newline="\n");os.replace(tmp,p);return p
        except PermissionError as exc:
            last=exc
            try:
                if tmp.exists():tmp.unlink()
            except Exception:pass
            if attempt>=max_attempts:break
            time.sleep(min(0.5,0.025*(2**(attempt-1))))
        finally:
            try:
                if tmp.exists():tmp.unlink()
            except Exception:pass
    raise last or PermissionError("OLF-030 attestation atomic replace failed")

@dataclass(frozen=True)
class BreadthAwareReasoningSummary:
    rows_read:int;markets_reasoned:int;experience_contexts:int;withheld_contexts:int;blind_contexts:int;learner_state_hash:str;idle:bool;execution_authority:bool=False
def refresh_breadth(root):
    a=materialize_learning_coverage_atlas(root);b=materialize_series_learning_gaps(root);c=materialize_series_maturity(root);h={a["learner_state_hash"],b["learner_state_hash"],c["learner_state_hash"]}
    if len(h)!=1:raise RuntimeError("Learning breadth lineage mismatch")
    return next(iter(h))
def _resolve(root,aware,reasoning):
    by={}
    for x in aware:by.setdefault(x.market_ticker,[]).append(x)
    return tuple(select_breadth_aware_experience(root,r.market_ticker,tuple(by.get(r.market_ticker,()))) for r in reasoning)
def run_breadth_aware_reasoning_cycle(root=None,limit=50,cursor_path=None,progress=print):
    root=Path(root or Path.cwd()).resolve();h=refresh_breadth(root);cp=Path(cursor_path or root/"runtime_state"/"ocr_reasoning_cursor.json");cursor=load_reasoning_cursor(cp);s=read_new_canonical_observations(root,cursor=cursor,limit=limit)
    if not s.rows:return BreadthAwareReasoningSummary(0,0,0,0,0,h,True,False)
    aware=join_rows_to_umd_context(s.rows)
    if not aware:raise RuntimeError("No market identities resolved")
    reasoning=reason_over_market_aware_observations(aware);proj=project_reasoning_results(reasoning)
    if len(reasoning)!=len(proj):raise RuntimeError("OIS projection count mismatch")
    ctx=_resolve(root,aware,reasoning);used=sum(x.experience_available for x in ctx);withheld=sum((not x.experience_available) and x.maturity not in ("BLIND",) for x in ctx);blind=sum(x.maturity=="BLIND" for x in ctx)
    oc,ov,oid=cursor_values_from_last_row(s);save_reasoning_cursor(cp,advance_reasoning_cursor(cursor,oc,ov,oid,len(s.rows)))
    payload={"revision":OLF_030_REVISION,"learner_state_hash":h,"rows_read":len(s.rows),"markets_reasoned":len(reasoning),"experience_contexts":used,"withheld_contexts":withheld,"blind_contexts":blind,"contexts":[asdict(x) for x in ctx],"execution_authority":False};path=root/"runtime_state"/ATTESTATION_NAME;_orh007_atomic_json(path,payload)
    progress(f"[OLF-030 OCR] rows={len(s.rows)} markets_reasoned={len(reasoning)} experience_context={used} withheld={withheld} blind={blind}");progress(f"[OLF-030 OCR] learner_state_hash={h}")
    return BreadthAwareReasoningSummary(len(s.rows),len(reasoning),used,withheld,blind,h,False,False)
def proof_recent_breadth(root=None,limit=250):
    from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations
    root=Path(root or Path.cwd()).resolve();h=refresh_breadth(root);rows=read_latest_canonical_observations(root,limit=limit).rows;aware=join_rows_to_umd_context(rows);reasoning=reason_over_market_aware_observations(aware);ctx=_resolve(root,aware,reasoning);return reasoning,tuple(x for x in ctx if x.experience_available),tuple(x for x in ctx if (not x.experience_available) and x.maturity!="BLIND"),tuple(x for x in ctx if x.maturity=="BLIND"),h
def verify_olf_030_breadth_aware_reasoning_runtime():return OLF_030_BUILD_ID=="OLF-030" and callable(run_breadth_aware_reasoning_cycle)
