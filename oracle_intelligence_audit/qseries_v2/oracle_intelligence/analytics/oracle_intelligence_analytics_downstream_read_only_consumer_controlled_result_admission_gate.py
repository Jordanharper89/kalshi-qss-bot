from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-013"
ENGINE_ID = "INT-OIA-013"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-controlled-result-admission.v1"
STATUS_ADMITTED = "downstream_read_only_consumer_controlled_result_admitted"

DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_invocation_result_attestation"
)
DEFAULT_ADMISSION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_result_admission"
)

APPROVED_RESULT_CLASS = "immutable_research_artifact"
APPROVED_RELEASE_MODE = "research_presentation_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
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
class ControlledResultAdmissionRecord:
    sequence: int
    result_admission_id: str
    consumer_id: str
    result_attestation_id: str
    invocation_execution_id: str
    invocation_nonce: str
    source_result_attestation_record_hash: str
    source_invocation_execution_record_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    result_type: str
    result_hash: str
    admitted_result_hash: str
    result_payload: Any
    result_class: str
    release_mode: str
    result_hash_verified: bool
    attestation_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    result_schema_safe: bool
    research_presentation_eligible: bool
    signals_eligible: bool
    alerts_eligible: bool
    qseries_handoff_eligible: bool
    qseries_execution_eligible: bool
    market_order_creation_eligible: bool
    funds_movement_eligible: bool
    portfolio_mutation_eligible: bool
    source_mutation_allowed: bool
    downstream_release_authorized: bool
    downstream_release_performed: bool
    admission_status: str
    result_admission_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionManifest:
    schema_version: str
    engine_id: str
    admitted_at: str
    result_admission_manifest_id: str
    result_admission_status: str
    result_admission_policy_id: str
    source_result_attestation_manifest_id: str
    source_result_attestation_manifest_hash: str
    source_invocation_execution_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    admission_record_count: int
    admission_records: tuple[ControlledResultAdmissionRecord, ...]
    all_attestation_hashes_verified: bool
    all_result_hashes_verified: bool
    all_attestation_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_result_schemas_safe: bool
    all_results_research_presentation_eligible: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    research_presentation_release_authorized: bool
    downstream_release_performed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    admission_artifact_persistence_allowed: bool
    result_admission_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionGate:
    def __init__(
        self,
        *,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
        admission_directory: Path | str = DEFAULT_ADMISSION_DIRECTORY,
    ) -> None:
        self.attestation_directory = Path(attestation_directory)
        self.admission_directory = Path(admission_directory)

    def _load_attestation(self) -> dict[str, Any]:
        path = self.attestation_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                f"INT-OIA-012 result-attestation artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                "INT-OIA-012 result-attestation artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("result_attestation_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                "INT-OIA-012 result-attestation manifest hash mismatch"
            )
        payload["result_attestation_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-012",
            "engine_id": "INT-OIA-012",
            "all_execution_hashes_verified": True,
            "all_result_hashes_verified": True,
            "all_execution_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "controlled_result_admission_authorized": True,
            "downstream_release_performed": False,
            "attestation_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                    f"unsafe or incomplete INT-OIA-012 field: {field}"
                )

        records = payload.get("attestation_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("attestation_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                "INT-OIA-012 result-attestation records invalid"
            )

        seen_attestations: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            record = dict(raw_record)
            record_hash = record.pop("result_attestation_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                    "INT-OIA-012 result-attestation record hash mismatch"
                )
            record["result_attestation_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                    "INT-OIA-012 result-attestation sequence mismatch"
                )

            attestation_id = record.get("result_attestation_id")
            if (
                not isinstance(attestation_id, str)
                or not attestation_id
                or attestation_id in seen_attestations
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                    "invalid or duplicate result attestation"
                )
            seen_attestations.add(attestation_id)

            if stable_hash(record.get("result_payload")) != record.get("result_hash"):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                    "INT-OIA-012 result payload hash mismatch"
                )
            if record.get("result_hash") != record.get("recomputed_result_hash"):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                    "INT-OIA-012 recomputed result hash mismatch"
                )

            required_record = {
                "result_hash_verified": True,
                "invocation_count_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "execution_lineage_verified": True,
                "database_connection_performed": False,
                "corpus_read_performed": False,
                "source_mutation_performed": False,
                "forecast_creation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_handoff_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "result_admission_authorized": True,
                "downstream_release_performed": False,
                "attestation_status": "result_verified_not_released",
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError(
                        f"unsafe INT-OIA-012 record field: {field}"
                    )

        payload["attestation_records"] = records
        return payload

    def admit(
        self,
        *,
        admitted_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionManifest:
        admitted_at = _aware(admitted_at, "admitted_at")
        source = self._load_attestation()

        records: list[ControlledResultAdmissionRecord] = []

        for sequence, attestation in enumerate(
            source["attestation_records"],
            start=1,
        ):
            admitted_result_hash = stable_hash(
                {
                    "result_hash": attestation["result_hash"],
                    "result_payload": attestation["result_payload"],
                    "result_class": APPROVED_RESULT_CLASS,
                    "release_mode": APPROVED_RELEASE_MODE,
                    "source_boundary_id": attestation["source_boundary_id"],
                    "source_boundary_hash": attestation["source_boundary_hash"],
                }
            )

            admission_id = stable_hash(
                {
                    "source_result_attestation_manifest_id": source[
                        "result_attestation_manifest_id"
                    ],
                    "result_attestation_id": attestation[
                        "result_attestation_id"
                    ],
                    "source_result_attestation_record_hash": attestation[
                        "result_attestation_record_hash"
                    ],
                    "admitted_result_hash": admitted_result_hash,
                    "admitted_at": admitted_at.isoformat(),
                }
            )

            body = {
                "sequence": sequence,
                "result_admission_id": admission_id,
                "consumer_id": attestation["consumer_id"],
                "result_attestation_id": attestation[
                    "result_attestation_id"
                ],
                "invocation_execution_id": attestation[
                    "invocation_execution_id"
                ],
                "invocation_nonce": attestation["invocation_nonce"],
                "source_result_attestation_record_hash": attestation[
                    "result_attestation_record_hash"
                ],
                "source_invocation_execution_record_hash": attestation[
                    "source_invocation_execution_record_hash"
                ],
                "source_boundary_id": attestation["source_boundary_id"],
                "source_boundary_hash": attestation["source_boundary_hash"],
                "result_type": attestation["result_type"],
                "result_hash": attestation["result_hash"],
                "admitted_result_hash": admitted_result_hash,
                "result_payload": attestation["result_payload"],
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
            records.append(
                ControlledResultAdmissionRecord(
                    **body,
                    result_admission_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_result_attestation_manifest_id": source[
                    "result_attestation_manifest_id"
                ],
                "source_result_attestation_manifest_hash": source[
                    "result_attestation_manifest_hash"
                ],
                "admitted_at": admitted_at.isoformat(),
                "result_admission_record_hashes": [
                    record.result_admission_record_hash
                    for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "admitted_at": admitted_at.isoformat(),
            "result_admission_manifest_id": manifest_id,
            "result_admission_status": STATUS_ADMITTED,
            "result_admission_policy_id": POLICY_ID,
            "source_result_attestation_manifest_id": source[
                "result_attestation_manifest_id"
            ],
            "source_result_attestation_manifest_hash": source[
                "result_attestation_manifest_hash"
            ],
            "source_invocation_execution_manifest_id": source[
                "source_invocation_execution_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "admission_record_count": len(records),
            "admission_records": tuple(records),
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

        serializable = dict(body)
        serializable["admission_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionManifest(
            **body,
            result_admission_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.admission_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.admission_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.admission_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.result_admission_id}.json",
                    asdict(record),
                )

        return manifest
