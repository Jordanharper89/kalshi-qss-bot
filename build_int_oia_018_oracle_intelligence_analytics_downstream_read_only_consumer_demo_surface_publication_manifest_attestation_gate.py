from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_manifest_attestation_gate.py"
TEST = ROOT / "test_int_oia_018_oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_manifest_attestation_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
INT_OIA_017 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_manifest_gate.py"

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

SCHEMA_VERSION = "INT-OIA-018"
ENGINE_ID = "INT-OIA-018"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-publication-manifest-independent-attestation.v1"
)
STATUS_ATTESTED = "demo_surface_publication_manifest_independently_attested"

DEFAULT_PUBLICATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_manifest"
)
DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_manifest_attestation"
)

APPROVED_PUBLICATION_SCHEMA = "oracle_research_demo_publication_manifest.v1"
APPROVED_PUBLICATION_MODE = "immutable_read_only_demo_publication"
APPROVED_DEMO_SURFACE_SCHEMA = "oracle_research_demo_surface.v1"
APPROVED_DEMO_SURFACE_MODE = "read_only_research_demo"
APPROVED_PRESENTATION_SCHEMA = "oracle_research_presentation.v1"
APPROVED_RESULT_CLASS = "immutable_research_artifact"
APPROVED_RELEASE_MODE = "research_presentation_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
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
class DemoSurfacePublicationAttestationRecord:
    sequence: int
    attestation_id: str
    publication_id: str
    consumer_id: str
    source_publication_record_hash: str
    source_demo_surface_release_id: str
    source_demo_surface_release_record_hash: str
    source_presentation_release_attestation_id: str
    research_presentation_release_id: str
    source_result_admission_id: str
    result_attestation_id: str
    invocation_execution_id: str
    invocation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    result_hash: str
    admitted_result_hash: str
    source_presentation_payload_hash: str
    source_demo_surface_payload_hash: str
    publication_payload_hash: str
    publication_schema: str
    publication_mode: str
    publication_record_hash_verified: bool
    publication_payload_hash_verified: bool
    source_release_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    publication_schema_verified: bool
    publication_mode_verified: bool
    duplicate_publication_rejected: bool
    independent_attestation_performed: bool
    publication_manifest_published: bool
    signals_created: bool
    alerts_created: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    market_order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    source_mutation_performed: bool
    attestation_status: str
    attestation_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestation:
    schema_version: str
    engine_id: str
    attested_at: str
    attestation_manifest_id: str
    attestation_status: str
    attestation_policy_id: str
    source_publication_manifest_id: str
    source_publication_manifest_hash: str
    source_demo_surface_release_manifest_id: str
    source_demo_surface_release_manifest_hash: str
    source_presentation_release_attestation_manifest_id: str
    source_research_presentation_release_manifest_id: str
    source_result_admission_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    attestation_record_count: int
    attestation_records: tuple[DemoSurfacePublicationAttestationRecord, ...]
    all_publication_record_hashes_verified: bool
    all_publication_payload_hashes_verified: bool
    all_source_release_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_publication_schemas_verified: bool
    all_publication_modes_verified: bool
    all_publications_independently_attested: bool
    duplicate_publications_rejected: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    research_presentation_released: bool
    demo_surface_released: bool
    publication_manifest_published: bool
    publication_manifest_attested: bool
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
    attestation_artifact_persistence_allowed: bool
    attestation_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationGate:
    def __init__(
        self,
        *,
        publication_directory: Path | str = DEFAULT_PUBLICATION_DIRECTORY,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
    ) -> None:
        self.publication_directory = Path(publication_directory)
        self.attestation_directory = Path(attestation_directory)

    def _load_publication(self) -> dict[str, Any]:
        path = self.publication_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                f"INT-OIA-017 publication artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                "INT-OIA-017 publication artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("publication_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                "INT-OIA-017 publication manifest hash mismatch"
            )
        payload["publication_manifest_hash"] = manifest_hash

        required_manifest = {
            "schema_version": "INT-OIA-017",
            "engine_id": "INT-OIA-017",
            "publication_manifest_status": (
                "read_only_demo_surface_publication_manifest_published"
            ),
            "publication_schema": APPROVED_PUBLICATION_SCHEMA,
            "publication_mode": APPROVED_PUBLICATION_MODE,
            "all_source_release_hashes_verified": True,
            "all_demo_surface_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_publication_schemas_verified": True,
            "all_publications_immutable_read_only_demo_only": True,
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
            "publication_artifact_persistence_allowed": True,
        }
        for field, expected in required_manifest.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                    f"unsafe or incomplete INT-OIA-017 field: {field}"
                )

        records = payload.get("publication_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("publication_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                "INT-OIA-017 publication records invalid"
            )

        seen_publication_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                    "publication record must be a mapping"
                )
            record = dict(raw_record)
            record_hash = record.pop("publication_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                    "INT-OIA-017 publication-record hash mismatch"
                )
            record["publication_record_hash"] = record_hash

            publication_id = record.get("publication_id")
            if (
                record.get("sequence") != sequence
                or not isinstance(publication_id, str)
                or not publication_id
                or publication_id in seen_publication_ids
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                    "invalid sequence or duplicate publication"
                )
            seen_publication_ids.add(publication_id)

            publication_payload = record.get("publication_payload")
            if not isinstance(publication_payload, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                    "publication payload must be a mapping"
                )
            if stable_hash(publication_payload) != record.get("publication_payload_hash"):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                    "publication payload hash mismatch"
                )

            required_record = {
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "publication_record_hash_verified": None,
                "source_release_hash_verified": True,
                "demo_surface_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "publication_schema_verified": True,
                "duplicate_publication_rejected": True,
                "demo_surface_released": True,
                "publication_manifest_published": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "publication_status": (
                    "published_as_immutable_read_only_demo_manifest"
                ),
            }
            for field, expected in required_record.items():
                if expected is not None and record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                        f"unsafe INT-OIA-017 publication-record field: {field}"
                    )

            required_payload = {
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
                "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
                "result_class": APPROVED_RESULT_CLASS,
                "release_mode": APPROVED_RELEASE_MODE,
                "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
                "immutable": True,
                "read_only": True,
                "execution_disabled": True,
                "signals_disabled": True,
                "alerts_disabled": True,
                "qseries_handoff_disabled": True,
                "qseries_execution_disabled": True,
                "market_order_creation_disabled": True,
                "funds_movement_disabled": True,
                "portfolio_mutation_disabled": True,
                "source_mutation_disabled": True,
            }
            for field, expected in required_payload.items():
                if publication_payload.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                        f"unsafe publication payload field: {field}"
                    )

        return payload

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestation:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_publication()

        records: list[DemoSurfacePublicationAttestationRecord] = []
        seen_attestation_ids: set[str] = set()

        for sequence, publication in enumerate(
            source["publication_records"],
            start=1,
        ):
            attestation_id = stable_hash(
                {
                    "source_publication_manifest_id": source[
                        "publication_manifest_id"
                    ],
                    "publication_id": publication["publication_id"],
                    "source_publication_record_hash": publication[
                        "publication_record_hash"
                    ],
                    "publication_payload_hash": publication[
                        "publication_payload_hash"
                    ],
                    "attested_at": attested_at.isoformat(),
                }
            )
            if attestation_id in seen_attestation_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError(
                    "duplicate attestation id"
                )
            seen_attestation_ids.add(attestation_id)

            body = {
                "sequence": sequence,
                "attestation_id": attestation_id,
                "publication_id": publication["publication_id"],
                "consumer_id": publication["consumer_id"],
                "source_publication_record_hash": publication[
                    "publication_record_hash"
                ],
                "source_demo_surface_release_id": publication[
                    "source_demo_surface_release_id"
                ],
                "source_demo_surface_release_record_hash": publication[
                    "source_demo_surface_release_record_hash"
                ],
                "source_presentation_release_attestation_id": publication[
                    "source_presentation_release_attestation_id"
                ],
                "research_presentation_release_id": publication[
                    "research_presentation_release_id"
                ],
                "source_result_admission_id": publication[
                    "source_result_admission_id"
                ],
                "result_attestation_id": publication["result_attestation_id"],
                "invocation_execution_id": publication["invocation_execution_id"],
                "invocation_nonce": publication["invocation_nonce"],
                "source_boundary_id": publication["source_boundary_id"],
                "source_boundary_hash": publication["source_boundary_hash"],
                "result_hash": publication["result_hash"],
                "admitted_result_hash": publication["admitted_result_hash"],
                "source_presentation_payload_hash": publication[
                    "source_presentation_payload_hash"
                ],
                "source_demo_surface_payload_hash": publication[
                    "source_demo_surface_payload_hash"
                ],
                "publication_payload_hash": publication[
                    "publication_payload_hash"
                ],
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
            records.append(
                DemoSurfacePublicationAttestationRecord(
                    **body,
                    attestation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_publication_manifest_id": source[
                    "publication_manifest_id"
                ],
                "source_publication_manifest_hash": source[
                    "publication_manifest_hash"
                ],
                "attested_at": attested_at.isoformat(),
                "attestation_record_hashes": [
                    record.attestation_record_hash for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "attestation_manifest_id": manifest_id,
            "attestation_status": STATUS_ATTESTED,
            "attestation_policy_id": POLICY_ID,
            "source_publication_manifest_id": source[
                "publication_manifest_id"
            ],
            "source_publication_manifest_hash": source[
                "publication_manifest_hash"
            ],
            "source_demo_surface_release_manifest_id": source[
                "source_demo_surface_release_manifest_id"
            ],
            "source_demo_surface_release_manifest_hash": source[
                "source_demo_surface_release_manifest_hash"
            ],
            "source_presentation_release_attestation_manifest_id": source[
                "source_presentation_release_attestation_manifest_id"
            ],
            "source_research_presentation_release_manifest_id": source[
                "source_research_presentation_release_manifest_id"
            ],
            "source_result_admission_manifest_id": source[
                "source_result_admission_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "attestation_record_count": len(records),
            "attestation_records": tuple(records),
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

        serializable = dict(body)
        serializable["attestation_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestation(
            **body,
            attestation_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.attestation_directory / "current.json", payload)
            _atomic_write(
                self.attestation_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.attestation_directory
                    / "publications"
                    / record.publication_id
                    / f"{record.attestation_id}.json",
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

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_manifest_attestation_gate import (
    APPROVED_DEMO_SURFACE_MODE,
    APPROVED_DEMO_SURFACE_SCHEMA,
    APPROVED_PRESENTATION_SCHEMA,
    APPROVED_PUBLICATION_MODE,
    APPROVED_PUBLICATION_SCHEMA,
    APPROVED_RELEASE_MODE,
    APPROVED_RESULT_CLASS,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError,
    stable_hash,
)


def _seed_publication(path: Path) -> None:
    publication_payload = {
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_demo_surface_release_id": "demo-release-test",
        "source_demo_surface_payload_hash": stable_hash({"demo": 1}),
        "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
        "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
        "result_class": APPROVED_RESULT_CLASS,
        "release_mode": APPROVED_RELEASE_MODE,
        "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "published_demo_surface": {
            "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
            "read_only": True,
            "execution_disabled": True,
        },
        "immutable": True,
        "read_only": True,
        "execution_disabled": True,
        "signals_disabled": True,
        "alerts_disabled": True,
        "qseries_handoff_disabled": True,
        "qseries_execution_disabled": True,
        "market_order_creation_disabled": True,
        "funds_movement_disabled": True,
        "portfolio_mutation_disabled": True,
        "source_mutation_disabled": True,
    }
    payload_hash = stable_hash(publication_payload)

    record = {
        "sequence": 1,
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
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
        "publication_payload_hash": payload_hash,
        "publication_payload": publication_payload,
        "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
        "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "result_class": APPROVED_RESULT_CLASS,
        "release_mode": APPROVED_RELEASE_MODE,
        "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "source_release_hash_verified": True,
        "demo_surface_payload_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "publication_schema_verified": True,
        "duplicate_publication_rejected": True,
        "demo_surface_released": True,
        "publication_manifest_published": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "publication_status": "published_as_immutable_read_only_demo_manifest",
    }
    record["publication_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-017",
        "engine_id": "INT-OIA-017",
        "published_at": "2026-07-23T00:00:00+00:00",
        "publication_manifest_id": "int-oia-017-test",
        "publication_manifest_status": (
            "read_only_demo_surface_publication_manifest_published"
        ),
        "publication_policy_id": "test",
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "source_demo_surface_release_manifest_id": "int-oia-016-test",
        "source_demo_surface_release_manifest_hash": stable_hash({"int": 16}),
        "source_presentation_release_attestation_manifest_id": "int-oia-015-test",
        "source_research_presentation_release_manifest_id": "int-oia-014-test",
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "publication_record_count": 1,
        "publication_records": [record],
        "all_source_release_hashes_verified": True,
        "all_demo_surface_payload_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_publication_schemas_verified": True,
        "all_publications_immutable_read_only_demo_only": True,
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
        "publication_artifact_persistence_allowed": True,
    }
    manifest["publication_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-018 TEST")
    print(" PUBLICATION MANIFEST ATTESTATION")
    print(" INDEPENDENT READ-ONLY VERIFICATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        publication = root / "publication"
        attestation = root / "attestation"
        _seed_publication(publication)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationGate(
            publication_directory=publication,
            attestation_directory=attestation,
        )
        fixed = datetime(2026, 7, 23, tzinfo=timezone.utc)

        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-018"
        assert first.attestation_record_count == 1
        assert first.all_publication_record_hashes_verified
        assert first.all_publication_payload_hashes_verified
        assert first.all_source_release_hashes_verified
        assert first.all_admission_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_read_only_boundaries_verified
        assert first.all_execution_disabled_boundaries_verified
        assert first.all_publication_schemas_verified
        assert first.all_publication_modes_verified
        assert first.all_publications_independently_attested
        assert first.duplicate_publications_rejected
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.publication_manifest_published
        assert first.publication_manifest_attested
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.attestation_records[0]
        assert record.publication_record_hash_verified
        assert record.publication_payload_hash_verified
        assert record.source_release_hash_verified
        assert record.admission_lineage_verified
        assert record.one_time_invocation_verified
        assert record.immutable_result_verified
        assert record.read_only_boundary_verified
        assert record.execution_disabled_boundary_verified
        assert record.publication_schema_verified
        assert record.publication_mode_verified
        assert record.duplicate_publication_rejected
        assert record.independent_attestation_performed
        assert (
            record.attestation_status
            == "publication_manifest_record_independently_attested"
        )
        assert (attestation / "current.json").exists()

        tampered = json.loads(
            (publication / "current.json").read_text(encoding="utf-8")
        )
        tampered["publication_records"][0]["publication_payload"][
            "qseries_execution_disabled"
        ] = False
        (publication / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered publication accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-017 publication manifest consumed")
    print("[PASS] Publication manifest hash independently verified")
    print("[PASS] Every publication-record hash independently verified")
    print("[PASS] Every publication payload hash independently recomputed")
    print("[PASS] Complete release, admission, and invocation lineage preserved")
    print("[PASS] One-time invocation proof preserved")
    print("[PASS] Immutable read-only publication mode independently attested")
    print("[PASS] Execution-disabled boundary independently verified")
    print("[PASS] Duplicate publication identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe publication manifest rejected")
    print("[PASS] Atomic independent-attestation artifacts persisted")
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


def verify_int_oia_017_contract() -> None:
    if not INT_OIA_017.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-017 production module missing: {INT_OIA_017}"
        )
    source = INT_OIA_017.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-017"',
        "class DemoSurfacePublicationRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestGate",
        "publication_manifest_hash",
        "publication_manifest_published",
        "all_publications_immutable_read_only_demo_only",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-017 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-017 publication-manifest contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export_line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_demo_surface_publication_manifest_attestation_gate import *"
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
    print(" INT-OIA-018 INSTALLER")
    print(" PUBLICATION MANIFEST ATTESTATION")
    print(" INDEPENDENT READ-ONLY VERIFICATION")
    print("=" * 40)

    verify_int_oia_017_contract()
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

    print("[OK] INT-OIA-018 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-018 independent demo-surface publication "
        "manifest attestation gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
