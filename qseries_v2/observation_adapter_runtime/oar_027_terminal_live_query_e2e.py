from __future__ import annotations

from dataclasses import dataclass

from .oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from .oar_026_live_ask_dispatch_binding import (
    LiveAskDispatchBinding,
)

BUILD_ID = "OAR-027"
OAR_027_REVISION = "OAR_027_TERMINAL_LIVE_QUERY_E2E_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class TerminalLiveQueryE2EResult:
    query: str
    live_handled: bool
    observation_count: int
    route: str
    evidence_hash: str | None
    fallback_to_existing_terminal: bool
    read_only: bool


class TerminalLiveQueryEndToEnd:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def execute(
        self,
        *,
        query: str,
        read_model: TerminalLiveIntelligenceReadModel | None,
    ) -> TerminalLiveQueryE2EResult:
        dispatch = (
            LiveAskDispatchBinding()
            .dispatch(
                query=query,
                read_model=read_model,
            )
        )

        response = (
            dispatch.live_response
        )

        return TerminalLiveQueryE2EResult(
            query=query,
            live_handled=response.handled,
            observation_count=(
                response.observation_count
            ),
            route=response.route,
            evidence_hash=(
                response.evidence_hash
            ),
            fallback_to_existing_terminal=(
                dispatch
                .consume_existing_terminal
            ),
            read_only=True,
        )


def verify_terminal_live_query_e2e() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True
