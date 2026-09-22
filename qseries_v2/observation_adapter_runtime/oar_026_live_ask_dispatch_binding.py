from __future__ import annotations

from dataclasses import dataclass

from .oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from .oar_024_oit_live_intelligence_bridge import (
    OITLiveIntelligenceBridge,
    OITLiveIntelligenceResponse,
)

BUILD_ID = "OAR-026"
OAR_026_REVISION = "OAR_026_LIVE_ASK_DISPATCH_BINDING_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveAskDispatchBindingResult:
    query: str
    live_response: OITLiveIntelligenceResponse
    consume_existing_terminal: bool
    read_only: bool


class LiveAskDispatchBinding:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def dispatch(
        self,
        *,
        query: str,
        read_model: TerminalLiveIntelligenceReadModel | None,
    ) -> LiveAskDispatchBindingResult:
        response = (
            OITLiveIntelligenceBridge()
            .respond(
                query=query,
                read_model=read_model,
            )
        )

        return LiveAskDispatchBindingResult(
            query=query,
            live_response=response,
            consume_existing_terminal=(
                response
                .fallback_to_existing_terminal
            ),
            read_only=True,
        )


def verify_live_ask_dispatch_binding() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True
