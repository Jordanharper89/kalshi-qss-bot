from dataclasses import dataclass
from .ois_046_runtime_state import verify_ois_046_oracle_live_runtime_state_model
from .ois_047_runtime_activation import verify_ois_047_oracle_live_runtime_activation_controller
from .ois_048_service_health_aggregation import verify_ois_048_runtime_service_registry_health_aggregation
from .ois_049_runtime_status_read_model import verify_ois_049_oracle_runtime_status_read_model

OIS_050_BUILD_ID="OIS-050"
OIS_050_REVISION="OIS_050_ORACLE_LIVE_RUNTIME_ACTIVATION_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class OracleLiveRuntimeActivationCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certified:bool=True

def certify_ois_046_through_050():
    checks=(
        verify_ois_046_oracle_live_runtime_state_model(),
        verify_ois_047_oracle_live_runtime_activation_controller(),
        verify_ois_048_runtime_service_registry_health_aggregation(),
        verify_ois_049_oracle_runtime_status_read_model(),
    )
    if not all(checks):
        raise RuntimeError("Oracle Live Runtime activation capability certification failed")
    return OracleLiveRuntimeActivationCertification(
        tuple("OIS-%03d"%i for i in range(46,51)),
        "oracle_live_runtime_state_activation_service_health_and_status_read_model",
        "oracle_live_runtime_launcher_supervision_and_final_ois_certification",
        True,
    )

def verify_ois_050_oracle_live_runtime_activation_capability_gate():
    c=certify_ois_046_through_050()
    return c.certified and len(c.builds)==5 and c.next_capability=="oracle_live_runtime_launcher_supervision_and_final_ois_certification"
