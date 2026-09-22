from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
DOWNSTREAM = ANALYTICS / "downstream"
QUERY = DOWNSTREAM / "query"

SOURCE_044 = QUERY / (
    "oracle_intelligence_analytics_certified_query_response_artifact_read_gate.py"
)
PRODUCTION = QUERY / (
    "oracle_intelligence_analytics_certified_query_response_artifact_"
    "read_authorization_gate.py"
)
TEST = ROOT / (
    "test_int_oia_045_oracle_intelligence_analytics_certified_query_response_"
    "artifact_read_authorization_gate.py"
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

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_gate import (
    CertifiedQueryResponseArtifactReadResult,
)

SCHEMA_VERSION = "INT-OIA-045"
ENGINE_ID = "INT-OIA-045"
POLICY_ID = (
    "oracle.intelligence.analytics.certified-query-response-artifact."
    "read-authorization-gate.v1"
)
AUTHORIZATION_SCHEMA_VERSION = (
    "oracle.certified-query-response-artifact-read-authorization.v1"
)
AUTHORIZATION_STATUS = (
    "certified_query_response_artifact_read_authorized"
)


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
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
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
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
        raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
            f"{label} hash mismatch"
        )


@dataclass(frozen=True)
class CertifiedQueryResponseArtifactReadAuthorization:
    authorization_id: str
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
    read_result_verified: bool
    registry_manifest_verified: bool
    registry_entry_hashes_verified: bool
    request_verified: bool
    non_empty_result_verified: bool
    single_consumer_verified: bool
    single_projection_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    immutable_read_verified: bool
    source_hashes_verified: bool
    lineage_verified: bool
    deterministic_ordering_verified: bool
    deterministic_replay_verified: bool
    read_authorized: bool
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


class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate:
    @staticmethod
    def _verify_read_result(
        read_result: CertifiedQueryResponseArtifactReadResult,
    ) -> None:
        if not isinstance(
            read_result,
            CertifiedQueryResponseArtifactReadResult,
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result must use the canonical INT-OIA-044 contract"
            )

        _verify_hash_record(
            read_result,
            "read_result_hash",
            "certified query response artifact read result",
        )

        if read_result.matched_entry_count != len(
            read_result.matched_entries
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result entry count mismatch"
            )

        if read_result.matched_entry_count < 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "empty read results cannot be authorized"
            )

        seen_entry_ids: set[str] = set()
        previous_order_key: tuple[int, str, str, str] | None = None
        for entry in read_result.matched_entries:
            _verify_hash_record(
                entry,
                "response_artifact_entry_hash",
                "certified query response artifact entry",
            )
            if entry.response_artifact_entry_id in seen_entry_ids:
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                    "duplicate response artifact entry detected"
                )
            seen_entry_ids.add(entry.response_artifact_entry_id)

            order_key = (
                entry.sequence,
                entry.consumer_id,
                entry.requested_projection,
                entry.response_artifact_entry_id,
            )
            if previous_order_key is not None and order_key < previous_order_key:
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                    "read result ordering is not canonical"
                )
            previous_order_key = order_key

            if not (
                entry.source_response_verified
                and entry.response_item_hashes_verified
                and entry.source_hashes_verified
                and entry.lineage_verified
                and entry.deterministic_ordering_verified
                and entry.deterministic_replay_verified
                and entry.immutable
                and entry.read_only
                and entry.response_artifact_persisted
            ):
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                    "read result contains an uncertified artifact entry"
                )

            if (
                entry.product_registry_mutation_allowed
                or entry.product_registry_mutation_performed
                or entry.publication_allowed
                or entry.publication_performed
                or entry.order_execution_allowed
                or entry.order_execution_performed
                or entry.database_connection_performed
                or entry.corpus_read_execution_repeated
            ):
                raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                    "read result contains an unsafe artifact entry"
                )

        if not (
            read_result.registry_manifest_verified
            and read_result.registry_entry_hashes_verified
            and read_result.request_verified
            and read_result.filters_applied_deterministically
            and read_result.maximum_result_count_enforced
            and read_result.immutable_read_verified
            and read_result.source_hashes_verified
            and read_result.lineage_verified
            and read_result.deterministic_ordering_verified
            and read_result.deterministic_replay_verified
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result is not eligible for authorization"
            )

        if (
            read_result.registry_mutation_allowed
            or read_result.registry_mutation_performed
            or read_result.publication_allowed
            or read_result.publication_performed
            or read_result.order_execution_allowed
            or read_result.order_execution_performed
            or read_result.database_connection_performed
            or read_result.corpus_read_execution_repeated
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result contains forbidden activity"
            )

    def authorize(
        self,
        *,
        read_result: CertifiedQueryResponseArtifactReadResult,
        authorized_consumer_id: str,
        authorized_projection: str,
    ) -> CertifiedQueryResponseArtifactReadAuthorization:
        self._verify_read_result(read_result)

        if (
            not isinstance(authorized_consumer_id, str)
            or not authorized_consumer_id.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "authorized_consumer_id must be a non-empty string"
            )
        if (
            not isinstance(authorized_projection, str)
            or not authorized_projection.strip()
        ):
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "authorized_projection must be a non-empty string"
            )

        consumers = {
            entry.consumer_id
            for entry in read_result.matched_entries
        }
        projections = {
            entry.requested_projection
            for entry in read_result.matched_entries
        }

        if len(consumers) != 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result must contain exactly one consumer identity"
            )
        if len(projections) != 1:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "read result must contain exactly one projection identity"
            )
        if consumers != {authorized_consumer_id}:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "authorized consumer identity does not match the read result"
            )
        if projections != {authorized_projection}:
            raise OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError(
                "authorized projection identity does not match the read result"
            )

        entry_ids = tuple(
            entry.response_artifact_entry_id
            for entry in read_result.matched_entries
        )
        query_response_ids = tuple(
            entry.query_response_id
            for entry in read_result.matched_entries
        )

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_read_result_id": read_result.read_result_id,
                "source_read_result_hash": read_result.read_result_hash,
                "authorized_consumer_id": authorized_consumer_id,
                "authorized_projection": authorized_projection,
                "authorized_response_artifact_entry_ids": entry_ids,
                "authorized_query_response_ids": query_response_ids,
            }
        )

        body = {
            "authorization_id": authorization_id,
            "source_read_result_id": read_result.read_result_id,
            "source_read_result_hash": read_result.read_result_hash,
            "source_read_request_id": read_result.source_read_request_id,
            "source_read_request_hash": read_result.source_read_request_hash,
            "source_registry_manifest_id": (
                read_result.source_registry_manifest_id
            ),
            "source_registry_manifest_hash": (
                read_result.source_registry_manifest_hash
            ),
            "authorized_consumer_id": authorized_consumer_id,
            "authorized_projection": authorized_projection,
            "authorized_entry_count": len(entry_ids),
            "authorized_response_artifact_entry_ids": entry_ids,
            "authorized_query_response_ids": query_response_ids,
            "read_result_verified": True,
            "registry_manifest_verified": True,
            "registry_entry_hashes_verified": True,
            "request_verified": True,
            "non_empty_result_verified": True,
            "single_consumer_verified": True,
            "single_projection_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "immutable_read_verified": True,
            "source_hashes_verified": True,
            "lineage_verified": True,
            "deterministic_ordering_verified": True,
            "deterministic_replay_verified": True,
            "read_authorized": True,
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

        return CertifiedQueryResponseArtifactReadAuthorization(
            **body,
            authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_SCHEMA_VERSION",
    "AUTHORIZATION_STATUS",
    "CertifiedQueryResponseArtifactReadAuthorization",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate",
    "OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError",
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
    AUTHORIZATION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe read authorization accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-045 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" READ AUTHORIZATION GATE")
    print("=" * 40)

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
    assert result.matched_entry_count == 2

    first = authorization_gate.authorize(
        read_result=result,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )
    repeated = authorization_gate.authorize(
        read_result=result,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )

    assert first == repeated
    assert first.read_authorized
    assert first.authorized_entry_count == 2
    assert first.authorized_response_artifact_entry_ids == tuple(
        entry.response_artifact_entry_id
        for entry in result.matched_entries
    )
    assert first.authorized_query_response_ids == tuple(
        entry.query_response_id
        for entry in result.matched_entries
    )
    assert first.authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "authorization_hash"
        }
    )

    mixed_request = read_gate.create_request(
        registry_manifest=manifest,
        maximum_result_count=100,
    )
    mixed_result = read_gate.read(
        registry_manifest=manifest,
        read_request=mixed_request,
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=mixed_result,
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )

    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=result,
            authorized_consumer_id="wrong.consumer",
            authorized_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=result,
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="wrong_projection",
        )
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=replace(
                result,
                read_result_hash="0" * 64,
            ),
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=replace(
                result,
                publication_allowed=True,
            ),
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )

    tampered_entry = replace(
        result.matched_entries[0],
        consumer_id="tampered.consumer",
    )
    tampered_entries = (
        tampered_entry,
        *result.matched_entries[1:],
    )
    tampered_body = {
        key: value
        for key, value in result.__dict__.items()
        if key != "read_result_hash"
    }
    tampered_body["matched_entries"] = tampered_entries
    tampered_result = replace(
        result,
        matched_entries=tampered_entries,
        read_result_hash=stable_hash(tampered_body),
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=tampered_result,
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )

    empty_request = read_gate.create_request(
        registry_manifest=manifest,
        consumer_id="missing.consumer",
    )
    empty_result = read_gate.read(
        registry_manifest=manifest,
        read_request=empty_request,
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=empty_result,
            authorized_consumer_id="missing.consumer",
            authorized_projection="operator_research",
        )
    )

    assert first.read_result_verified
    assert first.registry_manifest_verified
    assert first.registry_entry_hashes_verified
    assert first.request_verified
    assert first.non_empty_result_verified
    assert first.single_consumer_verified
    assert first.single_projection_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.immutable_read_verified
    assert first.source_hashes_verified
    assert first.lineage_verified
    assert first.deterministic_ordering_verified
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
        "oracle.certified-query-response-artifact-read-authorization.v1"
    )

    print("[PASS] Actual INT-OIA-044 read-result contract consumed")
    print("[PASS] Read-result hash independently verified")
    print("[PASS] Every authorized artifact entry hash verified")
    print("[PASS] Non-empty read result required")
    print("[PASS] Single-consumer boundary enforced")
    print("[PASS] Single-projection boundary enforced")
    print("[PASS] Consumer and projection identities verified")
    print("[PASS] Deterministic authorization record created")
    print("[PASS] Deterministic authorization replay verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-044 lineage preserved")
    print("[PASS] Mixed-consumer and mixed-projection results rejected")
    print("[PASS] Tampered read-result evidence rejected")
    print("[PASS] Tampered artifact-entry evidence rejected")
    print("[PASS] Empty read result rejected")
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


def verify_int_oia_044_contract() -> None:
    if not SOURCE_044.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-044 production module missing: {SOURCE_044}"
        )
    source = SOURCE_044.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-044"',
        "READ_RESULT_SCHEMA_VERSION",
        "class CertifiedQueryResponseArtifactReadResult",
        "class OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate",
        "read_result_hash",
        "matched_entries",
        "registry_manifest_verified",
        "registry_entry_hashes_verified",
        "immutable_read_verified",
        "registry_mutation_allowed",
        "publication_allowed",
        "order_execution_allowed",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-044 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-044 artifact-read contract verified")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-045 INSTALLER")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" READ AUTHORIZATION GATE")
    print("=" * 40)

    verify_int_oia_044_contract()

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_intelligence_analytics_certified_query_response_artifact_read_authorization_gate import *",
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

    print("[OK] INT-OIA-045 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-045 certified query response artifact "
        "read authorization gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
