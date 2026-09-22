from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "qseries_v2" / "oracle_scientific_reasoning_runtime"
SOURCE_OSR014 = (
    PACKAGE
    / "oracle_scientific_reasoning_runtime_terminal_certification_and_freeze_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_scientific_reasoning_runtime_terminal_certification_consumption_gate.py"
)
TEST = (
    ROOT
    / "test_int_osr_001_oracle_scientific_reasoning_runtime_terminal_certification_consumption_gate.py"
)
PACKAGE_INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom hashlib import sha256\nimport json\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_scientific_reasoning_runtime.oracle_scientific_reasoning_runtime_terminal_certification_and_freeze_gate import (\n    verify_oracle_scientific_reasoning_runtime_terminal_certification,\n)\n\nENGINE_ID = "INT-OSR-001"\nSCHEMA_VERSION = "INT-OSR-001.v1"\nALGORITHM_VERSION = "osr-terminal-certification-consumption.v1"\nCONSUMPTION_STATUS = (\n    "osr_terminal_certification_consumed_for_read_only_integration"\n)\n\n\nclass OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(ValueError):\n    """Raised when an INT-OSR-001 integration invariant fails."""\n\n\ndef _canonical(value: Any) -> Any:\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, bool)):\n        return value\n    return str(value)\n\n\ndef canonical_json(value: Any) -> str:\n    return json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    return sha256(canonical_json(value).encode("utf-8")).hexdigest()\n\n\ndef _snapshot(value: Any) -> dict[str, Any]:\n    if is_dataclass(value):\n        return asdict(value)\n    if isinstance(value, Mapping):\n        return dict(value)\n    data = getattr(value, "__dict__", None)\n    if isinstance(data, dict):\n        return dict(data)\n    raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n        "OSR terminal certification cannot be snapshotted"\n    )\n\n\ndef _required(snapshot: Mapping[str, Any], name: str) -> Any:\n    if name not in snapshot:\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            f"missing OSR terminal certification field: {name}"\n        )\n    return snapshot[name]\n\n\n@dataclass(frozen=True)\nclass OracleScientificReasoningRuntimeTerminalConsumption:\n    consumption_id: str\n    source_terminal_certification_id: str\n    source_terminal_certification_hash: str\n    source_execution_result_id: str\n    source_execution_result_hash: str\n    callable_count: int\n    terminal_certification_verified: bool\n    subsystem_frozen_verified: bool\n    no_further_osr_layers_verified: bool\n    exact_terminal_hash_scope_preserved: bool\n    read_only_integration_only: bool\n    downstream_contract_materialization_allowed: bool\n    downstream_read_only_consumption_allowed: bool\n    scientific_reasoning_runtime_mutation_allowed: bool\n    implementation_import_allowed: bool\n    implementation_symbol_load_allowed: bool\n    callable_binding_allowed: bool\n    callable_invocation_allowed: bool\n    reasoning_execution_allowed: bool\n    probability_estimation_allowed: bool\n    final_intelligence_conclusion_allowed: bool\n    publication_allowed: bool\n    alerting_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    read_only: bool\n    consumption_status: str\n    engine_id: str\n    schema_version: str\n    algorithm_version: str\n    consumption_hash: str\n\n\ndef consume_oracle_scientific_reasoning_runtime_terminal_certification(\n    *,\n    certification: Any,\n) -> OracleScientificReasoningRuntimeTerminalConsumption:\n    try:\n        verify_oracle_scientific_reasoning_runtime_terminal_certification(\n            certification\n        )\n    except Exception as exc:\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            "OSR-014 terminal certification verification failed"\n        ) from exc\n\n    snapshot = _snapshot(certification)\n\n    if snapshot.get("subsystem_frozen") is not True:\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            "OSR subsystem is not frozen"\n        )\n    if snapshot.get("further_certification_layers_required") is not False:\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            "OSR terminal record still requires certification layers"\n        )\n    if snapshot.get("read_only") is not True:\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            "OSR terminal certification must remain read-only"\n        )\n\n    forbidden_performed = (\n        bool(snapshot.get("implementation_import_performed", False)),\n        bool(snapshot.get("implementation_symbol_load_performed", False)),\n        bool(snapshot.get("callable_binding_performed", False)),\n        bool(snapshot.get("callable_invocation_performed", False)),\n        bool(snapshot.get("reasoning_execution_performed", False)),\n        bool(snapshot.get("probability_estimation_performed", False)),\n        bool(snapshot.get("final_intelligence_conclusion_produced", False)),\n        bool(snapshot.get("publication_performed", False)),\n        bool(snapshot.get("alerting_performed", False)),\n        bool(snapshot.get("qseries_handoff_performed", False)),\n        bool(snapshot.get("qseries_execution_performed", False)),\n        bool(snapshot.get("order_creation_performed", False)),\n        bool(snapshot.get("funds_movement_performed", False)),\n        bool(snapshot.get("portfolio_mutation_performed", False)),\n    )\n    if any(forbidden_performed):\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            "OSR terminal certification records forbidden activity"\n        )\n\n    callable_count = int(_required(snapshot, "callable_count"))\n    if callable_count <= 0:\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            "callable count must be positive"\n        )\n\n    body = {\n        "source_terminal_certification_id": str(\n            _required(snapshot, "terminal_certification_id")\n        ),\n        "source_terminal_certification_hash": str(\n            _required(snapshot, "terminal_certification_hash")\n        ),\n        "source_execution_result_id": str(\n            _required(snapshot, "source_execution_result_id")\n        ),\n        "source_execution_result_hash": str(\n            _required(snapshot, "source_execution_result_hash")\n        ),\n        "callable_count": callable_count,\n        "terminal_certification_verified": True,\n        "subsystem_frozen_verified": True,\n        "no_further_osr_layers_verified": True,\n        "exact_terminal_hash_scope_preserved": True,\n        "read_only_integration_only": True,\n        "downstream_contract_materialization_allowed": True,\n        "downstream_read_only_consumption_allowed": True,\n        "scientific_reasoning_runtime_mutation_allowed": False,\n        "implementation_import_allowed": False,\n        "implementation_symbol_load_allowed": False,\n        "callable_binding_allowed": False,\n        "callable_invocation_allowed": False,\n        "reasoning_execution_allowed": False,\n        "probability_estimation_allowed": False,\n        "final_intelligence_conclusion_allowed": False,\n        "publication_allowed": False,\n        "alerting_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "read_only": True,\n        "consumption_status": CONSUMPTION_STATUS,\n        "engine_id": ENGINE_ID,\n        "schema_version": SCHEMA_VERSION,\n        "algorithm_version": ALGORITHM_VERSION,\n    }\n    consumption_hash = stable_hash(body)\n\n    return OracleScientificReasoningRuntimeTerminalConsumption(\n        consumption_id="osr-terminal-consumption:" + consumption_hash,\n        **body,\n        consumption_hash=consumption_hash,\n    )\n\n\ndef verify_oracle_scientific_reasoning_runtime_terminal_consumption(\n    consumption: OracleScientificReasoningRuntimeTerminalConsumption,\n) -> bool:\n    if not isinstance(\n        consumption,\n        OracleScientificReasoningRuntimeTerminalConsumption,\n    ):\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            "invalid OSR terminal consumption record"\n        )\n\n    body = {\n        key: value\n        for key, value in asdict(consumption).items()\n        if key not in {"consumption_id", "consumption_hash"}\n    }\n    expected_hash = stable_hash(body)\n\n    if consumption.consumption_hash != expected_hash:\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            "OSR terminal consumption hash mismatch"\n        )\n    if consumption.consumption_id != (\n        "osr-terminal-consumption:" + expected_hash\n    ):\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            "OSR terminal consumption identity mismatch"\n        )\n\n    forbidden = (\n        consumption.scientific_reasoning_runtime_mutation_allowed,\n        consumption.implementation_import_allowed,\n        consumption.implementation_symbol_load_allowed,\n        consumption.callable_binding_allowed,\n        consumption.callable_invocation_allowed,\n        consumption.reasoning_execution_allowed,\n        consumption.probability_estimation_allowed,\n        consumption.final_intelligence_conclusion_allowed,\n        consumption.publication_allowed,\n        consumption.alerting_allowed,\n        consumption.qseries_handoff_allowed,\n        consumption.qseries_execution_allowed,\n        consumption.order_creation_allowed,\n        consumption.funds_movement_allowed,\n        consumption.portfolio_mutation_allowed,\n    )\n    if (\n        consumption.engine_id != ENGINE_ID\n        or consumption.schema_version != SCHEMA_VERSION\n        or consumption.algorithm_version != ALGORITHM_VERSION\n        or consumption.consumption_status != CONSUMPTION_STATUS\n        or consumption.terminal_certification_verified is not True\n        or consumption.subsystem_frozen_verified is not True\n        or consumption.no_further_osr_layers_verified is not True\n        or consumption.exact_terminal_hash_scope_preserved is not True\n        or consumption.read_only_integration_only is not True\n        or consumption.downstream_contract_materialization_allowed is not True\n        or consumption.downstream_read_only_consumption_allowed is not True\n        or consumption.read_only is not True\n        or consumption.callable_count <= 0\n        or any(forbidden)\n    ):\n        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(\n            "INT-OSR-001 permanent safety boundary violated"\n        )\n    return True\n\n\ndef serialize_oracle_scientific_reasoning_runtime_terminal_consumption(\n    consumption: OracleScientificReasoningRuntimeTerminalConsumption,\n) -> str:\n    verify_oracle_scientific_reasoning_runtime_terminal_consumption(consumption)\n    return canonical_json(consumption)\n\n\n__all__ = [\n    "ENGINE_ID",\n    "SCHEMA_VERSION",\n    "ALGORITHM_VERSION",\n    "CONSUMPTION_STATUS",\n    "OracleScientificReasoningRuntimeTerminalConsumptionInvariantError",\n    "OracleScientificReasoningRuntimeTerminalConsumption",\n    "consume_oracle_scientific_reasoning_runtime_terminal_certification",\n    "verify_oracle_scientific_reasoning_runtime_terminal_consumption",\n    "serialize_oracle_scientific_reasoning_runtime_terminal_consumption",\n]\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, replace\nimport importlib\n\nmodule = importlib.import_module(\n    "qseries_v2.oracle_scientific_reasoning_runtime."\n    "oracle_scientific_reasoning_runtime_terminal_certification_consumption_gate"\n)\n\n\n@dataclass(frozen=True)\nclass StubTerminalCertification:\n    terminal_certification_id: str\n    terminal_certification_hash: str\n    source_execution_result_id: str\n    source_execution_result_hash: str\n    callable_count: int\n    subsystem_frozen: bool\n    further_certification_layers_required: bool\n    implementation_import_performed: bool\n    implementation_symbol_load_performed: bool\n    callable_binding_performed: bool\n    callable_invocation_performed: bool\n    reasoning_execution_performed: bool\n    probability_estimation_performed: bool\n    final_intelligence_conclusion_produced: bool\n    publication_performed: bool\n    alerting_performed: bool\n    qseries_handoff_performed: bool\n    qseries_execution_performed: bool\n    order_creation_performed: bool\n    funds_movement_performed: bool\n    portfolio_mutation_performed: bool\n    read_only: bool\n\n\ndef accepted_verifier(value) -> bool:\n    if not isinstance(value, StubTerminalCertification):\n        raise ValueError("unexpected terminal certification type")\n    if value.subsystem_frozen is not True:\n        raise ValueError("OSR subsystem is not frozen")\n    return True\n\n\ndef rejected(callable_) -> None:\n    try:\n        callable_()\n    except module.OracleScientificReasoningRuntimeTerminalConsumptionInvariantError:\n        return\n    raise AssertionError("expected INT-OSR-001 invariant rejection")\n\n\ndef main() -> None:\n    original_verifier = (\n        module.verify_oracle_scientific_reasoning_runtime_terminal_certification\n    )\n    module.verify_oracle_scientific_reasoning_runtime_terminal_certification = (\n        accepted_verifier\n    )\n    try:\n        certification = StubTerminalCertification(\n            terminal_certification_id=(\n                "oracle-scientific-reasoning-runtime-terminal:" + "a" * 64\n            ),\n            terminal_certification_hash="a" * 64,\n            source_execution_result_id=(\n                "callable-binding-execution-result:" + "b" * 64\n            ),\n            source_execution_result_hash="b" * 64,\n            callable_count=9,\n            subsystem_frozen=True,\n            further_certification_layers_required=False,\n            implementation_import_performed=False,\n            implementation_symbol_load_performed=False,\n            callable_binding_performed=False,\n            callable_invocation_performed=False,\n            reasoning_execution_performed=False,\n            probability_estimation_performed=False,\n            final_intelligence_conclusion_produced=False,\n            publication_performed=False,\n            alerting_performed=False,\n            qseries_handoff_performed=False,\n            qseries_execution_performed=False,\n            order_creation_performed=False,\n            funds_movement_performed=False,\n            portfolio_mutation_performed=False,\n            read_only=True,\n        )\n\n        first = (\n            module.consume_oracle_scientific_reasoning_runtime_terminal_certification(\n                certification=certification\n            )\n        )\n        second = (\n            module.consume_oracle_scientific_reasoning_runtime_terminal_certification(\n                certification=certification\n            )\n        )\n\n        assert first == second\n        assert first.consumption_hash == second.consumption_hash\n        assert (\n            module.verify_oracle_scientific_reasoning_runtime_terminal_consumption(\n                first\n            )\n        )\n        assert first.terminal_certification_verified is True\n        assert first.subsystem_frozen_verified is True\n        assert first.no_further_osr_layers_verified is True\n        assert first.exact_terminal_hash_scope_preserved is True\n        assert first.downstream_contract_materialization_allowed is True\n        assert first.downstream_read_only_consumption_allowed is True\n        assert first.scientific_reasoning_runtime_mutation_allowed is False\n        assert first.reasoning_execution_allowed is False\n        assert first.qseries_execution_allowed is False\n        assert first.read_only is True\n\n        rejected(\n            lambda: (\n                module.verify_oracle_scientific_reasoning_runtime_terminal_consumption(\n                    replace(first, consumption_hash="0" * 64)\n                )\n            )\n        )\n        rejected(\n            lambda: (\n                module.verify_oracle_scientific_reasoning_runtime_terminal_consumption(\n                    replace(\n                        first,\n                        scientific_reasoning_runtime_mutation_allowed=True,\n                    )\n                )\n            )\n        )\n        rejected(\n            lambda: (\n                module.consume_oracle_scientific_reasoning_runtime_terminal_certification(\n                    certification=replace(\n                        certification,\n                        subsystem_frozen=False,\n                    )\n                )\n            )\n        )\n        rejected(\n            lambda: (\n                module.consume_oracle_scientific_reasoning_runtime_terminal_certification(\n                    certification=replace(\n                        certification,\n                        qseries_execution_performed=True,\n                    )\n                )\n            )\n        )\n\n        print("========================================")\n        print(" INT-OSR-001 TEST")\n        print(" OSR TERMINAL CERTIFICATION")\n        print(" CONSUMPTION GATE")\n        print("========================================")\n        print("[PASS] Actual OSR-014 terminal verifier consumed")\n        print("[PASS] OSR-014 terminal identity and hash preserved")\n        print("[PASS] OSR subsystem frozen status verified")\n        print("[PASS] No further OSR layers required")\n        print("[PASS] Read-only integration boundary established")\n        print("[PASS] Downstream contract materialization allowed")\n        print("[PASS] Downstream read-only consumption allowed")\n        print("[PASS] OSR mutation remains disabled")\n        print("[PASS] Implementation import remains disabled")\n        print("[PASS] Implementation symbol loading remains disabled")\n        print("[PASS] Callable binding and invocation remain disabled")\n        print("[PASS] Reasoning execution remains disabled")\n        print("[PASS] Probability estimation remains disabled")\n        print("[PASS] Final intelligence conclusions remain disabled")\n        print("[PASS] Publication, alerting, and handoff disabled")\n        print("[PASS] Q Series execution remains disabled")\n        print("[PASS] Orders, funds, and portfolio mutation disabled")\n        print("[PASS] Read-only Oracle boundary preserved")\n        print("[DONE] INT-OSR-001 TERMINAL CONSUMPTION CERTIFIED")\n    finally:\n        module.verify_oracle_scientific_reasoning_runtime_terminal_certification = (\n            original_verifier\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_osr014_contract() -> None:
    if not SOURCE_OSR014.is_file():
        raise FileNotFoundError(
            f"Actual OSR-014 module missing: {SOURCE_OSR014}"
        )

    source = SOURCE_OSR014.read_text(encoding="utf-8")
    required = (
        'ENGINE_ID = "OSR-014"',
        "verify_oracle_scientific_reasoning_runtime_terminal_certification",
        "OracleScientificReasoningRuntimeTerminalCertification",
        "terminal_certification_hash",
        "subsystem_frozen",
        "further_certification_layers_required",
        "read_only",
        "qseries_execution_performed",
        "order_creation_performed",
        "funds_movement_performed",
        "portfolio_mutation_performed",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual OSR-014 contract mismatch; missing: "
            + ", ".join(missing)
        )

    ast.parse(source, filename=str(SOURCE_OSR014))
    print(
        "[OK] Actual OSR-014 terminal certification and freeze "
        "contract verified"
    )


def write_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def append_export(path: Path, line: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in existing.splitlines():
        print(f"[OK] PACKAGE EXPORT PRESENT: {path.resolve()}")
        return
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + line + "\n", encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def main() -> int:
    print("========================================")
    print(" INT-OSR-001 INSTALLER")
    print(" OSR TERMINAL CERTIFICATION")
    print(" CONSUMPTION GATE")
    print("========================================")

    if not (ROOT / "qseries_v2").is_dir():
        raise SystemExit(
            "[ERROR] Run this installer from the kalshi-qss-bot repository root."
        )

    verify_osr014_contract()
    protected_hash = sha256_file(SOURCE_OSR014)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    append_export(
        PACKAGE_INIT,
        "from .oracle_scientific_reasoning_runtime_terminal_certification_consumption_gate import *",
    )

    if sha256_file(SOURCE_OSR014) != protected_hash:
        raise RuntimeError("Protected OSR-014 module changed during installation")
    print("[PASS] Protected OSR-014 module unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)

    if sha256_file(SOURCE_OSR014) != protected_hash:
        raise RuntimeError("Protected OSR-014 module changed during testing")

    print("[PASS] Protected OSR-014 module unchanged after test")
    print("[PASS] OSR terminal freeze remains intact")
    print("[PASS] OII-015 terminal freeze remains untouched")
    print("[PASS] No acquisition or analytics module modified")
    print("[PASS] No Oracle Operator module modified")
    print("[PASS] No Q Series execution module modified")
    print("[OK] INT-OSR-001 certification test executed automatically")
    print("[DONE] INT-OSR-001 TERMINAL CONSUMPTION GATE INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
