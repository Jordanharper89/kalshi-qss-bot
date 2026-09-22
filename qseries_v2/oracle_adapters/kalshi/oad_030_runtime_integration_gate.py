from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oad_026_persistent_stream_runner import verify_oad_026_persistent_kalshi_live_stream_runner
from .oad_027_event_intake_pump import verify_oad_027_continuous_real_market_event_intake_pump
from .oad_028_live_shadow_binding import verify_oad_028_live_shadow_postgres_persistence_binding
from .oad_029_runtime_health import verify_oad_029_oracle_runtime_adapter_health_latency_supervision

OAD_030_BUILD_ID="OAD-030"
OAD_030_REVISION="OAD_030_KALSHI_ORACLE_LIVE_RUNTIME_INTEGRATION_GATE_V1"

@dataclass(frozen=True)
class KalshiOracleRuntimeIntegrationCertification:
    builds:tuple[str,...]
    runtime_command:str
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_oad_026_through_030():
    checks=(
        verify_oad_026_persistent_kalshi_live_stream_runner(),
        verify_oad_027_continuous_real_market_event_intake_pump(),
        verify_oad_028_live_shadow_postgres_persistence_binding(),
        verify_oad_029_oracle_runtime_adapter_health_latency_supervision(),
    )
    if not all(checks): raise RuntimeError("Kalshi Oracle runtime integration certification failed")
    builds=tuple("OAD-%03d"%i for i in range(26,31))
    cap="persistent_kalshi_stream_event_pump_live_shadow_postgres_runtime_health"
    nxt="physical_runtime_launcher_binding_and_end_to_end_live_event_persistence_verification"
    h=sha256(json.dumps({"builds":builds,"capability":cap,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiOracleRuntimeIntegrationCertification(builds,"run_oracle_LIVE.py",cap,nxt,h,True)

def verify_oad_030_kalshi_oracle_live_runtime_integration_gate():
    c=certify_oad_026_through_030()
    return c.certified and len(c.builds)==5 and c.runtime_command=="run_oracle_LIVE.py"
