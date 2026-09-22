from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oad_006_kalshi_foundation import verify_oad_006_kalshi_adapter_foundation
from .oad_007_transport_auth import verify_oad_007_kalshi_transport_auth_boundary
from .oad_008_full_universe_discovery import verify_oad_008_kalshi_full_universe_discovery
from .oad_009_universe_reconciliation import verify_oad_009_kalshi_universe_reconciliation_lifecycle

OAD_010_BUILD_ID="OAD-010"
OAD_010_REVISION="OAD_010_KALSHI_FULL_UNIVERSE_DISCOVERY_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class KalshiDiscoveryCapabilityCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_oad_006_through_010():
    checks=(verify_oad_006_kalshi_adapter_foundation(),verify_oad_007_kalshi_transport_auth_boundary(),
            verify_oad_008_kalshi_full_universe_discovery(),verify_oad_009_kalshi_universe_reconciliation_lifecycle())
    if not all(checks): raise RuntimeError("Kalshi discovery capability certification failed")
    builds=tuple("OAD-%03d"%i for i in range(6,11))
    capability="kalshi_adapter_foundation_transport_auth_full_universe_discovery_reconciliation_lifecycle"
    nxt="kalshi_low_latency_websocket_market_data_streaming_subscription_partitioning_sequence_integrity"
    h=sha256(json.dumps({"builds":builds,"capability":capability,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiDiscoveryCapabilityCertification(builds,capability,nxt,h,True)

def build_oad_010_certification_manifest():
    c=certify_oad_006_through_010()
    return MappingProxyType({"build_id":OAD_010_BUILD_ID,"revision":OAD_010_REVISION,
        "capability":c.capability,"next_capability":c.next_capability,"read_only":True,"execution":False})

def verify_oad_010_kalshi_full_universe_discovery_capability_gate():
    c=certify_oad_006_through_010()
    return c.certified and len(c.builds)==5 and c.next_capability=="kalshi_low_latency_websocket_market_data_streaming_subscription_partitioning_sequence_integrity"
