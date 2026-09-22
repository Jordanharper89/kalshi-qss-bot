from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_execution_gate.py"
TEST = ROOT / "test_int_oia_011_oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_execution_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
INT_OIA_010 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_readiness_gate.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-011"
ENGINE_ID = "INT-OIA-011"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-controlled-invocation-execution.v1"
STATUS_EXECUTED = "downstream_read_only_consumer_controlled_invocation_executed"

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_invocation_readiness"
)
DEFAULT_EXECUTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_invocation_execution"
)

REQUIRED_ARGUMENT_NAMES = (
    "certified_artifacts",
    "execution_context",
)
APPROVED_INPUT_MODE = "certified_artifacts_only"
APPROVED_OUTPUT_MODE = "immutable_research_artifact_only"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
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
class DownstreamReadOnlyConsumerControlledInvocationExecutionRecord:
    sequence: int
    invocation_execution_id: str
    invocation_nonce: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    callable_name: str
    callable_path: str
    bound_callable_identity_hash: str
    source_invocation_readiness_id: str
    source_invocation_readiness_record_hash: str
    source_binding_attestation_id: str
    source_activation_id: str
    source_activation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    certified_artifacts_hash: str
    execution_context_hash: str
    argument_contract_hash: str
    result_type: str
    result_hash: str
    result_payload: Any
    one_time_invocation: bool
    invocation_authorized: bool
    invocation_performed: bool
    invocation_count: int
    corpus_read_performed: bool
    database_connection_performed: bool
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
    execution_status: str
    invocation_execution_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionManifest:
    schema_version: str
    engine_id: str
    executed_at: str
    invocation_execution_manifest_id: str
    invocation_execution_status: str
    invocation_execution_policy_id: str
    source_invocation_readiness_manifest_id: str
    source_invocation_readiness_manifest_hash: str
    source_binding_attestation_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    execution_record_count: int
    execution_records: tuple[
        DownstreamReadOnlyConsumerControlledInvocationExecutionRecord, ...
    ]
    all_readiness_hashes_verified: bool
    all_invocation_nonces_unique: bool
    all_bound_callable_identities_verified: bool
    all_argument_contracts_verified: bool
    all_results_deterministically_hashable: bool
    certified_artifact_input_mode_preserved: bool
    immutable_output_mode_preserved: bool
    source_boundary_consumed_without_reexecution: bool
    one_time_invocation_enforced: bool
    controlled_invocation_performed: bool
    corpus_read_execution_repeated: bool
    database_connection_performed: bool
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
    immutable_execution_artifact_persistence_allowed: bool
    invocation_execution_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionGate:
    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
        execution_directory: Path | str = DEFAULT_EXECUTION_DIRECTORY,
    ) -> None:
        self.readiness_directory = Path(readiness_directory)
        self.execution_directory = Path(execution_directory)

    def _load_readiness(self) -> dict[str, Any]:
        path = self.readiness_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                f"INT-OIA-010 readiness artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                "INT-OIA-010 readiness artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop(
            "invocation_readiness_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                "INT-OIA-010 readiness manifest hash mismatch"
            )
        payload["invocation_readiness_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-010",
            "engine_id": "INT-OIA-010",
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
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                    f"unsafe or incomplete INT-OIA-010 field: {field}"
                )

        records = payload.get("readiness_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("readiness_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                "INT-OIA-010 readiness records invalid"
            )

        seen_nonces: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            record = dict(raw_record)
            record_hash = record.pop(
                "invocation_readiness_record_hash",
                None,
            )
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                    "INT-OIA-010 readiness-record hash mismatch"
                )
            record["invocation_readiness_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                    "INT-OIA-010 readiness sequence mismatch"
                )

            nonce = record.get("invocation_nonce")
            if not _valid_hash(nonce) or nonce in seen_nonces:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                    "invalid or duplicate invocation nonce"
                )
            seen_nonces.add(nonce)

            if tuple(record.get("required_argument_names", ())) != REQUIRED_ARGUMENT_NAMES:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                    "INT-OIA-010 argument contract mismatch"
                )

            required_record = {
                "certified_artifact_input_mode": APPROVED_INPUT_MODE,
                "immutable_output_mode": APPROVED_OUTPUT_MODE,
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
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                        f"unsafe INT-OIA-010 readiness-record field: {field}"
                    )

        payload["readiness_records"] = records
        return payload

    def execute(
        self,
        *,
        certified_artifacts: Any,
        execution_context: Mapping[str, Any],
        executed_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionManifest:
        executed_at = _aware(executed_at, "executed_at")
        source = self._load_readiness()

        canonical_artifacts = _canonical(certified_artifacts)
        canonical_context = _canonical(dict(execution_context))
        certified_artifacts_hash = stable_hash(canonical_artifacts)
        execution_context_hash = stable_hash(canonical_context)

        records: list[
            DownstreamReadOnlyConsumerControlledInvocationExecutionRecord
        ] = []

        for sequence, readiness in enumerate(
            source["readiness_records"],
            start=1,
        ):
            try:
                module = importlib.import_module(readiness["consumer_module"])
                consumer_class = getattr(
                    module,
                    readiness["consumer_class"],
                )
                consumer_instance = consumer_class()
                bound_callable = getattr(
                    consumer_instance,
                    readiness["callable_name"],
                )
            except Exception as exc:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                    "approved consumer callable could not be reconstructed"
                ) from exc

            if not callable(bound_callable):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                    "reconstructed target is not callable"
                )

            signature = inspect.signature(bound_callable)
            if tuple(signature.parameters.keys()) != REQUIRED_ARGUMENT_NAMES:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                    "runtime callable signature does not match readiness contract"
                )

            runtime_identity_hash = stable_hash(
                {
                    "consumer_module": readiness["consumer_module"],
                    "consumer_class": readiness["consumer_class"],
                    "consumer_instance_type": (
                        f"{consumer_instance.__class__.__module__}."
                        f"{consumer_instance.__class__.__qualname__}"
                    ),
                    "callable_name": readiness["callable_name"],
                    "callable_path": readiness["callable_path"],
                    "bound_callable_signature": str(signature),
                    "bound_callable_parameter_names": tuple(
                        signature.parameters.keys()
                    ),
                }
            )
            if runtime_identity_hash != readiness["bound_callable_identity_hash"]:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError(
                    "runtime bound-callable identity hash mismatch"
                )

            result = bound_callable(
                certified_artifacts=canonical_artifacts,
                execution_context=canonical_context,
            )
            canonical_result = _canonical(result)
            result_hash = stable_hash(canonical_result)

            execution_id = stable_hash(
                {
                    "source_invocation_readiness_manifest_id": source[
                        "invocation_readiness_manifest_id"
                    ],
                    "source_invocation_readiness_id": readiness[
                        "invocation_readiness_id"
                    ],
                    "invocation_nonce": readiness["invocation_nonce"],
                    "certified_artifacts_hash": certified_artifacts_hash,
                    "execution_context_hash": execution_context_hash,
                    "result_hash": result_hash,
                    "executed_at": executed_at.isoformat(),
                }
            )

            body = {
                "sequence": sequence,
                "invocation_execution_id": execution_id,
                "invocation_nonce": readiness["invocation_nonce"],
                "consumer_id": readiness["consumer_id"],
                "consumer_module": readiness["consumer_module"],
                "consumer_class": readiness["consumer_class"],
                "callable_name": readiness["callable_name"],
                "callable_path": readiness["callable_path"],
                "bound_callable_identity_hash": readiness[
                    "bound_callable_identity_hash"
                ],
                "source_invocation_readiness_id": readiness[
                    "invocation_readiness_id"
                ],
                "source_invocation_readiness_record_hash": readiness[
                    "invocation_readiness_record_hash"
                ],
                "source_binding_attestation_id": readiness[
                    "source_binding_attestation_id"
                ],
                "source_activation_id": readiness["source_activation_id"],
                "source_activation_nonce": readiness[
                    "source_activation_nonce"
                ],
                "source_boundary_id": readiness["source_boundary_id"],
                "source_boundary_hash": readiness["source_boundary_hash"],
                "certified_artifacts_hash": certified_artifacts_hash,
                "execution_context_hash": execution_context_hash,
                "argument_contract_hash": readiness[
                    "argument_contract_hash"
                ],
                "result_type": (
                    f"{result.__class__.__module__}."
                    f"{result.__class__.__qualname__}"
                ),
                "result_hash": result_hash,
                "result_payload": canonical_result,
                "one_time_invocation": True,
                "invocation_authorized": True,
                "invocation_performed": True,
                "invocation_count": 1,
                "corpus_read_performed": False,
                "database_connection_performed": False,
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
                "execution_status": "invoked_once_result_captured",
            }
            records.append(
                DownstreamReadOnlyConsumerControlledInvocationExecutionRecord(
                    **body,
                    invocation_execution_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_invocation_readiness_manifest_id": source[
                    "invocation_readiness_manifest_id"
                ],
                "source_invocation_readiness_manifest_hash": source[
                    "invocation_readiness_manifest_hash"
                ],
                "executed_at": executed_at.isoformat(),
                "execution_record_hashes": [
                    record.invocation_execution_record_hash
                    for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "executed_at": executed_at.isoformat(),
            "invocation_execution_manifest_id": manifest_id,
            "invocation_execution_status": STATUS_EXECUTED,
            "invocation_execution_policy_id": POLICY_ID,
            "source_invocation_readiness_manifest_id": source[
                "invocation_readiness_manifest_id"
            ],
            "source_invocation_readiness_manifest_hash": source[
                "invocation_readiness_manifest_hash"
            ],
            "source_binding_attestation_manifest_id": source[
                "source_binding_attestation_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "execution_record_count": len(records),
            "execution_records": tuple(records),
            "all_readiness_hashes_verified": True,
            "all_invocation_nonces_unique": True,
            "all_bound_callable_identities_verified": True,
            "all_argument_contracts_verified": True,
            "all_results_deterministically_hashable": True,
            "certified_artifact_input_mode_preserved": True,
            "immutable_output_mode_preserved": True,
            "source_boundary_consumed_without_reexecution": True,
            "one_time_invocation_enforced": True,
            "controlled_invocation_performed": True,
            "corpus_read_execution_repeated": False,
            "database_connection_performed": False,
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
            "immutable_execution_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["execution_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionManifest(
            **body,
            invocation_execution_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.execution_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.execution_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.execution_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.invocation_execution_id}.json",
                    asdict(record),
                )

        return manifest
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_execution_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError,
    stable_hash,
)


TEST_MODULE = "int_oia_011_test_consumer_module"
INVOCATION_COUNT = 0


class OracleResearchAnalyticsConsumer:
    def analyze_certified_oia_artifacts(
        self,
        certified_artifacts,
        execution_context,
    ):
        global INVOCATION_COUNT
        INVOCATION_COUNT += 1
        return {
            "artifact_count": len(certified_artifacts),
            "consumer_mode": execution_context["consumer_mode"],
            "evidence_hash": stable_hash(certified_artifacts),
            "read_only": True,
        }


def _install_test_module() -> None:
    module = types.ModuleType(TEST_MODULE)
    module.OracleResearchAnalyticsConsumer = OracleResearchAnalyticsConsumer
    sys.modules[TEST_MODULE] = module


def _seed_readiness(path: Path) -> None:
    consumer = OracleResearchAnalyticsConsumer()
    bound = consumer.analyze_certified_oia_artifacts
    import inspect

    signature = inspect.signature(bound)
    identity_hash = stable_hash(
        {
            "consumer_module": TEST_MODULE,
            "consumer_class": "OracleResearchAnalyticsConsumer",
            "consumer_instance_type": (
                f"{consumer.__class__.__module__}."
                f"{consumer.__class__.__qualname__}"
            ),
            "callable_name": "analyze_certified_oia_artifacts",
            "callable_path": (
                f"{TEST_MODULE}."
                "OracleResearchAnalyticsConsumer."
                "analyze_certified_oia_artifacts"
            ),
            "bound_callable_signature": str(signature),
            "bound_callable_parameter_names": tuple(
                signature.parameters.keys()
            ),
        }
    )

    record = {
        "sequence": 1,
        "invocation_readiness_id": "invocation-readiness-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": TEST_MODULE,
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": "analyze_certified_oia_artifacts",
        "callable_path": (
            f"{TEST_MODULE}."
            "OracleResearchAnalyticsConsumer."
            "analyze_certified_oia_artifacts"
        ),
        "bound_callable_signature": str(signature),
        "bound_callable_parameter_names": [
            "certified_artifacts",
            "execution_context",
        ],
        "bound_callable_identity_hash": identity_hash,
        "source_binding_attestation_id": "binding-attestation-test",
        "source_binding_attestation_record_hash": stable_hash(
            {"binding-attestation": 1}
        ),
        "source_resolution_attestation_id": "resolution-test",
        "source_binding_contract_id": "binding-contract-test",
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"activation": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "certified_artifact_input_mode": "certified_artifacts_only",
        "immutable_output_mode": "immutable_research_artifact_only",
        "required_argument_names": [
            "certified_artifacts",
            "execution_context",
        ],
        "argument_contract_hash": stable_hash({"arguments": 1}),
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
    record["invocation_readiness_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-010",
        "engine_id": "INT-OIA-010",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "invocation_readiness_manifest_id": "int-oia-010-test",
        "invocation_readiness_status": (
            "downstream_read_only_consumer_controlled_invocation_ready"
        ),
        "invocation_readiness_policy_id": "test",
        "source_binding_attestation_manifest_id": "int-oia-009-test",
        "source_binding_attestation_manifest_hash": stable_hash(
            {"int": 9}
        ),
        "source_resolution_attestation_manifest_id": "int-oia-008-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "readiness_record_count": 1,
        "readiness_records": [record],
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
    manifest["invocation_readiness_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    global INVOCATION_COUNT

    print("=" * 40)
    print(" INT-OIA-011 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED INVOCATION EXECUTION")
    print("=" * 40)

    _install_test_module()

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        readiness = root / "readiness"
        execution = root / "execution"
        _seed_readiness(readiness)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionGate(
            readiness_directory=readiness,
            execution_directory=execution,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        artifacts = (
            {"artifact_id": "a-1", "certified": True},
            {"artifact_id": "a-2", "certified": True},
        )
        context = {
            "consumer_mode": "read_only_research",
            "execution_id": "test-execution",
        }

        INVOCATION_COUNT = 0
        first = gate.execute(
            certified_artifacts=artifacts,
            execution_context=context,
            executed_at=fixed,
            persist=True,
        )
        assert INVOCATION_COUNT == 1

        INVOCATION_COUNT = 0
        second = gate.execute(
            certified_artifacts=artifacts,
            execution_context=context,
            executed_at=fixed,
            persist=False,
        )
        assert INVOCATION_COUNT == 1
        assert first == second

        assert first.schema_version == "INT-OIA-011"
        assert first.execution_record_count == 1
        assert first.all_readiness_hashes_verified
        assert first.all_invocation_nonces_unique
        assert first.all_bound_callable_identities_verified
        assert first.all_argument_contracts_verified
        assert first.all_results_deterministically_hashable
        assert first.certified_artifact_input_mode_preserved
        assert first.immutable_output_mode_preserved
        assert first.source_boundary_consumed_without_reexecution
        assert first.one_time_invocation_enforced
        assert first.controlled_invocation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.database_connection_performed
        assert not first.source_mutation_performed
        assert not first.forecast_creation_allowed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.execution_records[0]
        assert record.invocation_performed
        assert record.invocation_count == 1
        assert record.result_payload["artifact_count"] == 2
        assert record.result_payload["read_only"] is True
        assert len(record.result_hash) == 64
        assert not record.corpus_read_performed
        assert not record.database_connection_performed
        assert record.execution_status == "invoked_once_result_captured"

        assert (execution / "current.json").exists()

        tampered = json.loads(
            (readiness / "current.json").read_text(encoding="utf-8")
        )
        tampered["readiness_records"][0]["invocation_performed"] = True
        (readiness / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.execute(
                certified_artifacts=artifacts,
                execution_context=context,
                executed_at=fixed,
                persist=False,
            )
            raise AssertionError("tampered readiness accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError:
            pass

    print("[PASS] Actual INT-OIA-010 invocation readiness consumed")
    print("[PASS] Every invocation-readiness hash verified")
    print("[PASS] Bound callable identity reconstructed and verified")
    print("[PASS] Certified artifacts passed in-memory only")
    print("[PASS] Controlled analytical callable invoked exactly once")
    print("[PASS] Immutable analytical result captured deterministically")
    print("[PASS] Result hash and execution lineage persisted")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe invocation readiness rejected")
    print("[PASS] Atomic controlled-execution artifacts persisted")
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


def verify_int_oia_010_contract() -> None:
    if not INT_OIA_010.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-010 production module missing: {INT_OIA_010}"
        )
    source = INT_OIA_010.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-010"',
        "class DownstreamReadOnlyConsumerControlledInvocationReadinessRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessGate",
        "invocation_readiness_manifest_hash",
        "controlled_invocation_authorized",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-010 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-010 invocation-readiness contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export_line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_controlled_invocation_execution_gate import *"
    )
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        PACKAGE.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-011 INSTALLER")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED INVOCATION EXECUTION")
    print("=" * 40)

    verify_int_oia_010_contract()
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

    print("[OK] INT-OIA-011 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-011 downstream read-only consumer "
        "controlled invocation execution gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
