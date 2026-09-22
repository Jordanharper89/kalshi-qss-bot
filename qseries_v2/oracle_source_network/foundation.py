from dataclasses import dataclass, asdict
from typing import Tuple
import hashlib, json

REVISION = "OSN_001_ORACLE_SOURCE_NETWORK_SUBSYSTEM_FOUNDATION_V1"
EXECUTION_AUTHORITY = False
VENUE_NEUTRAL = True
UPSTREAM_CONTROL_PLANE = ("OAD-414","OAD-415","OAD-416","OAD-417","OAD-418")

@dataclass(frozen=True)
class SourceNetworkDescriptor:
    subsystem: str = "OSN"
    purpose: str = "independent_source_network"
    execution_authority: bool = False
    venue_neutral: bool = True
    upstream_control_plane: Tuple[str, ...] = UPSTREAM_CONTROL_PLANE

    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",",":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def descriptor() -> SourceNetworkDescriptor:
    return SourceNetworkDescriptor()
