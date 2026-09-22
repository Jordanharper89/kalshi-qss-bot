from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-014"
ENGINE_ID = "INT-OIA-014"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-controlled-research-presentation-release.v1"
STATUS_RELEASED = "downstream_read_only_consumer_controlled_research_presentation_released"

DEFAULT_ADMISSION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_result_admission"
)
DEFAULT_RELEASE_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_research_presentation_release"
)

APPROVED_RESULT_CLASS = "immutable_research_artifact"
APPROVED_RELEASE_MODE = "research_presentation_only"
PRESENTATION_SCHEMA = "oracle_research_presentation.v1"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
            f"{field} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = (
        json.dumps(
            _canonical(payload),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
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
class ControlledResearchPresentationReleaseRecord:
    sequence: int
    research_presentation_release_id: str
    consumer_id: str
    source_result_admission_id: str
    source_result_admission_record_hash: str
    result_attestation_id: str
    invocation_execution_id: str
    invocation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    result_hash: str
    admitted_result_hash: str
    presentation_payload_hash: str
    presentation_payload: Any
    presentation_schema: str
    result_class: str
    release_mode: str
    admission_hash_verified: bool
    result_hash_verified: bool
    attestation_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    presentation_schema_verified: bool
    research_presentation_released: bool
    signals_created: bool
    alerts_created: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    market_order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    source_mutation_performed: bool
    release_status: str
    research_presentation_release_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseManifest:
    schema_version: str
    engine_id: str
    released_at: str
    research_presentation_release_manifest_id: str
    research_presentation_release_status: str
    research_presentation_release_policy_id: str
    source_result_admission_manifest_id: str
    source_result_admission_manifest_hash: str
    source_result_attestation_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    release_record_count: int
    release_records: tuple[ControlledResearchPresentationReleaseRecord, ...]
    all_admission_hashes_verified: bool
    all_result_hashes_verified: bool
    all_attestation_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_presentation_schemas_verified: bool
    all_releases_research_presentation_only: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    research_presentation_released: bool
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
    release_artifact_persistence_allowed: bool
    research_presentation_release_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseGate:
    def __init__(
        self,
        *,
        admission_directory: Path | str = DEFAULT_ADMISSION_DIRECTORY,
        release_directory: Path | str = DEFAULT_RELEASE_DIRECTORY,
    ) -> None:
        self.admission_directory = Path(admission_directory)
        self.release_directory = Path(release_directory)

    def _load_admission(self) -> dict[str, Any]:
        path = self.admission_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                f"INT-OIA-013 admission artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                "INT-OIA-013 admission artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("result_admission_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                "INT-OIA-013 admission manifest hash mismatch"
            )
        payload["result_admission_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-013",
            "engine_id": "INT-OIA-013",
            "all_attestation_hashes_verified": True,
            "all_result_hashes_verified": True,
            "all_attestation_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_result_schemas_safe": True,
            "all_results_research_presentation_eligible": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "research_presentation_release_authorized": True,
            "downstream_release_performed": False,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "admission_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                    f"unsafe or incomplete INT-OIA-013 field: {field}"
                )

        records = payload.get("admission_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("admission_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                "INT-OIA-013 admission records invalid"
            )

        seen_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            record = dict(raw_record)
            record_hash = record.pop("result_admission_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                    "INT-OIA-013 admission-record hash mismatch"
                )
            record["result_admission_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                    "INT-OIA-013 admission sequence mismatch"
                )

            admission_id = record.get("result_admission_id")
            if (
                not isinstance(admission_id, str)
                or not admission_id
                or admission_id in seen_ids
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                    "invalid or duplicate admission id"
                )
            seen_ids.add(admission_id)

            if stable_hash(record.get("result_payload")) != record.get("result_hash"):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                    "INT-OIA-013 admitted result payload hash mismatch"
                )

            expected_admitted_hash = stable_hash(
                {
                    "result_hash": record["result_hash"],
                    "result_payload": record["result_payload"],
                    "result_class": record["result_class"],
                    "release_mode": record["release_mode"],
                    "source_boundary_id": record["source_boundary_id"],
                    "source_boundary_hash": record["source_boundary_hash"],
                }
            )
            if expected_admitted_hash != record.get("admitted_result_hash"):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                    "INT-OIA-013 admitted-result hash mismatch"
                )

            required_record = {
                "result_class": APPROVED_RESULT_CLASS,
                "release_mode": APPROVED_RELEASE_MODE,
                "result_hash_verified": True,
                "attestation_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "result_schema_safe": True,
                "research_presentation_eligible": True,
                "signals_eligible": False,
                "alerts_eligible": False,
                "qseries_handoff_eligible": False,
                "qseries_execution_eligible": False,
                "market_order_creation_eligible": False,
                "funds_movement_eligible": False,
                "portfolio_mutation_eligible": False,
                "source_mutation_allowed": False,
                "downstream_release_authorized": True,
                "downstream_release_performed": False,
                "admission_status": "admitted_for_research_presentation_not_released",
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError(
                        f"unsafe INT-OIA-013 admission-record field: {field}"
                    )

        payload["admission_records"] = records
        return payload

    def release(
        self,
        *,
        released_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseManifest:
        released_at = _aware(released_at, "released_at")
        source = self._load_admission()

        records: list[ControlledResearchPresentationReleaseRecord] = []

        for sequence, admission in enumerate(
            source["admission_records"],
            start=1,
        ):
            presentation_payload = {
                "presentation_schema": PRESENTATION_SCHEMA,
                "consumer_id": admission["consumer_id"],
                "result_class": admission["result_class"],
                "release_mode": admission["release_mode"],
                "source_boundary_id": admission["source_boundary_id"],
                "source_boundary_hash": admission["source_boundary_hash"],
                "result_hash": admission["result_hash"],
                "admitted_result_hash": admission["admitted_result_hash"],
                "research_result": admission["result_payload"],
                "read_only": True,
                "execution_disabled": True,
            }
            presentation_payload_hash = stable_hash(presentation_payload)

            release_id = stable_hash(
                {
                    "source_result_admission_manifest_id": source[
                        "result_admission_manifest_id"
                    ],
                    "source_result_admission_id": admission[
                        "result_admission_id"
                    ],
                    "source_result_admission_record_hash": admission[
                        "result_admission_record_hash"
                    ],
                    "presentation_payload_hash": presentation_payload_hash,
                    "released_at": released_at.isoformat(),
                }
            )

            body = {
                "sequence": sequence,
                "research_presentation_release_id": release_id,
                "consumer_id": admission["consumer_id"],
                "source_result_admission_id": admission[
                    "result_admission_id"
                ],
                "source_result_admission_record_hash": admission[
                    "result_admission_record_hash"
                ],
                "result_attestation_id": admission[
                    "result_attestation_id"
                ],
                "invocation_execution_id": admission[
                    "invocation_execution_id"
                ],
                "invocation_nonce": admission["invocation_nonce"],
                "source_boundary_id": admission["source_boundary_id"],
                "source_boundary_hash": admission["source_boundary_hash"],
                "result_hash": admission["result_hash"],
                "admitted_result_hash": admission[
                    "admitted_result_hash"
                ],
                "presentation_payload_hash": presentation_payload_hash,
                "presentation_payload": presentation_payload,
                "presentation_schema": PRESENTATION_SCHEMA,
                "result_class": APPROVED_RESULT_CLASS,
                "release_mode": APPROVED_RELEASE_MODE,
                "admission_hash_verified": True,
                "result_hash_verified": True,
                "attestation_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "presentation_schema_verified": True,
                "research_presentation_released": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "release_status": "released_for_read_only_research_presentation",
            }
            records.append(
                ControlledResearchPresentationReleaseRecord(
                    **body,
                    research_presentation_release_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_result_admission_manifest_id": source[
                    "result_admission_manifest_id"
                ],
                "source_result_admission_manifest_hash": source[
                    "result_admission_manifest_hash"
                ],
                "released_at": released_at.isoformat(),
                "release_record_hashes": [
                    record.research_presentation_release_record_hash
                    for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "released_at": released_at.isoformat(),
            "research_presentation_release_manifest_id": manifest_id,
            "research_presentation_release_status": STATUS_RELEASED,
            "research_presentation_release_policy_id": POLICY_ID,
            "source_result_admission_manifest_id": source[
                "result_admission_manifest_id"
            ],
            "source_result_admission_manifest_hash": source[
                "result_admission_manifest_hash"
            ],
            "source_result_attestation_manifest_id": source[
                "source_result_attestation_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "release_record_count": len(records),
            "release_records": tuple(records),
            "all_admission_hashes_verified": True,
            "all_result_hashes_verified": True,
            "all_attestation_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_presentation_schemas_verified": True,
            "all_releases_research_presentation_only": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "research_presentation_released": True,
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
            "release_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["release_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseManifest(
            **body,
            research_presentation_release_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.release_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.release_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.release_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.research_presentation_release_id}.json",
                    asdict(record),
                )

        return manifest
