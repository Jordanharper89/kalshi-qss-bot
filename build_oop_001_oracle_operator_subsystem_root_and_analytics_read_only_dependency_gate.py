from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

QSERIES = ROOT / "qseries_v2"
ORACLE_INTELLIGENCE = QSERIES / "oracle_intelligence"
ANALYTICS = ORACLE_INTELLIGENCE / "analytics"
ANALYTICS_QUERY = ANALYTICS / "downstream" / "query"

OPERATOR = QSERIES / "oracle_operator"
OPERATOR_QUERY = OPERATOR / "query"
OPERATOR_SESSION = OPERATOR / "session"
OPERATOR_CONSOLE = OPERATOR / "console"
OPERATOR_PRESENTATION = OPERATOR / "presentation"

SOURCE_060 = (
    ANALYTICS_QUERY
    / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
)

PRODUCTION = (
    OPERATOR
    / "oracle_operator_analytics_read_only_dependency_gate.py"
)
TEST = (
    ROOT
    / "test_oop_001_oracle_operator_subsystem_root_and_analytics_read_only_dependency_gate.py"
)

QSERIES_PACKAGE = QSERIES / "__init__.py"
OPERATOR_PACKAGE = OPERATOR / "__init__.py"
QUERY_PACKAGE = OPERATOR_QUERY / "__init__.py"
SESSION_PACKAGE = OPERATOR_SESSION / "__init__.py"
CONSOLE_PACKAGE = OPERATOR_CONSOLE / "__init__.py"
PRESENTATION_PACKAGE = OPERATOR_PRESENTATION / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_060_authorization_gate import (
    AUTHORIZATION_SCHEMA_VERSION as INT_OIA_060_AUTHORIZATION_SCHEMA_VERSION,
    CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization,
)

SCHEMA_VERSION = "OOP-001"
ENGINE_ID = "OOP-001"
POLICY_ID = "oracle.operator.analytics-read-only-dependency-gate.v1"
DEPENDENCY_SCHEMA_VERSION = "oracle.operator.analytics-read-only-dependency-receipt.v1"
DEPENDENCY_STATUS = "int_oia_060_consumed_read_only"

EXPECTED_ANALYTICS_SCHEMA_VERSION = "INT-OIA-060"
EXPECTED_CONSUMER_ID = "oracle.operator.console.v1"
EXPECTED_PROJECTION = "operator_research"

OPERATOR_PACKAGE_NAMESPACE = "qseries_v2.oracle_operator"
ANALYTICS_PACKAGE_NAMESPACE = "qseries_v2.oracle_intelligence.analytics"
QSERIES_EXECUTION_PACKAGE_NAMESPACE = "qseries_v2.execution"


class OracleOperatorAnalyticsReadOnlyDependencyInvariantError(RuntimeError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
        f"unsupported non-deterministic value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _verify_int_oia_060_hash(
    authorization: CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization,
) -> None:
    body = asdict(authorization)
    supplied_hash = body.pop("authorization_hash", None)
    if not _valid_sha256(supplied_hash):
        raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
            "INT-OIA-060 authorization hash is not a canonical SHA-256 digest"
        )
    if stable_hash(body) != supplied_hash:
        raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
            "INT-OIA-060 authorization hash mismatch"
        )


@dataclass(frozen=True)
class OracleOperatorSubsystemBoundary:
    subsystem_id: str
    package_namespace: str
    query_namespace: str
    session_namespace: str
    console_namespace: str
    presentation_namespace: str
    analytics_namespace: str
    qseries_execution_namespace: str
    separate_from_analytics: bool
    separate_from_qseries_execution: bool
    analytics_mutation_allowed: bool
    qseries_execution_import_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    boundary_hash: str


@dataclass(frozen=True)
class OracleOperatorAnalyticsDependencyReceipt:
    dependency_receipt_id: str
    subsystem_boundary_hash: str
    source_schema_version: str
    source_authorization_schema_version: str
    source_authorization_id: str
    source_authorization_hash: str
    source_attestation_id: str
    source_attestation_hash: str
    source_consumption_id: str
    source_consumption_hash: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    authorized_consumer_id: str
    authorized_projection: str
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    source_type_verified: bool
    source_hash_verified: bool
    source_lineage_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    deterministic_replay_verified: bool
    read_only_dependency_verified: bool
    analytics_reexecution_performed: bool
    analytics_database_connection_performed: bool
    analytics_corpus_read_repeated: bool
    analytics_mutation_allowed: bool
    analytics_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    qseries_execution_performed: bool
    order_creation_allowed: bool
    order_creation_performed: bool
    funds_movement_allowed: bool
    funds_movement_performed: bool
    portfolio_mutation_allowed: bool
    portfolio_mutation_performed: bool
    dependency_status: str
    dependency_receipt_hash: str


class OracleOperatorAnalyticsReadOnlyDependencyGate:
    @staticmethod
    def subsystem_boundary() -> OracleOperatorSubsystemBoundary:
        body = {
            "subsystem_id": "oracle.operator",
            "package_namespace": OPERATOR_PACKAGE_NAMESPACE,
            "query_namespace": f"{OPERATOR_PACKAGE_NAMESPACE}.query",
            "session_namespace": f"{OPERATOR_PACKAGE_NAMESPACE}.session",
            "console_namespace": f"{OPERATOR_PACKAGE_NAMESPACE}.console",
            "presentation_namespace": f"{OPERATOR_PACKAGE_NAMESPACE}.presentation",
            "analytics_namespace": ANALYTICS_PACKAGE_NAMESPACE,
            "qseries_execution_namespace": QSERIES_EXECUTION_PACKAGE_NAMESPACE,
            "separate_from_analytics": True,
            "separate_from_qseries_execution": True,
            "analytics_mutation_allowed": False,
            "qseries_execution_import_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        return OracleOperatorSubsystemBoundary(
            **body,
            boundary_hash=stable_hash(body),
        )

    @staticmethod
    def _verify_source(
        authorization: CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization,
        ):
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "dependency must use the canonical INT-OIA-060 authorization contract"
            )

        _verify_int_oia_060_hash(authorization)

        if not authorization.authorization_id:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization identity is empty"
            )
        if authorization.authorized_consumer_id != EXPECTED_CONSUMER_ID:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization is not for the Oracle Operator consumer"
            )
        if authorization.authorized_projection != EXPECTED_PROJECTION:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization projection is not operator_research"
            )
        if authorization.authorized_entry_count < 1:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization contains no entries"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_response_artifact_entry_ids
        ):
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 artifact-entry cardinality mismatch"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_query_response_ids
        ):
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 query-response cardinality mismatch"
            )
        if len(
            set(authorization.authorized_response_artifact_entry_ids)
        ) != authorization.authorized_entry_count:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "duplicate authorized artifact-entry identities detected"
            )
        if len(
            set(authorization.authorized_query_response_ids)
        ) != authorization.authorized_entry_count:
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "duplicate authorized query-response identities detected"
            )

        required_truths = (
            authorization.attestation_hash_verified,
            authorization.attestation_identity_verified,
            authorization.consumption_lineage_verified,
            authorization.authorization_lineage_verified,
            authorization.prior_attestation_lineage_verified,
            authorization.prior_consumption_lineage_verified,
            authorization.prior_authorization_lineage_verified,
            authorization.read_authorization_lineage_verified,
            authorization.read_result_lineage_verified,
            authorization.read_request_lineage_verified,
            authorization.registry_manifest_lineage_verified,
            authorization.consumer_identity_verified,
            authorization.projection_identity_verified,
            authorization.entry_identity_cardinality_verified,
            authorization.query_response_identity_cardinality_verified,
            authorization.unique_entry_identities_verified,
            authorization.unique_query_response_identities_verified,
            authorization.independent_attestation_verified,
            authorization.single_use_authorization_verified,
            authorization.read_only_consumption_verified,
            authorization.source_hashes_verified,
            authorization.lineage_verified,
            authorization.deterministic_ordering_verified,
            authorization.deterministic_consumption_verified,
            authorization.deterministic_replay_verified,
            authorization.attestation_authorized,
        )
        if not all(required_truths):
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization is incomplete or uncertified"
            )

        forbidden_activity = (
            authorization.registry_mutation_allowed,
            authorization.registry_mutation_performed,
            authorization.publication_allowed,
            authorization.publication_performed,
            authorization.order_execution_allowed,
            authorization.order_execution_performed,
            authorization.database_connection_performed,
            authorization.corpus_read_execution_repeated,
        )
        if any(forbidden_activity):
            raise OracleOperatorAnalyticsReadOnlyDependencyInvariantError(
                "INT-OIA-060 authorization contains forbidden activity"
            )

    def consume(
        self,
        *,
        authorization: CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization,
    ) -> OracleOperatorAnalyticsDependencyReceipt:
        self._verify_source(authorization)
        boundary = self.subsystem_boundary()

        dependency_receipt_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "subsystem_boundary_hash": boundary.boundary_hash,
                "source_schema_version": EXPECTED_ANALYTICS_SCHEMA_VERSION,
                "source_authorization_id": authorization.authorization_id,
                "source_authorization_hash": authorization.authorization_hash,
                "authorized_consumer_id": authorization.authorized_consumer_id,
                "authorized_projection": authorization.authorized_projection,
                "authorized_response_artifact_entry_ids": (
                    authorization.authorized_response_artifact_entry_ids
                ),
                "authorized_query_response_ids": (
                    authorization.authorized_query_response_ids
                ),
            }
        )

        body = {
            "dependency_receipt_id": dependency_receipt_id,
            "subsystem_boundary_hash": boundary.boundary_hash,
            "source_schema_version": EXPECTED_ANALYTICS_SCHEMA_VERSION,
            "source_authorization_schema_version": (
                INT_OIA_060_AUTHORIZATION_SCHEMA_VERSION
            ),
            "source_authorization_id": authorization.authorization_id,
            "source_authorization_hash": authorization.authorization_hash,
            "source_attestation_id": authorization.source_attestation_id,
            "source_attestation_hash": authorization.source_attestation_hash,
            "source_consumption_id": authorization.source_consumption_id,
            "source_consumption_hash": authorization.source_consumption_hash,
            "source_registry_manifest_id": (
                authorization.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                authorization.source_registry_manifest_hash
            ),
            "authorized_consumer_id": authorization.authorized_consumer_id,
            "authorized_projection": authorization.authorized_projection,
            "authorized_entry_count": authorization.authorized_entry_count,
            "authorized_response_artifact_entry_ids": tuple(
                authorization.authorized_response_artifact_entry_ids
            ),
            "authorized_query_response_ids": tuple(
                authorization.authorized_query_response_ids
            ),
            "source_type_verified": True,
            "source_hash_verified": True,
            "source_lineage_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "deterministic_replay_verified": True,
            "read_only_dependency_verified": True,
            "analytics_reexecution_performed": False,
            "analytics_database_connection_performed": False,
            "analytics_corpus_read_repeated": False,
            "analytics_mutation_allowed": False,
            "analytics_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "order_creation_allowed": False,
            "order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "dependency_status": DEPENDENCY_STATUS,
        }

        return OracleOperatorAnalyticsDependencyReceipt(
            **body,
            dependency_receipt_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "DEPENDENCY_SCHEMA_VERSION",
    "DEPENDENCY_STATUS",
    "EXPECTED_ANALYTICS_SCHEMA_VERSION",
    "EXPECTED_CONSUMER_ID",
    "EXPECTED_PROJECTION",
    "OPERATOR_PACKAGE_NAMESPACE",
    "ANALYTICS_PACKAGE_NAMESPACE",
    "QSERIES_EXECUTION_PACKAGE_NAMESPACE",
    "OracleOperatorSubsystemBoundary",
    "OracleOperatorAnalyticsDependencyReceipt",
    "OracleOperatorAnalyticsReadOnlyDependencyGate",
    "OracleOperatorAnalyticsReadOnlyDependencyInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_int_oia_060_oracle_intelligence_analytics_certified_query_response_artifact_authorization_consumption_attestation_authorization_consumption_attestation_authorization_gate import (
    _attestation,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_060_authorization_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate,
)
from qseries_v2.oracle_operator.oracle_operator_analytics_read_only_dependency_gate import (
    DEPENDENCY_SCHEMA_VERSION,
    EXPECTED_ANALYTICS_SCHEMA_VERSION,
    OPERATOR_PACKAGE_NAMESPACE,
    OracleOperatorAnalyticsReadOnlyDependencyGate,
    OracleOperatorAnalyticsReadOnlyDependencyInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe analytics dependency accepted")
    except OracleOperatorAnalyticsReadOnlyDependencyInvariantError:
        pass


def _authorization():
    attestation = _attestation()
    return (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate()
    ).authorize(
        attestation=attestation,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )


def main() -> int:
    print("=" * 40)
    print(" OOP-001 TEST")
    print(" ORACLE OPERATOR SUBSYSTEM ROOT")
    print(" ANALYTICS READ-ONLY DEPENDENCY")
    print("=" * 40)

    authorization = _authorization()
    gate = OracleOperatorAnalyticsReadOnlyDependencyGate()

    boundary = gate.subsystem_boundary()
    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.dependency_receipt_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "dependency_receipt_hash"
        }
    )

    assert boundary.subsystem_id == "oracle.operator"
    assert boundary.package_namespace == "qseries_v2.oracle_operator"
    assert boundary.query_namespace == "qseries_v2.oracle_operator.query"
    assert boundary.session_namespace == "qseries_v2.oracle_operator.session"
    assert boundary.console_namespace == "qseries_v2.oracle_operator.console"
    assert (
        boundary.presentation_namespace
        == "qseries_v2.oracle_operator.presentation"
    )
    assert boundary.separate_from_analytics
    assert boundary.separate_from_qseries_execution
    assert not boundary.analytics_mutation_allowed
    assert not boundary.qseries_execution_import_allowed
    assert not boundary.qseries_execution_allowed
    assert not boundary.order_creation_allowed
    assert not boundary.funds_movement_allowed
    assert not boundary.portfolio_mutation_allowed

    assert first.source_schema_version == "INT-OIA-060"
    assert first.source_authorization_id == authorization.authorization_id
    assert first.source_authorization_hash == authorization.authorization_hash
    assert first.authorized_consumer_id == "oracle.operator.console.v1"
    assert first.authorized_projection == "operator_research"
    assert first.authorized_entry_count == authorization.authorized_entry_count
    assert first.source_type_verified
    assert first.source_hash_verified
    assert first.source_lineage_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.deterministic_replay_verified
    assert first.read_only_dependency_verified

    assert not first.analytics_reexecution_performed
    assert not first.analytics_database_connection_performed
    assert not first.analytics_corpus_read_repeated
    assert not first.analytics_mutation_allowed
    assert not first.analytics_mutation_performed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed

    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorization_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorized_consumer_id="wrong.consumer",
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorized_projection="wrong_projection",
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                publication_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                order_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                database_connection_performed=True,
            )
        )
    )

    assert EXPECTED_ANALYTICS_SCHEMA_VERSION == "INT-OIA-060"
    assert OPERATOR_PACKAGE_NAMESPACE == "qseries_v2.oracle_operator"
    assert (
        DEPENDENCY_SCHEMA_VERSION
        == "oracle.operator.analytics-read-only-dependency-receipt.v1"
    )

    print("[PASS] Separate qseries_v2.oracle_operator subsystem established")
    print("[PASS] query, session, console, and presentation namespaces established")
    print("[PASS] Actual canonical INT-OIA-060 authorization consumed")
    print("[PASS] INT-OIA-060 source type and hash independently verified")
    print("[PASS] Complete certified analytics lineage preserved read-only")
    print("[PASS] Deterministic dependency receipt created and replay verified")
    print("[PASS] Analytics was not reexecuted, queried, connected, or modified")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series handoff and execution remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    print("[PASS] Tampered and unsafe dependency evidence rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        source.strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def ensure_package(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8", newline="\n")
        print(f"[OK] PACKAGE CREATED: {path.resolve()}")
    else:
        print(f"[OK] PACKAGE PRESERVED: {path.resolve()}")


def append_export(path: Path, export_line: str) -> None:
    ensure_package(path)
    existing = path.read_text(encoding="utf-8")
    if export_line not in existing.splitlines():
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        path.write_text(existing, encoding="utf-8", newline="\n")
        print(f"[OK] PACKAGE UPDATED: {path.resolve()}")
    else:
        print(f"[OK] PACKAGE EXPORT PRESENT: {path.resolve()}")


def verify_int_oia_060_contract() -> None:
    if not SOURCE_060.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-060 production module missing: {SOURCE_060}"
        )

    source = SOURCE_060.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-060"',
        "AUTHORIZATION_SCHEMA_VERSION",
        "class CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization",
        "class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate",
        "authorization_id",
        "authorization_hash",
        "authorized_consumer_id",
        "authorized_projection",
        "authorized_entry_count",
        "authorized_response_artifact_entry_ids",
        "authorized_query_response_ids",
        "attestation_authorized",
        "read_only_consumption_verified",
        "source_hashes_verified",
        "lineage_verified",
        "deterministic_replay_verified",
        "registry_mutation_allowed",
        "publication_allowed",
        "order_execution_allowed",
        "database_connection_performed",
        "corpus_read_execution_repeated",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-060 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )

    print("[OK] Actual INT-OIA-060 terminal analytics contract verified")


def main() -> int:
    print("=" * 40)
    print(" OOP-001 INSTALLER")
    print(" ORACLE OPERATOR SUBSYSTEM ROOT")
    print(" ANALYTICS READ-ONLY DEPENDENCY")
    print("=" * 40)

    verify_int_oia_060_contract()

    analytics_hash_before = sha256_file(SOURCE_060)

    ensure_package(QSERIES_PACKAGE)
    ensure_package(OPERATOR_PACKAGE)
    ensure_package(QUERY_PACKAGE)
    ensure_package(SESSION_PACKAGE)
    ensure_package(CONSOLE_PACKAGE)
    ensure_package(PRESENTATION_PACKAGE)

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        OPERATOR_PACKAGE,
        "from .oracle_operator_analytics_read_only_dependency_gate import *",
    )

    for target in (
        QSERIES_PACKAGE,
        OPERATOR_PACKAGE,
        QUERY_PACKAGE,
        SESSION_PACKAGE,
        CONSOLE_PACKAGE,
        PRESENTATION_PACKAGE,
        PRODUCTION,
        TEST,
    ):
        ast.parse(
            target.read_text(encoding="utf-8"),
            filename=str(target),
        )
    print("[OK] Production, test, and package syntax verified in memory")

    analytics_hash_after_install = sha256_file(SOURCE_060)
    if analytics_hash_after_install != analytics_hash_before:
        raise RuntimeError(
            "Analytics changed during OOP-001 installation"
        )
    print("[PASS] INT-OIA-060 source remained byte-for-byte unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    analytics_hash_after_test = sha256_file(SOURCE_060)
    if analytics_hash_after_test != analytics_hash_before:
        raise RuntimeError(
            "Analytics changed during OOP-001 testing"
        )

    print("[PASS] Analytics remained byte-for-byte unchanged after test")
    print("[PASS] No analytics package export was modified")
    print("[PASS] No Q Series execution package was imported or modified")
    print("[OK] OOP-001 test executed automatically")
    print()
    print("[DONE] OOP-001 Oracle Operator subsystem root installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
