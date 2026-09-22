from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oad_011_websocket_foundation import verify_oad_011_kalshi_websocket_market_data_foundation
from .oad_012_subscription_partitioning import verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage
from .oad_013_market_data_normalization import verify_oad_013_kalshi_orderbook_trade_ticker_normalization
from .oad_014_sequence_integrity import verify_oad_014_kalshi_sequence_integrity_gap_detection_resync

OAD_015_BUILD_ID="OAD-015"
OAD_015_REVISION="OAD_015_KALSHI_LOW_LATENCY_STREAMING_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class KalshiStreamingCapabilityCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_oad_011_through_015():
    checks=(verify_oad_011_kalshi_websocket_market_data_foundation(),
            verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage(),
            verify_oad_013_kalshi_orderbook_trade_ticker_normalization(),
            verify_oad_014_kalshi_sequence_integrity_gap_detection_resync())
    if not all(checks): raise RuntimeError("Kalshi low-latency streaming certification failed")
    builds=tuple("OAD-%03d"%i for i in range(11,16))
    cap="kalshi_authenticated_websocket_subscription_partitioning_market_data_normalization_sequence_integrity"
    nxt="kalshi_reconnect_resubscribe_keepalive_latency_telemetry_hot_active_routing_live_runtime_binding"
    h=sha256(json.dumps({"builds":builds,"capability":cap,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiStreamingCapabilityCertification(builds,cap,nxt,h,True)

def build_oad_015_certification_manifest():
    c=certify_oad_011_through_015()
    return MappingProxyType({"build_id":OAD_015_BUILD_ID,"revision":OAD_015_REVISION,
        "capability":c.capability,"next_capability":c.next_capability,"read_only":True,"execution":False})

def verify_oad_015_kalshi_low_latency_streaming_capability_gate():
    c=certify_oad_011_through_015()
    return c.certified and len(c.builds)==5 and c.next_capability=="kalshi_reconnect_resubscribe_keepalive_latency_telemetry_hot_active_routing_live_runtime_binding"
