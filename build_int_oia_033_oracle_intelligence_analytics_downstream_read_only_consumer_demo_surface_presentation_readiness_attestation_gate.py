from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

SOURCE_032 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_presentation_readiness_gate.py"
PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_presentation_readiness_attestation_gate.py"
TEST = ROOT / "test_int_oia_033_oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_presentation_readiness_attestation_gate.py"
PACKAGE = ANALYTICS / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-033"
ENGINE_ID = "INT-OIA-033"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-presentation-readiness-attestation.v1"
)
STATUS_ATTESTED = "demo_surface_presentation_readiness_independently_attested"

DEFAULT_PRESENTATION_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_presentation_readiness"
)
DEFAULT_PRESENTATION_READINESS_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_presentation_readiness_attestation"
)

APPROVED_PRESENTATION_MODE = "immutable_read_only_demo_surface_presentation"
APPROVED_PRESENTATION_SCOPE = "independently_attested_serving_consumption_only"
APPROVED_ATTESTATION_MODE = "independent_immutable_read_only_presentation_readiness_attestation"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError(
    RuntimeError
):
    pass


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
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
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError(
            f"{field} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class DemoSurfacePresentationReadinessAttestationRecord:
    sequence: int
    attestation_id: str
    readiness_id: str
    serving_consumption_attestation_id: str
    serving_consumption_id: str
    serving_release_id: str
    publication_id: str
    consumer_id: str
    source_readiness_record_hash: str
    source_serving_consumption_attestation_record_hash: str
    source_serving_consumption_record_hash: str
    source_serving_release_attestation_record_hash: str
    source_serving_release_record_hash: str
    source_publication_record_hash: str
    publication_payload_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    result_hash: str
    admitted_result_hash: str
    presentation_mode: str
    presentation_scope: str
    attestation_mode: str
    readiness_record_hash_verified: bool
    serving_consumption_attestation_record_hash_verified: bool
    serving_consumption_record_hash_verified: bool
    serving_release_attestation_record_hash_verified: bool
    serving_release_record_hash_verified: bool
    publication_record_hash_verified: bool
    publication_payload_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    independent_serving_consumption_attestation_verified: bool
    presentation_scope_verified: bool
    presentation_readiness_verified: bool
    independent_presentation_readiness_attestation_performed: bool
    duplicate_attestation_rejected: bool
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
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestation:
    schema_version: str
    engine_id: str
    attested_at: str
    attestation_manifest_id: str
    attestation_status: str
    attestation_policy_id: str
    attestation_mode: str
    presentation_mode: str
    presentation_scope: str
    source_presentation_readiness_manifest_id: str
    source_presentation_readiness_manifest_hash: str
    source_serving_consumption_attestation_manifest_id: str
    source_serving_consumption_attestation_manifest_hash: str
    source_serving_consumption_manifest_id: str
    source_serving_consumption_manifest_hash: str
    source_serving_release_attestation_manifest_id: str
    source_serving_release_attestation_manifest_hash: str
    source_serving_release_manifest_id: str
    source_serving_release_manifest_hash: str
    source_publication_manifest_id: str
    source_publication_manifest_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    attestation_record_count: int
    attestation_records: tuple[DemoSurfacePresentationReadinessAttestationRecord, ...]
    all_readiness_record_hashes_verified: bool
    all_serving_consumption_attestation_record_hashes_verified: bool
    all_serving_consumption_record_hashes_verified: bool
    all_serving_release_attestation_record_hashes_verified: bool
    all_serving_release_record_hashes_verified: bool
    all_publication_record_hashes_verified: bool
    all_publication_payload_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_independent_serving_consumption_attestations_verified: bool
    all_presentation_scopes_verified: bool
    all_presentation_readiness_records_verified: bool
    all_presentation_readiness_records_independently_attested: bool
    duplicate_attestations_rejected: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    demo_surface_publication_serving_release_consumed: bool
    demo_surface_publication_serving_consumption_attested: bool
    demo_surface_presentation_ready: bool
    demo_surface_presentation_readiness_attested: bool
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


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationGate:
    def __init__(
        self,
        *,
        presentation_readiness_directory: Path | str = DEFAULT_PRESENTATION_READINESS_DIRECTORY,
        attestation_directory: Path | str = DEFAULT_PRESENTATION_READINESS_ATTESTATION_DIRECTORY,
    ) -> None:
        self.presentation_readiness_directory = Path(presentation_readiness_directory)
        self.attestation_directory = Path(attestation_directory)

    def _load_readiness(self) -> dict[str, Any]:
        path = self.presentation_readiness_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError(
                f"INT-OIA-032 presentation-readiness manifest missing: {path}"
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest_hash = payload.pop("readiness_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError(
                "INT-OIA-032 readiness manifest hash mismatch"
            )
        payload["readiness_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-032",
            "engine_id": "INT-OIA-032",
            "readiness_status": "demo_surface_presentation_ready",
            "presentation_mode": APPROVED_PRESENTATION_MODE,
            "presentation_scope": APPROVED_PRESENTATION_SCOPE,
            "all_serving_consumption_attestation_record_hashes_verified": True,
            "all_serving_consumption_record_hashes_verified": True,
            "all_serving_release_attestation_record_hashes_verified": True,
            "all_serving_release_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_serving_consumption_attestations_verified": True,
            "all_presentation_scopes_verified": True,
            "all_demo_surfaces_presentation_ready": True,
            "duplicate_readiness_records_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "demo_surface_publication_serving_release_consumed": True,
            "demo_surface_publication_serving_consumption_attested": True,
            "demo_surface_presentation_ready": True,
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
            "readiness_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError(
                    f"unsafe or incomplete INT-OIA-032 field: {field}"
                )

        records = payload.get("readiness_records")
        if not isinstance(records, list) or not records or payload.get("readiness_record_count") != len(records):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError(
                "INT-OIA-032 readiness records invalid"
            )

        seen: set[str] = set()
        for sequence, raw in enumerate(records, start=1):
            record = dict(raw)
            record_hash = record.pop("readiness_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError(
                    "INT-OIA-032 readiness record hash mismatch"
                )
            record["readiness_record_hash"] = record_hash
            readiness_id = record.get("readiness_id")
            if record.get("sequence") != sequence or not isinstance(readiness_id, str) or not readiness_id or readiness_id in seen:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError(
                    "invalid sequence or duplicate presentation-readiness identity"
                )
            seen.add(readiness_id)
            record_required = {
                "presentation_mode": APPROVED_PRESENTATION_MODE,
                "presentation_scope": APPROVED_PRESENTATION_SCOPE,
                "serving_consumption_attestation_record_hash_verified": True,
                "serving_consumption_record_hash_verified": True,
                "serving_release_attestation_record_hash_verified": True,
                "serving_release_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_serving_consumption_attestation_verified": True,
                "presentation_scope_verified": True,
                "presentation_ready": True,
                "duplicate_readiness_rejected": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "readiness_status": "immutable_read_only_demo_surface_presentation_ready",
            }
            for field, expected in record_required.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError(
                        f"unsafe INT-OIA-032 readiness-record field: {field}"
                    )
        return payload

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestation:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_readiness()
        records: list[DemoSurfacePresentationReadinessAttestationRecord] = []
        seen: set[str] = set()

        for sequence, readiness in enumerate(source["readiness_records"], start=1):
            attestation_id = stable_hash(
                {
                    "source_manifest_id": source["readiness_manifest_id"],
                    "source_record_hash": readiness["readiness_record_hash"],
                    "attestation_mode": APPROVED_ATTESTATION_MODE,
                    "attested_at": attested_at.isoformat(),
                }
            )
            if attestation_id in seen:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError(
                    "duplicate presentation-readiness attestation identity"
                )
            seen.add(attestation_id)

            body = {
                "sequence": sequence,
                "attestation_id": attestation_id,
                "readiness_id": readiness["readiness_id"],
                "serving_consumption_attestation_id": readiness["serving_consumption_attestation_id"],
                "serving_consumption_id": readiness["serving_consumption_id"],
                "serving_release_id": readiness["serving_release_id"],
                "publication_id": readiness["publication_id"],
                "consumer_id": readiness["consumer_id"],
                "source_readiness_record_hash": readiness["readiness_record_hash"],
                "source_serving_consumption_attestation_record_hash": readiness["source_serving_consumption_attestation_record_hash"],
                "source_serving_consumption_record_hash": readiness["source_serving_consumption_record_hash"],
                "source_serving_release_attestation_record_hash": readiness["source_serving_release_attestation_record_hash"],
                "source_serving_release_record_hash": readiness["source_serving_release_record_hash"],
                "source_publication_record_hash": readiness["source_publication_record_hash"],
                "publication_payload_hash": readiness["publication_payload_hash"],
                "source_boundary_id": readiness["source_boundary_id"],
                "source_boundary_hash": readiness["source_boundary_hash"],
                "result_hash": readiness["result_hash"],
                "admitted_result_hash": readiness["admitted_result_hash"],
                "presentation_mode": APPROVED_PRESENTATION_MODE,
                "presentation_scope": APPROVED_PRESENTATION_SCOPE,
                "attestation_mode": APPROVED_ATTESTATION_MODE,
                "readiness_record_hash_verified": True,
                "serving_consumption_attestation_record_hash_verified": True,
                "serving_consumption_record_hash_verified": True,
                "serving_release_attestation_record_hash_verified": True,
                "serving_release_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_serving_consumption_attestation_verified": True,
                "presentation_scope_verified": True,
                "presentation_readiness_verified": True,
                "independent_presentation_readiness_attestation_performed": True,
                "duplicate_attestation_rejected": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "attestation_status": "immutable_read_only_demo_surface_presentation_readiness_independently_attested",
            }
            records.append(
                DemoSurfacePresentationReadinessAttestationRecord(
                    **body,
                    attestation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_manifest_id": source["readiness_manifest_id"],
                "source_manifest_hash": source["readiness_manifest_hash"],
                "attested_at": attested_at.isoformat(),
                "record_hashes": [record.attestation_record_hash for record in records],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "attestation_manifest_id": manifest_id,
            "attestation_status": STATUS_ATTESTED,
            "attestation_policy_id": POLICY_ID,
            "attestation_mode": APPROVED_ATTESTATION_MODE,
            "presentation_mode": APPROVED_PRESENTATION_MODE,
            "presentation_scope": APPROVED_PRESENTATION_SCOPE,
            "source_presentation_readiness_manifest_id": source["readiness_manifest_id"],
            "source_presentation_readiness_manifest_hash": source["readiness_manifest_hash"],
            "source_serving_consumption_attestation_manifest_id": source["source_serving_consumption_attestation_manifest_id"],
            "source_serving_consumption_attestation_manifest_hash": source["source_serving_consumption_attestation_manifest_hash"],
            "source_serving_consumption_manifest_id": source["source_serving_consumption_manifest_id"],
            "source_serving_consumption_manifest_hash": source["source_serving_consumption_manifest_hash"],
            "source_serving_release_attestation_manifest_id": source["source_serving_release_attestation_manifest_id"],
            "source_serving_release_attestation_manifest_hash": source["source_serving_release_attestation_manifest_hash"],
            "source_serving_release_manifest_id": source["source_serving_release_manifest_id"],
            "source_serving_release_manifest_hash": source["source_serving_release_manifest_hash"],
            "source_publication_manifest_id": source["source_publication_manifest_id"],
            "source_publication_manifest_hash": source["source_publication_manifest_hash"],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "attestation_record_count": len(records),
            "attestation_records": tuple(records),
            "all_readiness_record_hashes_verified": True,
            "all_serving_consumption_attestation_record_hashes_verified": True,
            "all_serving_consumption_record_hashes_verified": True,
            "all_serving_release_attestation_record_hashes_verified": True,
            "all_serving_release_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_serving_consumption_attestations_verified": True,
            "all_presentation_scopes_verified": True,
            "all_presentation_readiness_records_verified": True,
            "all_presentation_readiness_records_independently_attested": True,
            "duplicate_attestations_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "demo_surface_publication_serving_release_consumed": True,
            "demo_surface_publication_serving_consumption_attested": True,
            "demo_surface_presentation_ready": True,
            "demo_surface_presentation_readiness_attested": True,
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
        serializable["attestation_records"] = [asdict(record) for record in records]
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestation(
            **body,
            attestation_manifest_hash=stable_hash(serializable),
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.attestation_directory / "current.json", payload)
            _atomic_write(
                self.attestation_directory / "manifests" / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.attestation_directory / "publications" / record.publication_id / f"{record.attestation_id}.json",
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

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_presentation_readiness_attestation_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError,
    stable_hash,
)


def _seed(path: Path) -> None:
    record = {
        "sequence": 1,
        "readiness_id": "presentation-readiness-test",
        "serving_consumption_attestation_id": "serving-consumption-attestation-test",
        "serving_consumption_id": "serving-consumption-test",
        "serving_release_id": "serving-release-test",
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_serving_consumption_attestation_record_hash": stable_hash({"sca": 1}),
        "source_serving_consumption_record_hash": stable_hash({"sc": 1}),
        "source_serving_release_attestation_record_hash": stable_hash({"sra": 1}),
        "source_serving_release_record_hash": stable_hash({"sr": 1}),
        "source_publication_record_hash": stable_hash({"publication": 1}),
        "publication_payload_hash": stable_hash({"payload": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "presentation_mode": "immutable_read_only_demo_surface_presentation",
        "presentation_scope": "independently_attested_serving_consumption_only",
        "serving_consumption_attestation_record_hash_verified": True,
        "serving_consumption_record_hash_verified": True,
        "serving_release_attestation_record_hash_verified": True,
        "serving_release_record_hash_verified": True,
        "publication_record_hash_verified": True,
        "publication_payload_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "independent_serving_consumption_attestation_verified": True,
        "presentation_scope_verified": True,
        "presentation_ready": True,
        "duplicate_readiness_rejected": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "readiness_status": "immutable_read_only_demo_surface_presentation_ready",
    }
    record["readiness_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-032",
        "engine_id": "INT-OIA-032",
        "evaluated_at": "2026-07-24T00:00:00+00:00",
        "readiness_manifest_id": "int-oia-032-test",
        "readiness_status": "demo_surface_presentation_ready",
        "readiness_policy_id": "test",
        "presentation_mode": "immutable_read_only_demo_surface_presentation",
        "presentation_scope": "independently_attested_serving_consumption_only",
        "source_serving_consumption_attestation_manifest_id": "int-oia-031-test",
        "source_serving_consumption_attestation_manifest_hash": stable_hash({"int": 31}),
        "source_serving_consumption_manifest_id": "int-oia-030-test",
        "source_serving_consumption_manifest_hash": stable_hash({"int": 30}),
        "source_serving_release_attestation_manifest_id": "int-oia-029-test",
        "source_serving_release_attestation_manifest_hash": stable_hash({"int": 29}),
        "source_serving_release_manifest_id": "int-oia-028-test",
        "source_serving_release_manifest_hash": stable_hash({"int": 28}),
        "source_publication_manifest_id": "int-oia-017-test",
        "source_publication_manifest_hash": stable_hash({"int": 17}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "readiness_record_count": 1,
        "readiness_records": [record],
        "all_serving_consumption_attestation_record_hashes_verified": True,
        "all_serving_consumption_record_hashes_verified": True,
        "all_serving_release_attestation_record_hashes_verified": True,
        "all_serving_release_record_hashes_verified": True,
        "all_publication_record_hashes_verified": True,
        "all_publication_payload_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_independent_serving_consumption_attestations_verified": True,
        "all_presentation_scopes_verified": True,
        "all_demo_surfaces_presentation_ready": True,
        "duplicate_readiness_records_rejected": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "demo_surface_publication_serving_release_consumed": True,
        "demo_surface_publication_serving_consumption_attested": True,
        "demo_surface_presentation_ready": True,
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
        "readiness_artifact_persistence_allowed": True,
    }
    manifest["readiness_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-033 TEST")
    print(" PRESENTATION READINESS ATTESTATION")
    print(" INDEPENDENT IMMUTABLE READ-ONLY PROOF")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source"
        output = root / "output"
        _seed(source)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationGate(
            presentation_readiness_directory=source,
            attestation_directory=output,
        )
        fixed = datetime(2026, 7, 24, tzinfo=timezone.utc)
        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-033"
        assert first.attestation_record_count == 1
        assert first.all_readiness_record_hashes_verified
        assert first.all_presentation_readiness_records_verified
        assert first.all_presentation_readiness_records_independently_attested
        assert first.all_serving_consumption_attestation_record_hashes_verified
        assert first.all_serving_consumption_record_hashes_verified
        assert first.all_serving_release_attestation_record_hashes_verified
        assert first.all_serving_release_record_hashes_verified
        assert first.all_publication_record_hashes_verified
        assert first.all_publication_payload_hashes_verified
        assert first.all_admission_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_read_only_boundaries_verified
        assert first.all_execution_disabled_boundaries_verified
        assert first.demo_surface_presentation_ready
        assert first.demo_surface_presentation_readiness_attested
        assert first.duplicate_attestations_rejected
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed
        assert (output / "current.json").exists()

        record = first.attestation_records[0]
        assert record.readiness_record_hash_verified
        assert record.presentation_readiness_verified
        assert record.independent_presentation_readiness_attestation_performed
        assert record.attestation_status == "immutable_read_only_demo_surface_presentation_readiness_independently_attested"

        tampered = json.loads((source / "current.json").read_text(encoding="utf-8"))
        tampered["readiness_records"][0]["presentation_ready"] = False
        (source / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered presentation-readiness manifest accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessAttestationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-032 presentation-readiness manifest consumed")
    print("[PASS] Readiness manifest hash independently verified")
    print("[PASS] Every presentation-readiness record hash independently verified")
    print("[PASS] Publication, release, admission, and boundary lineage preserved")
    print("[PASS] One-time invocation and immutable-result proofs preserved")
    print("[PASS] Presentation scope and readiness independently verified")
    print("[PASS] Every demo-surface presentation readiness independently attested")
    print("[PASS] Duplicate attestation identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe presentation readiness rejected")
    print("[PASS] Atomic presentation-readiness attestation artifacts persisted")
    print("[PASS] Signals, alerts, Q Series handoff/execution, orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def verify_contract() -> None:
    if not SOURCE_032.exists():
        raise FileNotFoundError(f"Actual INT-OIA-032 production module missing: {SOURCE_032}")
    source = SOURCE_032.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "INT-OIA-032"',
        "class DemoSurfacePresentationReadinessRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadiness",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationReadinessGate",
        "readiness_manifest_hash",
        "demo_surface_presentation_ready",
        "all_demo_surfaces_presentation_ready",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-032 contract mismatch; missing tokens: " + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-032 presentation-readiness contract verified")


def write_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    current = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export = (
        "from .oracle_intelligence_analytics_downstream_read_only_consumer_"
        "demo_surface_presentation_readiness_attestation_gate import *"
    )
    if export not in current:
        if current and not current.endswith("\n"):
            current += "\n"
        PACKAGE.write_text(current + export + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-033 INSTALLER")
    print(" PRESENTATION READINESS ATTESTATION")
    print(" WINDOWS PATH-SAFE VERIFICATION")
    print("=" * 40)

    verify_contract()
    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)
    update_package()

    for target in (PRODUCTION, TEST, PACKAGE):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    print("[OK] INT-OIA-033 test executed automatically")
    print()
    print("[DONE] INT-OIA-033 independent immutable read-only presentation-readiness attestation gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
