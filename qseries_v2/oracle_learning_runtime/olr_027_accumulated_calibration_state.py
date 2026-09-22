from __future__ import annotations
from dataclasses import dataclass
from statistics import mean
from .olr_026_durable_calibration_ledger import DurableCalibrationRecord

OLR_027_BUILD_ID="OLR-027"
OLR_027_REVISION="OLR_027_ACCUMULATED_CALIBRATION_STATE_V1"

@dataclass(frozen=True)
class AccumulatedCalibrationState:
    market_ticker:str
    samples:int
    mean_probability:float
    empirical_yes_rate:float
    mean_brier_score:float
    mean_absolute_error:float
    calibration_bias:float
    reliability_weight:float
    mature:bool
    execution_authority:bool=False

def accumulate_market_calibration(records,market_ticker,min_samples=5):
    rows=tuple(r for r in records if isinstance(r,DurableCalibrationRecord) and r.market_ticker==market_ticker)
    if not rows:
        return AccumulatedCalibrationState(str(market_ticker),0,.5,.5,.25,.5,0.0,0.0,False,False)
    mp=mean(r.probability for r in rows)
    yr=mean(r.outcome for r in rows)
    bs=mean(r.brier_score for r in rows)
    ae=mean(r.absolute_error for r in rows)
    weight=min(1.0,len(rows)/50.0)
    return AccumulatedCalibrationState(
        str(market_ticker),len(rows),mp,yr,bs,ae,yr-mp,weight,
        len(rows)>=int(min_samples),False
    )

def verify_olr_027_accumulated_calibration_state():
    rows=tuple(DurableCalibrationRecord(str(i),"KX",.6,1,.16,.4,"p","o","s") for i in range(5))
    x=accumulate_market_calibration(rows,"KX",5)
    return x.samples==5 and x.mature and not x.execution_authority
