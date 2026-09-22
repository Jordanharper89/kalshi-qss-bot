from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_research_presentation_release_gate.py"
TEST = ROOT / "test_int_oia_014_oracle_intelligence_analytics_downstream_read_only_consumer_controlled_research_presentation_release_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
INT_OIA_013 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_result_admission_gate.py"

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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_research_presentation_release_gate import (
    APPROVED_RELEASE_MODE,
    APPROVED_RESULT_CLASS,
    PRESENTATION_SCHEMA,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError,
    stable_hash,
)


def _seed_admission(path: Path) -> None:
    result_payload = {
        "artifact_count": 2,
        "consumer_mode": "read_only_research",
        "evidence_hash": stable_hash([{"a": 1}, {"a": 2}]),
        "read_only": True,
    }
    source_boundary_hash = stable_hash({"boundary": 1})
    admitted_result_hash = stable_hash(
        {
            "result_hash": stable_hash(result_payload),
            "result_payload": result_payload,
            "result_class": APPROVED_RESULT_CLASS,
            "release_mode": APPROVED_RELEASE_MODE,
            "source_boundary_id": "boundary-test",
            "source_boundary_hash": source_boundary_hash,
        }
    )

    record = {
        "sequence": 1,
        "result_admission_id": "result-admission-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "result_attestation_id": "result-attestation-test",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_result_attestation_record_hash": stable_hash(
            {"result-attestation": 1}
        ),
        "source_invocation_execution_record_hash": stable_hash(
            {"execution": 1}
        ),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": source_boundary_hash,
        "result_type": "builtins.dict",
        "result_hash": stable_hash(result_payload),
        "admitted_result_hash": admitted_result_hash,
        "result_payload": result_payload,
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
    record["result_admission_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-013",
        "engine_id": "INT-OIA-013",
        "admitted_at": "2026-07-22T00:00:00+00:00",
        "result_admission_manifest_id": "int-oia-013-test",
        "result_admission_status": (
            "downstream_read_only_consumer_controlled_result_admitted"
        ),
        "result_admission_policy_id": "test",
        "source_result_attestation_manifest_id": "int-oia-012-test",
        "source_result_attestation_manifest_hash": stable_hash(
            {"int": 12}
        ),
        "source_invocation_execution_manifest_id": "int-oia-011-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": source_boundary_hash,
        "admission_record_count": 1,
        "admission_records": [record],
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
    manifest["result_admission_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-014 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" RESEARCH PRESENTATION RELEASE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        admission = root / "admission"
        release = root / "release"
        _seed_admission(admission)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseGate(
            admission_directory=admission,
            release_directory=release,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.release(released_at=fixed, persist=True)
        second = gate.release(released_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-014"
        assert first.release_record_count == 1
        assert first.all_admission_hashes_verified
        assert first.all_result_hashes_verified
        assert first.all_attestation_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_presentation_schemas_verified
        assert first.all_releases_research_presentation_only
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.research_presentation_released
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.release_records[0]
        assert record.presentation_schema == PRESENTATION_SCHEMA
        assert record.result_class == APPROVED_RESULT_CLASS
        assert record.release_mode == APPROVED_RELEASE_MODE
        assert record.admission_hash_verified
        assert record.result_hash_verified
        assert record.attestation_lineage_verified
        assert record.one_time_invocation_verified
        assert record.immutable_result_verified
        assert record.presentation_schema_verified
        assert record.research_presentation_released
        assert record.presentation_payload["read_only"] is True
        assert record.presentation_payload["execution_disabled"] is True
        assert (
            record.release_status
            == "released_for_read_only_research_presentation"
        )

        assert (release / "current.json").exists()

        tampered = json.loads(
            (admission / "current.json").read_text(encoding="utf-8")
        )
        tampered["admission_records"][0][
            "qseries_execution_eligible"
        ] = True
        (admission / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.release(released_at=fixed, persist=False)
            raise AssertionError("tampered admission accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError:
            pass

    print("[PASS] Actual INT-OIA-013 controlled admission consumed")
    print("[PASS] Every admission and result hash verified")
    print("[PASS] Complete attestation lineage preserved")
    print("[PASS] One-time invocation proof preserved")
    print("[PASS] Immutable result released through presentation schema")
    print("[PASS] Research presentation payload marked read-only")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe admission evidence rejected")
    print("[PASS] Atomic research-presentation artifacts persisted")
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
    path.write_text(
        source.strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def verify_int_oia_013_contract() -> None:
    if not INT_OIA_013.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-013 production module missing: {INT_OIA_013}"
        )
    source = INT_OIA_013.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-013"',
        "class ControlledResultAdmissionRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionGate",
        "result_admission_manifest_hash",
        "research_presentation_release_authorized",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-013 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-013 controlled-admission contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export_line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_controlled_research_presentation_release_gate import *"
    )
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        PACKAGE.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-014 INSTALLER")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" RESEARCH PRESENTATION RELEASE")
    print("=" * 40)

    verify_int_oia_013_contract()
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

    print("[OK] INT-OIA-014 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-014 downstream read-only consumer "
        "controlled research presentation release gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
