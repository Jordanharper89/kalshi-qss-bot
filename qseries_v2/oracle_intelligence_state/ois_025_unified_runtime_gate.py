from dataclasses import dataclass
from .ois_021_unified_runtime import verify_ois_021_unified_oracle_runtime_composition
from .ois_022_pipeline_orchestrator import verify_ois_022_continuous_pipeline_cycle_orchestrator
from .ois_023_runtime_recovery import verify_ois_023_runtime_checkpoint_crash_recovery_coordination
from .ois_024_service_activation import verify_ois_024_24x7_service_activation_health_boundary

OIS_025_BUILD_ID="OIS-025"
OIS_025_REVISION="OIS_025_UNIFIED_24X7_ORACLE_RUNTIME_CERTIFICATION_GATE_V1"

@dataclass(frozen=True)
class UnifiedOracleRuntimeCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certified:bool=True

def certify_ois_021_through_025():
    checks=(
        verify_ois_021_unified_oracle_runtime_composition(),
        verify_ois_022_continuous_pipeline_cycle_orchestrator(),
        verify_ois_023_runtime_checkpoint_crash_recovery_coordination(),
        verify_ois_024_24x7_service_activation_health_boundary(),
    )
    if not all(checks): raise RuntimeError("unified Oracle Runtime certification failed")
    return UnifiedOracleRuntimeCertification(
        tuple("OIS-%03d"%i for i in range(21,26)),
        "unified_24x7_oracle_runtime_wiring_and_service_activation",
        "universal_venue_surveillance_and_opportunity_intelligence",
        True,
    )

def verify_ois_025_unified_24x7_oracle_runtime_certification_gate():
    c=certify_ois_021_through_025()
    return c.certified and len(c.builds)==5 and c.next_capability=="universal_venue_surveillance_and_opportunity_intelligence"
