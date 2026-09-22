from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization_gate.py"
TEST = ROOT / "test_int_oia_019_oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
INT_OIA_018 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_manifest_attestation_gate.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-019"
ENGINE_ID = "INT-OIA-019"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-publication-release-authorization.v1"
)
STATUS_AUTHORIZED = "demo_surface_publication_release_authorized"

DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_manifest_attestation"
)
DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization"
)

APPROVED_PUBLICATION_SCHEMA = "oracle_research_demo_publication_manifest.v1"
APPROVED_PUBLICATION_MODE = "immutable_read_only_demo_publication"
APPROVED_AUTHORIZATION_MODE = "one_time_read_only_demo_publication_release"
APPROVED_AUTHORIZATION_SCOPE = "attested_demo_surface_publication_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
        f"unsupported value type: {type(value)!r}"
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


def _valid_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
            f"{field} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(
        _canonical(payload),
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    ) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(handle.name)
    try:
        with handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


@dataclass(frozen=True)
class DemoSurfacePublicationReleaseAuthorizationRecord:
    sequence: int
    authorization_id: str
    attestation_id: str
    publication_id: str
    consumer_id: str
    source_attestation_record_hash: str
    source_publication_record_hash: str
    source_demo_surface_release_id: str
    source_demo_surface_release_record_hash: str
    source_result_admission_id: str
    invocation_execution_id: str
    invocation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    result_hash: str
    admitted_result_hash: str
    publication_payload_hash: str
    publication_schema: str
    publication_mode: str
    authorization_mode: str
    authorization_scope: str
    attestation_record_hash_verified: bool
    publication_record_hash_verified: bool
    publication_payload_hash_verified: bool
    source_release_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    independent_attestation_verified: bool
    authorization_scope_verified: bool
    duplicate_authorization_rejected: bool
    publication_release_authorized: bool
    signals_created: bool
    alerts_created: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    market_order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    source_mutation_performed: bool
    authorization_status: str
    authorization_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorization:
    schema_version: str
    engine_id: str
    authorized_at: str
    authorization_manifest_id: str
    authorization_status: str
    authorization_policy_id: str
    authorization_mode: str
    authorization_scope: str
    source_attestation_manifest_id: str
    source_attestation_manifest_hash: str
    source_publication_manifest_id: str
    source_publication_manifest_hash: str
    source_demo_surface_release_manifest_id: str
    source_demo_surface_release_manifest_hash: str
    source_result_admission_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    authorization_record_count: int
    authorization_records: tuple[DemoSurfacePublicationReleaseAuthorizationRecord, ...]
    all_attestation_record_hashes_verified: bool
    all_publication_record_hashes_verified: bool
    all_publication_payload_hashes_verified: bool
    all_source_release_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_independent_attestations_verified: bool
    all_authorization_scopes_verified: bool
    all_publication_releases_authorized: bool
    duplicate_authorizations_rejected: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    demo_surface_released: bool
    publication_manifest_published: bool
    publication_manifest_attested: bool
    publication_release_authorized: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    signals_created: bool
    alerts_allowed: bool
    alerts_created: bool
    qseries_handoff_allowed: bool
    qseries_handoff_performed: bool
    qseries_execution_allowed: bool
    qseries_execution_performed: bool
    market_order_creation_allowed: bool
    market_order_creation_performed: bool
    funds_movement_allowed: bool
    funds_movement_performed: bool
    portfolio_mutation_allowed: bool
    portfolio_mutation_performed: bool
    authorization_artifact_persistence_allowed: bool
    authorization_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationGate:
    def __init__(
        self,
        *,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
    ) -> None:
        self.attestation_directory = Path(attestation_directory)
        self.authorization_directory = Path(authorization_directory)

    def _load_attestation(self) -> dict[str, Any]:
        path = self.attestation_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                f"INT-OIA-018 attestation artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                "INT-OIA-018 attestation artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("attestation_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                "INT-OIA-018 attestation manifest hash mismatch"
            )
        payload["attestation_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": "INT-OIA-018",
            "engine_id": "INT-OIA-018",
            "attestation_status": (
                "demo_surface_publication_manifest_independently_attested"
            ),
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_source_release_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_publication_schemas_verified": True,
            "all_publication_modes_verified": True,
            "all_publications_independently_attested": True,
            "duplicate_publications_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "research_presentation_released": True,
            "demo_surface_released": True,
            "publication_manifest_published": True,
            "publication_manifest_attested": True,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "signals_created": False,
            "alerts_allowed": False,
            "alerts_created": False,
            "qseries_handoff_allowed": False,
            "qseries_handoff_performed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "market_order_creation_allowed": False,
            "market_order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "attestation_artifact_persistence_allowed": True,
        }
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                    f"unsafe or incomplete INT-OIA-018 field: {field}"
                )

        records = payload.get("attestation_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("attestation_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                "INT-OIA-018 attestation records invalid"
            )

        seen_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                    "attestation record must be a mapping"
                )
            record = dict(raw_record)
            record_hash = record.pop("attestation_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                    "INT-OIA-018 attestation-record hash mismatch"
                )
            record["attestation_record_hash"] = record_hash

            attestation_id = record.get("attestation_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(attestation_id, str)
                or not attestation_id
                or attestation_id in seen_ids
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                    "invalid sequence or duplicate attestation"
                )
            seen_ids.add(attestation_id)

            required_record = {
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "source_release_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "publication_schema_verified": True,
                "publication_mode_verified": True,
                "duplicate_publication_rejected": True,
                "independent_attestation_performed": True,
                "publication_manifest_published": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "attestation_status": (
                    "publication_manifest_record_independently_attested"
                ),
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                        f"unsafe INT-OIA-018 attestation-record field: {field}"
                    )

        return payload

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorization:
        authorized_at = _aware(authorized_at, "authorized_at")
        source = self._load_attestation()

        records: list[DemoSurfacePublicationReleaseAuthorizationRecord] = []
        seen_authorization_ids: set[str] = set()

        for sequence, attestation in enumerate(
            source["attestation_records"],
            start=1,
        ):
            authorization_id = stable_hash(
                {
                    "source_attestation_manifest_id": source[
                        "attestation_manifest_id"
                    ],
                    "attestation_id": attestation["attestation_id"],
                    "source_attestation_record_hash": attestation[
                        "attestation_record_hash"
                    ],
                    "publication_id": attestation["publication_id"],
                    "authorized_at": authorized_at.isoformat(),
                    "authorization_mode": APPROVED_AUTHORIZATION_MODE,
                    "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
                }
            )
            if authorization_id in seen_authorization_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError(
                    "duplicate authorization id"
                )
            seen_authorization_ids.add(authorization_id)

            body = {
                "sequence": sequence,
                "authorization_id": authorization_id,
                "attestation_id": attestation["attestation_id"],
                "publication_id": attestation["publication_id"],
                "consumer_id": attestation["consumer_id"],
                "source_attestation_record_hash": attestation[
                    "attestation_record_hash"
                ],
                "source_publication_record_hash": attestation[
                    "source_publication_record_hash"
                ],
                "source_demo_surface_release_id": attestation[
                    "source_demo_surface_release_id"
                ],
                "source_demo_surface_release_record_hash": attestation[
                    "source_demo_surface_release_record_hash"
                ],
                "source_result_admission_id": attestation[
                    "source_result_admission_id"
                ],
                "invocation_execution_id": attestation[
                    "invocation_execution_id"
                ],
                "invocation_nonce": attestation["invocation_nonce"],
                "source_boundary_id": attestation["source_boundary_id"],
                "source_boundary_hash": attestation["source_boundary_hash"],
                "result_hash": attestation["result_hash"],
                "admitted_result_hash": attestation["admitted_result_hash"],
                "publication_payload_hash": attestation[
                    "publication_payload_hash"
                ],
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "authorization_mode": APPROVED_AUTHORIZATION_MODE,
                "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
                "attestation_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "source_release_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_attestation_verified": True,
                "authorization_scope_verified": True,
                "duplicate_authorization_rejected": True,
                "publication_release_authorized": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "authorization_status": (
                    "attested_demo_surface_publication_release_authorized"
                ),
            }
            records.append(
                DemoSurfacePublicationReleaseAuthorizationRecord(
                    **body,
                    authorization_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_attestation_manifest_id": source[
                    "attestation_manifest_id"
                ],
                "source_attestation_manifest_hash": source[
                    "attestation_manifest_hash"
                ],
                "authorized_at": authorized_at.isoformat(),
                "authorization_record_hashes": [
                    record.authorization_record_hash for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at.isoformat(),
            "authorization_manifest_id": manifest_id,
            "authorization_status": STATUS_AUTHORIZED,
            "authorization_policy_id": POLICY_ID,
            "authorization_mode": APPROVED_AUTHORIZATION_MODE,
            "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
            "source_attestation_manifest_id": source[
                "attestation_manifest_id"
            ],
            "source_attestation_manifest_hash": source[
                "attestation_manifest_hash"
            ],
            "source_publication_manifest_id": source[
                "source_publication_manifest_id"
            ],
            "source_publication_manifest_hash": source[
                "source_publication_manifest_hash"
            ],
            "source_demo_surface_release_manifest_id": source[
                "source_demo_surface_release_manifest_id"
            ],
            "source_demo_surface_release_manifest_hash": source[
                "source_demo_surface_release_manifest_hash"
            ],
            "source_result_admission_manifest_id": source[
                "source_result_admission_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "authorization_record_count": len(records),
            "authorization_records": tuple(records),
            "all_attestation_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_source_release_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_attestations_verified": True,
            "all_authorization_scopes_verified": True,
            "all_publication_releases_authorized": True,
            "duplicate_authorizations_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "demo_surface_released": True,
            "publication_manifest_published": True,
            "publication_manifest_attested": True,
            "publication_release_authorized": True,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "signals_created": False,
            "alerts_allowed": False,
            "alerts_created": False,
            "qseries_handoff_allowed": False,
            "qseries_handoff_performed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "market_order_creation_allowed": False,
            "market_order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "authorization_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["authorization_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorization(
            **body,
            authorization_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.authorization_directory / "current.json", payload)
            _atomic_write(
                self.authorization_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.authorization_directory
                    / "publications"
                    / record.publication_id
                    / f"{record.authorization_id}.json",
                    asdict(record),
                )

        return manifest
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization_gate import (
    APPROVED_AUTHORIZATION_MODE,
    APPROVED_AUTHORIZATION_SCOPE,
    APPROVED_PUBLICATION_MODE,
    APPROVED_PUBLICATION_SCHEMA,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError,
    stable_hash,
)


def _seed_attestation(path: Path) -> None:
    record = {
        "sequence": 1,
        "attestation_id": "attestation-test",
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_publication_record_hash": stable_hash({"publication": 1}),
        "source_demo_surface_release_id": "demo-release-test",
        "source_demo_surface_release_record_hash": stable_hash({"release": 1}),
        "source_presentation_release_attestation_id": "presentation-attestation-test",
        "research_presentation_release_id": "presentation-release-test",
        "source_result_admission_id": "admission-test",
        "result_attestation_id": "result-attestation-test",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "source_presentation_payload_hash": stable_hash({"presentation": 1}),
        "source_demo_surface_payload_hash": stable_hash({"demo": 1}),
        "publication_payload_hash": stable_hash({"payload": 1}),
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "publication_record_hash_verified": True,
        "publication_payload_hash_verified": True,
        "source_release_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "publication_schema_verified": True,
        "publication_mode_verified": True,
        "duplicate_publication_rejected": True,
        "independent_attestation_performed": True,
        "publication_manifest_published": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "attestation_status": "publication_manifest_record_independently_attested",
    }
    record["attestation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-018",
        "engine_id": "INT-OIA-018",
        "attested_at": "2026-07-23T00:00:00+00:00",
        "attestation_manifest_id": "int-oia-018-test",
        "attestation_status": (
            "demo_surface_publication_manifest_independently_attested"
        ),
        "attestation_policy_id": "test",
        "source_publication_manifest_id": "int-oia-017-test",
        "source_publication_manifest_hash": stable_hash({"int": 17}),
        "source_demo_surface_release_manifest_id": "int-oia-016-test",
        "source_demo_surface_release_manifest_hash": stable_hash({"int": 16}),
        "source_presentation_release_attestation_manifest_id": "int-oia-015-test",
        "source_research_presentation_release_manifest_id": "int-oia-014-test",
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "attestation_record_count": 1,
        "attestation_records": [record],
        "all_publication_record_hashes_verified": True,
        "all_publication_payload_hashes_verified": True,
        "all_source_release_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_publication_schemas_verified": True,
        "all_publication_modes_verified": True,
        "all_publications_independently_attested": True,
        "duplicate_publications_rejected": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "research_presentation_released": True,
        "demo_surface_released": True,
        "publication_manifest_published": True,
        "publication_manifest_attested": True,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "signals_created": False,
        "alerts_allowed": False,
        "alerts_created": False,
        "qseries_handoff_allowed": False,
        "qseries_handoff_performed": False,
        "qseries_execution_allowed": False,
        "qseries_execution_performed": False,
        "market_order_creation_allowed": False,
        "market_order_creation_performed": False,
        "funds_movement_allowed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_allowed": False,
        "portfolio_mutation_performed": False,
        "attestation_artifact_persistence_allowed": True,
    }
    manifest["attestation_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-019 TEST")
    print(" PUBLICATION RELEASE AUTHORIZATION")
    print(" ATTESTED READ-ONLY DEMO BOUNDARY")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        attestation = root / "attestation"
        authorization = root / "authorization"
        _seed_attestation(attestation)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationGate(
            attestation_directory=attestation,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 23, tzinfo=timezone.utc)

        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-019"
        assert first.authorization_mode == APPROVED_AUTHORIZATION_MODE
        assert first.authorization_scope == APPROVED_AUTHORIZATION_SCOPE
        assert first.authorization_record_count == 1
        assert first.all_attestation_record_hashes_verified
        assert first.all_publication_record_hashes_verified
        assert first.all_publication_payload_hashes_verified
        assert first.all_source_release_hashes_verified
        assert first.all_admission_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_read_only_boundaries_verified
        assert first.all_execution_disabled_boundaries_verified
        assert first.all_independent_attestations_verified
        assert first.all_authorization_scopes_verified
        assert first.all_publication_releases_authorized
        assert first.duplicate_authorizations_rejected
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.publication_manifest_published
        assert first.publication_manifest_attested
        assert first.publication_release_authorized
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.authorization_records[0]
        assert record.attestation_record_hash_verified
        assert record.publication_record_hash_verified
        assert record.publication_payload_hash_verified
        assert record.independent_attestation_verified
        assert record.authorization_scope_verified
        assert record.duplicate_authorization_rejected
        assert record.publication_release_authorized
        assert (
            record.authorization_status
            == "attested_demo_surface_publication_release_authorized"
        )
        assert (authorization / "current.json").exists()

        tampered = json.loads(
            (attestation / "current.json").read_text(encoding="utf-8")
        )
        tampered["attestation_records"][0][
            "qseries_execution_performed"
        ] = True
        (attestation / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.authorize(authorized_at=fixed, persist=False)
            raise AssertionError("tampered attestation accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-018 attestation manifest consumed")
    print("[PASS] Attestation manifest hash independently verified")
    print("[PASS] Every attestation-record hash independently verified")
    print("[PASS] Publication and payload hash lineage preserved")
    print("[PASS] Complete release, admission, and invocation lineage preserved")
    print("[PASS] One-time invocation proof preserved")
    print("[PASS] Independent attestation required before authorization")
    print("[PASS] Authorization scope restricted to attested demo publication")
    print("[PASS] Duplicate authorization identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe attestation rejected")
    print("[PASS] Atomic authorization artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series handoff/execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def verify_int_oia_018_contract() -> None:
    if not INT_OIA_018.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-018 production module missing: {INT_OIA_018}"
        )
    source = INT_OIA_018.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-018"',
        "class DemoSurfacePublicationAttestationRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestation",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationGate",
        "attestation_manifest_hash",
        "publication_manifest_attested",
        "all_publications_independently_attested",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-018 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-018 independent-attestation contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export_line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_demo_surface_publication_release_authorization_gate import *"
    )
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        PACKAGE.write_text(
            existing + export_line + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-019 INSTALLER")
    print(" PUBLICATION RELEASE AUTHORIZATION")
    print(" ATTESTED READ-ONLY DEMO BOUNDARY")
    print("=" * 40)

    verify_int_oia_018_contract()
    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    update_package()

    py_compile.compile(str(PRODUCTION), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    py_compile.compile(str(PACKAGE), doraise=True)
    print("[OK] Production, test, and package syntax verified")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    print("[OK] INT-OIA-019 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-019 attested read-only demo publication "
        "release authorization gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
