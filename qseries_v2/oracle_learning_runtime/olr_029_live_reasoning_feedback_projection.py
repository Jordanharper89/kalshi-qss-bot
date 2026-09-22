from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import json,os
from .olr_026_durable_calibration_ledger import load_calibration_ledger
from .olr_027_accumulated_calibration_state import accumulate_market_calibration
from .olr_028_market_behavior_history import classify_market_behavior

OLR_029_BUILD_ID="OLR-029"
OLR_029_REVISION="OLR_029_LIVE_REASONING_FEEDBACK_PROJECTION_V1"

@dataclass(frozen=True)
class LiveReasoningFeedbackProjection:
    markets:int
    calibration_records:int
    mature_markets:int
    output_path:str
    execution_authority:bool=False

def materialize_live_reasoning_feedback(root=None,output_path=None,min_samples=5):
    root=Path(root or Path.cwd()).resolve()
    ledger_path=root/"runtime_state"/"oracle_calibration_ledger.json"
    ledger=load_calibration_ledger(ledger_path)
    records=tuple(ledger.values())
    tickers=sorted({r.market_ticker for r in records})
    rows=[]
    mature=0
    for ticker in tickers:
        state=accumulate_market_calibration(records,ticker,min_samples=min_samples)
        hist=classify_market_behavior(state)
        if state.mature:mature+=1
        rows.append({
            "market_ticker":ticker,
            "samples":state.samples,
            "mean_probability":state.mean_probability,
            "empirical_yes_rate":state.empirical_yes_rate,
            "mean_brier_score":state.mean_brier_score,
            "calibration_bias":state.calibration_bias,
            "reliability_weight":state.reliability_weight,
            "mature":state.mature,
            "behavior_class":hist.behavior_class,
            "stable":hist.stable,
            "execution_authority":False,
        })
    payload={
        "revision":OLR_029_REVISION,
        "calibration_records":len(records),
        "markets":rows,
        "execution_authority":False,
    }
    path=Path(output_path or root/"runtime_state"/"oracle_live_reasoning_feedback.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n")
    os.replace(tmp,path)
    return LiveReasoningFeedbackProjection(len(rows),len(records),mature,str(path.relative_to(root)),False)

def verify_olr_029_live_reasoning_feedback_projection():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        x=materialize_live_reasoning_feedback(Path(d))
        return x.markets==0 and x.calibration_records==0 and not x.execution_authority
