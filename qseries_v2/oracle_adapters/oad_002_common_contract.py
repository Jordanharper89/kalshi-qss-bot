from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .oad_001_foundation import OracleAdapterIdentity

OAD_002_BUILD_ID = "OAD-002"
OAD_002_REVISION = "OAD_002_COMMON_ADAPTER_CONTRACT_V1"

REQUIRED_OPERATIONS = (
    "discover_universe",
    "start_live_stream",
    "stop_live_stream",
    "subscribe",
    "unsubscribe",
    "get_snapshot",
    "health",
    "recover",
    "normalize_event",
)

@dataclass(frozen=True)
class OracleAdapterContract:
    identity: OracleAdapterIdentity
    operations: tuple[str, ...]
    supports_full_universe: bool
    supports_live_stream: bool
    read_only: bool = True

def build_oracle_adapter_contract(identity, supports_full_universe=True, supports_live_stream=True):
    if not isinstance(identity, OracleAdapterIdentity):
        raise ValueError("certified adapter identity required")
    return OracleAdapterContract(
        identity,
        REQUIRED_OPERATIONS,
        bool(supports_full_universe),
        bool(supports_live_stream),
        True,
    )

def validate_adapter_implementation(obj, contract):
    if not isinstance(contract, OracleAdapterContract):
        raise ValueError("certified adapter contract required")
    missing = tuple(name for name in contract.operations if not callable(getattr(obj, name, None)))
    return missing

def build_oad_002_certification_manifest():
    return MappingProxyType({
        "build_id": OAD_002_BUILD_ID,
        "revision": OAD_002_REVISION,
        "required_operations": REQUIRED_OPERATIONS,
        "read_only": True,
        "execution": False,
    })

def verify_oad_002_common_adapter_contract():
    from .oad_001_foundation import build_oracle_adapter_identity
    c = build_oracle_adapter_contract(build_oracle_adapter_identity("a","s","venue"))
    class Impl:
        pass
    for name in REQUIRED_OPERATIONS:
        setattr(Impl, name, lambda self: None)
    return c.read_only and validate_adapter_implementation(Impl(), c) == ()
