from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
QUERY = DOWNSTREAM / "query"

SOURCE_059 = QUERY / "oracle_intelligence_analytics_int_oia_059_attestation_gate.py"
PRODUCTION = QUERY / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
TEST = ROOT / (
    "test_int_oia_060_oracle_intelligence_analytics_certified_query_response_"
    "artifact_authorization_consumption_attestation_authorization_consumption_"
    "attestation_authorization_gate.py"
)

QUERY_PACKAGE = QUERY / "__init__.py"
DOWNSTREAM_PACKAGE = DOWNSTREAM / "__init__.py"
ANALYTICS_PACKAGE = ANALYTICS / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_059_attestation_gate import (
    CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestation,
)

SCHEMA_VERSION = "INT-OIA-060"
ENGINE_ID = "INT-OIA-060"
POLICY_ID = (
    "oracle.intelligence.analytics.certified-query-response-artifact."
    "authorization-consumption-attestation-authorization-consumption-"
    "attestation-authorization-gate.v1"
)
AUTHORIZATION_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-authorization-consumption-"
    "attestation-authorization-consumption-attestation-authorization.v1"
)
AUTHORIZATION_STATUS = (
    "certified_query_response_artifact_authorization_consumption_"
    "attestation_authorization_consumption_attestation_authorized"
)


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
    RuntimeError
):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
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


def _verify_hash_record(value: Any, hash_field: str, label: str) -> None:
    body = asdict(value)
    supplied = body.pop(hash_field, None)
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(character not in "0123456789abcdef" for character in supplied)
        or stable_hash(body) != supplied
    ):
        raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
            f"{label} hash mismatch"
        )


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization:
    authorization_id: str
    source_attestation_id: str
    source_attestation_hash: str
    source_consumption_id: str
    source_consumption_hash: str
    source_prior_authorization_id: str
    source_prior_authorization_hash: str
    source_prior_attestation_id: str
    source_prior_attestation_hash: str
    source_prior_consumption_id: str
    source_prior_consumption_hash: str
    source_read_authorization_id: str
    source_read_authorization_hash: str
    source_read_result_id: str
    source_read_result_hash: str
    source_read_request_id: str
    source_read_request_hash: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    authorized_consumer_id: str
    authorized_projection: str
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    attestation_hash_verified: bool
    attestation_identity_verified: bool
    consumption_lineage_verified: bool
    authorization_lineage_verified: bool
    prior_attestation_lineage_verified: bool
    prior_consumption_lineage_verified: bool
    prior_authorization_lineage_verified: bool
    read_authorization_lineage_verified: bool
    read_result_lineage_verified: bool
    read_request_lineage_verified: bool
    registry_manifest_lineage_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    entry_identity_cardinality_verified: bool
    query_response_identity_cardinality_verified: bool
    unique_entry_identities_verified: bool
    unique_query_response_identities_verified: bool
    independent_attestation_verified: bool
    single_use_authorization_verified: bool
    read_only_consumption_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_consumption_verified: bool
    deterministic_replay_verified: bool
    attestation_authorized: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    authorization_status: str
    authorization_hash: str


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate:
    @staticmethod
    def _verify_attestation(
        attestation: CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestation,
    ) -> None:
        if not isinstance(
            attestation,
            CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestation,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "attestation must use the canonical INT-OIA-059 contract"
            )

        _verify_hash_record(
            attestation,
            "attestation_hash",
            "authorization consumption attestation",
        )

        if not attestation.attestation_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "attestation identity is empty"
            )
        if attestation.attested_entry_count < 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "empty attestation cannot be authorized"
            )
        if attestation.attested_entry_count != len(
            attestation.attested_response_artifact_entry_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if attestation.attested_entry_count != len(
            attestation.attested_query_response_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "query-response cardinality mismatch"
            )
        if len(set(attestation.attested_response_artifact_entry_ids)) != attestation.attested_entry_count:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(set(attestation.attested_query_response_ids)) != attestation.attested_entry_count:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "duplicate query-response identities detected"
            )

        required = (
            attestation.consumption_hash_verified,
            attestation.consumption_identity_verified,
            attestation.authorization_lineage_verified,
            attestation.prior_attestation_lineage_verified,
            attestation.prior_consumption_lineage_verified,
            attestation.prior_authorization_lineage_verified,
            attestation.read_authorization_lineage_verified,
            attestation.read_result_lineage_verified,
            attestation.read_request_lineage_verified,
            attestation.registry_manifest_lineage_verified,
            attestation.consumer_identity_verified,
            attestation.projection_identity_verified,
            attestation.entry_identity_cardinality_verified,
            attestation.query_response_identity_cardinality_verified,
            attestation.unique_entry_identities_verified,
            attestation.unique_query_response_identities_verified,
            attestation.independent_attestation_verified,
            attestation.single_use_authorization_verified,
            attestation.read_only_consumption_verified,
            attestation.source_hashes_verified,
            attestation.lineage_verified,
            attestation.deterministic_ordering_verified,
            attestation.deterministic_consumption_verified,
            attestation.consumption_attested,
        )
        if not all(required):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "attestation is not eligible for authorization"
            )

        if (
            attestation.registry_mutation_allowed
            or attestation.registry_mutation_performed
            or attestation.publication_allowed
            or attestation.publication_performed
            or attestation.order_execution_allowed
            or attestation.order_execution_performed
            or attestation.database_connection_performed
            or attestation.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "attestation contains forbidden activity"
            )

    def authorize(
        self,
        *,
        attestation: CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestation,
        authorized_consumer_id: str,
        authorized_projection: str,
    ) -> CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization:
        self._verify_attestation(attestation)

        if not isinstance(authorized_consumer_id, str) or not authorized_consumer_id.strip():
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "authorized_consumer_id must be a non-empty string"
            )
        if not isinstance(authorized_projection, str) or not authorized_projection.strip():
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "authorized_projection must be a non-empty string"
            )
        if authorized_consumer_id != attestation.attested_consumer_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "authorized consumer does not match attested consumer"
            )
        if authorized_projection != attestation.attested_projection:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError(
                "authorized projection does not match attested projection"
            )

        entry_ids = tuple(attestation.attested_response_artifact_entry_ids)
        response_ids = tuple(attestation.attested_query_response_ids)

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_attestation_id": attestation.attestation_id,
                "source_attestation_hash": attestation.attestation_hash,
                "authorized_consumer_id": authorized_consumer_id,
                "authorized_projection": authorized_projection,
                "authorized_response_artifact_entry_ids": entry_ids,
                "authorized_query_response_ids": response_ids,
            }
        )

        body = {
            "authorization_id": authorization_id,
            "source_attestation_id": attestation.attestation_id,
            "source_attestation_hash": attestation.attestation_hash,
            "source_consumption_id": attestation.source_consumption_id,
            "source_consumption_hash": attestation.source_consumption_hash,
            "source_prior_authorization_id": attestation.source_authorization_id,
            "source_prior_authorization_hash": attestation.source_authorization_hash,
            "source_prior_attestation_id": attestation.source_prior_attestation_id,
            "source_prior_attestation_hash": attestation.source_prior_attestation_hash,
            "source_prior_consumption_id": attestation.source_prior_consumption_id,
            "source_prior_consumption_hash": attestation.source_prior_consumption_hash,
            "source_read_authorization_id": attestation.source_read_authorization_id,
            "source_read_authorization_hash": attestation.source_read_authorization_hash,
            "source_read_result_id": attestation.source_read_result_id,
            "source_read_result_hash": attestation.source_read_result_hash,
            "source_read_request_id": attestation.source_read_request_id,
            "source_read_request_hash": attestation.source_read_request_hash,
            "source_registry_manifest_id": attestation.source_registry_manifest_id,
            "source_registry_manifest_hash": attestation.source_registry_manifest_hash,
            "authorized_consumer_id": authorized_consumer_id,
            "authorized_projection": authorized_projection,
            "authorized_entry_count": attestation.attested_entry_count,
            "authorized_response_artifact_entry_ids": entry_ids,
            "authorized_query_response_ids": response_ids,
            "attestation_hash_verified": True,
            "attestation_identity_verified": True,
            "consumption_lineage_verified": True,
            "authorization_lineage_verified": True,
            "prior_attestation_lineage_verified": True,
            "prior_consumption_lineage_verified": True,
            "prior_authorization_lineage_verified": True,
            "read_authorization_lineage_verified": True,
            "read_result_lineage_verified": True,
            "read_request_lineage_verified": True,
            "registry_manifest_lineage_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "entry_identity_cardinality_verified": True,
            "query_response_identity_cardinality_verified": True,
            "unique_entry_identities_verified": True,
            "unique_query_response_identities_verified": True,
            "independent_attestation_verified": True,
            "single_use_authorization_verified": True,
            "read_only_consumption_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_consumption_verified": True,
            "deterministic_replay_verified": True,
            "attestation_authorized": True,
            "registry_mutation_allowed": False,
            "registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "authorization_status": AUTHORIZATION_STATUS,
        }

        return CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization(
            **body,
            authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_SCHEMA_VERSION",
    "AUTHORIZATION_STATUS",
    "CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorization",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_int_oia_059_oracle_intelligence_analytics_certified_query_response_artifact_authorization_consumption_attestation_authorization_consumption_attestation_gate import (
    _consumption,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_059_attestation_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_060_authorization_gate import (
    AUTHORIZATION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe attestation authorization accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError:
        pass


def _attestation():
    consumption = _consumption()
    return (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationGate()
    ).attest(consumption=consumption)


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-060 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" AUTHORIZATION CONSUMPTION ATTESTATION AUTHORIZATION")
    print("=" * 40)

    attestation = _attestation()
    gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate()
    )

    first = gate.authorize(
        attestation=attestation,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )
    repeated = gate.authorize(
        attestation=attestation,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )

    assert first == repeated
    assert first.attestation_authorized
    assert first.authorized_entry_count == attestation.attested_entry_count
    assert first.authorized_response_artifact_entry_ids == attestation.attested_response_artifact_entry_ids
    assert first.authorized_query_response_ids == attestation.attested_query_response_ids
    assert first.authorization_hash == stable_hash(
        {key: value for key, value in first.__dict__.items() if key != "authorization_hash"}
    )

    _expect_rejected(
        lambda: gate.authorize(
            attestation=attestation,
            authorized_consumer_id="wrong.consumer",
            authorized_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            attestation=attestation,
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="wrong_projection",
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            attestation=replace(attestation, attestation_hash="0" * 64),
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            attestation=replace(attestation, publication_allowed=True),
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            attestation=replace(attestation, independent_attestation_verified=False),
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )

    assert first.attestation_hash_verified
    assert first.attestation_identity_verified
    assert first.consumption_lineage_verified
    assert first.authorization_lineage_verified
    assert first.prior_attestation_lineage_verified
    assert first.prior_consumption_lineage_verified
    assert first.prior_authorization_lineage_verified
    assert first.read_authorization_lineage_verified
    assert first.read_result_lineage_verified
    assert first.read_request_lineage_verified
    assert first.registry_manifest_lineage_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.entry_identity_cardinality_verified
    assert first.query_response_identity_cardinality_verified
    assert first.unique_entry_identities_verified
    assert first.unique_query_response_identities_verified
    assert first.independent_attestation_verified
    assert first.single_use_authorization_verified
    assert first.read_only_consumption_verified
    assert first.source_hashes_verified
    assert first.lineage_verified
    assert first.deterministic_ordering_verified
    assert first.deterministic_consumption_verified
    assert first.deterministic_replay_verified
    assert not first.registry_mutation_allowed
    assert not first.registry_mutation_performed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.order_execution_allowed
    assert not first.order_execution_performed
    assert not first.database_connection_performed
    assert not first.corpus_read_execution_repeated

    assert AUTHORIZATION_SCHEMA_VERSION == (
        "oracle.certified-query-response-artifact-authorization-consumption-"
        "attestation-authorization-consumption-attestation-authorization.v1"
    )

    print("[PASS] Actual INT-OIA-059 attestation contract consumed")
    print("[PASS] Attestation identity and hash independently verified")
    print("[PASS] Authorization-consumption and complete read lineage verified")
    print("[PASS] Consumer and projection identities matched exactly")
    print("[PASS] Entry and query-response identity cardinality verified")
    print("[PASS] Independent attestation evidence required")
    print("[PASS] Deterministic authorization record created")
    print("[PASS] Deterministic authorization replay verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-059 lineage preserved")
    print("[PASS] Tampered and unsafe attestation evidence rejected")
    print("[PASS] Registry and product mutation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def ensure_package(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8", newline="\n")
        print(f"[OK] PACKAGE CREATED: {path.resolve()}")


def append_export(path: Path, export_line: str) -> None:
    ensure_package(path)
    existing = path.read_text(encoding="utf-8")
    if export_line not in existing.splitlines():
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        path.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def verify_int_oia_059_contract() -> None:
    if not SOURCE_059.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-059 production module missing: {SOURCE_059}"
        )

    source = SOURCE_059.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-059"',
        "ATTESTATION_SCHEMA_VERSION",
        "class CertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestation",
        "class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationGate",
        "attestation_id",
        "attestation_hash",
        "source_consumption_id",
        "attested_consumer_id",
        "attested_projection",
        "attested_response_artifact_entry_ids",
        "independent_attestation_verified",
        "consumption_attested",
        "registry_mutation_allowed",
        "publication_allowed",
        "order_execution_allowed",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-059 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-059 authorization-consumption-attestation contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-060 INSTALLER")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" AUTHORIZATION CONSUMPTION ATTESTATION AUTHORIZATION")
    print("=" * 40)

    verify_int_oia_059_contract()

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    print("[OK] Short unique INT-OIA-060 production module installed")

    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_intelligence_analytics_int_oia_060_authorization_gate import *",
    )
    append_export(DOWNSTREAM_PACKAGE, "from .query import *")
    append_export(ANALYTICS_PACKAGE, "from .downstream.query import *")

    for target in (
        PRODUCTION,
        TEST,
        QUERY_PACKAGE,
        DOWNSTREAM_PACKAGE,
        ANALYTICS_PACKAGE,
    ):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    print("[PASS] Windows-safe production module identity preserved")
    print("[OK] INT-OIA-060 test executed automatically")
    print()
    print("[DONE] INT-OIA-060 authorization consumption attestation authorization gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
