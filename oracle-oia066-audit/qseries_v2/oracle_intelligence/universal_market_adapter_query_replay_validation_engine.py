"""
OI-188 — Oracle Universal Market Adapter Query Replay Validation Engine

Read-only validation layer for Universal Market Adapter query replay manifests.

This engine validates replay manifests produced by OI-187. It verifies replay
integrity, deterministic ordering, dependency references, lineage consistency,
manifest hash context, chain hash context, explainability completeness, and
institutional telemetry readiness.

It never executes trades, never routes orders, never submits orders, never
manages positions, and never mutates market state. Oracle Intelligence remains
read-only. Q Series remains the sole execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
import json
import uuid


READ_ONLY_GUARDRAILS = {
    "oracle_read_only": True,
    "executes_trades": False,
    "routes_orders": False,
    "submits_orders": False,
    "manages_positions": False,
    "execution_owner": "Q_SERIES_ONLY",
}

REQUIRED_MANIFEST_FIELDS = [
    "manifest_id",
    "created_at",
    "oracle_instance_id",
    "module_id",
    "module_name",
    "manifest_version",
    "entry_count",
    "passed_count",
    "failed_count",
    "adapter_count",
    "query_count",
    "dependency_count",
    "manifest_hash",
    "chain_hash",
    "read_only_guardrails",
    "entries",
    "findings",
    "telemetry",
    "explainability",
]

REQUIRED_ENTRY_FIELDS = [
    "sequence",
    "audit_id",
    "adapter_id",
    "query_id",
    "replay_key",
    "passed",
    "query_hash",
    "resolver_hash",
    "market_model_hash",
    "source_hash",
    "finding_codes",
    "dependency_keys",
    "lineage",
    "integrity_hash",
]


_EXECUTION_LANGUAGE = {
    "execute",
    "executed",
    "execution",
    "submit_order",
    "route_order",
    "order_submitted",
    "trade_routed",
    "position_opened",
    "buy",
    "sell",
    "fill",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _safe_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, Mapping):
            return dict(converted)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


def _safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text.lower())


@dataclass(frozen=True)
class ReplayValidationFinding:
    code: str
    severity: str
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayValidationCheck:
    check_id: str
    name: str
    passed: bool
    severity: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayValidationReport:
    validation_id: str
    created_at: str
    oracle_instance_id: str
    module_id: str
    module_name: str
    target_manifest_id: str
    target_manifest_hash: str
    target_chain_hash: str
    passed: bool
    score: float
    check_count: int
    passed_check_count: int
    failed_check_count: int
    critical_count: int
    error_count: int
    warning_count: int
    info_count: int
    read_only_guardrails: Dict[str, Any]
    checks: List[ReplayValidationCheck]
    findings: List[ReplayValidationFinding]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]
    replay_validation_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UniversalMarketAdapterQueryReplayValidationEngine:
    """
    Validates OI-187 replay manifests without execution authority.

    The report produced by this engine is suitable for institutional telemetry,
    architecture registry review, replay governance, and deterministic audit
    trails. It is intentionally read-only and never mutates source manifests.
    """

    module_id = "OI-188"
    module_name = "Oracle Universal Market Adapter Query Replay Validation Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._reports: List[ReplayValidationReport] = []

    def validate_manifest(
        self,
        manifest: Any,
        *,
        strict_hash_validation: bool = False,
        validation_context: Optional[Mapping[str, Any]] = None,
    ) -> ReplayValidationReport:
        manifest_data = self._normalize_manifest(manifest)
        context = _safe_dict(validation_context)

        checks: List[ReplayValidationCheck] = []
        findings: List[ReplayValidationFinding] = []

        self._check_required_manifest_fields(manifest_data, checks, findings)
        entries = [_safe_dict(entry) for entry in _safe_list(manifest_data.get("entries"))]

        self._check_read_only_guardrails(manifest_data, checks, findings)
        self._check_entry_structure(entries, checks, findings)
        self._check_entry_counts(manifest_data, entries, checks, findings)
        self._check_deterministic_order(entries, checks, findings)
        self._check_unique_identifiers(entries, checks, findings)
        self._check_hash_shapes(manifest_data, entries, checks, findings)
        self._check_dependency_references(entries, checks, findings)
        self._check_lineage_consistency(entries, checks, findings)
        self._check_explainability(manifest_data, checks, findings)
        self._check_telemetry(manifest_data, checks, findings)
        self._check_execution_boundary(manifest_data, entries, context, checks, findings)
        self._check_manifest_findings(manifest_data, checks, findings)

        if strict_hash_validation:
            self._check_strict_manifest_hash(manifest_data, entries, context, checks, findings)

        critical_count = sum(1 for finding in findings if finding.severity == "critical")
        error_count = sum(1 for finding in findings if finding.severity == "error")
        warning_count = sum(1 for finding in findings if finding.severity == "warning")
        info_count = sum(1 for finding in findings if finding.severity == "info")
        failed_check_count = sum(1 for check in checks if not check.passed)
        passed_check_count = len(checks) - failed_check_count

        hard_failure = critical_count > 0 or error_count > 0
        passed = not hard_failure
        score = self._score(checks, findings)

        target_manifest_id = str(manifest_data.get("manifest_id") or "unknown.manifest")
        target_manifest_hash = str(manifest_data.get("manifest_hash") or "")
        target_chain_hash = str(manifest_data.get("chain_hash") or "")

        validation_payload = {
            "oracle_instance_id": self.oracle_instance_id,
            "module_id": self.module_id,
            "target_manifest_id": target_manifest_id,
            "target_manifest_hash": target_manifest_hash,
            "target_chain_hash": target_chain_hash,
            "passed": passed,
            "score": score,
            "checks": [check.to_dict() for check in checks],
            "findings": [finding.to_dict() for finding in findings],
        }
        validation_hash = _hash(validation_payload)

        report = ReplayValidationReport(
            validation_id="oi188.validation." + validation_hash[:24],
            created_at=_utc_now(),
            oracle_instance_id=self.oracle_instance_id,
            module_id=self.module_id,
            module_name=self.module_name,
            target_manifest_id=target_manifest_id,
            target_manifest_hash=target_manifest_hash,
            target_chain_hash=target_chain_hash,
            passed=passed,
            score=score,
            check_count=len(checks),
            passed_check_count=passed_check_count,
            failed_check_count=failed_check_count,
            critical_count=critical_count,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            checks=checks,
            findings=findings,
            telemetry={
                "oracle_instance_id": self.oracle_instance_id,
                "module_id": self.module_id,
                "module_name": self.module_name,
                "target_manifest_id": target_manifest_id,
                "entry_count": len(entries),
                "check_count": len(checks),
                "passed_check_count": passed_check_count,
                "failed_check_count": failed_check_count,
                "critical_count": critical_count,
                "error_count": error_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "strict_hash_validation": strict_hash_validation,
                "context_hash": _hash(context),
            },
            explainability={
                "purpose": "Validate query replay manifests generated by Oracle Intelligence replay infrastructure.",
                "read_only_reason": "Validation only inspects manifest metadata and produces a report; it does not execute or mutate market state.",
                "execution_boundary": "Q Series remains the only execution engine.",
                "validated_dimensions": [
                    "manifest required fields",
                    "read-only guardrails",
                    "entry structure",
                    "summary counts",
                    "deterministic ordering",
                    "unique identifiers",
                    "hash shape",
                    "dependency references",
                    "lineage consistency",
                    "explainability completeness",
                    "telemetry completeness",
                    "execution-boundary language",
                    "manifest findings",
                ],
                "score_method": "Starts at 100 and subtracts weighted penalties for critical, error, warning, info findings and failed checks.",
                "strict_hash_validation": strict_hash_validation,
            },
            replay_validation_hash=validation_hash,
        )

        self._reports.append(report)
        return report

    def validate_many(
        self,
        manifests: Iterable[Any],
        *,
        strict_hash_validation: bool = False,
        validation_context: Optional[Mapping[str, Any]] = None,
    ) -> List[ReplayValidationReport]:
        return [
            self.validate_manifest(
                manifest,
                strict_hash_validation=strict_hash_validation,
                validation_context=validation_context,
            )
            for manifest in manifests
        ]

    def reports(self) -> List[ReplayValidationReport]:
        return list(self._reports)

    def latest_report(self) -> Optional[ReplayValidationReport]:
        return self._reports[-1] if self._reports else None

    def telemetry_snapshot(self) -> Dict[str, Any]:
        latest = self.latest_report()
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "report_count": len(self._reports),
            "latest_validation_id": latest.validation_id if latest else None,
            "latest_passed": latest.passed if latest else None,
            "latest_score": latest.score if latest else None,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def validation_registry_record(self, report: Optional[ReplayValidationReport] = None) -> Dict[str, Any]:
        selected = report or self.latest_report()
        if selected is None:
            return {
                "module_id": self.module_id,
                "oracle_instance_id": self.oracle_instance_id,
                "record_status": "empty",
                "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
            }

        return {
            "record_status": "ready",
            "validation_id": selected.validation_id,
            "target_manifest_id": selected.target_manifest_id,
            "target_manifest_hash": selected.target_manifest_hash,
            "target_chain_hash": selected.target_chain_hash,
            "passed": selected.passed,
            "score": selected.score,
            "replay_validation_hash": selected.replay_validation_hash,
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
            "telemetry": selected.telemetry,
            "explainability": selected.explainability,
        }

    def _normalize_manifest(self, manifest: Any) -> Dict[str, Any]:
        return _safe_dict(manifest)

    def _add_check(
        self,
        checks: List[ReplayValidationCheck],
        *,
        name: str,
        passed: bool,
        severity: str,
        evidence: Optional[Mapping[str, Any]] = None,
    ) -> None:
        checks.append(ReplayValidationCheck(
            check_id="oi188.check." + _hash({
                "name": name,
                "passed": passed,
                "severity": severity,
                "evidence": _safe_dict(evidence),
                "ordinal": len(checks) + 1,
            })[:24],
            name=name,
            passed=passed,
            severity=severity,
            evidence=_safe_dict(evidence),
        ))

    def _add_finding(
        self,
        findings: List[ReplayValidationFinding],
        *,
        code: str,
        severity: str,
        message: str,
        evidence: Optional[Mapping[str, Any]] = None,
    ) -> None:
        findings.append(ReplayValidationFinding(
            code=code,
            severity=severity,
            message=message,
            evidence=_safe_dict(evidence),
        ))

    def _check_required_manifest_fields(
        self,
        manifest: Dict[str, Any],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
        passed = not missing
        self._add_check(checks, name="required_manifest_fields", passed=passed, severity="error", evidence={"missing": missing})
        if missing:
            self._add_finding(
                findings,
                code="MANIFEST_REQUIRED_FIELDS_MISSING",
                severity="error",
                message="Replay manifest is missing required institutional fields.",
                evidence={"missing": missing},
            )

    def _check_read_only_guardrails(
        self,
        manifest: Dict[str, Any],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        guardrails = _safe_dict(manifest.get("read_only_guardrails"))
        mismatches = {
            key: {"expected": expected, "actual": guardrails.get(key)}
            for key, expected in READ_ONLY_GUARDRAILS.items()
            if guardrails.get(key) != expected
        }
        passed = not mismatches
        self._add_check(checks, name="read_only_guardrails", passed=passed, severity="critical", evidence={"mismatches": mismatches})
        if mismatches:
            self._add_finding(
                findings,
                code="READ_ONLY_GUARDRAILS_MISMATCH",
                severity="critical",
                message="Replay manifest guardrails do not preserve Oracle read-only boundaries.",
                evidence={"mismatches": mismatches},
            )

    def _check_entry_structure(
        self,
        entries: List[Dict[str, Any]],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        missing_by_entry: Dict[str, List[str]] = {}
        for index, entry in enumerate(entries):
            audit_id = str(entry.get("audit_id") or f"entry_index_{index}")
            missing = [field for field in REQUIRED_ENTRY_FIELDS if field not in entry]
            if missing:
                missing_by_entry[audit_id] = missing
        passed = not missing_by_entry
        self._add_check(checks, name="entry_required_fields", passed=passed, severity="error", evidence={"missing_by_entry": missing_by_entry})
        if missing_by_entry:
            self._add_finding(
                findings,
                code="ENTRY_REQUIRED_FIELDS_MISSING",
                severity="error",
                message="One or more replay entries are missing required fields.",
                evidence={"missing_by_entry": missing_by_entry},
            )

    def _check_entry_counts(
        self,
        manifest: Dict[str, Any],
        entries: List[Dict[str, Any]],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        expected_entry_count = int(manifest.get("entry_count") or 0)
        expected_passed = int(manifest.get("passed_count") or 0)
        expected_failed = int(manifest.get("failed_count") or 0)
        expected_adapters = int(manifest.get("adapter_count") or 0)
        expected_queries = int(manifest.get("query_count") or 0)
        expected_dependencies = int(manifest.get("dependency_count") or 0)

        actual_entry_count = len(entries)
        actual_passed = sum(1 for entry in entries if bool(entry.get("passed")))
        actual_failed = actual_entry_count - actual_passed
        actual_adapters = len({str(entry.get("adapter_id")) for entry in entries}) if entries else 0
        actual_queries = len({str(entry.get("query_id")) for entry in entries}) if entries else 0
        actual_dependencies = sum(len(_safe_list(entry.get("dependency_keys"))) for entry in entries)

        mismatches = {}
        comparisons = {
            "entry_count": (expected_entry_count, actual_entry_count),
            "passed_count": (expected_passed, actual_passed),
            "failed_count": (expected_failed, actual_failed),
            "adapter_count": (expected_adapters, actual_adapters),
            "query_count": (expected_queries, actual_queries),
            "dependency_count": (expected_dependencies, actual_dependencies),
        }
        for key, (expected, actual) in comparisons.items():
            if expected != actual:
                mismatches[key] = {"expected": expected, "actual": actual}

        passed = not mismatches
        self._add_check(checks, name="manifest_summary_counts", passed=passed, severity="error", evidence={"mismatches": mismatches})
        if mismatches:
            self._add_finding(
                findings,
                code="MANIFEST_SUMMARY_COUNT_MISMATCH",
                severity="error",
                message="Manifest summary counts do not match replay entries.",
                evidence={"mismatches": mismatches},
            )

    def _check_deterministic_order(
        self,
        entries: List[Dict[str, Any]],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        actual_order = [(entry.get("replay_key"), entry.get("audit_id"), entry.get("adapter_id"), entry.get("query_id")) for entry in entries]
        expected_entries = sorted(entries, key=lambda item: (
            str(item.get("replay_key") or ""),
            str(item.get("audit_id") or ""),
            str(item.get("adapter_id") or ""),
            str(item.get("query_id") or ""),
        ))
        expected_order = [(entry.get("replay_key"), entry.get("audit_id"), entry.get("adapter_id"), entry.get("query_id")) for entry in expected_entries]
        sequence_values = [entry.get("sequence") for entry in entries]
        expected_sequence = list(range(1, len(entries) + 1))
        passed = actual_order == expected_order and sequence_values == expected_sequence
        self._add_check(checks, name="deterministic_order", passed=passed, severity="error", evidence={"sequence_values": sequence_values, "expected_sequence": expected_sequence})
        if not passed:
            self._add_finding(
                findings,
                code="NON_DETERMINISTIC_REPLAY_ORDER",
                severity="error",
                message="Replay entries are not ordered deterministically or sequence values are inconsistent.",
                evidence={"sequence_values": sequence_values, "expected_sequence": expected_sequence},
            )

    def _check_unique_identifiers(
        self,
        entries: List[Dict[str, Any]],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        audit_ids = [str(entry.get("audit_id") or "") for entry in entries]
        replay_keys = [str(entry.get("replay_key") or "") for entry in entries]
        duplicate_audit_ids = sorted(item for item in set(audit_ids) if audit_ids.count(item) > 1 and item)
        duplicate_replay_keys = sorted(item for item in set(replay_keys) if replay_keys.count(item) > 1 and item)
        passed = not duplicate_audit_ids and not duplicate_replay_keys
        self._add_check(checks, name="unique_replay_identifiers", passed=passed, severity="error", evidence={"duplicate_audit_ids": duplicate_audit_ids, "duplicate_replay_keys": duplicate_replay_keys})
        if duplicate_audit_ids or duplicate_replay_keys:
            self._add_finding(
                findings,
                code="DUPLICATE_REPLAY_IDENTIFIERS",
                severity="error",
                message="Replay manifest contains duplicate audit ids or replay keys.",
                evidence={"duplicate_audit_ids": duplicate_audit_ids, "duplicate_replay_keys": duplicate_replay_keys},
            )

    def _check_hash_shapes(
        self,
        manifest: Dict[str, Any],
        entries: List[Dict[str, Any]],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        invalid_manifest_hashes = [field for field in ("manifest_hash", "chain_hash") if not _is_sha256(manifest.get(field))]
        invalid_entry_hashes: Dict[str, List[str]] = {}
        for entry in entries:
            audit_id = str(entry.get("audit_id") or "unknown")
            bad = [field for field in ("query_hash", "resolver_hash", "market_model_hash", "source_hash", "integrity_hash") if not _is_sha256(entry.get(field))]
            if bad:
                invalid_entry_hashes[audit_id] = bad
        passed = not invalid_manifest_hashes and not invalid_entry_hashes
        self._add_check(checks, name="hash_shape_validation", passed=passed, severity="warning", evidence={"invalid_manifest_hashes": invalid_manifest_hashes, "invalid_entry_hashes": invalid_entry_hashes})
        if not passed:
            self._add_finding(
                findings,
                code="HASH_SHAPE_WEAK",
                severity="warning",
                message="Some manifest or entry hashes are not valid SHA-256 hex strings.",
                evidence={"invalid_manifest_hashes": invalid_manifest_hashes, "invalid_entry_hashes": invalid_entry_hashes},
            )

    def _check_dependency_references(
        self,
        entries: List[Dict[str, Any]],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        known = {str(entry.get("replay_key")) for entry in entries}
        dangling: Dict[str, List[str]] = {}
        self_references: List[str] = []
        for entry in entries:
            replay_key = str(entry.get("replay_key") or "")
            deps = [str(dep) for dep in _safe_list(entry.get("dependency_keys"))]
            missing = [dep for dep in deps if dep not in known]
            if missing:
                dangling[replay_key] = missing
            if replay_key in deps:
                self_references.append(replay_key)
        passed = not dangling and not self_references
        self._add_check(checks, name="dependency_references", passed=passed, severity="warning", evidence={"dangling": dangling, "self_references": self_references})
        if dangling:
            self._add_finding(
                findings,
                code="DANGLING_REPLAY_DEPENDENCIES",
                severity="warning",
                message="Replay manifest has dependency references that are not present in the manifest.",
                evidence={"dangling": dangling},
            )
        if self_references:
            self._add_finding(
                findings,
                code="SELF_REFERENTIAL_REPLAY_DEPENDENCY",
                severity="warning",
                message="Replay manifest has self-referential dependencies.",
                evidence={"self_references": self_references},
            )

    def _check_lineage_consistency(
        self,
        entries: List[Dict[str, Any]],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        mismatches: Dict[str, Dict[str, Dict[str, Any]]] = {}
        lineage_fields = ["audit_id", "adapter_id", "query_id", "replay_key", "query_hash", "resolver_hash", "market_model_hash", "source_hash"]
        for entry in entries:
            lineage = _safe_dict(entry.get("lineage"))
            audit_id = str(entry.get("audit_id") or "unknown")
            entry_mismatches = {}
            for field in lineage_fields:
                if str(lineage.get(field) or "") != str(entry.get(field) or ""):
                    entry_mismatches[field] = {"entry": entry.get(field), "lineage": lineage.get(field)}
            if entry_mismatches:
                mismatches[audit_id] = entry_mismatches
        passed = not mismatches
        self._add_check(checks, name="lineage_consistency", passed=passed, severity="error", evidence={"mismatches": mismatches})
        if mismatches:
            self._add_finding(
                findings,
                code="LINEAGE_CONTEXT_MISMATCH",
                severity="error",
                message="Replay entry lineage does not match top-level entry fields.",
                evidence={"mismatches": mismatches},
            )

    def _check_explainability(
        self,
        manifest: Dict[str, Any],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        explainability = _safe_dict(manifest.get("explainability"))
        required = ["purpose", "read_only_reason", "execution_boundary", "ordering_method", "integrity_method"]
        missing = [field for field in required if not explainability.get(field)]
        passed = not missing
        self._add_check(checks, name="explainability_completeness", passed=passed, severity="warning", evidence={"missing": missing})
        if missing:
            self._add_finding(
                findings,
                code="EXPLAINABILITY_CONTEXT_WEAK",
                severity="warning",
                message="Replay manifest explainability metadata is incomplete.",
                evidence={"missing": missing},
            )

    def _check_telemetry(
        self,
        manifest: Dict[str, Any],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        telemetry = _safe_dict(manifest.get("telemetry"))
        required = ["oracle_instance_id", "module_id", "module_name", "entry_count", "passed_count", "failed_count"]
        missing = [field for field in required if field not in telemetry]
        passed = not missing
        self._add_check(checks, name="telemetry_completeness", passed=passed, severity="warning", evidence={"missing": missing})
        if missing:
            self._add_finding(
                findings,
                code="TELEMETRY_CONTEXT_WEAK",
                severity="warning",
                message="Replay manifest telemetry metadata is incomplete.",
                evidence={"missing": missing},
            )

    def _check_execution_boundary(
        self,
        manifest: Dict[str, Any],
        entries: List[Dict[str, Any]],
        context: Dict[str, Any],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        payload = _stable_json({"manifest": manifest, "context": context}).lower()
        hard_flags = []
        for flag in ("executed", "order_submitted", "trade_routed", "position_opened"):
            pass
        for entry in entries:
            finding_codes = [str(code) for code in _safe_list(entry.get("finding_codes"))]
            if "EXECUTION_BOUNDARY_VIOLATION" in finding_codes:
                hard_flags.append(str(entry.get("audit_id") or entry.get("replay_key") or "unknown"))
        detected_terms = sorted(term for term in _EXECUTION_LANGUAGE if term in payload)
        passed = not hard_flags
        self._add_check(checks, name="execution_boundary_validation", passed=passed, severity="critical", evidence={"hard_flags": hard_flags, "detected_terms": detected_terms})
        if hard_flags:
            self._add_finding(
                findings,
                code="EXECUTION_BOUNDARY_REPLAY_VALIDATION_FAILURE",
                severity="critical",
                message="Replay manifest includes records marked with execution-boundary violations. Oracle remains read-only.",
                evidence={"audit_ids": hard_flags},
            )
        elif detected_terms:
            self._add_finding(
                findings,
                code="EXECUTION_LANGUAGE_PRESENT_FOR_REVIEW",
                severity="info",
                message="Execution-like language appears in replay metadata, but no hard execution-boundary violation was found.",
                evidence={"detected_terms": detected_terms},
            )

    def _check_manifest_findings(
        self,
        manifest: Dict[str, Any],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        manifest_findings = [_safe_dict(item) for item in _safe_list(manifest.get("findings"))]
        critical_or_error = [item for item in manifest_findings if item.get("severity") in {"critical", "error"}]
        passed = not critical_or_error
        self._add_check(checks, name="manifest_internal_findings", passed=passed, severity="error", evidence={"critical_or_error_count": len(critical_or_error)})
        if critical_or_error:
            self._add_finding(
                findings,
                code="MANIFEST_INTERNAL_FINDINGS_BLOCKING",
                severity="error",
                message="Replay manifest already contains critical or error findings.",
                evidence={"blocking_findings": critical_or_error},
            )

    def _check_strict_manifest_hash(
        self,
        manifest: Dict[str, Any],
        entries: List[Dict[str, Any]],
        context: Dict[str, Any],
        checks: List[ReplayValidationCheck],
        findings: List[ReplayValidationFinding],
    ) -> None:
        chain = "oi187.chain.root"
        chain_inputs = []
        for entry in entries:
            item = {
                "previous_chain_hash": chain,
                "entry_integrity_hash": entry.get("integrity_hash"),
                "audit_id": entry.get("audit_id"),
                "replay_key": entry.get("replay_key"),
                "sequence": entry.get("sequence"),
            }
            chain_inputs.append(item)
            chain = _hash(item)
        expected_chain_hash = chain
        actual_chain_hash = str(manifest.get("chain_hash") or "")
        passed = expected_chain_hash == actual_chain_hash
        self._add_check(checks, name="strict_chain_hash_validation", passed=passed, severity="warning", evidence={"expected_chain_hash": expected_chain_hash, "actual_chain_hash": actual_chain_hash})
        if not passed:
            self._add_finding(
                findings,
                code="STRICT_CHAIN_HASH_MISMATCH",
                severity="warning",
                message="Strict chain hash recalculation does not match manifest chain hash.",
                evidence={"expected_chain_hash": expected_chain_hash, "actual_chain_hash": actual_chain_hash},
            )

    def _score(self, checks: List[ReplayValidationCheck], findings: List[ReplayValidationFinding]) -> float:
        score = 100.0
        score -= 35.0 * sum(1 for finding in findings if finding.severity == "critical")
        score -= 20.0 * sum(1 for finding in findings if finding.severity == "error")
        score -= 6.0 * sum(1 for finding in findings if finding.severity == "warning")
        score -= 1.0 * sum(1 for finding in findings if finding.severity == "info")
        score -= 2.0 * sum(1 for check in checks if not check.passed)
        if score < 0:
            score = 0.0
        if score > 100:
            score = 100.0
        return round(score, 2)


def create_query_replay_validation_engine(
    oracle_instance_id: str = "oracle.default",
) -> UniversalMarketAdapterQueryReplayValidationEngine:
    return UniversalMarketAdapterQueryReplayValidationEngine(
        oracle_instance_id=oracle_instance_id
    )


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "REQUIRED_MANIFEST_FIELDS",
    "REQUIRED_ENTRY_FIELDS",
    "ReplayValidationFinding",
    "ReplayValidationCheck",
    "ReplayValidationReport",
    "UniversalMarketAdapterQueryReplayValidationEngine",
    "create_query_replay_validation_engine",
]
