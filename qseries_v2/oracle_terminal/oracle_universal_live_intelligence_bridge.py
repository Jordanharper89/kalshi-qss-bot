from __future__ import annotations

from qseries_v2.observation_adapter_runtime.oar_024_oit_live_intelligence_bridge import (
    OITLiveIntelligenceBridge,
)

BUILD_ID = "OAR-024-OIT"
REVISION = "OAR_024_OIT_READ_ONLY_LIVE_INTELLIGENCE_BRIDGE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


def build_oracle_universal_live_intelligence_bridge():
    return OITLiveIntelligenceBridge()


def verify_oracle_universal_live_intelligence_bridge() -> bool:
    bridge = (
        build_oracle_universal_live_intelligence_bridge()
    )

    assert bridge.read_only is True
    assert bridge.execution_allowed is False
    assert bridge.publication_allowed is False
    assert bridge.persistence_allowed is False

    return True


__all__ = [
    "BUILD_ID",
    "REVISION",
    "READ_ONLY",
    "EXECUTION_ALLOWED",
    "PUBLICATION_ALLOWED",
    "PERSISTENCE_ALLOWED",
    "build_oracle_universal_live_intelligence_bridge",
    "verify_oracle_universal_live_intelligence_bridge",
]
