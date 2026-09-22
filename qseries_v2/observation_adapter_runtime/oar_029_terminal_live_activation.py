from __future__ import annotations

from dataclasses import dataclass

from .oar_027_terminal_live_query_e2e import (
    TerminalLiveQueryEndToEnd,
)

BUILD_ID = "OAR-029"
OAR_029_REVISION = "OAR_029_TERMINAL_LIVE_ACTIVATION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PRODUCTION_READ_ACTIVATION_ALLOWED = True


@dataclass(frozen=True, slots=True)
class TerminalLiveActivation:
    activation_id: str
    read_path_name: str
    legacy_fallback_enabled: bool
    live_query_interception_enabled: bool
    read_only: bool
    execution_allowed: bool


class TerminalLiveActivationBoundary:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def activate(self) -> TerminalLiveActivation:
        return TerminalLiveActivation(
            activation_id=(
                "oracle.terminal.live.read.v1"
            ),
            read_path_name=(
                "OAR-027 TerminalLiveQueryEndToEnd"
            ),
            legacy_fallback_enabled=True,
            live_query_interception_enabled=True,
            read_only=True,
            execution_allowed=False,
        )

    def build_read_path(
        self,
    ) -> TerminalLiveQueryEndToEnd:
        return TerminalLiveQueryEndToEnd()


def verify_terminal_live_activation() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PRODUCTION_READ_ACTIVATION_ALLOWED is True
    return True
