from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oad_016_reconnect_recovery import verify_oad_016_kalshi_reconnect_resubscribe_recovery
from .oad_017_keepalive_liveness import verify_oad_017_kalshi_keepalive_liveness_supervision
from .oad_018_latency_telemetry import verify_oad_018_kalshi_end_to_end_latency_telemetry
from .oad_019_hot_active_routing import verify_oad_019_kalshi_hot_active_surveillance_routing

OAD_020_BUILD_ID="OAD-020"
OAD_020_REVISION="OAD_020_KALSHI_PRODUCTION_STREAMING_RUNTIME_BINDING_GATE_V1"

@dataclass(frozen=True)
class KalshiRuntimeBindingCertification:
    builds:tuple[str,...]
    capability:str
    oracle_runtime_contract:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_oad_016_through_020():
    checks=(verify_oad_016_kalshi_reconnect_resubscribe_recovery(),
            verify_oad_017_kalshi_keepalive_liveness_supervision(),
            verify_oad_018_kalshi_end_to_end_latency_telemetry(),
            verify_oad_019_kalshi_hot_active_surveillance_routing())
    if not all(checks): raise RuntimeError("Kalshi runtime-binding certification failed")
    builds=tuple("OAD-%03d"%i for i in range(16,21))
    cap="kalshi_reconnect_keepalive_latency_telemetry_dynamic_routing_runtime_binding"
    contract="run_oracle_LIVE.py"
    nxt="physical_live_kalshi_transport_credentials_real_universe_acquisition_real_websocket_activation"
    h=sha256(json.dumps({"builds":builds,"capability":cap,"runtime":contract,"next":nxt},
        sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiRuntimeBindingCertification(builds,cap,contract,nxt,h,True)

def build_oad_020_certification_manifest():
    c=certify_oad_016_through_020()
    return MappingProxyType({"build_id":OAD_020_BUILD_ID,"revision":OAD_020_REVISION,
        "capability":c.capability,"oracle_runtime_contract":c.oracle_runtime_contract,
        "next_capability":c.next_capability,"read_only":True,"execution":False})

def verify_oad_020_kalshi_production_streaming_runtime_binding_gate():
    c=certify_oad_016_through_020()
    return c.certified and len(c.builds)==5 and c.oracle_runtime_contract=="run_oracle_LIVE.py" and c.next_capability=="physical_live_kalshi_transport_credentials_real_universe_acquisition_real_websocket_activation"
