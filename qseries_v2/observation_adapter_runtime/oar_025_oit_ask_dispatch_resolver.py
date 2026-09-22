from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OAR-025"
OAR_025_REVISION = "OAR_025_OIT_ASK_DISPATCH_RESOLVER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class OITAskDispatchCandidate:
    module_name: str
    symbol_name: str
    symbol_kind: str
    score: int
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OITAskDispatchResolution:
    candidates: tuple[OITAskDispatchCandidate, ...]
    candidate_count: int
    exact_boundary_resolved: bool
    read_only: bool


class OITAskDispatchResolver:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def resolve(
        self,
        candidates: tuple[OITAskDispatchCandidate, ...],
    ) -> OITAskDispatchResolution:
        ordered = tuple(
            sorted(
                candidates,
                key=lambda x: (
                    -x.score,
                    x.module_name,
                    x.symbol_name,
                    x.symbol_kind,
                ),
            )
        )

        exact = bool(
            ordered
            and ordered[0].score >= 6
        )

        return OITAskDispatchResolution(
            candidates=ordered,
            candidate_count=len(ordered),
            exact_boundary_resolved=exact,
            read_only=True,
        )


def verify_oit_ask_dispatch_resolver() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True
