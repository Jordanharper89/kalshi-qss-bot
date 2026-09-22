from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from .oar_027_terminal_live_query_e2e import (
    TerminalLiveQueryEndToEnd,
)

BUILD_ID = "OAR-028"
OAR_028_REVISION = "OAR_028_FULL_LIVE_INTELLIGENCE_CERTIFICATION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class FullLiveIntelligenceCertificationResult:
    bitcoin_query_passed: bool
    kalshi_query_passed: bool
    fallback_query_passed: bool
    observation_count: int
    evidence_hash: str
    read_only: bool
    execution_allowed: bool


class FullLiveIntelligenceCertification:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def certify(
        self,
        *,
        read_model: TerminalLiveIntelligenceReadModel,
    ) -> FullLiveIntelligenceCertificationResult:
        if not isinstance(
            read_model,
            TerminalLiveIntelligenceReadModel,
        ):
            raise TypeError(
                "read_model must be TerminalLiveIntelligenceReadModel"
            )

        if read_model.read_only is not True:
            raise ValueError(
                "read_model must be read-only"
            )

        if read_model.lineage_valid is not True:
            raise ValueError(
                "read_model lineage must be valid"
            )

        engine = TerminalLiveQueryEndToEnd()

        bitcoin = engine.execute(
            query="why is bitcoin moving?",
            read_model=read_model,
        )

        kalshi = engine.execute(
            query=(
                "explain why the edge for up "
                "on Astros strikeouts just went up"
            ),
            read_model=read_model,
        )

        fallback = engine.execute(
            query="show current session",
            read_model=read_model,
        )

        bitcoin_passed = (
            bitcoin.live_handled
            and not bitcoin.fallback_to_existing_terminal
        )

        kalshi_passed = (
            kalshi.live_handled
            and not kalshi.fallback_to_existing_terminal
        )

        fallback_passed = (
            not fallback.live_handled
            and fallback.fallback_to_existing_terminal
        )

        if not (
            bitcoin_passed
            and kalshi_passed
            and fallback_passed
        ):
            raise RuntimeError(
                "full live-intelligence certification failed"
            )

        return FullLiveIntelligenceCertificationResult(
            bitcoin_query_passed=True,
            kalshi_query_passed=True,
            fallback_query_passed=True,
            observation_count=read_model.observation_count,
            evidence_hash=read_model.evidence_hash,
            read_only=True,
            execution_allowed=False,
        )


def verify_full_live_intelligence_certification() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True
