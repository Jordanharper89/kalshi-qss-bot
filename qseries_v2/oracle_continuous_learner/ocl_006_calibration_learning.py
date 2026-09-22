from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .ocl_004_learning_event import LearningEvent,verify_learning_event
OCL_006_BUILD_ID="OCL-006";OCL_006_REVISION="OCL_006_PROBABILITY_CALIBRATION_LEARNING_V1"
@dataclass(frozen=True)
class CalibrationObservation:
 event_id:str; forecast_probability:float; outcome:bool; brier_score:float
def learn_calibration(event,probability,outcome):
 if not verify_learning_event(event):raise ValueError("invalid learning event")
 p=float(probability)
 if p<0 or p>1:raise ValueError("probability outside [0,1]")
 y=1.0 if outcome else 0.0
 return CalibrationObservation(event.event_id,p,bool(outcome),(p-y)**2)
def calibration_mean(rows):
 rows=tuple(rows)
 if not rows:raise ValueError("calibration evidence required")
 return sum(x.brier_score for x in rows)/len(rows)
def build_ocl_006_certification_manifest():return MappingProxyType({"build_id":OCL_006_BUILD_ID,"revision":OCL_006_REVISION,"metric":"brier_score","execution":False,"upstream_mutation":False})
def verify_ocl_006_probability_calibration_learning():
 class E:pass
 # verifier uses a structurally valid real event
 from .ocl_003_outcome_observation import build_outcome_observation
 from .ocl_004_learning_event import assemble_learning_event
 o=build_outcome_observation("m","settlement",1,"t","s","a"*64);e=assemble_learning_event("m","b"*64,"c"*64,o)
 return learn_calibration(e,.8,True).brier_score==(.8-1.0)**2
