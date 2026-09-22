from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_008_source_calibration_profile import SourceCalibrationProfile
OCL_009_BUILD_ID="OCL-009";OCL_009_REVISION="OCL_009_LEARNED_SOURCE_STATE_SNAPSHOT_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class LearnedSourceStateSnapshot:
 profiles:tuple[SourceCalibrationProfile,...]; snapshot_hash:str
def build_learned_source_state_snapshot(profiles):
 rows=tuple(sorted(profiles,key=lambda x:x.source_id))
 if len({x.source_id for x in rows})!=len(rows):raise ValueError("duplicate source profile")
 raw=[{"source_id":x.source_id,"reliability":x.reliability,"mean_brier":x.mean_brier,"evidence_count":x.evidence_count,"confidence_weight":x.confidence_weight} for x in rows]
 return LearnedSourceStateSnapshot(rows,_h(raw))
def build_ocl_009_certification_manifest():return MappingProxyType({"build_id":OCL_009_BUILD_ID,"revision":OCL_009_REVISION,"snapshot":"deterministic_read_model","execution":False,"publication":False})
def verify_ocl_009_learned_source_state_snapshot():
 from .ocl_008_source_calibration_profile import build_source_calibration_profile
 a=build_source_calibration_profile("a",.8,.1,10);b=build_source_calibration_profile("b",.7,.2,10)
 return build_learned_source_state_snapshot((b,a)).snapshot_hash==build_learned_source_state_snapshot((a,b)).snapshot_hash
