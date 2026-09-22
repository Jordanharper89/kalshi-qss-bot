from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OAD_001_BUILD_ID = "OAD-001"
OAD_001_REVISION = "OAD_001_ORACLE_ADAPTER_SUBSYSTEM_FOUNDATION_V1"

@dataclass(frozen=True)
class OracleAdapterSubsystemPolicy:
    source_specific_implementations_separate_from_ois: bool = True
    read_only_acquisition: bool = True
    execution_authority: bool = False
    publication_authority: bool = False
    full_universe_capability_required_when_applicable: bool = True
    event_driven_preferred_when_available: bool = True

@dataclass(frozen=True)
class OracleAdapterIdentity:
    adapter_id: str
    source_id: str
    source_type: str
    category_scope: str

def build_oracle_adapter_identity(adapter_id, source_id, source_type, category_scope="ALL"):
    if not all((adapter_id, source_id, source_type, category_scope)):
        raise ValueError("complete adapter identity required")
    return OracleAdapterIdentity(adapter_id, source_id, source_type, category_scope)

def build_oad_001_certification_manifest():
    return MappingProxyType({
        "build_id": OAD_001_BUILD_ID,
        "revision": OAD_001_REVISION,
        "package": "qseries_v2.oracle_adapters",
        "read_only_acquisition": True,
        "execution": False,
        "publication": False,
        "separate_from_ois": True,
    })

def verify_oad_001_oracle_adapter_subsystem_foundation():
    p = OracleAdapterSubsystemPolicy()
    x = build_oracle_adapter_identity("kalshi_universal", "kalshi", "venue", "ALL")
    return (
        p.source_specific_implementations_separate_from_ois
        and p.read_only_acquisition
        and not p.execution_authority
        and not p.publication_authority
        and x.category_scope == "ALL"
    )
