from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OAR-023"
OAR_023_REVISION = "OAR_023_TERMINAL_LIVE_QUERY_ROUTER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False

ROUTE_LIVE_FACT = "live_fact"
ROUTE_LIVE_EXPLANATION = "live_explanation"
ROUTE_LIVE_DIRECTION = "live_direction"
ROUTE_EXISTING_TERMINAL = "existing_terminal"

_FACT_TOKENS = (
    "current price",
    "price of",
    "what is the price",
    "how much is",
    "current value",
)

_EXPLANATION_TOKENS = (
    "why is",
    "why did",
    "explain why",
    "what caused",
    "what changed",
    "why has",
    "why did the edge",
    "why the edge",
)

_DIRECTION_TOKENS = (
    "where is",
    "where will",
    "moving",
    "direction",
    "next hour",
    "next 30 minutes",
    "next 15 minutes",
    "up or down",
)


@dataclass(frozen=True, slots=True)
class TerminalLiveQueryRoute:
    raw_query: str
    normalized_query: str
    route: str
    live_intelligence_required: bool
    explanation_required: bool
    directional_reasoning_required: bool
    read_only: bool


class TerminalLiveQueryRouter:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def route(
        self,
        query: str,
    ) -> TerminalLiveQueryRoute:
        raw = str(query)

        normalized = " ".join(
            raw.strip().lower().split()
        )

        if not normalized:
            raise ValueError(
                "query must not be empty"
            )

        if any(
            token in normalized
            for token in _EXPLANATION_TOKENS
        ):
            route = ROUTE_LIVE_EXPLANATION
            live_required = True
            explanation_required = True
            direction_required = False

        elif any(
            token in normalized
            for token in _DIRECTION_TOKENS
        ):
            route = ROUTE_LIVE_DIRECTION
            live_required = True
            explanation_required = True
            direction_required = True

        elif any(
            token in normalized
            for token in _FACT_TOKENS
        ):
            route = ROUTE_LIVE_FACT
            live_required = True
            explanation_required = False
            direction_required = False

        else:
            route = ROUTE_EXISTING_TERMINAL
            live_required = False
            explanation_required = False
            direction_required = False

        return TerminalLiveQueryRoute(
            raw_query=raw,
            normalized_query=normalized,
            route=route,
            live_intelligence_required=(
                live_required
            ),
            explanation_required=(
                explanation_required
            ),
            directional_reasoning_required=(
                direction_required
            ),
            read_only=True,
        )


def verify_terminal_live_query_router() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_023_REVISION",
    "ROUTE_LIVE_FACT",
    "ROUTE_LIVE_EXPLANATION",
    "ROUTE_LIVE_DIRECTION",
    "ROUTE_EXISTING_TERMINAL",
    "TerminalLiveQueryRoute",
    "TerminalLiveQueryRouter",
    "verify_terminal_live_query_router",
]
