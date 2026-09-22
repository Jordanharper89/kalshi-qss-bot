from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

OLR_036_BUILD_ID="OLR-036"
OLR_036_REVISION="OLR_036_LIVE_FEEDBACK_READ_MODEL_V1"

@dataclass(frozen=True)
class LiveCalibrationFeedback:
    market_ticker:str
    samples:int
    calibration_bias:float
    mean_brier_score:float
    reliability_weight:float
    mature:bool
    behavior_class:str
    stable:bool
    execution_authority:bool=False

def load_live_feedback_snapshot(root=None):
    root=Path(root or Path.cwd()).resolve()
    path=root/"runtime_state"/"oracle_live_reasoning_feedback.json"
    if not path.is_file():
        return {}
    data=json.loads(path.read_text(encoding="utf-8"))
    out={}
    for row in data.get("markets",[]):
        if not isinstance(row,dict):continue
        ticker=str(row.get("market_ticker") or "")
        if not ticker:continue
        out[ticker]=LiveCalibrationFeedback(
            ticker,
            int(row.get("samples",0)),
            float(row.get("calibration_bias",0.0)),
            float(row.get("mean_brier_score",0.25)),
            float(row.get("reliability_weight",0.0)),
            bool(row.get("mature",False)),
            str(row.get("behavior_class") or "insufficient_history"),
            bool(row.get("stable",False)),
            False,
        )
    return out

def verify_olr_036_live_feedback_read_model():
    return load_live_feedback_snapshot(Path("__missing__"))=={}
