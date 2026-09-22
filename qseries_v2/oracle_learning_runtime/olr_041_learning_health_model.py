from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

OLR_041_BUILD_ID="OLR-041"
OLR_041_REVISION="OLR_041_LEARNING_HEALTH_MODEL_V1"

@dataclass(frozen=True)
class LearningHealthSnapshot:
    learning_state_present:bool
    calibration_state_present:bool
    calibration_ledger_present:bool
    feedback_snapshot_present:bool
    learning_cycles:int
    outcomes_learned:int
    calibration_cycles:int
    calibration_records:int
    mature_markets:int
    health:str
    reason:str
    execution_authority:bool=False

def _read(path):
    p=Path(path)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def inspect_learning_health(root=None):
    root=Path(root or Path.cwd()).resolve()
    learning_path=root/"runtime_state"/"oracle_learning_runtime_state.json"
    calibration_state_path=root/"runtime_state"/"oracle_calibration_ingestion_state.json"
    ledger_path=root/"runtime_state"/"oracle_calibration_ledger.json"
    feedback_path=root/"runtime_state"/"oracle_live_reasoning_feedback.json"

    learning=_read(learning_path)
    calibration=_read(calibration_state_path)
    ledger=_read(ledger_path)
    feedback=_read(feedback_path)

    learning_present=learning_path.is_file()
    calibration_present=calibration_state_path.is_file()
    ledger_present=ledger_path.is_file()
    feedback_present=feedback_path.is_file()

    learning_cycles=int(learning.get("cycles",0)) if isinstance(learning,dict) else 0
    outcomes_learned=int(learning.get("outcomes_learned",0)) if isinstance(learning,dict) else 0
    calibration_cycles=int(calibration.get("cycles_completed",0)) if isinstance(calibration,dict) else 0
    calibration_records=len(ledger) if isinstance(ledger,dict) else 0
    markets=feedback.get("markets",[]) if isinstance(feedback,dict) else []
    mature_markets=sum(1 for r in markets if isinstance(r,dict) and r.get("mature") is True)

    if not learning_present:
        health="NOT_READY";reason="learning_state_missing"
    elif not calibration_state_path.parent.exists():
        health="DEGRADED";reason="runtime_state_directory_missing"
    elif outcomes_learned==0 and calibration_records==0:
        health="HEALTHY_WAITING_FOR_ELIGIBLE_OUTCOMES";reason="no_eligible_learning_yet"
    elif calibration_records==0:
        health="HEALTHY_LEARNING_NO_CALIBRATION_YET";reason="learning_exists_but_no_defensible_calibration_records"
    elif mature_markets==0:
        health="HEALTHY_ACCUMULATING_HISTORY";reason="calibration_history_not_mature"
    else:
        health="HEALTHY_MATURE";reason="mature_learning_available"

    return LearningHealthSnapshot(
        learning_present,calibration_present,ledger_present,feedback_present,
        learning_cycles,outcomes_learned,calibration_cycles,calibration_records,
        mature_markets,health,reason,False
    )

def verify_olr_041_learning_health_model():
    x=inspect_learning_health(Path("__missing_olr_health_root__"))
    return x.health=="NOT_READY" and x.execution_authority is False
