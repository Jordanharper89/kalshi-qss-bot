from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-016"
ENGINE_ID = "INT-OIA-016"
POLICY_ID = (
    "oracle.intelligence.analytics.downstream-read-only-consumer-"
    "controlled-demo-surface-release.v1"
)
STATUS_RELEASED = (
    "downstream_read_only_consumer_controlled_demo_surface_released"
)

DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_"
    "research_presentation_release_attestation"
)
DEFAULT_DEMO_RELEASE_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_demo_surface_release"
)

APPROVED_RESULT_CLASS = "immutable_research_artifact"
APPROVED_RELEASE_MODE = "research_presentation_only"
APPROVED_PRESENTATION_SCHEMA = "oracle_research_presentation.v1"
APPROVED_DEMO_SURFACE_SCHEMA = "oracle_research_demo_surface.v1"
APPROVED_DEMO_SURFACE_MODE = "read_only_research_demo"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
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
class ControlledDemoSurfaceReleaseRecord:
    sequence: int
    demo_surface_release_id: str
    consumer_id: str
    source_presentation_release_attestation_id: str
    source_presentation_release_attestation_record_hash: str
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
    demo_surface_payload_hash: str
    demo_surface_payload: Any
    presentation_schema: str
    demo_surface_schema: str
    result_class: str
    release_mode: str
    demo_surface_mode: str
    attestation_hash_verified: bool
    presentation_payload_hash_verified: bool
    admission_lineage_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    read_only_boundary_verified: bool
    execution_disabled_boundary_verified: bool
    demo_surface_schema_verified: bool
    research_presentation_released: bool
    demo_surface_released: bool
    signals_created: bool
    alerts_created: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    market_order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    source_mutation_performed: bool
    release_status: str
    demo_surface_release_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseManifest:
    schema_version: str
    engine_id: str
    released_at: str
    demo_surface_release_manifest_id: str
    demo_surface_release_status: str
    demo_surface_release_policy_id: str
    source_presentation_release_attestation_manifest_id: str
    source_presentation_release_attestation_manifest_hash: str
    source_research_presentation_release_manifest_id: str
    source_result_admission_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    release_record_count: int
    release_records: tuple[ControlledDemoSurfaceReleaseRecord, ...]
    all_attestation_hashes_verified: bool
    all_presentation_payload_hashes_verified: bool
    all_admission_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    all_read_only_boundaries_verified: bool
    all_execution_disabled_boundaries_verified: bool
    all_demo_surface_schemas_verified: bool
    all_releases_read_only_research_demo_only: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    research_presentation_released: bool
    demo_surface_released: bool
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
    demo_surface_artifact_persistence_allowed: bool
    demo_surface_release_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseGate:
    def __init__(
        self,
        *,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
        demo_release_directory: Path | str = DEFAULT_DEMO_RELEASE_DIRECTORY,
    ) -> None:
        self.attestation_directory = Path(attestation_directory)
        self.demo_release_directory = Path(demo_release_directory)

    def _load_attestation(self) -> dict[str, Any]:
        path = self.attestation_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                f"INT-OIA-015 attestation artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                "INT-OIA-015 attestation artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop(
            "presentation_release_attestation_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                "INT-OIA-015 attestation manifest hash mismatch"
            )
        payload["presentation_release_attestation_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-015",
            "engine_id": "INT-OIA-015",
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
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                    f"unsafe or incomplete INT-OIA-015 field: {field}"
                )

        records = payload.get("attestation_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("attestation_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                "INT-OIA-015 attestation records invalid"
            )

        seen_attestation_ids: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            if not isinstance(raw_record, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                    "INT-OIA-015 attestation record must be a mapping"
                )
            record = dict(raw_record)
            record_hash = record.pop(
                "presentation_release_attestation_record_hash",
                None,
            )
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                    "INT-OIA-015 attestation-record hash mismatch"
                )
            record["presentation_release_attestation_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                    "INT-OIA-015 attestation sequence mismatch"
                )

            attestation_id = record.get(
                "presentation_release_attestation_id"
            )
            if (
                not isinstance(attestation_id, str)
                or not attestation_id
                or attestation_id in seen_attestation_ids
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                    "invalid or duplicate presentation-release attestation id"
                )
            seen_attestation_ids.add(attestation_id)

            presentation_payload = record.get("presentation_payload")
            if not isinstance(presentation_payload, Mapping):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                    "attested presentation payload must be a mapping"
                )

            recomputed_payload_hash = stable_hash(presentation_payload)
            if recomputed_payload_hash != record.get(
                "presentation_payload_hash"
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                    "INT-OIA-015 presentation payload hash mismatch"
                )
            if recomputed_payload_hash != record.get(
                "recomputed_presentation_payload_hash"
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                    "INT-OIA-015 independently recomputed payload hash mismatch"
                )
            if presentation_payload.get("read_only") is not True:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                    "presentation payload is not read-only"
                )
            if presentation_payload.get("execution_disabled") is not True:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                    "presentation payload does not disable execution"
                )

            required_record = {
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
                "attestation_status": (
                    "presentation_release_attested_"
                    "demo_surface_not_released"
                ),
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError(
                        f"unsafe INT-OIA-015 attestation-record field: {field}"
                    )

        payload["attestation_records"] = records
        return payload

    def release(
        self,
        *,
        released_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseManifest:
        released_at = _aware(released_at, "released_at")
        source = self._load_attestation()

        records: list[ControlledDemoSurfaceReleaseRecord] = []

        for sequence, attestation in enumerate(
            source["attestation_records"],
            start=1,
        ):
            source_payload = attestation["presentation_payload"]
            demo_payload = {
                "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
                "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
                "presentation_schema": attestation["presentation_schema"],
                "consumer_id": attestation["consumer_id"],
                "result_class": attestation["result_class"],
                "release_mode": attestation["release_mode"],
                "source_boundary_id": attestation["source_boundary_id"],
                "source_boundary_hash": attestation["source_boundary_hash"],
                "result_hash": attestation["result_hash"],
                "admitted_result_hash": attestation[
                    "admitted_result_hash"
                ],
                "source_presentation_payload_hash": attestation[
                    "presentation_payload_hash"
                ],
                "research_result": source_payload["research_result"],
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
            demo_payload_hash = stable_hash(demo_payload)
            release_id = stable_hash(
                {
                    "source_presentation_release_attestation_manifest_id": source[
                        "presentation_release_attestation_manifest_id"
                    ],
                    "source_presentation_release_attestation_id": attestation[
                        "presentation_release_attestation_id"
                    ],
                    "source_presentation_release_attestation_record_hash": attestation[
                        "presentation_release_attestation_record_hash"
                    ],
                    "demo_surface_payload_hash": demo_payload_hash,
                    "released_at": released_at.isoformat(),
                }
            )

            body = {
                "sequence": sequence,
                "demo_surface_release_id": release_id,
                "consumer_id": attestation["consumer_id"],
                "source_presentation_release_attestation_id": attestation[
                    "presentation_release_attestation_id"
                ],
                "source_presentation_release_attestation_record_hash": attestation[
                    "presentation_release_attestation_record_hash"
                ],
                "research_presentation_release_id": attestation[
                    "research_presentation_release_id"
                ],
                "source_result_admission_id": attestation[
                    "source_result_admission_id"
                ],
                "result_attestation_id": attestation[
                    "result_attestation_id"
                ],
                "invocation_execution_id": attestation[
                    "invocation_execution_id"
                ],
                "invocation_nonce": attestation["invocation_nonce"],
                "source_boundary_id": attestation["source_boundary_id"],
                "source_boundary_hash": attestation[
                    "source_boundary_hash"
                ],
                "result_hash": attestation["result_hash"],
                "admitted_result_hash": attestation[
                    "admitted_result_hash"
                ],
                "source_presentation_payload_hash": attestation[
                    "presentation_payload_hash"
                ],
                "demo_surface_payload_hash": demo_payload_hash,
                "demo_surface_payload": demo_payload,
                "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
                "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
                "result_class": APPROVED_RESULT_CLASS,
                "release_mode": APPROVED_RELEASE_MODE,
                "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
                "attestation_hash_verified": True,
                "presentation_payload_hash_verified": True,
                "admission_lineage_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "read_only_boundary_verified": True,
                "execution_disabled_boundary_verified": True,
                "demo_surface_schema_verified": True,
                "research_presentation_released": True,
                "demo_surface_released": True,
                "signals_created": False,
                "alerts_created": False,
                "qseries_handoff_performed": False,
                "qseries_execution_performed": False,
                "market_order_creation_performed": False,
                "funds_movement_performed": False,
                "portfolio_mutation_performed": False,
                "source_mutation_performed": False,
                "release_status": (
                    "released_to_read_only_research_demo_surface"
                ),
            }
            records.append(
                ControlledDemoSurfaceReleaseRecord(
                    **body,
                    demo_surface_release_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_presentation_release_attestation_manifest_id": source[
                    "presentation_release_attestation_manifest_id"
                ],
                "source_presentation_release_attestation_manifest_hash": source[
                    "presentation_release_attestation_manifest_hash"
                ],
                "released_at": released_at.isoformat(),
                "release_record_hashes": [
                    record.demo_surface_release_record_hash
                    for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "released_at": released_at.isoformat(),
            "demo_surface_release_manifest_id": manifest_id,
            "demo_surface_release_status": STATUS_RELEASED,
            "demo_surface_release_policy_id": POLICY_ID,
            "source_presentation_release_attestation_manifest_id": source[
                "presentation_release_attestation_manifest_id"
            ],
            "source_presentation_release_attestation_manifest_hash": source[
                "presentation_release_attestation_manifest_hash"
            ],
            "source_research_presentation_release_manifest_id": source[
                "source_research_presentation_release_manifest_id"
            ],
            "source_result_admission_manifest_id": source[
                "source_result_admission_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "release_record_count": len(records),
            "release_records": tuple(records),
            "all_attestation_hashes_verified": True,
            "all_presentation_payload_hashes_verified": True,
            "all_admission_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "all_read_only_boundaries_verified": True,
            "all_execution_disabled_boundaries_verified": True,
            "all_demo_surface_schemas_verified": True,
            "all_releases_read_only_research_demo_only": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "research_presentation_released": True,
            "demo_surface_released": True,
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
            "demo_surface_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["release_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseManifest(
            **body,
            demo_surface_release_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.demo_release_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.demo_release_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.demo_release_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.demo_surface_release_id}.json",
                    asdict(record),
                )

        return manifest
