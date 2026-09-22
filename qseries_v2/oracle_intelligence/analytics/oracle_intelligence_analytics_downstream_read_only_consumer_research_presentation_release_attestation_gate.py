from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-015"
ENGINE_ID = "INT-OIA-015"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-research-presentation-release-attestation.v1"
STATUS_ATTESTED = "downstream_read_only_consumer_research_presentation_release_attested"

DEFAULT_RELEASE_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_research_presentation_release"
)
DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_research_presentation_release_attestation"
)

APPROVED_RESULT_CLASS = "immutable_research_artifact"
APPROVED_RELEASE_MODE = "research_presentation_only"
APPROVED_PRESENTATION_SCHEMA = "oracle_research_presentation.v1"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
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
class ResearchPresentationReleaseAttestationRecord:
    sequence: int
    presentation_release_attestation_id: str
    consumer_id: str
    research_presentation_release_id: str
    source_research_presentation_release_record_hash: str
    source_result_admission_id: str
    result_attestation_id: str
    invocation_execution_id: str
    invocation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    result_hash: str
    admitted_result_hash: str
    presentation_payload_hash: str
    recomputed_presentation_payload_hash: str
    presentation_payload: Any
    presentation_schema: str
    result_class: str
    release_mode: str
    release_hash_verified: bool
    presentation_payload_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    demo_surface_eligible: bool
    demo_surface_release_performed: bool
    signals_created: bool
    alerts_created: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    market_order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    source_mutation_performed: bool
    attestation_status: str
    presentation_release_attestation_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationManifest:
    schema_version: str
    engine_id: str
    attested_at: str
    presentation_release_attestation_manifest_id: str
    presentation_release_attestation_status: str
    presentation_release_attestation_policy_id: str
    source_research_presentation_release_manifest_id: str
    source_research_presentation_release_manifest_hash: str
    source_result_admission_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    attestation_record_count: int
    attestation_records: tuple[ResearchPresentationReleaseAttestationRecord, ...]
    all_release_hashes_verified: bool
    all_presentation_payload_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_presentations_demo_surface_eligible: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    research_presentation_released: bool
    demo_surface_release_authorized: bool
    demo_surface_release_performed: bool
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
    presentation_release_attestation_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationGate:
    def __init__(
        self,
        *,
        release_directory: Path | str = DEFAULT_RELEASE_DIRECTORY,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
    ) -> None:
        self.release_directory = Path(release_directory)
        self.attestation_directory = Path(attestation_directory)

    def _load_release(self) -> dict[str, Any]:
        path = self.release_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                f"INT-OIA-014 release artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                "INT-OIA-014 release artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop(
            "research_presentation_release_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                "INT-OIA-014 release manifest hash mismatch"
            )
        payload["research_presentation_release_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-014",
            "engine_id": "INT-OIA-014",
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
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                    f"unsafe or incomplete INT-OIA-014 field: {field}"
                )

        records = payload.get("release_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("release_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                "INT-OIA-014 release records invalid"
            )

        seen_release_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            record = dict(raw_record)
            record_hash = record.pop(
                "research_presentation_release_record_hash",
                None,
            )
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                    "INT-OIA-014 release-record hash mismatch"
                )
            record["research_presentation_release_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                    "INT-OIA-014 release sequence mismatch"
                )

            release_id = record.get("research_presentation_release_id")
            if (
                not isinstance(release_id, str)
                or not release_id
                or release_id in seen_release_ids
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                    "invalid or duplicate research-presentation release id"
                )
            seen_release_ids.add(release_id)

            payload_hash = stable_hash(record.get("presentation_payload"))
            if payload_hash != record.get("presentation_payload_hash"):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                    "INT-OIA-014 presentation payload hash mismatch"
                )

            presentation_payload = record.get("presentation_payload")
            if not isinstance(presentation_payload, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                    "presentation payload must be a mapping"
                )
            if presentation_payload.get("read_only") is not True:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                    "presentation payload is not marked read-only"
                )
            if presentation_payload.get("execution_disabled") is not True:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                    "presentation payload does not disable execution"
                )

            required_record = {
                "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
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
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError(
                        f"unsafe INT-OIA-014 release-record field: {field}"
                    )

        payload["release_records"] = records
        return payload

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationManifest:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_release()

        records: list[ResearchPresentationReleaseAttestationRecord] = []

        for sequence, release in enumerate(source["release_records"], start=1):
            recomputed_payload_hash = stable_hash(
                release["presentation_payload"]
            )
            attestation_id = stable_hash(
                {
                    "source_research_presentation_release_manifest_id": source[
                        "research_presentation_release_manifest_id"
                    ],
                    "research_presentation_release_id": release[
                        "research_presentation_release_id"
                    ],
                    "source_research_presentation_release_record_hash": release[
                        "research_presentation_release_record_hash"
                    ],
                    "recomputed_presentation_payload_hash": recomputed_payload_hash,
                    "attested_at": attested_at.isoformat(),
                }
            )

            body = {
                "sequence": sequence,
                "presentation_release_attestation_id": attestation_id,
                "consumer_id": release["consumer_id"],
                "research_presentation_release_id": release[
                    "research_presentation_release_id"
                ],
                "source_research_presentation_release_record_hash": release[
                    "research_presentation_release_record_hash"
                ],
                "source_result_admission_id": release[
                    "source_result_admission_id"
                ],
                "result_attestation_id": release["result_attestation_id"],
                "invocation_execution_id": release[
                    "invocation_execution_id"
                ],
                "invocation_nonce": release["invocation_nonce"],
                "source_boundary_id": release["source_boundary_id"],
                "source_boundary_hash": release["source_boundary_hash"],
                "result_hash": release["result_hash"],
                "admitted_result_hash": release["admitted_result_hash"],
                "presentation_payload_hash": release[
                    "presentation_payload_hash"
                ],
                "recomputed_presentation_payload_hash": recomputed_payload_hash,
                "presentation_payload": release["presentation_payload"],
                "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
                "result_class": APPROVED_RESULT_CLASS,
                "release_mode": APPROVED_RELEASE_MODE,
                "release_hash_verified": True,
                "presentation_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "demo_surface_eligible": True,
                "demo_surface_release_performed": False,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "attestation_status": "presentation_release_attested_demo_surface_not_released",
            }
            records.append(
                ResearchPresentationReleaseAttestationRecord(
                    **body,
                    presentation_release_attestation_record_hash=stable_hash(
                        body
                    ),
                )
            )

        manifest_id = stable_hash(
            {
                "source_research_presentation_release_manifest_id": source[
                    "research_presentation_release_manifest_id"
                ],
                "source_research_presentation_release_manifest_hash": source[
                    "research_presentation_release_manifest_hash"
                ],
                "attested_at": attested_at.isoformat(),
                "attestation_record_hashes": [
                    record.presentation_release_attestation_record_hash
                    for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "presentation_release_attestation_manifest_id": manifest_id,
            "presentation_release_attestation_status": STATUS_ATTESTED,
            "presentation_release_attestation_policy_id": POLICY_ID,
            "source_research_presentation_release_manifest_id": source[
                "research_presentation_release_manifest_id"
            ],
            "source_research_presentation_release_manifest_hash": source[
                "research_presentation_release_manifest_hash"
            ],
            "source_result_admission_manifest_id": source[
                "source_result_admission_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "attestation_record_count": len(records),
            "attestation_records": tuple(records),
            "all_release_hashes_verified": True,
            "all_presentation_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_presentations_demo_surface_eligible": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "research_presentation_released": True,
            "demo_surface_release_authorized": True,
            "demo_surface_release_performed": False,
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

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationManifest(
            **body,
            presentation_release_attestation_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.attestation_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.attestation_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.attestation_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.presentation_release_attestation_id}.json",
                    asdict(record),
                )

        return manifest
