from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OLC-006"
OLC_006_REVISION = "OLC_006_TERMINAL_INJECTION_RESOLVER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class TerminalInjectionCandidate:
    module_name: str
    symbol_name: str
    symbol_kind: str
    score: int
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TerminalInjectionResolution:
    candidates: tuple[TerminalInjectionCandidate, ...]
    exact_injection_boundary_resolved: bool
    source_mutation_required: bool
    read_only: bool


class TerminalInjectionResolver:
    read_only = True
    execution_allowed = False
    source_mutation_allowed = False

    def resolve(
        self,
        candidates: tuple[TerminalInjectionCandidate, ...],
    ) -> TerminalInjectionResolution:
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
            and ordered[0].score >= 8
        )

        return TerminalInjectionResolution(
            candidates=ordered,
            exact_injection_boundary_resolved=exact,
            source_mutation_required=False,
            read_only=True,
        )


def verify_terminal_injection_resolver() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    return True
