from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OAD_004_BUILD_ID = "OAD-004"
OAD_004_REVISION = "OAD_004_ADAPTER_LIFECYCLE_HEALTH_CONTRACT_V1"

ADAPTER_STATES = (
    "REGISTERED",
    "CONNECTING",
    "CONNECTED",
    "UNIVERSE_READY",
    "STREAM_READY",
    "LIVE",
    "DEGRADED",
    "RECOVERING",
    "DOWN",
    "STOPPED",
)

@dataclass(frozen=True)
class AdapterLifecycleState:
    adapter_id: str
    state: str
    connected: bool
    universe_ready: bool
    stream_ready: bool
    lag_seconds: float

@dataclass(frozen=True)
class AdapterHealthDecision:
    status: str
    production_ready: bool
    recovery_required: bool
    reason: str

def build_adapter_lifecycle_state(adapter_id, state, connected, universe_ready, stream_ready, lag_seconds):
    if not adapter_id or state not in ADAPTER_STATES or float(lag_seconds) < 0:
        raise ValueError("valid adapter lifecycle state required")
    return AdapterLifecycleState(
        adapter_id, state, bool(connected), bool(universe_ready), bool(stream_ready), float(lag_seconds)
    )

def evaluate_adapter_health(state, max_lag_seconds=5.0):
    if not isinstance(state, AdapterLifecycleState):
        raise ValueError("certified lifecycle state required")

    if state.state in ("DOWN","STOPPED"):
        return AdapterHealthDecision("DOWN", False, True, "adapter_down")
    if not state.connected:
        return AdapterHealthDecision("DEGRADED", False, True, "not_connected")
    if not state.universe_ready:
        return AdapterHealthDecision("DEGRADED", False, True, "universe_not_ready")
    if not state.stream_ready:
        return AdapterHealthDecision("DEGRADED", False, True, "stream_not_ready")
    if state.lag_seconds > max_lag_seconds:
        return AdapterHealthDecision("LAGGING", False, False, "lag_exceeded")
    if state.state == "LIVE":
        return AdapterHealthDecision("READY", True, False, "ready")
    return AdapterHealthDecision("DEGRADED", False, False, "not_live")

def build_oad_004_certification_manifest():
    return MappingProxyType({
        "build_id": OAD_004_BUILD_ID,
        "revision": OAD_004_REVISION,
        "states": ADAPTER_STATES,
        "health_contract": True,
        "execution": False,
    })

def verify_oad_004_adapter_lifecycle_health_contract():
    x = build_adapter_lifecycle_state("a","LIVE",True,True,True,.1)
    h = evaluate_adapter_health(x)
    return h.status=="READY" and h.production_ready and not h.recovery_required
