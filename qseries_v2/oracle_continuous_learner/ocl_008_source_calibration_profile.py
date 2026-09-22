from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
OCL_008_BUILD_ID="OCL-008";OCL_008_REVISION="OCL_008_SOURCE_CALIBRATION_PROFILE_V1"
@dataclass(frozen=True)
class SourceCalibrationProfile:
 source_id:str; reliability:float; mean_brier:float; evidence_count:int; confidence_weight:float
def build_source_calibration_profile(source_id,reliability,mean_brier,evidence_count):
 if not 0<=reliability<=1 or not 0<=mean_brier<=1 or evidence_count<1:raise ValueError("invalid profile evidence")
 weight=reliability*(1-mean_brier)*(evidence_count/(evidence_count+10))
 return SourceCalibrationProfile(source_id,reliability,mean_brier,evidence_count,weight)
def build_ocl_008_certification_manifest():return MappingProxyType({"build_id":OCL_008_BUILD_ID,"revision":OCL_008_REVISION,"combines":"reliability+calibration+evidence_count","decision_authority":False})
def verify_ocl_008_source_calibration_profile():
 p=build_source_calibration_profile("s",.8,.1,20);return 0<p.confidence_weight<1
