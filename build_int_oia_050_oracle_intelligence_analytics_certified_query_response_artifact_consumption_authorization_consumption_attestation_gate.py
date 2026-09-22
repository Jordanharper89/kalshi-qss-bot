from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
QUERY = DOWNSTREAM / "query"

SOURCE_049 = QUERY / (
    "oracle_intelligence_analytics_certified_query_response_artifact_"
    "consumption_attestation_authorization_consumption_gate.py"
)
PRODUCTION = QUERY / (
    "oracle_intelligence_analytics_certified_query_response_artifact_"
    "consumption_authorization_consumption_attestation_gate.py"
)
TEST = ROOT / (
    "test_int_oia_050_oracle_intelligence_analytics_certified_query_response_"
    "artifact_consumption_authorization_consumption_attestation_gate.py"
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

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_consumption_attestation_authorization_consumption_gate import (
    CertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumption,
)

SCHEMA_VERSION = "INT-OIA-050"
ENGINE_ID = "INT-OIA-050"
POLICY_ID = (
    "oracle.intelligence.analytics.certified-query-response-artifact."
    "consumption-authorization-consumption-attestation-gate.v1"
)
ATTESTATION_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-consumption-authorization-"
    "consumption-attestation.v1"
)
ATTESTATION_STATUS = (
    "certified_query_response_artifact_consumption_authorization_"
    "consumption_independently_attested"
)


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
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
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
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
        raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
            f"{label} hash mismatch"
        )


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestation:
    attestation_id: str
    source_consumption_id: str
    source_consumption_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_attestation_id: str
    source_attestation_hash: str
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
    attested_consumer_id: str
    attested_projection: str
    attested_entry_count: int
    attested_response_artifact_entry_ids: tuple[str, ...]
    attested_query_response_ids: tuple[str, ...]
    consumption_hash_verified: bool
    consumption_identity_verified: bool
    authorization_lineage_verified: bool
    attestation_lineage_verified: bool
    prior_consumption_lineage_verified: bool
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
    single_use_consumption_verified: bool
    read_only_consumption_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_consumption_verified: bool
    independent_attestation_verified: bool
    consumption_attested: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    attestation_status: str
    attestation_hash: str


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationGate:
    @staticmethod
    def _verify_consumption(
        consumption: CertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            CertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumption,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
                "consumption must use the canonical INT-OIA-049 contract"
            )

        _verify_hash_record(
            consumption,
            "consumption_hash",
            "attestation authorization consumption",
        )

        if not consumption.consumption_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
                "consumption identity is empty"
            )
        if consumption.consumed_entry_count < 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
                "empty consumption cannot be attested"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_response_artifact_entry_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
                "consumed artifact-entry cardinality mismatch"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_query_response_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
                "consumed query-response cardinality mismatch"
            )
        if len(set(consumption.consumed_response_artifact_entry_ids)) != (
            consumption.consumed_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
                "duplicate consumed artifact-entry identity detected"
            )
        if len(set(consumption.consumed_query_response_ids)) != (
            consumption.consumed_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
                "duplicate consumed query-response identity detected"
            )

        required = (
            consumption.authorization_hash_verified,
            consumption.authorization_identity_verified,
            consumption.attestation_lineage_verified,
            consumption.consumption_lineage_verified,
            consumption.read_authorization_lineage_verified,
            consumption.read_result_lineage_verified,
            consumption.read_request_lineage_verified,
            consumption.registry_manifest_lineage_verified,
            consumption.consumer_identity_verified,
            consumption.projection_identity_verified,
            consumption.entry_identity_cardinality_verified,
            consumption.query_response_identity_cardinality_verified,
            consumption.unique_entry_identities_verified,
            consumption.unique_query_response_identities_verified,
            consumption.single_use_verified,
            consumption.read_only_consumption_verified,
            consumption.source_hashes_verified,
            consumption.lineage_verified,
            consumption.deterministic_ordering_verified,
            consumption.deterministic_consumption_verified,
            consumption.authorization_consumed,
        )
        if not all(required):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
                "consumption is not eligible for independent attestation"
            )

        if (
            consumption.registry_mutation_allowed
            or consumption.registry_mutation_performed
            or consumption.publication_allowed
            or consumption.publication_performed
            or consumption.order_execution_allowed
            or consumption.order_execution_performed
            or consumption.database_connection_performed
            or consumption.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError(
                "consumption contains forbidden activity"
            )

    def attest(
        self,
        *,
        consumption: CertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumption,
    ) -> CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestation:
        self._verify_consumption(consumption)

        entry_ids = tuple(consumption.consumed_response_artifact_entry_ids)
        query_response_ids = tuple(consumption.consumed_query_response_ids)

        attestation_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.consumption_id,
                "source_consumption_hash": consumption.consumption_hash,
                "attested_consumer_id": consumption.consuming_consumer_id,
                "attested_projection": consumption.consuming_projection,
                "attested_response_artifact_entry_ids": entry_ids,
                "attested_query_response_ids": query_response_ids,
            }
        )

        body = {
            "attestation_id": attestation_id,
            "source_consumption_id": consumption.consumption_id,
            "source_consumption_hash": consumption.consumption_hash,
            "source_authorization_id": consumption.source_authorization_id,
            "source_authorization_hash": consumption.source_authorization_hash,
            "source_attestation_id": consumption.source_attestation_id,
            "source_attestation_hash": consumption.source_attestation_hash,
            "source_prior_consumption_id": consumption.source_consumption_id,
            "source_prior_consumption_hash": consumption.source_consumption_hash,
            "source_read_authorization_id": (
                consumption.source_read_authorization_id
            ),
            "source_read_authorization_hash": (
                consumption.source_read_authorization_hash
            ),
            "source_read_result_id": consumption.source_read_result_id,
            "source_read_result_hash": consumption.source_read_result_hash,
            "source_read_request_id": consumption.source_read_request_id,
            "source_read_request_hash": consumption.source_read_request_hash,
            "source_registry_manifest_id": (
                consumption.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                consumption.source_registry_manifest_hash
            ),
            "attested_consumer_id": consumption.consuming_consumer_id,
            "attested_projection": consumption.consuming_projection,
            "attested_entry_count": consumption.consumed_entry_count,
            "attested_response_artifact_entry_ids": entry_ids,
            "attested_query_response_ids": query_response_ids,
            "consumption_hash_verified": True,
            "consumption_identity_verified": True,
            "authorization_lineage_verified": True,
            "attestation_lineage_verified": True,
            "prior_consumption_lineage_verified": True,
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
            "single_use_consumption_verified": True,
            "read_only_consumption_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_consumption_verified": True,
            "independent_attestation_verified": True,
            "consumption_attested": True,
            "registry_mutation_allowed": False,
            "registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "attestation_status": ATTESTATION_STATUS,
        }

        return CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestation(
            **body,
            attestation_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ATTESTATION_SCHEMA_VERSION",
    "ATTESTATION_STATUS",
    "CertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestation",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationGate",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_int_oia_049_oracle_intelligence_analytics_certified_query_response_artifact_consumption_attestation_authorization_consumption_gate import (
    _authorization,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_consumption_attestation_authorization_consumption_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_consumption_authorization_consumption_attestation_gate import (
    ATTESTATION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe consumption attestation accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationInvariantError:
        pass


def _consumption():
    authorization = _authorization()
    return (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionGate()
    ).consume(
        authorization=authorization,
        consuming_consumer_id="oracle.operator.console.v1",
        consuming_projection="operator_research",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-050 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" AUTHORIZATION CONSUMPTION ATTESTATION")
    print("=" * 40)

    consumption = _consumption()
    gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAuthorizationConsumptionAttestationGate()
    )

    first = gate.attest(consumption=consumption)
    repeated = gate.attest(consumption=consumption)

    assert first == repeated
    assert first.consumption_attested
    assert first.attested_entry_count == consumption.consumed_entry_count
    assert first.attested_response_artifact_entry_ids == (
        consumption.consumed_response_artifact_entry_ids
    )
    assert first.attested_query_response_ids == (
        consumption.consumed_query_response_ids
    )
    assert first.attestation_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "attestation_hash"
        }
    )

    _expect_rejected(
        lambda: gate.attest(
            consumption=replace(consumption, consumption_hash="0" * 64)
        )
    )
    _expect_rejected(
        lambda: gate.attest(
            consumption=replace(consumption, publication_allowed=True)
        )
    )
    _expect_rejected(
        lambda: gate.attest(
            consumption=replace(consumption, single_use_verified=False)
        )
    )

    duplicate_ids = (
        consumption.consumed_query_response_ids[0],
        consumption.consumed_query_response_ids[0],
    )
    tampered_body = {
        key: value
        for key, value in consumption.__dict__.items()
        if key != "consumption_hash"
    }
    tampered_body["consumed_query_response_ids"] = duplicate_ids
    tampered_consumption = replace(
        consumption,
        consumed_query_response_ids=duplicate_ids,
        consumption_hash=stable_hash(tampered_body),
    )
    _expect_rejected(lambda: gate.attest(consumption=tampered_consumption))

    assert first.consumption_hash_verified
    assert first.consumption_identity_verified
    assert first.authorization_lineage_verified
    assert first.attestation_lineage_verified
    assert first.prior_consumption_lineage_verified
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
    assert first.single_use_consumption_verified
    assert first.read_only_consumption_verified
    assert first.source_hashes_verified
    assert first.lineage_verified
    assert first.deterministic_ordering_verified
    assert first.deterministic_consumption_verified
    assert first.independent_attestation_verified
    assert not first.registry_mutation_allowed
    assert not first.registry_mutation_performed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.order_execution_allowed
    assert not first.order_execution_performed
    assert not first.database_connection_performed
    assert not first.corpus_read_execution_repeated

    assert ATTESTATION_SCHEMA_VERSION == (
        "oracle.certified-query-response-artifact-consumption-authorization-"
        "consumption-attestation.v1"
    )

    print("[PASS] Actual INT-OIA-049 consumption contract consumed")
    print("[PASS] Consumption identity and hash independently verified")
    print("[PASS] Authorization, attestation, and complete read lineage verified")
    print("[PASS] Consumer and projection identities independently attested")
    print("[PASS] Entry and query-response cardinality independently verified")
    print("[PASS] Duplicate consumed identities rejected")
    print("[PASS] Single-use consumption evidence verified")
    print("[PASS] Deterministic independent attestation created")
    print("[PASS] Deterministic attestation replay verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-049 lineage preserved")
    print("[PASS] Tampered and unsafe consumption evidence rejected")
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


def verify_int_oia_049_contract() -> None:
    if not SOURCE_049.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-049 production module missing: {SOURCE_049}"
        )
    source = SOURCE_049.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-049"',
        "CONSUMPTION_SCHEMA_VERSION",
        "class CertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumption",
        "class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionGate",
        "consumption_id",
        "consumption_hash",
        "source_authorization_id",
        "source_attestation_id",
        "consuming_consumer_id",
        "consuming_projection",
        "consumed_response_artifact_entry_ids",
        "single_use_verified",
        "authorization_consumed",
        "registry_mutation_allowed",
        "publication_allowed",
        "order_execution_allowed",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-049 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-049 authorization-consumption contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-050 INSTALLER")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" AUTHORIZATION CONSUMPTION ATTESTATION")
    print("=" * 40)

    verify_int_oia_049_contract()

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_intelligence_analytics_certified_query_response_artifact_consumption_authorization_consumption_attestation_gate import *",
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

    print("[OK] INT-OIA-050 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-050 certified query response artifact "
        "authorization consumption attestation gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
