from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

from .oad_001_foundation import verify_oad_001_oracle_adapter_subsystem_foundation
from .oad_002_common_contract import verify_oad_002_common_adapter_contract
from .oad_003_canonical_event import verify_oad_003_canonical_source_event_envelope
from .oad_004_lifecycle_health import verify_oad_004_adapter_lifecycle_health_contract

OAD_005_BUILD_ID = "OAD-005"
OAD_005_REVISION = "OAD_005_ADAPTER_FOUNDATION_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class OracleAdapterFoundationCertification:
    builds: tuple[str, ...]
    capability: str
    next_capability: str
    certification_hash: str
    certified: bool = True

def certify_oad_001_through_005():
    checks = (
        verify_oad_001_oracle_adapter_subsystem_foundation(),
        verify_oad_002_common_adapter_contract(),
        verify_oad_003_canonical_source_event_envelope(),
        verify_oad_004_adapter_lifecycle_health_contract(),
    )
    if not all(checks):
        raise RuntimeError("Oracle Adapter foundation certification failed")

    builds = tuple("OAD-%03d" % i for i in range(1,6))
    capability = "oracle_adapter_subsystem_foundation_common_contract_canonical_events_lifecycle_health"
    next_capability = "kalshi_adapter_foundation_full_universe_discovery_and_live_market_streaming"
    digest = sha256(
        json.dumps(
            {"builds":builds,"capability":capability,"next_capability":next_capability},
            sort_keys=True,separators=(",",":")
        ).encode()
    ).hexdigest()

    return OracleAdapterFoundationCertification(
        builds, capability, next_capability, digest, True
    )

def build_oad_005_certification_manifest():
    c = certify_oad_001_through_005()
    return MappingProxyType({
        "build_id": OAD_005_BUILD_ID,
        "revision": OAD_005_REVISION,
        "capability": c.capability,
        "next_capability": c.next_capability,
        "certified": c.certified,
        "execution": False,
        "publication": False,
    })

def verify_oad_005_adapter_foundation_capability_gate():
    c = certify_oad_001_through_005()
    return (
        c.certified
        and len(c.builds)==5
        and c.next_capability=="kalshi_adapter_foundation_full_universe_discovery_and_live_market_streaming"
    )
