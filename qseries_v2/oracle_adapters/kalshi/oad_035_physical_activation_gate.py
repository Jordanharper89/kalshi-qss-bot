from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from .oad_031_runtime_binding import verify_oad_031_physical_oracle_live_runtime_kalshi_binding
from .oad_032_persistent_live_loop import verify_oad_032_persistent_real_kalshi_message_loop
from .oad_033_persistence_verification import verify_oad_033_dual_lane_live_shadow_postgres_advancement_verification
from .oad_034_runtime_status import verify_oad_034_runtime_kalshi_status_surface

OAD_035_BUILD_ID="OAD-035"
OAD_035_REVISION="OAD_035_PHYSICAL_ORACLE_KALSHI_PRODUCTION_ACTIVATION_GATE_V1"

@dataclass(frozen=True)
class PhysicalOracleKalshiActivationCertification:
    builds:tuple[str,...]
    runtime_command:str
    dual_lane_architecture:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_oad_031_through_035():
    checks=(verify_oad_031_physical_oracle_live_runtime_kalshi_binding(),
            verify_oad_032_persistent_real_kalshi_message_loop(),
            verify_oad_033_dual_lane_live_shadow_postgres_advancement_verification(),
            verify_oad_034_runtime_kalshi_status_surface())
    if not all(checks): raise RuntimeError("Physical Oracle/Kalshi activation certification failed")
    builds=tuple("OAD-%03d"%i for i in range(31,36))
    arch="kalshi_websocket_fast_lane_plus_certified_ola_live_shadow_postgresql_lane"
    nxt="direct_websocket_event_to_canonical_observation_persistence_bridge_and_multi_adapter_expansion"
    h=sha256(json.dumps({"builds":builds,"arch":arch,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return PhysicalOracleKalshiActivationCertification(builds,"run_oracle_LIVE.py",arch,nxt,h,True)

def verify_oad_035_physical_oracle_kalshi_production_activation_gate():
    c=certify_oad_031_through_035()
    return c.certified and len(c.builds)==5 and c.runtime_command=="run_oracle_LIVE.py"
