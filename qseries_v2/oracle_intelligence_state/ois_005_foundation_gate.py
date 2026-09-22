from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ois_001_foundation import verify_ois_001_intelligence_state_foundation
from .ois_002_osr_intake_boundary import verify_ois_002_certified_osr_state_intake_boundary
from .ois_003_canonical_state import verify_ois_003_canonical_intelligence_state_assembly
from .ois_004_query_snapshot import verify_ois_004_read_only_query_snapshot

OIS_005_BUILD_ID="OIS-005"
OIS_005_REVISION="OIS_005_INTELLIGENCE_STATE_FOUNDATION_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class IntelligenceStateFoundationCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_ois_001_through_005():
    checks=(
        verify_ois_001_intelligence_state_foundation(),
        verify_ois_002_certified_osr_state_intake_boundary(),
        verify_ois_003_canonical_intelligence_state_assembly(),
        verify_ois_004_read_only_query_snapshot(),
    )
    if not all(checks):
        raise RuntimeError("OIS foundation capability certification failed")

    builds=tuple("OIS-%03d"%i for i in range(1,6))
    raw={
        "builds":builds,
        "capability":"canonical_oracle_intelligence_state_foundation",
        "next_capability":"continuous_state_update_persistence_and_runtime",
        "certified":True,
    }
    digest=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return IntelligenceStateFoundationCertification(
        builds,raw["capability"],raw["next_capability"],digest
    )

def build_ois_005_certification_manifest():
    c=certify_ois_001_through_005()
    return MappingProxyType({
        "build_id":OIS_005_BUILD_ID,
        "revision":OIS_005_REVISION,
        "capability":c.capability,
        "next_capability":c.next_capability,
        "certified":True,
        "execution":False,
        "publication":False,
    })

def verify_ois_005_intelligence_state_foundation_capability_gate():
    c=certify_ois_001_through_005()
    return c.certified and len(c.builds)==5 and c.next_capability=="continuous_state_update_persistence_and_runtime"
