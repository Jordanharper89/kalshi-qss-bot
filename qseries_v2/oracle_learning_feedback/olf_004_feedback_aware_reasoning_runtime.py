from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import json,os

from qseries_v2.oracle_continuous_reasoning.ocr_011_reasoning_cursor_state import (
    load_reasoning_cursor,save_reasoning_cursor,advance_reasoning_cursor,
)
from qseries_v2.oracle_continuous_reasoning.ocr_012_incremental_observation_selection import (
    read_new_canonical_observations,cursor_values_from_last_row,
)
from qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join import (
    join_rows_to_umd_context,
)
from qseries_v2.oracle_continuous_reasoning.ocr_008_scientific_reasoning_invocation import (
    reason_over_market_aware_observations,
)
from qseries_v2.oracle_continuous_reasoning.ocr_009_intelligence_state_projection import (
    project_reasoning_results,
)
from .olf_003_reasoning_learning_context import build_learning_aware_reasoning_context

OLF_004_BUILD_ID="OLF-004"
OLF_004_REVISION="OLF_004_FEEDBACK_AWARE_CONTINUOUS_REASONING_RUNTIME_V1"
ATTESTATION_NAME="oracle_learning_feedback_reasoning_attestation.json"

@dataclass(frozen=True)
class FeedbackAwareReasoningCycleSummary:
    rows_read:int
    markets_reasoned:int
    markets_with_learning_context:int
    markets_with_calibration_adjustment:int
    learner_state_hash:str
    cursor_advanced:bool
    idle:bool
    execution_authority:bool=False

def _write_attestation(root,payload):
    path=Path(root)/"runtime_state"/ATTESTATION_NAME
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(
        json.dumps(payload,sort_keys=True,separators=(",",":")),
        encoding="utf-8",newline="\n"
    )
    os.replace(tmp,path)
    return path

def run_feedback_aware_reasoning_cycle(root=None,limit=50,cursor_path=None,progress=print):
    root=Path(root or Path.cwd()).resolve()
    cp=Path(cursor_path or root/"runtime_state"/"ocr_reasoning_cursor.json")
    cursor=load_reasoning_cursor(cp)
    slice_=read_new_canonical_observations(root,cursor=cursor,limit=limit)

    if not slice_.rows:
        progress("[OLF OCR] idle no_new_observations")
        return FeedbackAwareReasoningCycleSummary(0,0,0,0,"",False,True,False)

    aware=join_rows_to_umd_context(slice_.rows)
    if not aware:
        raise RuntimeError("New observations found but none resolved to market identity")

    reasoning=reason_over_market_aware_observations(aware)
    projections=project_reasoning_results(reasoning)
    if len(projections)!=len(reasoning):
        raise RuntimeError("OIS projection count mismatch")

    contexts=[]
    hashes=set()
    for result in reasoning:
        ctx=build_learning_aware_reasoning_context(root,result.market_ticker)
        contexts.append(ctx)
        if ctx.learner_state_hash:
            hashes.add(ctx.learner_state_hash)

    if len(hashes)>1:
        raise RuntimeError("Reasoning consumed inconsistent learner-state hashes")

    state_hash=next(iter(hashes),"")
    consumed=sum(1 for x in contexts if x.learning_context_consumed)
    calibrated=sum(1 for x in contexts if x.calibration_applied)

    order_column,order_value,observation_id=cursor_values_from_last_row(slice_)
    new_cursor=advance_reasoning_cursor(
        cursor,order_column,order_value,observation_id,len(slice_.rows)
    )
    save_reasoning_cursor(cp,new_cursor)

    payload={
        "revision":OLF_004_REVISION,
        "learner_state_hash":state_hash,
        "rows_read":len(slice_.rows),
        "markets_reasoned":len(reasoning),
        "markets_with_learning_context":consumed,
        "markets_with_calibration_adjustment":calibrated,
        "markets":[asdict(x) for x in contexts],
        "cursor":{
            "order_column":order_column,
            "order_value":str(order_value),
            "observation_id":observation_id,
        },
        "execution_authority":False,
    }
    _write_attestation(root,payload)

    progress(
        f"[OLF OCR] rows={len(slice_.rows)} markets_reasoned={len(reasoning)} "
        f"learning_context={consumed} calibrated={calibrated}"
    )
    progress(f"[OLF OCR] learner_state_hash={state_hash}")
    progress(f"[OLF OCR] cursor={order_column}:{order_value}:{observation_id}")

    return FeedbackAwareReasoningCycleSummary(
        len(slice_.rows),len(reasoning),consumed,calibrated,state_hash,True,False,False
    )

def verify_olf_004_feedback_aware_continuous_reasoning_runtime():
    return OLF_004_BUILD_ID=="OLF-004" and callable(run_feedback_aware_reasoning_cycle)
