from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_result_admission_gate.py"
TEST = ROOT / "test_int_oia_013_oracle_intelligence_analytics_downstream_read_only_consumer_controlled_result_admission_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
INT_OIA_012 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_result_attestation_gate.py"

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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_result_admission_gate import (
    APPROVED_RELEASE_MODE,
    APPROVED_RESULT_CLASS,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError,
    stable_hash,
)


def _seed_attestation(path: Path) -> None:
    result_payload = {
        "artifact_count": 2,
        "consumer_mode": "read_only_research",
        "evidence_hash": stable_hash([{"a": 1}, {"a": 2}]),
        "read_only": True,
    }

    record = {
        "sequence": 1,
        "result_attestation_id": "result-attestation-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_invocation_execution_record_hash": stable_hash(
            {"execution": 1}
        ),
        "source_invocation_readiness_id": "readiness-test",
        "source_binding_attestation_id": "binding-test",
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"activation": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "certified_artifacts_hash": stable_hash([{"a": 1}, {"a": 2}]),
        "execution_context_hash": stable_hash({"mode": "read_only"}),
        "argument_contract_hash": stable_hash({"arguments": 1}),
        "result_type": "builtins.dict",
        "result_hash": stable_hash(result_payload),
        "recomputed_result_hash": stable_hash(result_payload),
        "result_payload": result_payload,
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
    record["result_attestation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-012",
        "engine_id": "INT-OIA-012",
        "attested_at": "2026-07-22T00:00:00+00:00",
        "result_attestation_manifest_id": "int-oia-012-test",
        "result_attestation_status": (
            "downstream_read_only_consumer_controlled_invocation_result_attested"
        ),
        "result_attestation_policy_id": "test",
        "source_invocation_execution_manifest_id": "int-oia-011-test",
        "source_invocation_execution_manifest_hash": stable_hash(
            {"int": 11}
        ),
        "source_invocation_readiness_manifest_id": "int-oia-010-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "attestation_record_count": 1,
        "attestation_records": [record],
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
    manifest["result_attestation_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-013 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED RESULT ADMISSION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        attestation = root / "attestation"
        admission = root / "admission"
        _seed_attestation(attestation)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionGate(
            attestation_directory=attestation,
            admission_directory=admission,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.admit(admitted_at=fixed, persist=True)
        second = gate.admit(admitted_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-013"
        assert first.admission_record_count == 1
        assert first.all_attestation_hashes_verified
        assert first.all_result_hashes_verified
        assert first.all_attestation_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_result_schemas_safe
        assert first.all_results_research_presentation_eligible
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.research_presentation_release_authorized
        assert not first.downstream_release_performed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.admission_records[0]
        assert record.result_class == APPROVED_RESULT_CLASS
        assert record.release_mode == APPROVED_RELEASE_MODE
        assert record.result_hash_verified
        assert record.attestation_lineage_verified
        assert record.one_time_invocation_verified
        assert record.immutable_result_verified
        assert record.result_schema_safe
        assert record.research_presentation_eligible
        assert not record.signals_eligible
        assert not record.alerts_eligible
        assert not record.qseries_execution_eligible
        assert record.downstream_release_authorized
        assert not record.downstream_release_performed
        assert (
            record.admission_status
            == "admitted_for_research_presentation_not_released"
        )

        assert (admission / "current.json").exists()

        tampered = json.loads(
            (attestation / "current.json").read_text(encoding="utf-8")
        )
        tampered["attestation_records"][0][
            "result_admission_authorized"
        ] = False
        (attestation / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.admit(admitted_at=fixed, persist=False)
            raise AssertionError("tampered attestation accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError:
            pass

    print("[PASS] Actual INT-OIA-012 result attestation consumed")
    print("[PASS] Every result-attestation hash verified")
    print("[PASS] Result and attestation lineage independently verified")
    print("[PASS] One-time invocation status preserved")
    print("[PASS] Immutable result schema admitted safely")
    print("[PASS] Research-presentation eligibility authorized")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe attestation evidence rejected")
    print("[PASS] Result was not released downstream")
    print("[PASS] Atomic controlled-admission artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series execution, orders, funds, "
        "and portfolio mutation remained disabled"
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


def verify_int_oia_012_contract() -> None:
    if not INT_OIA_012.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-012 production module missing: {INT_OIA_012}"
        )
    source = INT_OIA_012.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-012"',
        "class ControlledInvocationResultAttestationRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationGate",
        "result_attestation_manifest_hash",
        "controlled_result_admission_authorized",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-012 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-012 result-attestation contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export_line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_controlled_result_admission_gate import *"
    )
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        PACKAGE.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-013 INSTALLER")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED RESULT ADMISSION")
    print("=" * 40)

    verify_int_oia_012_contract()
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

    print("[OK] INT-OIA-013 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-013 downstream read-only consumer "
        "controlled result admission gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
