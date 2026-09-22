from dataclasses import dataclass
from types import MappingProxyType

OAD_017_BUILD_ID="OAD-017"
OAD_017_REVISION="OAD_017_KALSHI_KEEPALIVE_LIVENESS_SUPERVISION_V1"

@dataclass(frozen=True)
class KeepaliveState:
    last_server_ping_ns:int
    last_client_pong_ns:int
    now_ns:int
    ping_interval_seconds:float
    pong_required:bool
    healthy:bool

def evaluate_keepalive(last_server_ping_ns,last_client_pong_ns,now_ns,ping_interval_seconds=10.0,grace_multiplier=2.5):
    vals=(int(last_server_ping_ns),int(last_client_pong_ns),int(now_ns))
    if any(x<0 for x in vals) or float(ping_interval_seconds)<=0 or float(grace_multiplier)<=1:
        raise ValueError("valid keepalive timing required")
    age_s=(vals[2]-vals[0])/1_000_000_000
    pong_ok=vals[1]>=vals[0]
    healthy=age_s<=float(ping_interval_seconds)*float(grace_multiplier) and pong_ok
    return KeepaliveState(vals[0],vals[1],vals[2],float(ping_interval_seconds),True,healthy)

def should_reconnect_keepalive(state):
    if not isinstance(state,KeepaliveState): raise ValueError("certified keepalive state required")
    return not state.healthy

def build_oad_017_certification_manifest():
    return MappingProxyType({"build_id":OAD_017_BUILD_ID,"revision":OAD_017_REVISION,
        "server_ping_interval_seconds":10.0,"pong_required":True,"reconnect_on_liveness_failure":True})

def verify_oad_017_kalshi_keepalive_liveness_supervision():
    good=evaluate_keepalive(0,1,10_000_000_000)
    bad=evaluate_keepalive(0,0,30_000_000_000)
    return good.healthy and should_reconnect_keepalive(bad)
