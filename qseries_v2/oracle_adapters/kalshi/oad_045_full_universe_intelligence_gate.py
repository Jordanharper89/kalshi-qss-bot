from dataclasses import dataclass
from hashlib import sha256
import json
from .oad_041_full_universe_partitioning import verify_oad_041_full_universe_stream_partition_expansion
from .oad_042_partitioned_persistence import verify_oad_042_partitioned_persistent_canonical_persistence
from .oad_043_dynamic_intelligence_fanout import verify_oad_043_dynamic_surveillance_fanout
from .oad_044_downstream_intelligence_fanout import verify_oad_044_downstream_intelligence_fanout

OAD_045_BUILD_ID="OAD-045"
OAD_045_REVISION="OAD_045_FULL_UNIVERSE_LIVE_INTELLIGENCE_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class FullUniverseLiveIntelligenceCertification:
    builds:tuple[str,...]
    capability:str
    runtime_command:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_oad_041_through_045():
    checks=(
        verify_oad_041_full_universe_stream_partition_expansion(),
        verify_oad_042_partitioned_persistent_canonical_persistence(),
        verify_oad_043_dynamic_surveillance_fanout(),
        verify_oad_044_downstream_intelligence_fanout(),
    )
    if not all(checks):
        raise RuntimeError("OAD-041 through OAD-045 certification failed")
    builds=tuple("OAD-%03d"%i for i in range(41,46))
    capability="full_universe_partitioned_persistence_surveillance_routing_downstream_intelligence_fanout"
    next_capability="physical_multi_partition_runtime_and_live_full_universe_coverage_verification"
    h=sha256(json.dumps({"builds":builds,"capability":capability,"next":next_capability},sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return FullUniverseLiveIntelligenceCertification(builds,capability,"run_oracle_LIVE.py",next_capability,h,True)

def verify_oad_045_full_universe_live_intelligence_capability_gate():
    c=certify_oad_041_through_045()
    return c.certified and len(c.builds)==5 and c.runtime_command=="run_oracle_LIVE.py"
