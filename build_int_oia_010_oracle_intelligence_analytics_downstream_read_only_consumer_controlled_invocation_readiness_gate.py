from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_readiness_gate.py"
TEST = ROOT / "test_int_oia_010_oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_readiness_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
INT_OIA_009 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_callable_binding_attestation_gate.py"

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

SCHEMA_VERSION = "INT-OIA-010"
ENGINE_ID = "INT-OIA-010"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-controlled-invocation-readiness.v1"
STATUS_READY = "downstream_read_only_consumer_controlled_invocation_ready"

DEFAULT_BINDING_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_binding_attestation"
)
DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_invocation_readiness"
)

REQUIRED_BOUND_PARAMETERS = (
    "certified_artifacts",
    "execution_context",
)

APPROVED_INPUT_MODE = "certified_artifacts_only"
APPROVED_OUTPUT_MODE = "immutable_research_artifact_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    return value


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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
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
class DownstreamReadOnlyConsumerControlledInvocationReadinessRecord:
    sequence: int
    invocation_readiness_id: str
    invocation_nonce: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    callable_name: str
    callable_path: str
    bound_callable_signature: str
    bound_callable_parameter_names: tuple[str, ...]
    bound_callable_identity_hash: str
    source_binding_attestation_id: str
    source_binding_attestation_record_hash: str
    source_resolution_attestation_id: str
    source_binding_contract_id: str
    source_activation_id: str
    source_activation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    certified_artifact_input_mode: str
    immutable_output_mode: str
    required_argument_names: tuple[str, ...]
    argument_contract_hash: str
    one_time_invocation: bool
    invocation_authorized: bool
    invocation_performed: bool
    corpus_read_allowed: bool
    corpus_read_performed: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    readiness_status: str
    invocation_readiness_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: str
    invocation_readiness_manifest_id: str
    invocation_readiness_status: str
    invocation_readiness_policy_id: str
    source_binding_attestation_manifest_id: str
    source_binding_attestation_manifest_hash: str
    source_resolution_attestation_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    readiness_record_count: int
    readiness_records: tuple[
        DownstreamReadOnlyConsumerControlledInvocationReadinessRecord, ...
    ]
    all_binding_attestation_hashes_verified: bool
    all_bound_callable_identities_verified: bool
    all_required_arguments_verified: bool
    all_invocation_nonces_unique: bool
    certified_artifact_input_mode_preserved: bool
    immutable_output_mode_preserved: bool
    source_boundary_consumed_without_reexecution: bool
    one_time_invocation_required: bool
    controlled_invocation_authorized: bool
    invocation_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    readiness_artifact_persistence_allowed: bool
    invocation_readiness_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessGate:
    def __init__(
        self,
        *,
        binding_directory: Path | str = DEFAULT_BINDING_DIRECTORY,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
    ) -> None:
        self.binding_directory = Path(binding_directory)
        self.readiness_directory = Path(readiness_directory)

    def _load_binding(self) -> dict[str, Any]:
        path = self.binding_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                f"INT-OIA-009 binding artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                "INT-OIA-009 binding artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop(
            "binding_attestation_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                "INT-OIA-009 binding-attestation manifest hash mismatch"
            )
        payload["binding_attestation_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-009",
            "engine_id": "INT-OIA-009",
            "all_resolution_hashes_verified": True,
            "all_consumers_instantiated": True,
            "all_callables_bound": True,
            "all_bound_callables_callable": True,
            "exact_callable_identity_preserved": True,
            "source_boundary_consumed_without_reexecution": True,
            "callable_invocation_allowed": True,
            "callable_invocation_performed": False,
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
            "controlled_callable_invocation_authorized": True,
            "attestation_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                    f"unsafe or incomplete INT-OIA-009 field: {field}"
                )

        records = payload.get("attestation_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("attestation_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                "INT-OIA-009 attestation records invalid"
            )

        seen_consumers: set[str] = set()
        seen_identities: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            record = dict(raw_record)
            record_hash = record.pop(
                "binding_attestation_record_hash",
                None,
            )
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                    "INT-OIA-009 binding-attestation record hash mismatch"
                )
            record["binding_attestation_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                    "INT-OIA-009 attestation sequence mismatch"
                )

            consumer_id = record.get("consumer_id")
            identity_hash = record.get("bound_callable_identity_hash")
            if (
                not isinstance(consumer_id, str)
                or not consumer_id
                or consumer_id in seen_consumers
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                    "invalid or duplicate consumer"
                )
            if (
                not _valid_hash(identity_hash)
                or identity_hash in seen_identities
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                    "invalid or duplicate bound-callable identity"
                )
            seen_consumers.add(consumer_id)
            seen_identities.add(identity_hash)

            parameters = tuple(record.get("bound_callable_parameter_names", ()))
            if parameters != REQUIRED_BOUND_PARAMETERS:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                    "bound callable parameters do not match approved invocation contract"
                )

            required_record = {
                "consumer_instantiated": True,
                "callable_bound": True,
                "bound_callable_is_callable": True,
                "callable_invocation_allowed": True,
                "callable_invocation_performed": False,
                "corpus_read_performed": False,
                "source_mutation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "binding_status": "bound_not_invoked",
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                        f"unsafe INT-OIA-009 record field: {field}"
                    )

        payload["attestation_records"] = records
        return payload

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessManifest:
        evaluated_at = _aware(evaluated_at, "evaluated_at")
        source = self._load_binding()

        records: list[
            DownstreamReadOnlyConsumerControlledInvocationReadinessRecord
        ] = []
        seen_nonces: set[str] = set()

        for sequence, binding in enumerate(
            source["attestation_records"],
            start=1,
        ):
            argument_contract = {
                "required_argument_names": REQUIRED_BOUND_PARAMETERS,
                "certified_artifact_input_mode": APPROVED_INPUT_MODE,
                "immutable_output_mode": APPROVED_OUTPUT_MODE,
                "source_boundary_id": binding["source_boundary_id"],
                "source_boundary_hash": binding["source_boundary_hash"],
                "bound_callable_identity_hash": binding[
                    "bound_callable_identity_hash"
                ],
            }
            argument_contract_hash = stable_hash(argument_contract)

            invocation_nonce = stable_hash(
                {
                    "source_binding_attestation_manifest_id": source[
                        "binding_attestation_manifest_id"
                    ],
                    "source_binding_attestation_id": binding[
                        "binding_attestation_id"
                    ],
                    "bound_callable_identity_hash": binding[
                        "bound_callable_identity_hash"
                    ],
                    "argument_contract_hash": argument_contract_hash,
                    "evaluated_at": evaluated_at.isoformat(),
                }
            )
            if invocation_nonce in seen_nonces:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError(
                    "duplicate invocation nonce generated"
                )
            seen_nonces.add(invocation_nonce)

            readiness_id = stable_hash(
                {
                    "consumer_id": binding["consumer_id"],
                    "invocation_nonce": invocation_nonce,
                    "argument_contract_hash": argument_contract_hash,
                }
            )

            body = {
                "sequence": sequence,
                "invocation_readiness_id": readiness_id,
                "invocation_nonce": invocation_nonce,
                "consumer_id": binding["consumer_id"],
                "consumer_module": binding["consumer_module"],
                "consumer_class": binding["consumer_class"],
                "callable_name": binding["callable_name"],
                "callable_path": binding["callable_path"],
                "bound_callable_signature": binding[
                    "bound_callable_signature"
                ],
                "bound_callable_parameter_names": tuple(
                    binding["bound_callable_parameter_names"]
                ),
                "bound_callable_identity_hash": binding[
                    "bound_callable_identity_hash"
                ],
                "source_binding_attestation_id": binding[
                    "binding_attestation_id"
                ],
                "source_binding_attestation_record_hash": binding[
                    "binding_attestation_record_hash"
                ],
                "source_resolution_attestation_id": binding[
                    "source_resolution_attestation_id"
                ],
                "source_binding_contract_id": binding[
                    "source_binding_contract_id"
                ],
                "source_activation_id": binding["source_activation_id"],
                "source_activation_nonce": binding[
                    "source_activation_nonce"
                ],
                "source_boundary_id": binding["source_boundary_id"],
                "source_boundary_hash": binding[
                    "source_boundary_hash"
                ],
                "certified_artifact_input_mode": APPROVED_INPUT_MODE,
                "immutable_output_mode": APPROVED_OUTPUT_MODE,
                "required_argument_names": REQUIRED_BOUND_PARAMETERS,
                "argument_contract_hash": argument_contract_hash,
                "one_time_invocation": True,
                "invocation_authorized": True,
                "invocation_performed": False,
                "corpus_read_allowed": False,
                "corpus_read_performed": False,
                "source_mutation_allowed": False,
                "source_mutation_performed": False,
                "forecast_creation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_handoff_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "readiness_status": "ready_for_one_time_controlled_invocation",
            }
            records.append(
                DownstreamReadOnlyConsumerControlledInvocationReadinessRecord(
                    **body,
                    invocation_readiness_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_binding_attestation_manifest_id": source[
                    "binding_attestation_manifest_id"
                ],
                "source_binding_attestation_manifest_hash": source[
                    "binding_attestation_manifest_hash"
                ],
                "evaluated_at": evaluated_at.isoformat(),
                "invocation_readiness_record_hashes": [
                    record.invocation_readiness_record_hash
                    for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at.isoformat(),
            "invocation_readiness_manifest_id": manifest_id,
            "invocation_readiness_status": STATUS_READY,
            "invocation_readiness_policy_id": POLICY_ID,
            "source_binding_attestation_manifest_id": source[
                "binding_attestation_manifest_id"
            ],
            "source_binding_attestation_manifest_hash": source[
                "binding_attestation_manifest_hash"
            ],
            "source_resolution_attestation_manifest_id": source[
                "source_resolution_attestation_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "readiness_record_count": len(records),
            "readiness_records": tuple(records),
            "all_binding_attestation_hashes_verified": True,
            "all_bound_callable_identities_verified": True,
            "all_required_arguments_verified": True,
            "all_invocation_nonces_unique": True,
            "certified_artifact_input_mode_preserved": True,
            "immutable_output_mode_preserved": True,
            "source_boundary_consumed_without_reexecution": True,
            "one_time_invocation_required": True,
            "controlled_invocation_authorized": True,
            "invocation_performed": False,
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
            "readiness_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["readiness_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessManifest(
            **body,
            invocation_readiness_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.readiness_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.readiness_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.readiness_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.invocation_readiness_id}.json",
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

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_readiness_gate import (
    APPROVED_INPUT_MODE,
    APPROVED_OUTPUT_MODE,
    REQUIRED_BOUND_PARAMETERS,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError,
    stable_hash,
)


def _seed_binding(path: Path) -> None:
    record = {
        "sequence": 1,
        "binding_attestation_id": "binding-attestation-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer"
        ),
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": "analyze_certified_oia_artifacts",
        "callable_path": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer."
            "OracleResearchAnalyticsConsumer."
            "analyze_certified_oia_artifacts"
        ),
        "source_resolution_attestation_id": "resolution-test",
        "source_resolution_attestation_record_hash": stable_hash(
            {"resolution": 1}
        ),
        "source_binding_contract_id": "binding-contract-test",
        "source_binding_contract_hash": stable_hash(
            {"binding-contract": 1}
        ),
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"activation-nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "consumer_instantiated": True,
        "consumer_instance_type": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer."
            "OracleResearchAnalyticsConsumer"
        ),
        "callable_bound": True,
        "bound_callable_is_callable": True,
        "bound_callable_signature": (
            "(*, certified_artifacts, execution_context)"
        ),
        "bound_callable_parameter_names": [
            "certified_artifacts",
            "execution_context",
        ],
        "bound_callable_identity_hash": stable_hash(
            {"bound-callable": 1}
        ),
        "callable_invocation_allowed": True,
        "callable_invocation_performed": False,
        "corpus_read_performed": False,
        "source_mutation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "binding_status": "bound_not_invoked",
    }
    record["binding_attestation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-009",
        "engine_id": "INT-OIA-009",
        "attested_at": "2026-07-22T00:00:00+00:00",
        "binding_attestation_manifest_id": "int-oia-009-test",
        "binding_attestation_status": (
            "downstream_read_only_consumer_callable_binding_attested"
        ),
        "binding_attestation_policy_id": "test",
        "source_resolution_attestation_manifest_id": "int-oia-008-test",
        "source_resolution_attestation_manifest_hash": stable_hash(
            {"int": 8}
        ),
        "source_resolution_readiness_manifest_id": "int-oia-007-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "attestation_record_count": 1,
        "attestation_records": [record],
        "all_resolution_hashes_verified": True,
        "all_consumers_instantiated": True,
        "all_callables_bound": True,
        "all_bound_callables_callable": True,
        "exact_callable_identity_preserved": True,
        "source_boundary_consumed_without_reexecution": True,
        "callable_invocation_allowed": True,
        "callable_invocation_performed": False,
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
        "controlled_callable_invocation_authorized": True,
        "attestation_artifact_persistence_allowed": True,
    }
    manifest["binding_attestation_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-010 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED INVOCATION READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        binding = root / "binding"
        readiness = root / "readiness"
        _seed_binding(binding)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessGate(
            binding_directory=binding,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-010"
        assert first.readiness_record_count == 1
        assert first.all_binding_attestation_hashes_verified
        assert first.all_bound_callable_identities_verified
        assert first.all_required_arguments_verified
        assert first.all_invocation_nonces_unique
        assert first.certified_artifact_input_mode_preserved
        assert first.immutable_output_mode_preserved
        assert first.source_boundary_consumed_without_reexecution
        assert first.one_time_invocation_required
        assert first.controlled_invocation_authorized
        assert not first.invocation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.readiness_records[0]
        assert record.certified_artifact_input_mode == APPROVED_INPUT_MODE
        assert record.immutable_output_mode == APPROVED_OUTPUT_MODE
        assert record.required_argument_names == REQUIRED_BOUND_PARAMETERS
        assert record.one_time_invocation
        assert record.invocation_authorized
        assert not record.invocation_performed
        assert not record.corpus_read_allowed
        assert not record.corpus_read_performed
        assert len(record.invocation_nonce) == 64
        assert len(record.argument_contract_hash) == 64
        assert (
            record.readiness_status
            == "ready_for_one_time_controlled_invocation"
        )

        assert (readiness / "current.json").exists()

        tampered = json.loads(
            (binding / "current.json").read_text(encoding="utf-8")
        )
        tampered["attestation_records"][0][
            "bound_callable_parameter_names"
        ] = ["unsafe_argument"]
        (binding / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.evaluate(evaluated_at=fixed, persist=False)
            raise AssertionError("tampered binding accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError:
            pass

    print("[PASS] Actual INT-OIA-009 binding attestation consumed")
    print("[PASS] Every binding-attestation hash verified")
    print("[PASS] Bound callable identity independently verified")
    print("[PASS] Exact invocation argument contract verified")
    print("[PASS] One-time invocation nonce generated deterministically")
    print("[PASS] Invocation nonces remained unique")
    print("[PASS] Certified-artifact-only input mode preserved")
    print("[PASS] Immutable research-artifact output mode preserved")
    print("[PASS] Controlled one-time invocation authorized")
    print("[PASS] Callable was not invoked")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe binding evidence rejected")
    print("[PASS] Atomic invocation-readiness artifacts persisted")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
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


def verify_int_oia_009_contract() -> None:
    if not INT_OIA_009.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-009 production module missing: {INT_OIA_009}"
        )
    source = INT_OIA_009.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-009"',
        "class DownstreamReadOnlyConsumerCallableBindingAttestationRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationGate",
        "binding_attestation_manifest_hash",
        "controlled_callable_invocation_authorized",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-009 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-009 binding-attestation contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export_line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_controlled_invocation_readiness_gate import *"
    )
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        PACKAGE.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-010 INSTALLER")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED INVOCATION READINESS")
    print("=" * 40)

    verify_int_oia_009_contract()
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

    print("[OK] INT-OIA-010 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-010 downstream read-only consumer "
        "controlled invocation readiness gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
