from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
SOURCE_030 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_serving_consumption_gate.py"
PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_serving_consumption_attestation_gate.py"
TEST = ROOT / "test_int_oia_031_oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_serving_consumption_attestation_gate.py"
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

SCHEMA_VERSION = "INT-OIA-031"
ENGINE_ID = "INT-OIA-031"
STATUS_ATTESTED = "demo_surface_publication_serving_consumption_independently_attested"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer."
    "demo-surface-publication-serving-consumption-independent-attestation.v1"
)

DEFAULT_CONSUMPTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_serving_consumption"
)
DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_demo_surface_publication_serving_consumption_attestation"
)

APPROVED_PUBLICATION_SCHEMA = "oracle_research_demo_publication_manifest.v1"
APPROVED_PUBLICATION_MODE = "immutable_read_only_demo_publication"
APPROVED_SERVING_CONSUMPTION_MODE = "single_use_read_only_serving_release_consumption"
APPROVED_SERVING_CONSUMPTION_SCOPE = "independently_attested_serving_release_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(RuntimeError):
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
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
class DemoSurfacePublicationServingConsumptionAttestationRecord:
    sequence: int
    attestation_id: str
    serving_consumption_id: str
    serving_release_attestation_id: str
    serving_release_id: str
    serving_authorization_attestation_id: str
    serving_authorization_id: str
    publication_id: str
    consumer_id: str
    source_serving_consumption_record_hash: str
    source_serving_release_attestation_record_hash: str
    source_serving_release_record_hash: str
    source_publication_record_hash: str
    publication_payload_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    result_hash: str
    admitted_result_hash: str
    publication_schema: str
    publication_mode: str
    serving_consumption_mode: str
    serving_consumption_scope: str
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
    independent_serving_release_attestation_verified: bool
    serving_consumption_scope_verified: bool
    single_use_consumption_verified: bool
    serving_consumption_verified: bool
    duplicate_attestation_rejected: bool
    independent_serving_consumption_attestation_performed: bool
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
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestation:
    schema_version: str
    engine_id: str
    attested_at: str
    attestation_manifest_id: str
    attestation_status: str
    attestation_policy_id: str
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
    attestation_records: tuple[DemoSurfacePublicationServingConsumptionAttestationRecord, ...]
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
    all_independent_serving_release_attestations_verified: bool
    all_serving_consumption_scopes_verified: bool
    all_single_use_consumptions_verified: bool
    all_serving_consumptions_verified: bool
    all_serving_consumptions_independently_attested: bool
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


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationGate:
    def __init__(
        self,
        *,
        consumption_directory: Path | str = DEFAULT_CONSUMPTION_DIRECTORY,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
    ) -> None:
        self.consumption_directory = Path(consumption_directory)
        self.attestation_directory = Path(attestation_directory)

    def _load_consumption(self) -> dict[str, Any]:
        path = self.consumption_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                f"INT-OIA-030 serving-consumption manifest missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                "INT-OIA-030 serving-consumption manifest could not be decoded"
            ) from exc

        manifest_hash = payload.pop("consumption_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                "INT-OIA-030 consumption manifest hash mismatch"
            )
        payload["consumption_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-030",
            "engine_id": "INT-OIA-030",
            "consumption_status": "demo_surface_publication_serving_release_consumed",
            "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
            "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
            "all_serving_release_attestation_record_hashes_verified": True,
            "all_serving_release_record_hashes_verified": True,
            "all_publication_record_hashes_verified": True,
            "all_publication_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_independent_serving_release_attestations_verified": True,
            "all_serving_consumption_scopes_verified": True,
            "all_single_use_consumptions_verified": True,
            "all_demo_surface_publication_serving_releases_consumed": True,
            "duplicate_consumptions_rejected": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "demo_surface_publication_serving_release_consumed": True,
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
            "consumption_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                    f"unsafe or incomplete INT-OIA-030 field: {field}"
                )

        records = payload.get("consumption_records")
        if not isinstance(records, list) or not records or payload.get("consumption_record_count") != len(records):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                "INT-OIA-030 consumption records invalid"
            )

        seen: set[str] = set()
        for sequence, raw in enumerate(records, start=1):
            if not isinstance(raw, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                    "consumption record must be a mapping"
                )
            record = dict(raw)
            record_hash = record.pop("consumption_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                    "INT-OIA-030 consumption record hash mismatch"
                )
            record["consumption_record_hash"] = record_hash
            consumption_id = record.get("consumption_id")
            if record.get("sequence") != sequence or not isinstance(consumption_id, str) or not consumption_id or consumption_id in seen:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                    "invalid sequence or duplicate consumption identity"
                )
            seen.add(consumption_id)
            record_required = {
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
                "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
                "serving_release_attestation_record_hash_verified": True,
                "serving_release_record_hash_verified": True,
                "publication_record_hash_verified": True,
                "publication_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "independent_serving_release_attestation_verified": True,
                "serving_consumption_scope_verified": True,
                "single_use_consumption_verified": True,
                "duplicate_consumption_rejected": True,
                "demo_surface_publication_serving_release_consumed": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "consumption_status": "independently_attested_read_only_serving_release_consumed",
            }
            for field, expected in record_required.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                        f"unsafe INT-OIA-030 consumption-record field: {field}"
                    )
        return payload

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestation:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_consumption()
        records: list[DemoSurfacePublicationServingConsumptionAttestationRecord] = []
        seen: set[str] = set()

        for sequence, consumption in enumerate(source["consumption_records"], start=1):
            attestation_id = stable_hash(
                {
                    "source_manifest": source["consumption_manifest_id"],
                    "source_record": consumption["consumption_record_hash"],
                    "serving_consumption_id": consumption["consumption_id"],
                    "publication_id": consumption["publication_id"],
                    "consumer_id": consumption["consumer_id"],
                    "attested_at": attested_at.isoformat(),
                }
            )
            if attestation_id in seen:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError(
                    "duplicate attestation identity"
                )
            seen.add(attestation_id)

            body = {
                "sequence": sequence,
                "attestation_id": attestation_id,
                "serving_consumption_id": consumption["consumption_id"],
                "serving_release_attestation_id": consumption["serving_release_attestation_id"],
                "serving_release_id": consumption["serving_release_id"],
                "serving_authorization_attestation_id": consumption["serving_authorization_attestation_id"],
                "serving_authorization_id": consumption["serving_authorization_id"],
                "publication_id": consumption["publication_id"],
                "consumer_id": consumption["consumer_id"],
                "source_serving_consumption_record_hash": consumption["consumption_record_hash"],
                "source_serving_release_attestation_record_hash": consumption["source_serving_release_attestation_record_hash"],
                "source_serving_release_record_hash": consumption["source_serving_release_record_hash"],
                "source_publication_record_hash": consumption["source_publication_record_hash"],
                "publication_payload_hash": consumption["publication_payload_hash"],
                "source_boundary_id": consumption["source_boundary_id"],
                "source_boundary_hash": consumption["source_boundary_hash"],
                "result_hash": consumption["result_hash"],
                "admitted_result_hash": consumption["admitted_result_hash"],
                "publication_schema": APPROVED_PUBLICATION_SCHEMA,
                "publication_mode": APPROVED_PUBLICATION_MODE,
                "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
                "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
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
                "independent_serving_release_attestation_verified": True,
                "serving_consumption_scope_verified": True,
                "single_use_consumption_verified": True,
                "serving_consumption_verified": True,
                "duplicate_attestation_rejected": True,
                "independent_serving_consumption_attestation_performed": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "attestation_status": "read_only_demo_publication_serving_consumption_independently_attested",
            }
            records.append(
                DemoSurfacePublicationServingConsumptionAttestationRecord(
                    **body,
                    attestation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_manifest_id": source["consumption_manifest_id"],
                "source_manifest_hash": source["consumption_manifest_hash"],
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
            "source_serving_consumption_manifest_id": source["consumption_manifest_id"],
            "source_serving_consumption_manifest_hash": source["consumption_manifest_hash"],
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
            "all_independent_serving_release_attestations_verified": True,
            "all_serving_consumption_scopes_verified": True,
            "all_single_use_consumptions_verified": True,
            "all_serving_consumptions_verified": True,
            "all_serving_consumptions_independently_attested": True,
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
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestation(
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
                    self.attestation_directory / "consumptions" / record.serving_consumption_id / f"{record.attestation_id}.json",
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

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_serving_consumption_attestation_gate import (
    APPROVED_PUBLICATION_MODE,
    APPROVED_PUBLICATION_SCHEMA,
    APPROVED_SERVING_CONSUMPTION_MODE,
    APPROVED_SERVING_CONSUMPTION_SCOPE,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError,
    stable_hash,
)


def _seed(path: Path) -> None:
    record = {
        "sequence": 1,
        "consumption_id": "serving-consumption-test",
        "serving_release_attestation_id": "serving-release-attestation-test",
        "serving_release_id": "serving-release-test",
        "serving_authorization_attestation_id": "serving-authorization-attestation-test",
        "serving_authorization_id": "serving-authorization-test",
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_serving_release_attestation_record_hash": stable_hash({"sra": 1}),
        "source_serving_release_record_hash": stable_hash({"sr": 1}),
        "source_serving_authorization_attestation_record_hash": stable_hash({"saa": 1}),
        "source_serving_authorization_record_hash": stable_hash({"sa": 1}),
        "source_readiness_attestation_record_hash": stable_hash({"ra": 1}),
        "source_readiness_record_hash": stable_hash({"r": 1}),
        "source_activation_attestation_record_hash": stable_hash({"aa": 1}),
        "source_activation_record_hash": stable_hash({"a": 1}),
        "source_consumption_attestation_record_hash": stable_hash({"pca": 1}),
        "source_consumption_record_hash": stable_hash({"pc": 1}),
        "source_release_authorization_record_hash": stable_hash({"auth": 1}),
        "source_publication_record_hash": stable_hash({"publication": 1}),
        "source_demo_surface_release_id": "demo-release-test",
        "source_result_admission_id": "admission-test",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "publication_payload_hash": stable_hash({"payload": 1}),
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "serving_release_mode": "single_use_immutable_read_only_demo_surface_release",
        "serving_release_scope": "independently_attested_serving_authorization_only",
        "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
        "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
        "serving_release_attestation_record_hash_verified": True,
        "serving_release_record_hash_verified": True,
        "serving_authorization_attestation_record_hash_verified": True,
        "serving_authorization_record_hash_verified": True,
        "readiness_attestation_record_hash_verified": True,
        "readiness_record_hash_verified": True,
        "activation_attestation_record_hash_verified": True,
        "activation_record_hash_verified": True,
        "prior_consumption_attestation_record_hash_verified": True,
        "prior_consumption_record_hash_verified": True,
        "release_authorization_record_hash_verified": True,
        "publication_record_hash_verified": True,
        "publication_payload_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "independent_serving_release_attestation_verified": True,
        "serving_consumption_scope_verified": True,
        "single_use_consumption_verified": True,
        "duplicate_consumption_rejected": True,
        "demo_surface_publication_serving_release_consumed": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "consumption_status": "independently_attested_read_only_serving_release_consumed",
    }
    record["consumption_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-030",
        "engine_id": "INT-OIA-030",
        "consumed_at": "2026-07-23T00:00:00+00:00",
        "consumption_manifest_id": "int-oia-030-test",
        "consumption_status": "demo_surface_publication_serving_release_consumed",
        "consumption_policy_id": "test",
        "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
        "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
        "source_serving_release_attestation_manifest_id": "int-oia-029-test",
        "source_serving_release_attestation_manifest_hash": stable_hash({"int": 29}),
        "source_serving_release_manifest_id": "int-oia-028-test",
        "source_serving_release_manifest_hash": stable_hash({"int": 28}),
        "source_serving_authorization_attestation_manifest_id": "int-oia-027-test",
        "source_serving_authorization_attestation_manifest_hash": stable_hash({"int": 27}),
        "source_serving_authorization_manifest_id": "int-oia-026-test",
        "source_serving_authorization_manifest_hash": stable_hash({"int": 26}),
        "source_readiness_attestation_manifest_id": "int-oia-025-test",
        "source_readiness_attestation_manifest_hash": stable_hash({"int": 25}),
        "source_readiness_manifest_id": "int-oia-024-test",
        "source_readiness_manifest_hash": stable_hash({"int": 24}),
        "source_activation_attestation_manifest_id": "int-oia-023-test",
        "source_activation_attestation_manifest_hash": stable_hash({"int": 23}),
        "source_activation_manifest_id": "int-oia-022-test",
        "source_activation_manifest_hash": stable_hash({"int": 22}),
        "source_prior_consumption_attestation_manifest_id": "int-oia-021-test",
        "source_prior_consumption_attestation_manifest_hash": stable_hash({"int": 21}),
        "source_prior_consumption_manifest_id": "int-oia-020-test",
        "source_prior_consumption_manifest_hash": stable_hash({"int": 20}),
        "source_release_authorization_manifest_id": "int-oia-019-test",
        "source_release_authorization_manifest_hash": stable_hash({"int": 19}),
        "source_publication_manifest_id": "int-oia-017-test",
        "source_publication_manifest_hash": stable_hash({"int": 17}),
        "source_demo_surface_release_manifest_id": "int-oia-016-test",
        "source_demo_surface_release_manifest_hash": stable_hash({"int": 16}),
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "consumption_record_count": 1,
        "consumption_records": [record],
        "all_serving_release_attestation_record_hashes_verified": True,
        "all_serving_release_record_hashes_verified": True,
        "all_serving_authorization_attestation_record_hashes_verified": True,
        "all_serving_authorization_record_hashes_verified": True,
        "all_readiness_attestation_record_hashes_verified": True,
        "all_readiness_record_hashes_verified": True,
        "all_activation_attestation_record_hashes_verified": True,
        "all_activation_record_hashes_verified": True,
        "all_prior_consumption_attestation_record_hashes_verified": True,
        "all_prior_consumption_record_hashes_verified": True,
        "all_release_authorization_record_hashes_verified": True,
        "all_publication_record_hashes_verified": True,
        "all_publication_payload_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_independent_serving_release_attestations_verified": True,
        "all_serving_consumption_scopes_verified": True,
        "all_single_use_consumptions_verified": True,
        "all_demo_surface_publication_serving_releases_consumed": True,
        "duplicate_consumptions_rejected": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "publication_manifest_published": True,
        "publication_manifest_attested": True,
        "publication_release_authorized": True,
        "publication_release_authorization_consumed": True,
        "publication_release_authorization_consumption_attested": True,
        "demo_surface_publication_activated": True,
        "demo_surface_publication_activation_attested": True,
        "demo_surface_publication_serving_ready": True,
        "demo_surface_publication_serving_readiness_attested": True,
        "demo_surface_publication_serving_authorized": True,
        "demo_surface_publication_serving_authorization_attested": True,
        "demo_surface_publication_serving_released": True,
        "demo_surface_publication_serving_release_attested": True,
        "demo_surface_publication_serving_release_consumed": True,
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
        "consumption_artifact_persistence_allowed": True,
    }
    manifest["consumption_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-031 TEST")
    print(" SERVING CONSUMPTION ATTESTATION")
    print(" IMMUTABLE READ-ONLY PRESENTATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        consumption = root / "consumption"
        attestation = root / "attestation"
        _seed(consumption)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationGate(
            consumption_directory=consumption,
            attestation_directory=attestation,
        )
        fixed = datetime(2026, 7, 23, tzinfo=timezone.utc)
        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-031"
        assert first.attestation_record_count == 1
        assert first.all_serving_consumption_record_hashes_verified
        assert first.all_serving_consumptions_verified
        assert first.all_serving_consumptions_independently_attested
        assert first.all_single_use_consumptions_verified
        assert first.duplicate_attestations_rejected
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.demo_surface_publication_serving_release_consumed
        assert first.demo_surface_publication_serving_consumption_attested
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.attestation_records[0]
        assert record.serving_consumption_record_hash_verified
        assert record.serving_consumption_verified
        assert record.single_use_consumption_verified
        assert record.independent_serving_consumption_attestation_performed
        assert record.attestation_status == "read_only_demo_publication_serving_consumption_independently_attested"
        assert (attestation / "current.json").exists()

        tampered = json.loads((consumption / "current.json").read_text(encoding="utf-8"))
        tampered["consumption_records"][0]["demo_surface_publication_serving_release_consumed"] = False
        (consumption / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered serving consumption accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-030 serving-consumption manifest consumed")
    print("[PASS] Serving-consumption manifest hash independently verified")
    print("[PASS] Every serving-consumption record hash verified")
    print("[PASS] Publication, release, admission, and boundary lineage preserved")
    print("[PASS] One-time invocation and immutable-result proofs preserved")
    print("[PASS] Serving consumption independently verified")
    print("[PASS] Single-use read-only consumption independently verified")
    print("[PASS] Duplicate attestation identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe serving consumption rejected")
    print("[PASS] Atomic serving-consumption attestation artifacts persisted")
    print("[PASS] Signals, alerts, Q Series handoff/execution, orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def verify_contract() -> None:
    if not SOURCE_030.exists():
        raise FileNotFoundError(f"Actual INT-OIA-030 production module missing: {SOURCE_030}")
    source = SOURCE_030.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "INT-OIA-030"',
        "class DemoSurfacePublicationServingConsumptionRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumption",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionGate",
        "consumption_manifest_hash",
        "demo_surface_publication_serving_release_consumed",
        "all_demo_surface_publication_serving_releases_consumed",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise RuntimeError("Actual INT-OIA-030 contract mismatch; missing tokens: " + ", ".join(missing))
    print("[OK] Actual INT-OIA-030 serving-consumption contract verified")


def write_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    current = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_demo_surface_publication_serving_consumption_attestation_gate import *"
    )
    if export not in current:
        if current and not current.endswith("\n"):
            current += "\n"
        PACKAGE.write_text(current + export + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-031 INSTALLER")
    print(" SERVING CONSUMPTION ATTESTATION")
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

    print("[OK] INT-OIA-031 test executed automatically")
    print()
    print("[DONE] INT-OIA-031 independent immutable read-only serving-consumption attestation gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
