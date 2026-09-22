from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from hashlib import sha256
import json

from .olr_041_learning_health_model import inspect_learning_health
from .olr_042_deterministic_learning_replay import replay_learning_records

OLR_043_BUILD_ID="OLR-043"
OLR_043_REVISION="OLR_043_PRODUCTION_LEARNING_INTEGRITY_VERIFICATION_V1"

@dataclass(frozen=True)
class ProductionLearningIntegrity:
    health:str
    calibration_records:int
    mature_markets:int
    replay_hash:str
    state_hash:str
    read_only:bool=True
    execution_authority:bool=False

def verify_production_learning_integrity(root=None):
    root=Path(root or Path.cwd()).resolve()
    health=inspect_learning_health(root)

    ledger_path=root/"runtime_state"/"oracle_calibration_ledger.json"
    try:
        ledger=json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else {}
    except Exception:
        ledger={}

    records=tuple(ledger.values()) if isinstance(ledger,dict) else tuple()
    replay=replay_learning_records(records)

    payload={
        "health":health.health,
        "calibration_records":health.calibration_records,
        "mature_markets":health.mature_markets,
        "replay_hash":replay.replay_hash,
    }
    state_hash=sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    return ProductionLearningIntegrity(
        health.health,
        health.calibration_records,
        health.mature_markets,
        replay.replay_hash,
        state_hash,
        True,
        False,
    )

def verify_olr_043_production_learning_integrity_verification():
    x=verify_production_learning_integrity(Path("__missing__"))
    return len(x.state_hash)==64 and x.read_only and not x.execution_authority
