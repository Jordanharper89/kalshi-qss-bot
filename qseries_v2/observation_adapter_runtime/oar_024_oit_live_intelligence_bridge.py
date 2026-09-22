from __future__ import annotations

from dataclasses import dataclass

from .oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from .oar_023_terminal_live_query_router import (
    ROUTE_EXISTING_TERMINAL,
    TerminalLiveQueryRoute,
    TerminalLiveQueryRouter,
)

BUILD_ID = "OAR-024"
OAR_024_REVISION = "OAR_024_OIT_LIVE_INTELLIGENCE_BRIDGE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class OITLiveIntelligenceResponse:
    handled: bool
    route: str
    query: str
    read_model_id: str | None
    observation_count: int
    evidence_hash: str | None
    fallback_to_existing_terminal: bool
    read_only: bool


class OITLiveIntelligenceBridge:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def classify(
        self,
        query: str,
    ) -> TerminalLiveQueryRoute:
        return (
            TerminalLiveQueryRouter()
            .route(
                query
            )
        )

    def respond(
        self,
        *,
        query: str,
        read_model: TerminalLiveIntelligenceReadModel | None,
    ) -> OITLiveIntelligenceResponse:
        route = self.classify(
            query
        )

        if (
            route.route
            == ROUTE_EXISTING_TERMINAL
        ):
            return OITLiveIntelligenceResponse(
                handled=False,
                route=route.route,
                query=route.raw_query,
                read_model_id=None,
                observation_count=0,
                evidence_hash=None,
                fallback_to_existing_terminal=True,
                read_only=True,
            )

        if read_model is None:
            return OITLiveIntelligenceResponse(
                handled=False,
                route=route.route,
                query=route.raw_query,
                read_model_id=None,
                observation_count=0,
                evidence_hash=None,
                fallback_to_existing_terminal=True,
                read_only=True,
            )

        if not isinstance(
            read_model,
            TerminalLiveIntelligenceReadModel,
        ):
            raise TypeError(
                "read_model must be "
                "TerminalLiveIntelligenceReadModel or None"
            )

        if read_model.read_only is not True:
            raise ValueError(
                "terminal live read model must be read-only"
            )

        return OITLiveIntelligenceResponse(
            handled=True,
            route=route.route,
            query=route.raw_query,
            read_model_id=read_model.read_model_id,
            observation_count=read_model.observation_count,
            evidence_hash=read_model.evidence_hash,
            fallback_to_existing_terminal=False,
            read_only=True,
        )


def verify_oit_live_intelligence_bridge() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_024_REVISION",
    "OITLiveIntelligenceResponse",
    "OITLiveIntelligenceBridge",
    "verify_oit_live_intelligence_bridge",
]
