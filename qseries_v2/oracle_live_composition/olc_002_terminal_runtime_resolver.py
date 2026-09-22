from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OLC-002"
OLC_002_REVISION = "OLC_002_TERMINAL_RUNTIME_RESOLVER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class TerminalRuntimeCandidate:
    module_name: str
    symbol_name: str
    symbol_kind: str
    score: int
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TerminalRuntimeResolution:
    candidates: tuple[TerminalRuntimeCandidate, ...]
    candidate_count: int
    exact_runtime_resolved: bool
    read_only: bool


class TerminalRuntimeResolver:
    read_only = True
    execution_allowed = False

    def resolve(
        self,
        candidates: tuple[TerminalRuntimeCandidate, ...],
    ) -> TerminalRuntimeResolution:
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

        return TerminalRuntimeResolution(
            candidates=ordered,
            candidate_count=len(ordered),
            exact_runtime_resolved=bool(
                ordered
                and ordered[0].score >= 8
            ),
            read_only=True,
        )


def verify_terminal_runtime_resolver() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True
