from __future__ import annotations

from qseries_v2.observation_adapter_runtime.oar_026_live_ask_dispatch_binding import (
    LiveAskDispatchBinding,
)

BUILD_ID = "OAR-026-OIT"
REVISION = "OAR_026_OIT_LIVE_ASK_DISPATCH_ADAPTER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


def build_oracle_live_ask_dispatch_adapter():
    return LiveAskDispatchBinding()


def verify_oracle_live_ask_dispatch_adapter() -> bool:
    adapter = (
        build_oracle_live_ask_dispatch_adapter()
    )

    assert adapter.read_only is True
    assert adapter.execution_allowed is False
    assert adapter.publication_allowed is False
    assert adapter.persistence_allowed is False

    return True
