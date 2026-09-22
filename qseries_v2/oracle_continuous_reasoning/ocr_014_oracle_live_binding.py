from __future__ import annotations
from dataclasses import dataclass

OCR_014_BUILD_ID="OCR-014"
OCR_014_REVISION="OCR_014_ORACLE_LIVE_REASONING_CHILD_BINDING_V1"

@dataclass(frozen=True)
class OracleLiveReasoningBinding:
    reasoning_child:str
    cursor_state_path:str
    supervised:bool
    terminal_dependency:bool=False
    execution_authority:bool=False

def build_oracle_live_reasoning_binding():
    return OracleLiveReasoningBinding(
        "run_ocr_013_continuous_reasoning_runtime.py",
        "runtime_state/ocr_reasoning_cursor.json",
        True,
        False,
        False,
    )

def verify_ocr_014_oracle_live_reasoning_child_binding():
    b=build_oracle_live_reasoning_binding()
    return b.supervised and not b.terminal_dependency and not b.execution_authority
