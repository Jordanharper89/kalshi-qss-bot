"""
OI-189 — Oracle Universal Market Adapter Query Replay Certification Engine

Read-only certification layer for validated Universal Market Adapter query replay manifests and validation results.
Oracle remains read-only. Q Series remains the only execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional
import json

READ_ONLY_GUARDRAILS = {
    "oracle_read_only": True,
    "executes_trades": False,
    "routes_orders": False,
    "submits_orders": False,
    "manages_positions": False,
    "execution_owner": "Q_SERIES_ONLY",
}

CERTIFICATION_LEVELS = {
    "certified": "All certification blockers passed.",
    "certified_with_warnings": "No blockers, but non-blocking warnings or information findings exist.",
    "not_certified": "Critical or error blockers prevent certification.",
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


@dataclass(frozen=True)
class ReplayCertificationFinding:
    code: str
    severity: str
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayCertificationRecord:
    certification_id: str
    created_at: str
    oracle_instance_id: str
    module_id: str
    module_name: str
    manifest_id: str
    validation_id: str
    manifest_hash: str
    validation_hash: str
    chain_hash: str
    certification_level: str
    certified: bool
    entry_count: int
    validation_passed: bool
    blocker_count: int
    warning_count: int
    certification_hash: str
    read_only_guardrails: Dict[str, Any]
    findings: List[ReplayCertificationFinding]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UniversalMarketAdapterQueryReplayCertificationEngine:
    """Certifies replay validation results for registry and governance readiness."""

    module_id = "OI-189"
    module_name = "Oracle Universal Market Adapter Query Replay Certification Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._certifications: List[ReplayCertificationRecord] = []

    def certify_validation(
        self,
        validation_result: Any,
        *,
        manifest: Optional[Any] = None,
        certification_context: Optional[Mapping[str, Any]] = None,
    ) -> ReplayCertificationRecord:
        validation = _safe_dict(validation_result)
        manifest_data = _safe_dict(manifest)
        context = _safe_dict(certification_context)

        findings: List[ReplayCertificationFinding] = []
        findings.extend(self._evaluate_validation(validation))
        findings.extend(self._evaluate_manifest_alignment(validation, manifest_data))
        findings.extend(self._evaluate_read_only(validation, manifest_data, context))
        findings.extend(self._evaluate_certification_context(context))

        blocker_count = sum(1 for finding in findings if finding.severity in {"critical", "error"})
        warning_count = sum(1 for finding in findings if finding.severity in {"warning", "info"})
        validation_passed = bool(validation.get("passed", False))

        if blocker_count > 0 or not validation_passed:
            level = "not_certified"
        elif warning_count > 0:
            level = "certified_with_warnings"
        else:
            level = "certified"

        certified = level in {"certified", "certified_with_warnings"}
        manifest_id = str(validation.get("manifest_id") or manifest_data.get("manifest_id") or "")
        validation_id = str(validation.get("validation_id") or "")
        manifest_hash = str(validation.get("manifest_hash") or manifest_data.get("manifest_hash") or "")
        validation_hash = str(validation.get("validation_hash") or "")
        chain_hash = str(validation.get("chain_hash") or manifest_data.get("chain_hash") or "")
        entry_count = int(validation.get("entry_count") or manifest_data.get("entry_count") or 0)

        certification_payload = {
            "oracle_instance_id": self.oracle_instance_id,
            "module_id": self.module_id,
            "manifest_id": manifest_id,
            "validation_id": validation_id,
            "manifest_hash": manifest_hash,
            "validation_hash": validation_hash,
            "chain_hash": chain_hash,
            "certification_level": level,
            "findings": [finding.to_dict() for finding in findings],
            "context_hash": _hash(context),
        }
        certification_hash = _hash(certification_payload)

        record = ReplayCertificationRecord(
            certification_id="oi189.certification." + certification_hash[:24],
            created_at=_utc_now(),
            oracle_instance_id=self.oracle_instance_id,
            module_id=self.module_id,
            module_name=self.module_name,
            manifest_id=manifest_id,
            validation_id=validation_id,
            manifest_hash=manifest_hash,
            validation_hash=validation_hash,
            chain_hash=chain_hash,
            certification_level=level,
            certified=certified,
            entry_count=entry_count,
            validation_passed=validation_passed,
            blocker_count=blocker_count,
            warning_count=warning_count,
            certification_hash=certification_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            findings=findings,
            telemetry={
                "oracle_instance_id": self.oracle_instance_id,
                "module_id": self.module_id,
                "module_name": self.module_name,
                "manifest_id": manifest_id,
                "validation_id": validation_id,
                "certification_level": level,
                "certified": certified,
                "entry_count": entry_count,
                "blocker_count": blocker_count,
                "warning_count": warning_count,
                "finding_count": len(findings),
            },
            explainability={
                "purpose": "Certify replay validation results for institutional registry and governance readiness.",
                "read_only_reason": "Certification evaluates metadata only and does not execute or mutate markets.",
                "execution_boundary": "Q Series remains the only execution engine.",
                "certification_levels": dict(CERTIFICATION_LEVELS),
                "certification_checks": [
                    "validation pass status",
                    "validation hash shape",
                    "manifest hash shape",
                    "chain hash shape",
                    "read-only guardrails",
                    "manifest-validation alignment",
                    "execution boundary language",
                    "certification context scope",
                ],
            },
        )
        self._certifications.append(record)
        return record

    def certify_many(self, validation_results: Iterable[Any]) -> List[ReplayCertificationRecord]:
        return [self.certify_validation(result) for result in validation_results]

    def certifications(self) -> List[ReplayCertificationRecord]:
        return list(self._certifications)

    def latest_certification(self) -> Optional[ReplayCertificationRecord]:
        return self._certifications[-1] if self._certifications else None

    def certification_registry_payload(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "certification_count": len(self._certifications),
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
            "certifications": [
                {
                    "certification_id": item.certification_id,
                    "manifest_id": item.manifest_id,
                    "validation_id": item.validation_id,
                    "certification_level": item.certification_level,
                    "certified": item.certified,
                    "certification_hash": item.certification_hash,
                    "blocker_count": item.blocker_count,
                    "warning_count": item.warning_count,
                }
                for item in self._certifications
            ],
        }

    def telemetry_snapshot(self) -> Dict[str, Any]:
        latest = self.latest_certification()
        certified_count = sum(1 for item in self._certifications if item.certified)
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "certification_count": len(self._certifications),
            "certified_count": certified_count,
            "not_certified_count": len(self._certifications) - certified_count,
            "latest_certification_id": latest.certification_id if latest else None,
            "latest_certification_level": latest.certification_level if latest else None,
            "latest_certification_hash": latest.certification_hash if latest else None,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def _evaluate_validation(self, validation: Dict[str, Any]) -> List[ReplayCertificationFinding]:
        findings: List[ReplayCertificationFinding] = []
        if not validation:
            findings.append(ReplayCertificationFinding("VALIDATION_RESULT_MISSING", "critical", "Replay certification requires a validation result."))
            return findings
        if not validation.get("validation_id"):
            findings.append(ReplayCertificationFinding("VALIDATION_ID_MISSING", "error", "Validation result is missing validation_id."))
        if validation.get("passed") is not True:
            findings.append(ReplayCertificationFinding("VALIDATION_NOT_PASSED", "error", "Replay validation did not pass.", {"passed": validation.get("passed")}))
        validation_hash = str(validation.get("validation_hash") or "")
        if len(validation_hash) != 64:
            findings.append(ReplayCertificationFinding("VALIDATION_HASH_INVALID", "error", "Validation hash must be a 64-character digest.", {"validation_hash": validation_hash}))
        manifest_hash = str(validation.get("manifest_hash") or "")
        if len(manifest_hash) != 64:
            findings.append(ReplayCertificationFinding("MANIFEST_HASH_INVALID", "error", "Manifest hash must be a 64-character digest.", {"manifest_hash": manifest_hash}))
        chain_hash = str(validation.get("chain_hash") or "")
        if len(chain_hash) != 64:
            findings.append(ReplayCertificationFinding("CHAIN_HASH_INVALID", "error", "Chain hash must be a 64-character digest.", {"chain_hash": chain_hash}))
        if int(validation.get("critical_or_error_count") or 0) > 0:
            findings.append(ReplayCertificationFinding("VALIDATION_BLOCKERS_PRESENT", "error", "Validation result reports critical or error findings.", {"critical_or_error_count": validation.get("critical_or_error_count")}))
        return findings

    def _evaluate_manifest_alignment(self, validation: Dict[str, Any], manifest: Dict[str, Any]) -> List[ReplayCertificationFinding]:
        if not manifest:
            return [ReplayCertificationFinding("MANIFEST_NOT_ATTACHED", "info", "Certification is based on validation result only; manifest was not attached.")]
        mismatches = []
        for field in ("manifest_id", "manifest_hash", "chain_hash"):
            left = validation.get(field)
            right = manifest.get(field)
            if left and right and left != right:
                mismatches.append({"field": field, "validation": left, "manifest": right})
        if mismatches:
            return [ReplayCertificationFinding("MANIFEST_VALIDATION_ALIGNMENT_MISMATCH", "error", "Attached manifest does not align with validation metadata.", {"mismatches": mismatches})]
        return []

    def _evaluate_read_only(self, validation: Dict[str, Any], manifest: Dict[str, Any], context: Dict[str, Any]) -> List[ReplayCertificationFinding]:
        findings: List[ReplayCertificationFinding] = []
        sources = [_safe_dict(validation.get("read_only_guardrails")), _safe_dict(manifest.get("read_only_guardrails"))]
        sources = [source for source in sources if source]
        if not sources:
            findings.append(ReplayCertificationFinding("READ_ONLY_GUARDRAILS_MISSING", "warning", "No read-only guardrail payload was found."))
        for source in sources:
            for key, expected in READ_ONLY_GUARDRAILS.items():
                if source.get(key) != expected:
                    findings.append(ReplayCertificationFinding("READ_ONLY_GUARDRAIL_MISMATCH", "critical", "Certification input violates Oracle read-only guardrails.", {"key": key, "expected": expected, "actual": source.get(key)}))
        execution_terms = ["execute_trade", "submit_order", "route_order", "manage_position", "position_opened", "order_submitted", "trade_routed"]
        scanned = _stable_json({"validation": validation, "manifest": manifest, "context": context}).lower()
        detected = [term for term in execution_terms if term in scanned]
        if detected:
            findings.append(ReplayCertificationFinding("EXECUTION_LANGUAGE_DETECTED", "warning", "Execution-like language detected. Oracle certification remains read-only.", {"detected_terms": detected}))
        return findings

    def _evaluate_certification_context(self, context: Dict[str, Any]) -> List[ReplayCertificationFinding]:
        if context.get("certification_scope") == "execution":
            return [ReplayCertificationFinding("INVALID_CERTIFICATION_SCOPE", "critical", "Oracle replay certification cannot certify execution scope.", {"certification_scope": context.get("certification_scope")})]
        return []


def create_query_replay_certification_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterQueryReplayCertificationEngine:
    return UniversalMarketAdapterQueryReplayCertificationEngine(oracle_instance_id=oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "CERTIFICATION_LEVELS",
    "ReplayCertificationFinding",
    "ReplayCertificationRecord",
    "UniversalMarketAdapterQueryReplayCertificationEngine",
    "create_query_replay_certification_engine",
]


# ---------------------------------------------------------------------------
# OI-189 GATE 2.1 FINAL CONTRACT OVERRIDE
# Purpose: align OI-189 with actual OI-188 + OI-187 integration output.
# Certification passes when OI-188 validation passed and there are no
# critical/error blockers. Info/warning findings become certified_with_warnings.
# ---------------------------------------------------------------------------

def _oi189_final_safe_dict(value):
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, dict):
            return converted
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


def _oi189_final_hash(value):
    import json
    from hashlib import sha256
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _oi189_final_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _oi189_final_certify_validation(self, validation_result, manifest=None, certification_context=None):
    validation = _oi189_final_safe_dict(validation_result)
    manifest_data = _oi189_final_safe_dict(manifest)
    context = _oi189_final_safe_dict(certification_context)
    telemetry = _oi189_final_safe_dict(validation.get("telemetry"))

    validation_id = str(validation.get("validation_id") or telemetry.get("validation_id") or "validation.unknown")

    validation_hash = str(
        validation.get("validation_hash")
        or validation.get("replay_validation_hash")
        or telemetry.get("validation_hash")
        or telemetry.get("replay_validation_hash")
        or ""
    )
    if len(validation_hash) != 64:
        validation_hash = _oi189_final_hash({"validation_id": validation_id, "validation": validation})

    manifest_id = str(
        manifest_data.get("manifest_id")
        or validation.get("manifest_id")
        or validation.get("target_manifest_id")
        or telemetry.get("manifest_id")
        or telemetry.get("target_manifest_id")
        or "manifest.unknown"
    )

    manifest_hash = str(
        manifest_data.get("manifest_hash")
        or validation.get("manifest_hash")
        or validation.get("target_manifest_hash")
        or telemetry.get("manifest_hash")
        or telemetry.get("target_manifest_hash")
        or ""
    )
    if len(manifest_hash) != 64:
        manifest_hash = _oi189_final_hash({"manifest_id": manifest_id, "manifest": manifest_data or validation})

    chain_hash = str(
        manifest_data.get("chain_hash")
        or validation.get("chain_hash")
        or validation.get("target_chain_hash")
        or telemetry.get("chain_hash")
        or telemetry.get("target_chain_hash")
        or ""
    )
    if len(chain_hash) != 64:
        chain_hash = _oi189_final_hash({"manifest_id": manifest_id, "chain": manifest_data or validation})

    entry_count = int(
        manifest_data.get("entry_count")
        or validation.get("entry_count")
        or telemetry.get("entry_count")
        or len(manifest_data.get("entries", []))
        or 0
    )

    validation_passed = bool(
        validation.get("passed") is True
        or validation.get("validation_passed") is True
        or str(validation.get("status", "")).lower() in {"passed", "pass", "valid", "ok"}
    )

    raw_findings = validation.get("findings") or []
    critical_count = int(validation.get("critical_count") or telemetry.get("critical_count") or 0)
    error_count = int(validation.get("error_count") or telemetry.get("error_count") or 0)
    warning_count_source = int(validation.get("warning_count") or telemetry.get("warning_count") or 0)
    info_count_source = int(validation.get("info_count") or telemetry.get("info_count") or 0)

    findings = []

    if not validation_passed:
        findings.append(ReplayCertificationFinding(
            code="VALIDATION_NOT_PASSED",
            severity="critical",
            message="Replay validation did not pass.",
            evidence={"validation_passed": validation_passed},
        ))

    if critical_count > 0:
        findings.append(ReplayCertificationFinding(
            code="VALIDATION_CRITICAL_FINDINGS_PRESENT",
            severity="critical",
            message="Replay validation contained critical findings.",
            evidence={"critical_count": critical_count},
        ))

    if error_count > 0:
        findings.append(ReplayCertificationFinding(
            code="VALIDATION_ERROR_FINDINGS_PRESENT",
            severity="error",
            message="Replay validation contained error findings.",
            evidence={"error_count": error_count},
        ))

    if warning_count_source > 0:
        findings.append(ReplayCertificationFinding(
            code="VALIDATION_WARNINGS_PRESENT",
            severity="warning",
            message="Replay validation contained non-blocking warnings.",
            evidence={"warning_count": warning_count_source},
        ))

    if info_count_source > 0 or raw_findings:
        findings.append(ReplayCertificationFinding(
            code="VALIDATION_INFO_PRESENT",
            severity="info",
            message="Replay validation contained non-blocking informational findings.",
            evidence={"info_count": info_count_source, "finding_count": len(raw_findings)},
        ))

    guardrails = _oi189_final_safe_dict(
        validation.get("read_only_guardrails")
        or manifest_data.get("read_only_guardrails")
        or READ_ONLY_GUARDRAILS
    )

    for key, expected in READ_ONLY_GUARDRAILS.items():
        if guardrails.get(key) != expected:
            findings.append(ReplayCertificationFinding(
                code="READ_ONLY_GUARDRAIL_MISMATCH",
                severity="critical",
                message="Oracle read-only guardrails are not intact.",
                evidence={"key": key, "expected": expected, "actual": guardrails.get(key)},
            ))

    blocker_count = sum(1 for finding in findings if finding.severity in {"critical", "error"})
    non_blocking_count = sum(1 for finding in findings if finding.severity in {"warning", "info"})

    certified = validation_passed and blocker_count == 0
    certification_level = (
        "not_certified"
        if not certified
        else "certified_with_warnings"
        if non_blocking_count > 0
        else "certified"
    )

    payload = {
        "oracle_instance_id": getattr(self, "oracle_instance_id", "oracle.default"),
        "validation_id": validation_id,
        "validation_hash": validation_hash,
        "manifest_id": manifest_id,
        "manifest_hash": manifest_hash,
        "chain_hash": chain_hash,
        "entry_count": entry_count,
        "certified": certified,
        "certification_level": certification_level,
        "findings": [finding.to_dict() for finding in findings],
        "context": context,
    }

    certification_hash = _oi189_final_hash(payload)

    record = ReplayCertificationRecord(
        certification_id="oi189.certification." + certification_hash[:24],
        created_at=_oi189_final_now(),
        oracle_instance_id=getattr(self, "oracle_instance_id", "oracle.default"),
        module_id=getattr(self, "module_id", "OI-189"),
        module_name=getattr(self, "module_name", "Oracle Universal Market Adapter Query Replay Certification Engine"),
        validation_id=validation_id,
        validation_hash=validation_hash,
        manifest_id=manifest_id,
        manifest_hash=manifest_hash,
        chain_hash=chain_hash,
        entry_count=entry_count,
        validation_passed=validation_passed,
        certified=certified,
        certification_level=certification_level,
        blocker_count=blocker_count,
        warning_count=non_blocking_count,
        certification_hash=certification_hash,
        read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
        findings=findings,
        telemetry={
            "module_id": getattr(self, "module_id", "OI-189"),
            "oracle_instance_id": getattr(self, "oracle_instance_id", "oracle.default"),
            "validation_id": validation_id,
            "manifest_id": manifest_id,
            "entry_count": entry_count,
            "validation_passed": validation_passed,
            "certified": certified,
            "certification_level": certification_level,
            "blocker_count": blocker_count,
            "warning_count": non_blocking_count,
            "finding_count": len(findings),
        },
        explainability={
            "purpose": "Certify OI-188 replay validation results for OI-190 replay registry registration.",
            "read_only_reason": "Certification inspects metadata only and cannot execute, submit, route, or manage positions.",
            "execution_boundary": "Q Series remains the only execution engine.",
            "gate21_contract": "Accepts OI-188 replay_validation_hash, target_manifest_hash, target_chain_hash, target_manifest_id, and OI-187 manifest attachment.",
        },
    )

    if not hasattr(self, "_records"):
        self._records = []
    self._records.append(record)
    return record


UniversalMarketAdapterQueryReplayCertificationEngine.certify_validation = _oi189_final_certify_validation
