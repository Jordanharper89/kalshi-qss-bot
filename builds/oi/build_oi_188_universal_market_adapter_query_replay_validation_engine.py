from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "universal_market_adapter_query_replay_validation_engine.py"
TEST = ROOT / "test_oi_188_universal_market_adapter_query_replay_validation_engine.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
"""
OI-188 — Oracle Universal Market Adapter Query Replay Validation Engine

Read-only validation layer for OI-187 replay manifests.

This engine validates replay manifests for deterministic structure, lineage
integrity, dependency integrity, chain consistency, replay package readiness,
explainability, telemetry, Universal Market Model compatibility, and Oracle
execution-boundary preservation.

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
class ReplayValidationFinding:
    code: str
    severity: str
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayValidationResult:
    validation_id: str
    created_at: str
    oracle_instance_id: str
    module_id: str
    module_name: str
    manifest_id: str
    manifest_hash: str
    chain_hash: str
    entry_count: int
    validated_entry_count: int
    finding_count: int
    critical_or_error_count: int
    passed: bool
    validation_hash: str
    read_only_guardrails: Dict[str, Any]
    findings: List[ReplayValidationFinding]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UniversalMarketAdapterQueryReplayValidationEngine:
    """
    Validates OI-187 replay manifests without creating execution authority.
    """

    module_id = "OI-188"
    module_name = "Oracle Universal Market Adapter Query Replay Validation Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._results: List[ReplayValidationResult] = []

    def validate_manifest(self, manifest: Any) -> ReplayValidationResult:
        data = _safe_dict(manifest)
        entries = [_safe_dict(entry) for entry in _safe_list(data.get("entries"))]
        findings: List[ReplayValidationFinding] = []

        findings.extend(self._validate_top_level(data))
        findings.extend(self._validate_entries(entries))
        findings.extend(self._validate_dependencies(entries))
        findings.extend(self._validate_chain(data, entries))
        findings.extend(self._validate_read_only(data, entries))
        findings.extend(self._validate_explainability(data))
        findings.extend(self._validate_telemetry(data))

        critical_or_error_count = sum(
            1 for finding in findings
            if finding.severity in {"critical", "error"}
        )
        passed = critical_or_error_count == 0

        manifest_id = str(data.get("manifest_id") or "")
        manifest_hash = str(data.get("manifest_hash") or "")
        chain_hash = str(data.get("chain_hash") or "")

        validation_payload = {
            "oracle_instance_id": self.oracle_instance_id,
            "module_id": self.module_id,
            "manifest_id": manifest_id,
            "manifest_hash": manifest_hash,
            "chain_hash": chain_hash,
            "entry_count": len(entries),
            "findings": [finding.to_dict() for finding in findings],
        }
        validation_hash = _hash(validation_payload)

        result = ReplayValidationResult(
            validation_id="oi188.validation." + validation_hash[:24],
            created_at=_utc_now(),
            oracle_instance_id=self.oracle_instance_id,
            module_id=self.module_id,
            module_name=self.module_name,
            manifest_id=manifest_id,
            manifest_hash=manifest_hash,
            chain_hash=chain_hash,
            entry_count=int(data.get("entry_count") or len(entries)),
            validated_entry_count=len(entries),
            finding_count=len(findings),
            critical_or_error_count=critical_or_error_count,
            passed=passed,
            validation_hash=validation_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            findings=findings,
            telemetry={
                "oracle_instance_id": self.oracle_instance_id,
                "module_id": self.module_id,
                "module_name": self.module_name,
                "manifest_id": manifest_id,
                "manifest_hash": manifest_hash,
                "chain_hash": chain_hash,
                "entry_count": len(entries),
                "finding_count": len(findings),
                "critical_or_error_count": critical_or_error_count,
                "passed": passed,
            },
            explainability={
                "purpose": "Validate replay manifest readiness, lineage integrity, dependency integrity, and replay determinism.",
                "read_only_reason": "Validation checks metadata and hashes only; it does not execute trades or mutate market state.",
                "execution_boundary": "Q Series remains the only execution engine.",
                "validation_checks": [
                    "top-level manifest identity",
                    "manifest hash shape",
                    "entry count consistency",
                    "entry lineage completeness",
                    "duplicate replay keys",
                    "duplicate audit ids",
                    "dependency references",
                    "chain hash shape",
                    "read-only guardrails",
                    "execution-boundary findings",
                    "explainability fields",
                    "telemetry fields",
                ],
            },
        )

        self._results.append(result)
        return result

    def validate_package(self, replay_package: Any) -> ReplayValidationResult:
        package = _safe_dict(replay_package)
        manifest_like = {
            "manifest_id": package.get("manifest_id", ""),
            "manifest_hash": package.get("manifest_hash", ""),
            "chain_hash": package.get("chain_hash", ""),
            "entry_count": len(_safe_list(package.get("entries"))),
            "entries": package.get("entries", []),
            "findings": package.get("findings", []),
            "read_only_guardrails": package.get("read_only_guardrails", {}),
            "explainability": package.get("explainability", {}),
            "telemetry": {
                "package_id": package.get("package_id"),
                "package_status": package.get("package_status"),
            },
        }
        result = self.validate_manifest(manifest_like)

        if package.get("package_status") != "ready":
            extra = ReplayValidationFinding(
                code="REPLAY_PACKAGE_NOT_READY",
                severity="error",
                message="Replay package is not marked ready.",
                evidence={"package_status": package.get("package_status")},
            )
            return self._append_finding(result, extra)

        return result

    def results(self) -> List[ReplayValidationResult]:
        return list(self._results)

    def latest_result(self) -> Optional[ReplayValidationResult]:
        return self._results[-1] if self._results else None

    def telemetry_snapshot(self) -> Dict[str, Any]:
        latest = self.latest_result()
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "validation_count": len(self._results),
            "latest_validation_id": latest.validation_id if latest else None,
            "latest_passed": latest.passed if latest else None,
            "latest_validation_hash": latest.validation_hash if latest else None,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def replay_validation_manifest(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "oracle_instance_id": self.oracle_instance_id,
            "validation_count": len(self._results),
            "results": [
                {
                    "validation_id": result.validation_id,
                    "manifest_id": result.manifest_id,
                    "manifest_hash": result.manifest_hash,
                    "chain_hash": result.chain_hash,
                    "passed": result.passed,
                    "validation_hash": result.validation_hash,
                    "finding_count": result.finding_count,
                }
                for result in self._results
            ],
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def _validate_top_level(self, data: Dict[str, Any]) -> List[ReplayValidationFinding]:
        findings: List[ReplayValidationFinding] = []

        if not data.get("manifest_id"):
            findings.append(ReplayValidationFinding(
                code="MANIFEST_ID_MISSING",
                severity="error",
                message="Replay manifest is missing manifest_id.",
            ))

        manifest_hash = str(data.get("manifest_hash") or "")
        if len(manifest_hash) != 64:
            findings.append(ReplayValidationFinding(
                code="MANIFEST_HASH_INVALID",
                severity="error",
                message="Replay manifest hash must be a 64-character SHA-256 hex digest.",
                evidence={"manifest_hash": manifest_hash},
            ))

        chain_hash = str(data.get("chain_hash") or "")
        if len(chain_hash) != 64:
            findings.append(ReplayValidationFinding(
                code="CHAIN_HASH_INVALID",
                severity="error",
                message="Replay chain hash must be a 64-character SHA-256 hex digest.",
                evidence={"chain_hash": chain_hash},
            ))

        entries = _safe_list(data.get("entries"))
        declared_count = data.get("entry_count")
        if declared_count is not None and int(declared_count) != len(entries):
            findings.append(ReplayValidationFinding(
                code="ENTRY_COUNT_MISMATCH",
                severity="error",
                message="Declared entry_count does not match actual entries length.",
                evidence={"declared": declared_count, "actual": len(entries)},
            ))

        return findings

with MODULE.open("a", encoding="utf-8") as f:
    f.write(r'''

    def _validate_entries(self, entries: List[Dict[str, Any]]) -> List[ReplayValidationFinding]:
        findings: List[ReplayValidationFinding] = []

        if not entries:
            findings.append(ReplayValidationFinding(
                code="NO_REPLAY_ENTRIES",
                severity="warning",
                message="Replay manifest contains no entries.",
            ))
            return findings

        replay_keys = [str(entry.get("replay_key") or "") for entry in entries]
        audit_ids = [str(entry.get("audit_id") or "") for entry in entries]

        duplicate_replay_keys = sorted(
            key for key in set(replay_keys)
            if key and replay_keys.count(key) > 1
        )
        if duplicate_replay_keys:
            findings.append(ReplayValidationFinding(
                code="DUPLICATE_REPLAY_KEYS",
                severity="error",
                message="Replay manifest contains duplicate replay keys.",
                evidence={"duplicate_replay_keys": duplicate_replay_keys},
            ))

        duplicate_audit_ids = sorted(
            audit_id for audit_id in set(audit_ids)
            if audit_id and audit_ids.count(audit_id) > 1
        )
        if duplicate_audit_ids:
            findings.append(ReplayValidationFinding(
                code="DUPLICATE_AUDIT_IDS",
                severity="error",
                message="Replay manifest contains duplicate audit identifiers.",
                evidence={"duplicate_audit_ids": duplicate_audit_ids},
            ))

        required_fields = [
            "sequence",
            "audit_id",
            "adapter_id",
            "query_id",
            "replay_key",
            "query_hash",
            "resolver_hash",
            "market_model_hash",
            "integrity_hash",
        ]

        for index, entry in enumerate(entries):
            missing = [field for field in required_fields if entry.get(field) in (None, "")]
            if missing:
                findings.append(ReplayValidationFinding(
                    code="REPLAY_ENTRY_FIELDS_MISSING",
                    severity="error",
                    message="Replay entry is missing required lineage or integrity fields.",
                    evidence={"entry_index": index, "missing_fields": missing},
                ))

            if str(entry.get("query_hash") or "") and len(str(entry.get("query_hash"))) != 64:
                findings.append(ReplayValidationFinding(
                    code="QUERY_HASH_SHAPE_INVALID",
                    severity="warning",
                    message="Replay entry query_hash is not a 64-character digest.",
                    evidence={"audit_id": entry.get("audit_id"), "query_hash": entry.get("query_hash")},
                ))

            if str(entry.get("resolver_hash") or "") and len(str(entry.get("resolver_hash"))) != 64:
                findings.append(ReplayValidationFinding(
                    code="RESOLVER_HASH_SHAPE_INVALID",
                    severity="warning",
                    message="Replay entry resolver_hash is not a 64-character digest.",
                    evidence={"audit_id": entry.get("audit_id"), "resolver_hash": entry.get("resolver_hash")},
                ))

            finding_codes = [str(code) for code in _safe_list(entry.get("finding_codes"))]
            if "EXECUTION_BOUNDARY_VIOLATION" in finding_codes:
                findings.append(ReplayValidationFinding(
                    code="EXECUTION_BOUNDARY_REPLAY_BLOCKER",
                    severity="critical",
                    message="Replay entry contains an execution-boundary violation. Oracle remains read-only.",
                    evidence={"audit_id": entry.get("audit_id"), "replay_key": entry.get("replay_key")},
                ))

        sequences = [entry.get("sequence") for entry in entries]
        expected = list(range(1, len(entries) + 1))
        if sequences != expected:
            findings.append(ReplayValidationFinding(
                code="REPLAY_SEQUENCE_NON_DETERMINISTIC",
                severity="error",
                message="Replay entry sequences are not deterministic and contiguous.",
                evidence={"actual": sequences, "expected": expected},
            ))

        return findings

    def _validate_dependencies(self, entries: List[Dict[str, Any]]) -> List[ReplayValidationFinding]:
        findings: List[ReplayValidationFinding] = []
        known = {str(entry.get("replay_key") or "") for entry in entries}

        dangling: Dict[str, List[str]] = {}
        self_references: List[str] = []

        for entry in entries:
            replay_key = str(entry.get("replay_key") or "")
            deps = [str(dep) for dep in _safe_list(entry.get("dependency_keys"))]
            missing = [dep for dep in deps if dep not in known]
            if missing:
                dangling[replay_key] = missing
            if replay_key and replay_key in deps:
                self_references.append(replay_key)

        if dangling:
            findings.append(ReplayValidationFinding(
                code="DANGLING_DEPENDENCIES",
                severity="error",
                message="Replay manifest has dependencies that do not exist in the manifest.",
                evidence={"dangling": dangling},
            ))

        if self_references:
            findings.append(ReplayValidationFinding(
                code="SELF_REFERENTIAL_DEPENDENCIES",
                severity="error",
                message="Replay entries cannot depend on themselves.",
                evidence={"replay_keys": self_references},
            ))

        return findings

    def _validate_chain(
        self,
        data: Dict[str, Any],
        entries: List[Dict[str, Any]],
    ) -> List[ReplayValidationFinding]:
        findings: List[ReplayValidationFinding] = []
        chain_hash = str(data.get("chain_hash") or "")

        if len(chain_hash) != 64:
            return findings

        calculated = self._calculate_chain_hash(entries)

        if data.get("strict_chain_validation") is True and calculated != chain_hash:
            findings.append(ReplayValidationFinding(
                code="CHAIN_HASH_MISMATCH",
                severity="error",
                message="Strict chain validation failed.",
                evidence={"declared": chain_hash, "calculated": calculated},
            ))

        return findings

    def _validate_read_only(
        self,
        data: Dict[str, Any],
        entries: List[Dict[str, Any]],
    ) -> List[ReplayValidationFinding]:
        findings: List[ReplayValidationFinding] = []

        guardrails = _safe_dict(data.get("read_only_guardrails"))
        for key, expected in READ_ONLY_GUARDRAILS.items():
            if guardrails.get(key) != expected:
                findings.append(ReplayValidationFinding(
                    code="READ_ONLY_GUARDRAIL_MISMATCH",
                    severity="critical",
                    message="Replay manifest guardrails do not preserve Oracle read-only execution boundary.",
                    evidence={"key": key, "expected": expected, "actual": guardrails.get(key)},
                ))

        execution_flags = [
            "executed",
            "order_submitted",
            "trade_routed",
            "position_opened",
            "submit_order",
            "route_order",
            "manage_position",
        ]

        scanned = _stable_json({"manifest": data, "entries": entries}).lower()
        detected = [flag for flag in execution_flags if flag in scanned]
        if detected:
            findings.append(ReplayValidationFinding(
                code="EXECUTION_LANGUAGE_DETECTED",
                severity="warning",
                message="Execution-like language detected during replay validation. Oracle remains read-only.",
                evidence={"detected_terms": detected},
            ))

        return findings

    def _validate_explainability(self, data: Dict[str, Any]) -> List[ReplayValidationFinding]:
        explainability = _safe_dict(data.get("explainability"))
        if not explainability:
            return [
                ReplayValidationFinding(
                    code="EXPLAINABILITY_MISSING",
                    severity="warning",
                    message="Replay manifest does not include explainability metadata.",
                )
            ]

        return []

    def _validate_telemetry(self, data: Dict[str, Any]) -> List[ReplayValidationFinding]:
        telemetry = _safe_dict(data.get("telemetry"))
        if not telemetry:
            return [
                ReplayValidationFinding(
                    code="TELEMETRY_MISSING",
                    severity="warning",
                    message="Replay manifest does not include telemetry metadata.",
                )
            ]

        return []

    def _calculate_chain_hash(self, entries: List[Dict[str, Any]]) -> str:
        chain = "oi187.chain.root"
        for entry in entries:
            chain = _hash({
                "previous_chain_hash": chain,
                "entry_integrity_hash": entry.get("integrity_hash"),
                "audit_id": entry.get("audit_id"),
                "replay_key": entry.get("replay_key"),
                "sequence": entry.get("sequence"),
            })
        return chain

    def _append_finding(
        self,
        result: ReplayValidationResult,
        finding: ReplayValidationFinding,
    ) -> ReplayValidationResult:
        findings = list(result.findings) + [finding]
        critical_or_error_count = sum(
            1 for item in findings
            if item.severity in {"critical", "error"}
        )
        validation_payload = {
            "previous_validation_hash": result.validation_hash,
            "additional_finding": finding.to_dict(),
        }
        validation_hash = _hash(validation_payload)

        updated = ReplayValidationResult(
            validation_id="oi188.validation." + validation_hash[:24],
            created_at=_utc_now(),
            oracle_instance_id=result.oracle_instance_id,
            module_id=result.module_id,
            module_name=result.module_name,
            manifest_id=result.manifest_id,
            manifest_hash=result.manifest_hash,
            chain_hash=result.chain_hash,
            entry_count=result.entry_count,
            validated_entry_count=result.validated_entry_count,
            finding_count=len(findings),
            critical_or_error_count=critical_or_error_count,
            passed=critical_or_error_count == 0,
            validation_hash=validation_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            findings=findings,
            telemetry={
                **result.telemetry,
                "finding_count": len(findings),
                "critical_or_error_count": critical_or_error_count,
                "passed": critical_or_error_count == 0,
            },
            explainability=result.explainability,
        )
        self._results[-1] = updated
        return updated


def create_query_replay_validation_engine(
    oracle_instance_id: str = "oracle.default",
) -> UniversalMarketAdapterQueryReplayValidationEngine:
    return UniversalMarketAdapterQueryReplayValidationEngine(
        oracle_instance_id=oracle_instance_id
    )


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "ReplayValidationFinding",
    "ReplayValidationResult",
    "UniversalMarketAdapterQueryReplayValidationEngine",
    "create_query_replay_validation_engine",
]
'''.lstrip(), encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_validation_engine import (
    READ_ONLY_GUARDRAILS,
    UniversalMarketAdapterQueryReplayValidationEngine,
    create_query_replay_validation_engine,
)


def test_oi_188_query_replay_validation_engine():
    engine = create_query_replay_validation_engine("oracle.test")

    good_manifest = {
        "manifest_id": "oi187.manifest.good",
        "manifest_hash": "a" * 64,
        "chain_hash": "b" * 64,
        "entry_count": 2,
        "read_only_guardrails": READ_ONLY_GUARDRAILS,
        "telemetry": {"source": "unit_test"},
        "explainability": {"purpose": "test replay validation"},
        "entries": [
            {
                "sequence": 1,
                "audit_id": "audit-001",
                "adapter_id": "adp.kalshi",
                "query_id": "q-001",
                "replay_key": "replay-001",
                "passed": True,
                "query_hash": "c" * 64,
                "resolver_hash": "d" * 64,
                "market_model_hash": "e" * 64,
                "source_hash": "f" * 64,
                "finding_codes": [],
                "dependency_keys": [],
                "integrity_hash": "g" * 64,
            },
            {
                "sequence": 2,
                "audit_id": "audit-002",
                "adapter_id": "adp.kalshi",
                "query_id": "q-002",
                "replay_key": "replay-002",
                "passed": True,
                "query_hash": "h" * 64,
                "resolver_hash": "i" * 64,
                "market_model_hash": "j" * 64,
                "source_hash": "k" * 64,
                "finding_codes": [],
                "dependency_keys": ["replay-001"],
                "integrity_hash": "l" * 64,
            },
        ],
    }

    result = engine.validate_manifest(good_manifest)

    assert result.module_id == "OI-188"
    assert result.manifest_id == "oi187.manifest.good"
    assert result.entry_count == 2
    assert result.validated_entry_count == 2
    assert result.critical_or_error_count == 0
    assert result.passed is True
    assert len(result.validation_hash) == 64
    assert result.read_only_guardrails == READ_ONLY_GUARDRAILS

    bad_manifest = {
        "manifest_id": "oi187.manifest.bad",
        "manifest_hash": "short",
        "chain_hash": "also-short",
        "entry_count": 3,
        "read_only_guardrails": {
            "oracle_read_only": False,
            "executes_trades": True,
            "routes_orders": True,
            "submits_orders": True,
            "manages_positions": True,
            "execution_owner": "ORACLE",
        },
        "entries": [
            {
                "sequence": 2,
                "audit_id": "audit-bad",
                "adapter_id": "adp.bad",
                "query_id": "q-bad",
                "replay_key": "same",
                "passed": False,
                "query_hash": "x",
                "resolver_hash": "y",
                "market_model_hash": "",
                "finding_codes": ["EXECUTION_BOUNDARY_VIOLATION"],
                "dependency_keys": ["missing-key", "same"],
                "integrity_hash": "z",
            },
            {
                "sequence": 2,
                "audit_id": "audit-bad",
                "adapter_id": "adp.bad",
                "query_id": "q-bad-2",
                "replay_key": "same",
                "passed": True,
                "query_hash": "x",
                "resolver_hash": "y",
                "market_model_hash": "m",
                "finding_codes": [],
                "dependency_keys": [],
                "integrity_hash": "z",
            },
        ],
    }

    bad = engine.validate_manifest(bad_manifest)
    codes = {finding.code for finding in bad.findings}

    assert bad.passed is False
    assert "MANIFEST_HASH_INVALID" in codes
    assert "CHAIN_HASH_INVALID" in codes
    assert "ENTRY_COUNT_MISMATCH" in codes
    assert "DUPLICATE_REPLAY_KEYS" in codes
    assert "DUPLICATE_AUDIT_IDS" in codes
    assert "REPLAY_SEQUENCE_NON_DETERMINISTIC" in codes
    assert "DANGLING_DEPENDENCIES" in codes
    assert "SELF_REFERENTIAL_DEPENDENCIES" in codes
    assert "EXECUTION_BOUNDARY_REPLAY_BLOCKER" in codes
    assert "READ_ONLY_GUARDRAIL_MISMATCH" in codes

    package_result = engine.validate_package({
        "package_status": "not_ready",
        "manifest_id": "pkg-1",
        "manifest_hash": "p" * 64,
        "chain_hash": "q" * 64,
        "entries": [],
        "read_only_guardrails": READ_ONLY_GUARDRAILS,
        "explainability": {"purpose": "package test"},
    })

    assert package_result.passed is False
    assert any(f.code == "REPLAY_PACKAGE_NOT_READY" for f in package_result.findings)

    snapshot = engine.telemetry_snapshot()
    assert snapshot["validation_count"] == 3
    assert snapshot["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    manifest = engine.replay_validation_manifest()
    assert manifest["module_id"] == "OI-188"
    assert len(manifest["results"]) == 3

    empty = UniversalMarketAdapterQueryReplayValidationEngine("oracle.empty")
    assert empty.telemetry_snapshot()["validation_count"] == 0


if __name__ == "__main__":
    test_oi_188_query_replay_validation_engine()
    print("[PASS] OI-188 Universal Market Adapter Query Replay Validation Engine")
'''.lstrip(), encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

import_line = "from .universal_market_adapter_query_replay_validation_engine import UniversalMarketAdapterQueryReplayValidationEngine, create_query_replay_validation_engine\n"
if import_line not in init_text:
    init_text += ("\n" if init_text and not init_text.endswith("\n") else "") + import_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-188 INSTALLER")
print(" Universal Market Adapter Query Replay Validation Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-188 installed")
print()
print("Run:")
print("py test_oi_188_universal_market_adapter_query_replay_validation_engine.py")
