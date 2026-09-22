from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .ocr_011_reasoning_cursor_state import load_reasoning_cursor,save_reasoning_cursor,advance_reasoning_cursor
from .ocr_012_incremental_observation_selection import read_new_canonical_observations,cursor_values_from_last_row
from .ocr_007_umd_context_join import join_rows_to_umd_context
from .ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations
from .ocr_009_intelligence_state_projection import project_reasoning_results

OCR_013_BUILD_ID="OCR-013"
OCR_013_REVISION="OCR_013_CONTINUOUS_MARKET_AWARE_REASONING_LOOP_V1"

@dataclass(frozen=True)
class ContinuousReasoningCycleSummary:
    rows_read:int
    market_aware_rows:int
    markets_reasoned:int
    ois_projections:int
    cursor_advanced:bool
    idle:bool

def run_continuous_reasoning_cycle(root=None,limit=50,cursor_path=None,progress=print):
    root=Path(root or Path.cwd()).resolve()
    cp=Path(cursor_path or root/"runtime_state"/"ocr_reasoning_cursor.json")
    cursor=load_reasoning_cursor(cp)
    slice_=read_new_canonical_observations(root,cursor=cursor,limit=limit)
    if not slice_.rows:
        progress("[OCR] idle no_new_observations")
        return ContinuousReasoningCycleSummary(0,0,0,0,False,True)
    aware=join_rows_to_umd_context(slice_.rows)
    if not aware:
        raise RuntimeError("New observations found but none resolved to market identity")
    reasoning=reason_over_market_aware_observations(aware)
    projections=project_reasoning_results(reasoning)
    if len(projections)!=len(reasoning):
        raise RuntimeError("OIS projection count mismatch")
    order_column,order_value,observation_id=cursor_values_from_last_row(slice_)
    new_cursor=advance_reasoning_cursor(cursor,order_column,order_value,observation_id,len(slice_.rows))
    save_reasoning_cursor(cp,new_cursor)
    progress(f"[OCR] rows={len(slice_.rows)} market_aware={len(aware)} markets_reasoned={len(reasoning)} ois_projections={len(projections)}")
    progress(f"[OCR] cursor={order_column}:{order_value}:{observation_id}")
    return ContinuousReasoningCycleSummary(len(slice_.rows),len(aware),len(reasoning),len(projections),True,False)

def verify_ocr_013_continuous_market_aware_reasoning_loop():
    return callable(run_continuous_reasoning_cycle)
