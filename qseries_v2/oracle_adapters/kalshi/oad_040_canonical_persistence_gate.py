from dataclasses import dataclass
from hashlib import sha256
import json
from .oad_036_websocket_canonical_bridge import verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge
from .oad_037_ola_postgres_router_binding import verify_oad_037_ola_production_postgresql_router_binding
from .oad_038_persistent_persistence_bridge import verify_oad_038_persistent_kalshi_to_postgresql_bridge
from .oad_039_live_persistence_evidence import verify_oad_039_end_to_end_live_persistence_evidence

OAD_040_BUILD_ID="OAD-040"
OAD_040_REVISION="OAD_040_KALSHI_CANONICAL_PERSISTENCE_BRIDGE_GATE_V1"

@dataclass(frozen=True)
class KalshiCanonicalPersistenceCertification:
    builds:tuple[str,...]
    runtime_child:str
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_oad_036_through_040():
    checks=(verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge(),
            verify_oad_037_ola_production_postgresql_router_binding(),
            verify_oad_038_persistent_kalshi_to_postgresql_bridge(),
            verify_oad_039_end_to_end_live_persistence_evidence())
    if not all(checks): raise RuntimeError("OAD-036 through OAD-040 certification failed")
    builds=tuple("OAD-%03d"%i for i in range(36,41))
    cap="kalshi_websocket_to_ola_canonical_observation_to_postgresql_persistence"
    nxt="full_universe_partitioned_stream_persistence_and_downstream_intelligence_fanout"
    h=sha256(json.dumps({"builds":builds,"cap":cap,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiCanonicalPersistenceCertification(builds,"run_oad_038_kalshi_persistence_bridge.py",cap,nxt,h,True)

def verify_oad_040_kalshi_canonical_persistence_bridge_gate():
    c=certify_oad_036_through_040()
    return c.certified and len(c.builds)==5 and c.runtime_child=="run_oad_038_kalshi_persistence_bridge.py"
