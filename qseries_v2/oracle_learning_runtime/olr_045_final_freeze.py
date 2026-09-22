from __future__ import annotations
from dataclasses import dataclass,asdict
from hashlib import sha256
from pathlib import Path
import json

from .olr_044_final_production_certification_gate import certify_olr_final_production_boundary

OLR_045_BUILD_ID="OLR-045"
OLR_045_REVISION="OLR_045_FINAL_FREEZE_V1"
OLR_FREEZE_POLICY="DEFECT_CORRECTIONS_ONLY"

@dataclass(frozen=True)
class OLRFreezeManifest:
    subsystem:str
    frozen_start:str
    frozen_end:str
    policy:str
    execution_authority:bool
    terminal_dependency:str
    manifest_hash:str

def build_olr_freeze_manifest():
    cert=certify_olr_final_production_boundary()
    payload={
        "subsystem":"Oracle Learning Runtime",
        "frozen_start":"OLR-001",
        "frozen_end":"OLR-045",
        "policy":OLR_FREEZE_POLICY,
        "execution_authority":False,
        "terminal_dependency":"NONE",
        "certified_runtime_role":cert.runtime_role,
    }
    h=sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return OLRFreezeManifest(
        payload["subsystem"],payload["frozen_start"],payload["frozen_end"],
        payload["policy"],False,"NONE",h
    )

def verify_olr_045_final_freeze():
    x=build_olr_freeze_manifest()
    return x.frozen_end=="OLR-045" and x.policy=="DEFECT_CORRECTIONS_ONLY" and not x.execution_authority and len(x.manifest_hash)==64
