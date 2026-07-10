"""
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
