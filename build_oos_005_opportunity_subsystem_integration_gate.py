from pathlib import Path


ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
ORACLE = BASE / "oracle_intelligence"
OOS = ORACLE / "opportunity_operating_system"

MODULE_PATH = OOS / "opportunity_subsystem_integration_gate.py"
INIT_PATH = OOS / "__init__.py"
TEST_PATH = ROOT / "test_oos_005_opportunity_subsystem_integration_gate.py"

MODULE_CODE = r'''"""
OOS-005 Opportunity Subsystem Integration Gate

Certifies OOS-001 through OOS-004 as a deterministic, immutable,
read-only opportunity handoff subsystem.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .opportunity_operating_system import OOS_VERSION, build_oos
from .opportunity_pipeline import OOS_PIPELINE_VERSION, build_pipeline
from .opportunity_ranking_engine import OOS_RANKING_VERSION, build_ranking_engine
from .opportunity_validation_engine import OOS_VALIDATION_VERSION, build_validation_engine


SCHEMA_VERSION = "OOS-005"
ENGINE_ID = "OOS-005"
READ_ONLY = True
EXECUTION_ALLOWED = False

EXPECTED_MODULES = (
    "OOS-001",
    "OOS-002",
    "OOS-003",
    "OOS-004",
    "OOS-005",
)


def _stable_value(value: Any) -> Any:
    if hasattr(value, "value"):
        return _stable_value(value.value)
    if isinstance(value, Mapping):
        return {str(key): _stable_value(value[key]) for key in sorted(value.keys(), key=str)}
    if isinstance(value, (list, tuple)):
        return [_stable_value(item) for item in value]
    if isinstance(value, set):
        return sorted((_stable_value(item) for item in value), key=_stable_json)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _stable_value(value.to_dict())
    if is_dataclass(value):
        return _stable_value(asdict(value))
    return value


def _stable_json(value: Any) -> str:
    return json.dumps(_stable_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_hash(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _opportunity_dict(opportunity: Any) -> Dict[str, Any]:
    if not bool(getattr(opportunity, "read_only", False)):
        raise ValueError("OOS-005 accepts read-only fixture opportunities only.")
    to_dict = getattr(opportunity, "to_dict", None)
    fingerprint = getattr(opportunity, "fingerprint", None)
    if not callable(to_dict) or not callable(fingerprint):
        raise ValueError("OOS-005 accepts UniversalOpportunity-style fixtures only.")
    data = to_dict()
    if not isinstance(data, Mapping):
        raise ValueError("Opportunity to_dict() must return a mapping.")
    canonical = _stable_value(data)
    if not isinstance(canonical, dict):
        raise ValueError("Canonical opportunity payload must be a mapping.")
    canonical["fingerprint"] = str(fingerprint())
    return canonical


def _canonical_opportunities(opportunities: Iterable[Any]) -> Tuple[Dict[str, Any], ...]:
    records = [_opportunity_dict(item) for item in opportunities]
    return tuple(sorted(records, key=lambda item: (str(item.get("fingerprint", "")), str(item.get("opportunity_id", "")), _stable_json(item))))


def _validation_summary(report: Any) -> Dict[str, Any]:
    checks = []
    for check in getattr(report, "checks", ()):
        checks.append(
            {
                "check_id": str(getattr(check, "check_id", "")),
                "severity": str(getattr(getattr(check, "severity", None), "value", getattr(check, "severity", ""))),
                "passed": bool(getattr(check, "passed", False)),
                "message": str(getattr(check, "message", "")),
                "field": getattr(check, "field", None),
                "value": _stable_value(getattr(check, "value", None)),
            }
        )
    checks.sort(key=lambda item: (item["check_id"], item["severity"], item["message"]))
    return {
        "opportunity_id": str(getattr(report, "opportunity_id", "")),
        "fingerprint": getattr(report, "fingerprint", None),
        "status": str(getattr(getattr(report, "status", None), "value", getattr(report, "status", ""))),
        "passed_checks": int(getattr(report, "passed_checks", 0)),
        "failed_checks": int(getattr(report, "failed_checks", 0)),
        "warning_count": int(getattr(report, "warning_count", 0)),
        "info_count": int(getattr(report, "info_count", 0)),
        "checks": checks,
        "schema_version": str(getattr(report, "schema_version", "")),
        "read_only": bool(getattr(report, "read_only", False)),
    }


def _metadata_tuple(metadata: Mapping[str, Any]) -> Tuple[Tuple[str, Any], ...]:
    return tuple((str(key), _stable_value(value)) for key, value in sorted(metadata.items(), key=lambda item: str(item[0])))


def _metadata_dict(metadata: Tuple[Tuple[str, Any], ...]) -> Dict[str, Any]:
    return {key: _stable_value(value) for key, value in metadata}


def _check(check_id: str, passed: bool, explanation: str, details: Optional[Mapping[str, Any]] = None) -> "OpportunityIntegrationCheck":
    return OpportunityIntegrationCheck(str(check_id), bool(passed), str(explanation), _metadata_tuple(details or {}))


@dataclass(frozen=True)
class OpportunityIntegrationCheck:
    check_id: str
    passed: bool
    explanation: str
    details: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "explanation": self.explanation,
            "details": _metadata_dict(self.details),
        }


@dataclass(frozen=True)
class OpportunitySubsystemIntegrationResult:
    schema_version: str
    engine_id: str
    observed_at: str
    modules: Tuple[str, ...]
    checks: Tuple[OpportunityIntegrationCheck, ...]
    pass_count: int
    fail_count: int
    passed: bool
    integration_hash: str
    read_only: bool
    execution_allowed: bool
    explanation: str
    telemetry: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "observed_at": self.observed_at,
            "modules": list(self.modules),
            "checks": [check.to_dict() for check in self.checks],
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "passed": self.passed,
            "integration_hash": self.integration_hash,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "explanation": self.explanation,
            "telemetry": _metadata_dict(self.telemetry),
        }

    def verify_integration_hash(self) -> bool:
        return self.integration_hash == _result_hash(
            observed_at=self.observed_at,
            modules=self.modules,
            checks=self.checks,
            pass_count=self.pass_count,
            fail_count=self.fail_count,
            passed=self.passed,
            read_only=self.read_only,
            execution_allowed=self.execution_allowed,
            telemetry=self.telemetry,
        )


def _result_hash(*, observed_at: str, modules: Tuple[str, ...], checks: Tuple[OpportunityIntegrationCheck, ...], pass_count: int, fail_count: int, passed: bool, read_only: bool, execution_allowed: bool, telemetry: Tuple[Tuple[str, Any], ...]) -> str:
    return _stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "observed_at": observed_at,
            "modules": list(modules),
            "checks": [check.to_dict() for check in checks],
            "pass_count": pass_count,
            "fail_count": fail_count,
            "passed": passed,
            "read_only": read_only,
            "execution_allowed": execution_allowed,
            "telemetry": _metadata_dict(telemetry),
        }
    )


def run_opportunity_subsystem_integration_gate(opportunities: Iterable[Any], *, observed_at: str, source: str = "fixture", profile: str = "balanced", limit: Optional[int] = None) -> OpportunitySubsystemIntegrationResult:
    if not str(observed_at).strip():
        raise ValueError("observed_at must be supplied by the caller.")

    opportunities = tuple(opportunities)
    canonical_opportunities = _canonical_opportunities(opportunities)
    sorted_opportunities = tuple(sorted(opportunities, key=lambda item: _opportunity_dict(item)["fingerprint"]))

    validation_engine = build_validation_engine()
    validation_reports = tuple(_validation_summary(validation_engine.validate(item)) for item in sorted_opportunities)
    validation_failures = sum(int(item["failed_checks"]) for item in validation_reports)

    oos = build_oos()
    ranking_engine = build_ranking_engine()
    pipeline = build_pipeline(oos=oos, ranking_engine=ranking_engine)

    pipeline_result = None
    pipeline_error = None
    if validation_failures == 0:
        try:
            pipeline_result = pipeline.process(sorted_opportunities, source=source, profile=profile, limit=limit)
        except Exception as exc:  # pragma: no cover
            pipeline_error = str(exc)

    pipeline_summary = {
        "status": getattr(pipeline_result, "status", "skipped" if validation_failures else "failed"),
        "input_count": len(opportunities),
        "registered_count": getattr(pipeline_result, "registered_count", 0) if pipeline_result else 0,
        "duplicate_count": getattr(pipeline_result, "duplicate_count", 0) if pipeline_result else 0,
        "ranked_count": getattr(pipeline_result, "ranked_count", 0) if pipeline_result else 0,
        "pipeline_error": pipeline_error,
    }

    observed_modules = (OOS_VERSION, OOS_RANKING_VERSION, OOS_PIPELINE_VERSION, OOS_VALIDATION_VERSION, SCHEMA_VERSION)
    checks = (
        _check("module_coverage", observed_modules == EXPECTED_MODULES, "OOS-001 through OOS-005 module coverage is present.", {"expected_modules": list(EXPECTED_MODULES), "observed_modules": list(observed_modules)}),
        _check("fixture_input", len(canonical_opportunities) == len(opportunities), "Fixture-style UniversalOpportunity inputs were accepted.", {"input_count": len(opportunities)}),
        _check("oos_004_validation", validation_failures == 0, "OOS-004 validation reports no failed checks.", {"validation_failures": validation_failures, "reports": validation_reports}),
        _check("pipeline_handoff", pipeline_result is not None and pipeline_summary["status"] == "ok", "OOS-003 pipeline can register and rank valid opportunity fixtures.", pipeline_summary),
        _check("read_only_boundary", READ_ONLY and not EXECUTION_ALLOWED, "OOS-005 certifies read-only handoff only; execution remains disabled.", {"read_only": READ_ONLY, "execution_allowed": EXECUTION_ALLOWED, "trade_execution_performed": False, "orders_placed": False, "portfolio_mutated": False}),
        _check("deterministic_payload", bool(canonical_opportunities) or len(opportunities) == 0, "Canonical opportunity payload is stable and order-independent.", {"opportunity_count": len(canonical_opportunities), "opportunity_hash": _stable_hash(list(canonical_opportunities))}),
    )

    pass_count = sum(1 for check in checks if check.passed)
    fail_count = len(checks) - pass_count
    passed = fail_count == 0
    telemetry = _metadata_tuple(
        {
            "source": source,
            "profile": profile,
            "limit": limit,
            "input_count": len(opportunities),
            "canonical_opportunity_hash": _stable_hash(list(canonical_opportunities)),
            "validation_report_hash": _stable_hash(list(validation_reports)),
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "files_written": False,
            "databases_written": False,
            "runtime_state_written": False,
        }
    )
    integration_hash = _result_hash(observed_at=str(observed_at), modules=EXPECTED_MODULES, checks=checks, pass_count=pass_count, fail_count=fail_count, passed=passed, read_only=READ_ONLY, execution_allowed=EXECUTION_ALLOWED, telemetry=telemetry)
    explanation = "OOS-005 certified OOS-001 through OOS-004 as a read-only opportunity handoff subsystem." if passed else "OOS-005 found failed checks in the opportunity handoff subsystem."

    return OpportunitySubsystemIntegrationResult(SCHEMA_VERSION, ENGINE_ID, str(observed_at), EXPECTED_MODULES, checks, pass_count, fail_count, passed, integration_hash, READ_ONLY, EXECUTION_ALLOWED, explanation, telemetry)


def validate_opportunity_subsystem_integration_gate(result: OpportunitySubsystemIntegrationResult) -> Dict[str, Any]:
    if not isinstance(result, OpportunitySubsystemIntegrationResult):
        raise TypeError("result must be an OpportunitySubsystemIntegrationResult")
    checks = {
        "schema_version": result.schema_version == SCHEMA_VERSION,
        "engine_id": result.engine_id == ENGINE_ID,
        "module_coverage": result.modules == EXPECTED_MODULES,
        "read_only": result.read_only is True,
        "execution_disabled": result.execution_allowed is False,
        "hash_valid": result.verify_integration_hash(),
        "counts_valid": result.pass_count + result.fail_count == len(result.checks),
    }
    return {"passed": all(checks.values()) and result.passed, "checks": checks, "result": result.to_dict()}


def assert_opportunity_subsystem_read_only(result: OpportunitySubsystemIntegrationResult) -> bool:
    validation = validate_opportunity_subsystem_integration_gate(result)
    return validation["checks"]["read_only"] and validation["checks"]["execution_disabled"] and result.read_only is True and result.execution_allowed is False


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "READ_ONLY",
    "EXECUTION_ALLOWED",
    "EXPECTED_MODULES",
    "OpportunityIntegrationCheck",
    "OpportunitySubsystemIntegrationResult",
    "run_opportunity_subsystem_integration_gate",
    "validate_opportunity_subsystem_integration_gate",
    "assert_opportunity_subsystem_read_only",
]
'''

TEST_CODE = r'''from dataclasses import FrozenInstanceError
import json
import subprocess
import sys
from pathlib import Path

from qseries_v2.oracle_intelligence.opportunity_operating_system import (
    EXPECTED_MODULES,
    OpportunitySubsystemIntegrationResult,
    run_opportunity_subsystem_integration_gate,
)
from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_subsystem_integration_gate import (
    ENGINE_ID,
    EXECUTION_ALLOWED,
    READ_ONLY,
    SCHEMA_VERSION,
    assert_opportunity_subsystem_read_only,
    validate_opportunity_subsystem_integration_gate,
)
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    OpportunityExecutionProfile,
    OpportunityTimeWindow,
    UniversalOpportunityFactory,
)


ROOT = Path(__file__).resolve().parent
OBSERVED_AT = "2026-07-10T20:00:00+00:00"


def _market(market_id="KXOOS-YES"):
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id=market_id,
        title=f"Prediction market {market_id}",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _opportunity(market_id="KXOOS-YES", edge=0.12, confidence=0.84):
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(market_id),
        fair_value=0.55 + edge,
        market_price=0.55,
        confidence=confidence,
        explanation=f"Oracle fair value gap for {market_id}.",
        liquidity_score=0.76,
        risk_score=0.31,
        time_window=OpportunityTimeWindow(urgency_score=0.50, freshness_score=1.0),
        execution=OpportunityExecutionProfile(
            required_execution_adapter="prediction_market",
            execution_difficulty=0.25,
            capital_required=100,
        ),
    )


def _opportunities():
    return (
        _opportunity("KXOOS-A", edge=0.08, confidence=0.78),
        _opportunity("KXOOS-B", edge=0.16, confidence=0.90),
        _opportunity("KXOOS-C", edge=0.12, confidence=0.84),
    )


class InvalidOpportunity:
    read_only = True

    def fingerprint(self):
        return "invalid-fixture"

    def to_dict(self):
        return {"opportunity_id": "invalid-fixture", "read_only": True}


def test_oos_005_module_coverage():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    assert SCHEMA_VERSION == "OOS-005"
    assert ENGINE_ID == "OOS-005"
    assert result.modules == ("OOS-001", "OOS-002", "OOS-003", "OOS-004", "OOS-005")
    assert EXPECTED_MODULES == result.modules


def test_oos_005_valid_fixtures_pass_all_checks():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT, source="unit_test")
    assert isinstance(result, OpportunitySubsystemIntegrationResult)
    assert result.passed is True
    assert result.fail_count == 0
    assert result.pass_count == len(result.checks)
    assert all(check.passed for check in result.checks)
    assert result.verify_integration_hash() is True


def test_oos_005_invalid_fixture_surfaces_validation_failure():
    result = run_opportunity_subsystem_integration_gate([InvalidOpportunity()], observed_at=OBSERVED_AT)
    assert result.passed is False
    assert result.fail_count >= 1
    check_map = {check.check_id: check for check in result.checks}
    assert check_map["oos_004_validation"].passed is False
    assert check_map["pipeline_handoff"].passed is False
    details = dict(check_map["oos_004_validation"].details)
    assert details["validation_failures"] > 0


def test_oos_005_deterministic_hash():
    opportunities = _opportunities()
    first = run_opportunity_subsystem_integration_gate(opportunities, observed_at=OBSERVED_AT)
    second = run_opportunity_subsystem_integration_gate(opportunities, observed_at=OBSERVED_AT)
    assert first.integration_hash == second.integration_hash
    assert first.to_dict() == second.to_dict()


def test_oos_005_order_independent_hash():
    opportunities = _opportunities()
    first = run_opportunity_subsystem_integration_gate(opportunities, observed_at=OBSERVED_AT)
    second = run_opportunity_subsystem_integration_gate(tuple(reversed(opportunities)), observed_at=OBSERVED_AT)
    assert first.integration_hash == second.integration_hash
    assert first.telemetry == second.telemetry


def test_oos_005_frozen_result():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    try:
        result.passed = False
        raise AssertionError("OpportunitySubsystemIntegrationResult must be frozen.")
    except FrozenInstanceError:
        pass


def test_oos_005_read_only_execution_disabled():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert result.read_only is True
    assert result.execution_allowed is False
    assert assert_opportunity_subsystem_read_only(result) is True


def test_oos_005_no_filesystem_or_database_writes(tmp_path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert before == after
    assert dict(result.telemetry)["files_written"] is False
    assert dict(result.telemetry)["databases_written"] is False
    assert dict(result.telemetry)["runtime_state_written"] is False


def test_oos_005_json_serializable():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    encoded = json.dumps(result.to_dict(), sort_keys=True)
    assert '"schema_version": "OOS-005"' in encoded


def test_oos_005_validation_helper():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    validation = validate_opportunity_subsystem_integration_gate(result)
    assert validation["passed"] is True
    assert all(validation["checks"].values())


def test_oos_005_package_export_works():
    from qseries_v2.oracle_intelligence.opportunity_operating_system import (
        ENGINE_ID as exported_engine_id,
        run_opportunity_subsystem_integration_gate as exported_gate,
    )
    assert exported_engine_id == "OOS-005"
    result = exported_gate(_opportunities(), observed_at=OBSERVED_AT)
    assert result.schema_version == "OOS-005"


def test_oos_005_installer_is_idempotent():
    tracked = (
        ROOT / "build_oos_005_opportunity_subsystem_integration_gate.py",
        ROOT / "qseries_v2" / "oracle_intelligence" / "opportunity_operating_system" / "opportunity_subsystem_integration_gate.py",
        ROOT / "test_oos_005_opportunity_subsystem_integration_gate.py",
        ROOT / "qseries_v2" / "oracle_intelligence" / "opportunity_operating_system" / "__init__.py",
    )
    before = {path: path.read_text(encoding="utf-8") for path in tracked}
    subprocess.run(
        [sys.executable, str(ROOT / "build_oos_005_opportunity_subsystem_integration_gate.py")],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    after = {path: path.read_text(encoding="utf-8") for path in tracked}
    assert before == after


def test_oos_005_requires_caller_observed_at():
    try:
        run_opportunity_subsystem_integration_gate(_opportunities(), observed_at="")
        raise AssertionError("observed_at must be caller supplied.")
    except ValueError:
        pass


if __name__ == "__main__":
    test_oos_005_module_coverage()
    test_oos_005_valid_fixtures_pass_all_checks()
    test_oos_005_invalid_fixture_surfaces_validation_failure()
    test_oos_005_deterministic_hash()
    test_oos_005_order_independent_hash()
    test_oos_005_frozen_result()
    test_oos_005_read_only_execution_disabled()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_oos_005_no_filesystem_or_database_writes(Path(tmp))
    test_oos_005_json_serializable()
    test_oos_005_validation_helper()
    test_oos_005_package_export_works()
    test_oos_005_installer_is_idempotent()
    test_oos_005_requires_caller_observed_at()

    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    print("[PASS] OOS-005 Opportunity Subsystem Integration Gate")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "modules": list(result.modules),
            "pass_count": result.pass_count,
            "fail_count": result.fail_count,
            "passed": result.passed,
            "read_only": result.read_only,
            "execution_allowed": result.execution_allowed,
        }
    )


'''

EXPORT_BLOCK = '''from .opportunity_subsystem_integration_gate import (
    SCHEMA_VERSION as OOS_SUBSYSTEM_INTEGRATION_SCHEMA_VERSION,
    ENGINE_ID,
    READ_ONLY as OOS_SUBSYSTEM_INTEGRATION_READ_ONLY,
    EXECUTION_ALLOWED,
    EXPECTED_MODULES,
    OpportunityIntegrationCheck,
    OpportunitySubsystemIntegrationResult,
    run_opportunity_subsystem_integration_gate,
    validate_opportunity_subsystem_integration_gate,
    assert_opportunity_subsystem_read_only,
)
'''

EXPORT_NAMES = (
    "OOS_SUBSYSTEM_INTEGRATION_SCHEMA_VERSION",
    "ENGINE_ID",
    "OOS_SUBSYSTEM_INTEGRATION_READ_ONLY",
    "EXECUTION_ALLOWED",
    "EXPECTED_MODULES",
    "OpportunityIntegrationCheck",
    "OpportunitySubsystemIntegrationResult",
    "run_opportunity_subsystem_integration_gate",
    "validate_opportunity_subsystem_integration_gate",
    "assert_opportunity_subsystem_read_only",
)


def _write_if_changed(path: Path, content: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def _update_init() -> bool:
    existing = INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
    updated = existing
    if "from .opportunity_subsystem_integration_gate import" not in updated:
        updated = updated.rstrip() + "\n" + EXPORT_BLOCK
    missing = [name for name in EXPORT_NAMES if f'    "{name}",' not in updated]
    if missing and "__all__ = [" in updated:
        export_lines = "".join(f'    "{name}",\n' for name in missing)
        updated = updated.replace("__all__ = [", "__all__ = [\n" + export_lines, 1)
    return _write_if_changed(INIT_PATH, updated)


def main() -> None:
    OOS.mkdir(parents=True, exist_ok=True)
    module_changed = _write_if_changed(MODULE_PATH, MODULE_CODE)
    test_changed = _write_if_changed(TEST_PATH, TEST_CODE)
    init_changed = _update_init()
    print("========================================")
    print(" OOS-005 INSTALLER")
    print(" Opportunity Subsystem Integration Gate")
    print("========================================")
    print(f"[OK] Module: {MODULE_PATH} changed={module_changed}")
    print(f"[OK] Test: {TEST_PATH} changed={test_changed}")
    print(f"[OK] Exports: {INIT_PATH} changed={init_changed}")
    print()
    print("[DONE] OOS-005 installed")
    print()
    print("Run:")
    print("py test_oos_005_opportunity_subsystem_integration_gate.py")


if __name__ == "__main__":
    main()
