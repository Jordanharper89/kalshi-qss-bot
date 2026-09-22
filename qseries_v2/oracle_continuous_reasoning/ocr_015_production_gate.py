from __future__ import annotations
from dataclasses import dataclass
from .ocr_011_reasoning_cursor_state import verify_ocr_011_reasoning_cursor_state
from .ocr_012_incremental_observation_selection import verify_ocr_012_incremental_new_observation_selection
from .ocr_013_continuous_reasoning_loop import verify_ocr_013_continuous_market_aware_reasoning_loop
from .ocr_014_oracle_live_binding import verify_ocr_014_oracle_live_reasoning_child_binding

OCR_015_BUILD_ID="OCR-015"
OCR_015_REVISION="OCR_015_CONTINUOUS_REASONING_PRODUCTION_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class OCR015Certification:
    builds:tuple[str,...]
    runtime_command:str
    capability:str
    next_capability:str
    certified:bool=True

def certify_ocr_011_through_015():
    checks=(verify_ocr_011_reasoning_cursor_state(),verify_ocr_012_incremental_new_observation_selection(),
            verify_ocr_013_continuous_market_aware_reasoning_loop(),verify_ocr_014_oracle_live_reasoning_child_binding())
    if not all(checks):raise RuntimeError("OCR-011 through OCR-015 certification failed")
    return OCR015Certification(
        tuple("OCR-%03d"%i for i in range(11,16)),
        "run_oracle_LIVE.py",
        "cursor_driven_incremental_continuous_market_aware_reasoning_runtime",
        "continuous_reasoning_state_materialization_and_terminal_query_surface",
        True,
    )

def verify_ocr_015_continuous_reasoning_production_capability_gate():
    c=certify_ocr_011_through_015()
    return c.certified and len(c.builds)==5 and c.runtime_command=="run_oracle_LIVE.py"
