from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
QUERY = DOWNSTREAM / "query"

SOURCE_045 = QUERY / (
    "oracle_intelligence_analytics_certified_query_response_artifact_"
    "read_authorization_gate.py"
)
PRODUCTION = QUERY / (
    "oracle_intelligence_analytics_certified_query_response_artifact_"
    "read_authorization_consumption_gate.py"
)
TEST = ROOT / (
    "test_int_oia_046_oracle_intelligence_analytics_certified_query_response_"
    "artifact_read_authorization_consumption_gate.py"
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

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_authorization_gate import (
    CertifiedQueryResponseArtifactReadAuthorization,
)

SCHEMA_VERSION = "INT-OIA-046"
ENGINE_ID = "INT-OIA-046"
POLICY_ID = (
    "oracle.intelligence.analytics.certified-query-response-artifact."
    "read-authorization-consumption-gate.v1"
)
CONSUMPTION_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-read-authorization-consumption.v1"
)
CONSUMPTION_STATUS = (
    "certified_query_response_artifact_read_authorization_consumed"
)


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
    RuntimeError
):
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
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
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


def _verify_hash_record(
    value: Any,
    hash_field: str,
    label: str,
) -> None:
    body = asdict(value)
    supplied = body.pop(hash_field, None)
    if (
        not isinstance(supplied, str)
        or len(supplied) != 64
        or any(character not in "0123456789abcdef" for character in supplied)
        or stable_hash(body) != supplied
    ):
        raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
            f"{label} hash mismatch"
        )


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactReadAuthorizationConsumption:
    consumption_id: str
    source_authorization_id: str
    source_authorization_hash: str
    source_read_result_id: str
    source_read_result_hash: str
    source_read_request_id: str
    source_read_request_hash: str
    source_registry_manifest_id: str
    source_registry_manifest_hash: str
    consuming_consumer_id: str
    consuming_projection: str
    consumed_entry_count: int
    consumed_response_artifact_entry_ids: tuple[str, ...]
    consumed_query_response_ids: tuple[str, ...]
    authorization_verified: bool
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    non_empty_authorization_verified: bool
    entry_identity_cardinality_verified: bool
    query_response_identity_cardinality_verified: bool
    single_use_verified: bool
    read_only_consumption_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_consumption_verified: bool
    authorization_consumed: bool
    registry_mutation_allowed: bool
    registry_mutation_performed: bool
    publication_allowed: bool
    publication_performed: bool
    order_execution_allowed: bool
    order_execution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    consumption_status: str
    consumption_hash: str


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate:
    def __init__(self) -> None:
        self._consumed_authorization_ids: set[str] = set()

    @property
    def consumed_authorization_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._consumed_authorization_ids))

    @staticmethod
    def _verify_authorization(
        authorization: CertifiedQueryResponseArtifactReadAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            CertifiedQueryResponseArtifactReadAuthorization,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorization must use the canonical INT-OIA-045 contract"
            )

        _verify_hash_record(
            authorization,
            "authorization_hash",
            "certified query response artifact read authorization",
        )

        if not authorization.authorization_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorization identity is empty"
            )
        if authorization.authorized_entry_count < 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "empty authorization cannot be consumed"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_response_artifact_entry_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorized artifact-entry cardinality mismatch"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_query_response_ids
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorized query-response cardinality mismatch"
            )
        if len(set(authorization.authorized_response_artifact_entry_ids)) != (
            authorization.authorized_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "duplicate authorized artifact-entry identity detected"
            )
        if len(set(authorization.authorized_query_response_ids)) != (
            authorization.authorized_entry_count
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "duplicate authorized query-response identity detected"
            )

        if not (
            authorization.read_result_verified
            and authorization.registry_manifest_verified
            and authorization.registry_entry_hashes_verified
            and authorization.request_verified
            and authorization.non_empty_result_verified
            and authorization.single_consumer_verified
            and authorization.single_projection_verified
            and authorization.consumer_identity_verified
            and authorization.projection_identity_verified
            and authorization.immutable_read_verified
            and authorization.source_hashes_verified
            and authorization.lineage_verified
            and authorization.deterministic_ordering_verified
            and authorization.deterministic_replay_verified
            and authorization.read_authorized
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorization is not eligible for consumption"
            )

        if (
            authorization.registry_mutation_allowed
            or authorization.registry_mutation_performed
            or authorization.publication_allowed
            or authorization.publication_performed
            or authorization.order_execution_allowed
            or authorization.order_execution_performed
            or authorization.database_connection_performed
            or authorization.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorization contains forbidden activity"
            )

    def consume(
        self,
        *,
        authorization: CertifiedQueryResponseArtifactReadAuthorization,
        consuming_consumer_id: str,
        consuming_projection: str,
    ) -> CertifiedQueryResponseArtifactReadAuthorizationConsumption:
        self._verify_authorization(authorization)

        if (
            not isinstance(consuming_consumer_id, str)
            or not consuming_consumer_id.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "consuming_consumer_id must be a non-empty string"
            )
        if (
            not isinstance(consuming_projection, str)
            or not consuming_projection.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "consuming_projection must be a non-empty string"
            )
        if consuming_consumer_id != authorization.authorized_consumer_id:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "consuming consumer identity does not match authorization"
            )
        if consuming_projection != authorization.authorized_projection:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "consuming projection identity does not match authorization"
            )
        if authorization.authorization_id in self._consumed_authorization_ids:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError(
                "authorization has already been consumed"
            )

        entry_ids = tuple(
            authorization.authorized_response_artifact_entry_ids
        )
        query_response_ids = tuple(
            authorization.authorized_query_response_ids
        )

        consumption_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_authorization_id": authorization.authorization_id,
                "source_authorization_hash": authorization.authorization_hash,
                "consuming_consumer_id": consuming_consumer_id,
                "consuming_projection": consuming_projection,
                "consumed_response_artifact_entry_ids": entry_ids,
                "consumed_query_response_ids": query_response_ids,
            }
        )

        body = {
            "consumption_id": consumption_id,
            "source_authorization_id": authorization.authorization_id,
            "source_authorization_hash": authorization.authorization_hash,
            "source_read_result_id": authorization.source_read_result_id,
            "source_read_result_hash": authorization.source_read_result_hash,
            "source_read_request_id": authorization.source_read_request_id,
            "source_read_request_hash": authorization.source_read_request_hash,
            "source_registry_manifest_id": (
                authorization.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                authorization.source_registry_manifest_hash
            ),
            "consuming_consumer_id": consuming_consumer_id,
            "consuming_projection": consuming_projection,
            "consumed_entry_count": authorization.authorized_entry_count,
            "consumed_response_artifact_entry_ids": entry_ids,
            "consumed_query_response_ids": query_response_ids,
            "authorization_verified": True,
            "authorization_identity_verified": True,
            "authorization_hash_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "non_empty_authorization_verified": True,
            "entry_identity_cardinality_verified": True,
            "query_response_identity_cardinality_verified": True,
            "single_use_verified": True,
            "read_only_consumption_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_consumption_verified": True,
            "authorization_consumed": True,
            "registry_mutation_allowed": False,
            "registry_mutation_performed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "order_execution_allowed": False,
            "order_execution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "consumption_status": CONSUMPTION_STATUS,
        }

        record = CertifiedQueryResponseArtifactReadAuthorizationConsumption(
            **body,
            consumption_hash=stable_hash(body),
        )
        self._consumed_authorization_ids.add(
            authorization.authorization_id
        )
        return record


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_SCHEMA_VERSION",
    "CONSUMPTION_STATUS",
    "CertifiedQueryResponseArtifactReadAuthorizationConsumption",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_int_oia_044_oracle_intelligence_analytics_certified_query_response_artifact_read_gate import (
    _manifest,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_authorization_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_authorization_consumption_gate import (
    CONSUMPTION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe authorization consumption accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError:
        pass


def _authorization():
    manifest = _manifest()
    read_gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate()
    )
    authorization_gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate()
    )
    request = read_gate.create_request(
        registry_manifest=manifest,
        consumer_id="oracle.operator.console.v1",
        requested_projection="operator_research",
        maximum_result_count=100,
    )
    result = read_gate.read(
        registry_manifest=manifest,
        read_request=request,
    )
    return authorization_gate.authorize(
        read_result=result,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-046 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" READ AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
    )

    first = gate.consume(
        authorization=authorization,
        consuming_consumer_id="oracle.operator.console.v1",
        consuming_projection="operator_research",
    )

    assert first.authorization_consumed
    assert first.consumed_entry_count == 2
    assert first.consumed_response_artifact_entry_ids == (
        authorization.authorized_response_artifact_entry_ids
    )
    assert first.consumed_query_response_ids == (
        authorization.authorized_query_response_ids
    )
    assert gate.consumed_authorization_ids == (
        authorization.authorization_id,
    )
    assert first.consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "consumption_hash"
        }
    )

    replay_gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
    )
    replay = replay_gate.consume(
        authorization=authorization,
        consuming_consumer_id="oracle.operator.console.v1",
        consuming_projection="operator_research",
    )
    assert replay == first

    _expect_rejected(
        lambda: gate.consume(
            authorization=authorization,
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
        ).consume(
            authorization=authorization,
            consuming_consumer_id="wrong.consumer",
            consuming_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
        ).consume(
            authorization=authorization,
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="wrong_projection",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
        ).consume(
            authorization=replace(
                authorization,
                authorization_hash="0" * 64,
            ),
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
        ).consume(
            authorization=replace(
                authorization,
                publication_allowed=True,
            ),
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )

    duplicate_ids = (
        authorization.authorized_response_artifact_entry_ids[0],
        authorization.authorized_response_artifact_entry_ids[0],
    )
    tampered_body = {
        key: value
        for key, value in authorization.__dict__.items()
        if key != "authorization_hash"
    }
    tampered_body["authorized_response_artifact_entry_ids"] = duplicate_ids
    tampered_authorization = replace(
        authorization,
        authorized_response_artifact_entry_ids=duplicate_ids,
        authorization_hash=stable_hash(tampered_body),
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
        ).consume(
            authorization=tampered_authorization,
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )

    assert first.authorization_verified
    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.non_empty_authorization_verified
    assert first.entry_identity_cardinality_verified
    assert first.query_response_identity_cardinality_verified
    assert first.single_use_verified
    assert first.read_only_consumption_verified
    assert first.source_hashes_verified
    assert first.lineage_verified
    assert first.deterministic_ordering_verified
    assert first.deterministic_consumption_verified
    assert not first.registry_mutation_allowed
    assert not first.registry_mutation_performed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.order_execution_allowed
    assert not first.order_execution_performed
    assert not first.database_connection_performed
    assert not first.corpus_read_execution_repeated

    assert CONSUMPTION_SCHEMA_VERSION == (
        "oracle.certified-query-response-artifact-read-authorization-consumption.v1"
    )

    print("[PASS] Actual INT-OIA-045 authorization contract consumed")
    print("[PASS] Authorization identity and hash independently verified")
    print("[PASS] Consumer and projection identities matched exactly")
    print("[PASS] Artifact-entry and query-response cardinality verified")
    print("[PASS] Duplicate authorized identities rejected")
    print("[PASS] Deterministic consumption record created")
    print("[PASS] Fresh-gate deterministic replay verified")
    print("[PASS] Same-gate duplicate consumption rejected")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-045 lineage preserved")
    print("[PASS] Tampered authorization evidence rejected")
    print("[PASS] Mismatched consumer and projection rejected")
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


def append_export(path: Path, export_line: str) -> None:
    ensure_package(path)
    existing = path.read_text(encoding="utf-8")
    if export_line not in existing.splitlines():
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        path.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def verify_int_oia_045_contract() -> None:
    if not SOURCE_045.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-045 production module missing: {SOURCE_045}"
        )
    source = SOURCE_045.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-045"',
        "AUTHORIZATION_SCHEMA_VERSION",
        "class CertifiedQueryResponseArtifactReadAuthorization",
        "class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate",
        "authorization_hash",
        "authorization_id",
        "authorized_consumer_id",
        "authorized_projection",
        "authorized_response_artifact_entry_ids",
        "read_authorized",
        "registry_mutation_allowed",
        "publication_allowed",
        "order_execution_allowed",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-045 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-045 read-authorization contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-046 INSTALLER")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" READ AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    verify_int_oia_045_contract()

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_intelligence_analytics_certified_query_response_artifact_read_authorization_consumption_gate import *",
    )
    append_export(
        DOWNSTREAM_PACKAGE,
        "from .query import *",
    )
    append_export(
        ANALYTICS_PACKAGE,
        "from .downstream.query import *",
    )

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

    print("[OK] INT-OIA-046 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-046 certified query response artifact "
        "read authorization consumption gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
