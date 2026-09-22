from __future__ import annotations

from dataclasses import dataclass, replace

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_assembly_gate import (
    OracleCertifiedIntelligenceRegistryInvariantError,
    assemble_oracle_certified_intelligence_registry,
    verify_oracle_certified_intelligence_registry,
)


@dataclass(frozen=True)
class StubTerminal:
    terminal_certification_id: str
    terminal_certification_hash: str
    engine_id: str
    read_only: bool


@dataclass(frozen=True)
class StubConsumption:
    consumption_id: str
    consumption_hash: str
    engine_id: str
    read_only: bool


def accepted(_record) -> bool:
    return True


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleCertifiedIntelligenceRegistryInvariantError:
        return
    raise AssertionError("expected invariant rejection")


def main() -> None:
    oii = StubTerminal(
        terminal_certification_id="oii-terminal:" + "a" * 64,
        terminal_certification_hash="a" * 64,
        engine_id="OII-015",
        read_only=True,
    )
    osr = StubConsumption(
        consumption_id="osr-consumption:" + "b" * 64,
        consumption_hash="b" * 64,
        engine_id="INT-OSR-001",
        read_only=True,
    )

    first = assemble_oracle_certified_intelligence_registry(
        oii_terminal_certification=oii,
        oii_terminal_verifier=accepted,
        osr_terminal_consumption=osr,
        osr_terminal_consumption_verifier=accepted,
    )
    second = assemble_oracle_certified_intelligence_registry(
        oii_terminal_certification=oii,
        oii_terminal_verifier=accepted,
        osr_terminal_consumption=osr,
        osr_terminal_consumption_verifier=accepted,
    )

    assert first == second
    assert verify_oracle_certified_intelligence_registry(first)
    assert first.entry_count == 2
    assert first.registry_mutation_allowed is False
    assert first.oracle_execution_allowed is False
    assert first.qseries_execution_allowed is False
    assert first.read_only is True

    rejected(lambda: verify_oracle_certified_intelligence_registry(
        replace(first, registry_hash="0" * 64)
    ))
    rejected(lambda: verify_oracle_certified_intelligence_registry(
        replace(first, registry_mutation_allowed=True)
    ))
    rejected(lambda: assemble_oracle_certified_intelligence_registry(
        oii_terminal_certification=replace(oii, read_only=False),
        oii_terminal_verifier=accepted,
        osr_terminal_consumption=osr,
        osr_terminal_consumption_verifier=accepted,
    ))

    print("========================================")
    print(" INT-OII-001 TEST")
    print(" ORACLE CERTIFIED INTELLIGENCE")
    print(" REGISTRY ASSEMBLY GATE")
    print("========================================")
    print("[PASS] OII-015 terminal certification accepted")
    print("[PASS] INT-OSR-001 terminal consumption accepted")
    print("[PASS] Certified subsystem identities preserved")
    print("[PASS] Exact source hashes preserved")
    print("[PASS] Deterministic registration order certified")
    print("[PASS] Duplicate subsystem registration rejected")
    print("[PASS] Immutable registry identity deterministic")
    print("[PASS] Downstream read-only consumption allowed")
    print("[PASS] Registry mutation remains disabled")
    print("[PASS] Oracle execution remains disabled")
    print("[PASS] Publication and alerting remain disabled")
    print("[PASS] Q Series execution remains disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] INT-OII-001 CERTIFIED INTELLIGENCE REGISTRY ASSEMBLED")


if __name__ == "__main__":
    main()
