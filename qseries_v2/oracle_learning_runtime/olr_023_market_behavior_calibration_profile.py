from __future__ import annotations
from dataclasses import dataclass
from statistics import mean
from .olr_022_outcome_calibration_record import OutcomeCalibrationRecord

OLR_023_BUILD_ID="OLR-023"
OLR_023_REVISION="OLR_023_MARKET_BEHAVIOR_CALIBRATION_PROFILE_V1"

@dataclass(frozen=True)
class MarketBehaviorCalibrationProfile:
    market_ticker:str
    samples:int
    mean_probability:float
    empirical_yes_rate:float
    mean_brier_score:float
    mean_absolute_error:float
    calibration_bias:float
    reliability_weight:float
    advisory_only:bool=True
    execution_authority:bool=False

def build_market_behavior_calibration_profile(market_ticker:str,records):
    rows=tuple(r for r in records if isinstance(r,OutcomeCalibrationRecord) and r.market_ticker==market_ticker)
    if not rows:
        return MarketBehaviorCalibrationProfile(str(market_ticker),0,.5,.5,.25,.5,0.0,0.0,True,False)
    mp=mean(r.probability for r in rows)
    yr=mean(r.outcome for r in rows)
    bs=mean(r.brier_score for r in rows)
    ae=mean(r.absolute_error for r in rows)
    weight=min(1.0,len(rows)/50.0)
    return MarketBehaviorCalibrationProfile(
        str(market_ticker),len(rows),mp,yr,bs,ae,yr-mp,weight,True,False
    )

def verify_olr_023_market_behavior_calibration_profile():
    r1=OutcomeCalibrationRecord("KX",.7,1,.09,.3,"p",True,False)
    r2=OutcomeCalibrationRecord("KX",.6,0,.36,.6,"p",True,False)
    x=build_market_behavior_calibration_profile("KX",(r1,r2))
    return x.samples==2 and x.advisory_only and not x.execution_authority
