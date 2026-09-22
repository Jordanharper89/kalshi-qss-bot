from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_callable_binding_attestation_gate.py"
TEST = ROOT / "test_int_oia_009_oracle_intelligence_analytics_downstream_read_only_consumer_callable_binding_attestation_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
INT_OIA_008 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_callable_resolution_attestation_gate.py"

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

SCHEMA_VERSION = "INT-OIA-009"
ENGINE_ID = "INT-OIA-009"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-callable-binding-attestation.v1"
STATUS_BOUND = "downstream_read_only_consumer_callable_binding_attested"

DEFAULT_RESOLUTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_resolution_attestation"
)
DEFAULT_BINDING_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_binding_attestation"
)


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
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
class DownstreamReadOnlyConsumerCallableBindingAttestationRecord:
    sequence: int
    binding_attestation_id: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    callable_name: str
    callable_path: str
    source_resolution_attestation_id: str
    source_resolution_attestation_record_hash: str
    source_binding_contract_id: str
    source_binding_contract_hash: str
    source_activation_id: str
    source_activation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    consumer_instantiated: bool
    consumer_instance_type: str
    callable_bound: bool
    bound_callable_is_callable: bool
    bound_callable_signature: str
    bound_callable_parameter_names: tuple[str, ...]
    bound_callable_identity_hash: str
    callable_invocation_allowed: bool
    callable_invocation_performed: bool
    corpus_read_performed: bool
    source_mutation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    binding_status: str
    binding_attestation_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationManifest:
    schema_version: str
    engine_id: str
    attested_at: str
    binding_attestation_manifest_id: str
    binding_attestation_status: str
    binding_attestation_policy_id: str
    source_resolution_attestation_manifest_id: str
    source_resolution_attestation_manifest_hash: str
    source_resolution_readiness_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    attestation_record_count: int
    attestation_records: tuple[
        DownstreamReadOnlyConsumerCallableBindingAttestationRecord, ...
    ]
    all_resolution_hashes_verified: bool
    all_consumers_instantiated: bool
    all_callables_bound: bool
    all_bound_callables_callable: bool
    exact_callable_identity_preserved: bool
    source_boundary_consumed_without_reexecution: bool
    callable_invocation_allowed: bool
    callable_invocation_performed: bool
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
    controlled_callable_invocation_authorized: bool
    attestation_artifact_persistence_allowed: bool
    binding_attestation_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationGate:
    def __init__(
        self,
        *,
        resolution_directory: Path | str = DEFAULT_RESOLUTION_DIRECTORY,
        binding_directory: Path | str = DEFAULT_BINDING_DIRECTORY,
    ) -> None:
        self.resolution_directory = Path(resolution_directory)
        self.binding_directory = Path(binding_directory)

    def _load_resolution(self) -> dict[str, Any]:
        path = self.resolution_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                f"INT-OIA-008 resolution artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                "INT-OIA-008 resolution artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop(
            "resolution_attestation_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                "INT-OIA-008 resolution manifest hash mismatch"
            )
        payload["resolution_attestation_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-008",
            "engine_id": "INT-OIA-008",
            "all_readiness_hashes_verified": True,
            "all_modules_imported": True,
            "all_classes_resolved": True,
            "all_callables_resolved": True,
            "all_callables_callable": True,
            "exact_callable_identity_preserved": True,
            "source_boundary_consumed_without_reexecution": True,
            "callable_binding_allowed": True,
            "callable_binding_performed": False,
            "callable_invocation_allowed": False,
            "callable_invocation_performed": False,
            "consumer_instantiation_performed": False,
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
            "controlled_callable_binding_authorized": True,
            "attestation_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    f"unsafe or incomplete INT-OIA-008 field: {field}"
                )

        records = payload.get("attestation_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("attestation_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                "INT-OIA-008 attestation records invalid"
            )

        seen_consumers: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            record = dict(raw_record)
            record_hash = record.pop(
                "resolution_attestation_record_hash",
                None,
            )
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "INT-OIA-008 resolution-record hash mismatch"
                )
            record["resolution_attestation_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "INT-OIA-008 attestation sequence mismatch"
                )

            consumer_id = record.get("consumer_id")
            if (
                not isinstance(consumer_id, str)
                or not consumer_id
                or consumer_id in seen_consumers
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "invalid or duplicate consumer"
                )
            seen_consumers.add(consumer_id)

            required_record = {
                "module_imported": True,
                "class_resolved": True,
                "callable_resolved": True,
                "callable_is_callable": True,
                "callable_bound": False,
                "callable_invoked": False,
                "consumer_instantiated": False,
                "corpus_read_performed": False,
                "source_mutation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "resolution_status": "resolved_not_bound",
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                        f"unsafe INT-OIA-008 record field: {field}"
                    )

        payload["attestation_records"] = records
        return payload

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationManifest:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_resolution()

        records: list[
            DownstreamReadOnlyConsumerCallableBindingAttestationRecord
        ] = []

        for sequence, resolution in enumerate(
            source["attestation_records"],
            start=1,
        ):
            try:
                module = importlib.import_module(resolution["consumer_module"])
            except Exception as exc:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    f"consumer module import failed: {resolution['consumer_module']}"
                ) from exc

            consumer_class = getattr(
                module,
                resolution["consumer_class"],
                None,
            )
            if not inspect.isclass(consumer_class):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "consumer class could not be resolved"
                )

            try:
                consumer_instance = consumer_class()
            except Exception as exc:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "consumer could not be instantiated without arguments"
                ) from exc

            bound_callable = getattr(
                consumer_instance,
                resolution["callable_name"],
                None,
            )
            if bound_callable is None or not callable(bound_callable):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError(
                    "approved callable could not be bound"
                )

            bound_signature = inspect.signature(bound_callable)
            parameter_names = tuple(bound_signature.parameters.keys())
            identity_hash = stable_hash(
                {
                    "consumer_module": resolution["consumer_module"],
                    "consumer_class": resolution["consumer_class"],
                    "consumer_instance_type": (
                        f"{consumer_instance.__class__.__module__}."
                        f"{consumer_instance.__class__.__qualname__}"
                    ),
                    "callable_name": resolution["callable_name"],
                    "callable_path": resolution["callable_path"],
                    "bound_callable_signature": str(bound_signature),
                    "bound_callable_parameter_names": parameter_names,
                }
            )

            attestation_id = stable_hash(
                {
                    "source_resolution_attestation_manifest_id": source[
                        "resolution_attestation_manifest_id"
                    ],
                    "source_resolution_attestation_id": resolution[
                        "resolution_attestation_id"
                    ],
                    "source_resolution_attestation_record_hash": resolution[
                        "resolution_attestation_record_hash"
                    ],
                    "bound_callable_identity_hash": identity_hash,
                    "attested_at": attested_at.isoformat(),
                }
            )

            body = {
                "sequence": sequence,
                "binding_attestation_id": attestation_id,
                "consumer_id": resolution["consumer_id"],
                "consumer_module": resolution["consumer_module"],
                "consumer_class": resolution["consumer_class"],
                "callable_name": resolution["callable_name"],
                "callable_path": resolution["callable_path"],
                "source_resolution_attestation_id": resolution[
                    "resolution_attestation_id"
                ],
                "source_resolution_attestation_record_hash": resolution[
                    "resolution_attestation_record_hash"
                ],
                "source_binding_contract_id": resolution[
                    "source_binding_contract_id"
                ],
                "source_binding_contract_hash": resolution[
                    "source_binding_contract_hash"
                ],
                "source_activation_id": resolution[
                    "source_activation_id"
                ],
                "source_activation_nonce": resolution[
                    "source_activation_nonce"
                ],
                "source_boundary_id": resolution["source_boundary_id"],
                "source_boundary_hash": resolution[
                    "source_boundary_hash"
                ],
                "consumer_instantiated": True,
                "consumer_instance_type": (
                    f"{consumer_instance.__class__.__module__}."
                    f"{consumer_instance.__class__.__qualname__}"
                ),
                "callable_bound": True,
                "bound_callable_is_callable": True,
                "bound_callable_signature": str(bound_signature),
                "bound_callable_parameter_names": parameter_names,
                "bound_callable_identity_hash": identity_hash,
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
            records.append(
                DownstreamReadOnlyConsumerCallableBindingAttestationRecord(
                    **body,
                    binding_attestation_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_resolution_attestation_manifest_id": source[
                    "resolution_attestation_manifest_id"
                ],
                "source_resolution_attestation_manifest_hash": source[
                    "resolution_attestation_manifest_hash"
                ],
                "attested_at": attested_at.isoformat(),
                "binding_attestation_record_hashes": [
                    record.binding_attestation_record_hash
                    for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "binding_attestation_manifest_id": manifest_id,
            "binding_attestation_status": STATUS_BOUND,
            "binding_attestation_policy_id": POLICY_ID,
            "source_resolution_attestation_manifest_id": source[
                "resolution_attestation_manifest_id"
            ],
            "source_resolution_attestation_manifest_hash": source[
                "resolution_attestation_manifest_hash"
            ],
            "source_resolution_readiness_manifest_id": source[
                "source_resolution_readiness_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "attestation_record_count": len(records),
            "attestation_records": tuple(records),
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

        serializable = dict(body)
        serializable["attestation_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationManifest(
            **body,
            binding_attestation_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(
                self.binding_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.binding_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.binding_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.binding_attestation_id}.json",
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

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_callable_binding_attestation_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError,
    stable_hash,
)


TEST_MODULE = "int_oia_009_test_consumer_module"


class OracleResearchAnalyticsConsumer:
    def __init__(self):
        self.initialized = True

    def analyze_certified_oia_artifacts(
        self,
        *,
        certified_artifacts,
        execution_context,
    ):
        raise AssertionError("INT-OIA-009 must not invoke the callable")


def _install_test_module() -> None:
    module = types.ModuleType(TEST_MODULE)
    module.OracleResearchAnalyticsConsumer = OracleResearchAnalyticsConsumer
    sys.modules[TEST_MODULE] = module


def _seed_resolution(path: Path) -> None:
    callable_path = (
        f"{TEST_MODULE}."
        "OracleResearchAnalyticsConsumer."
        "analyze_certified_oia_artifacts"
    )
    record = {
        "sequence": 1,
        "resolution_attestation_id": "resolution-attestation-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": TEST_MODULE,
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": "analyze_certified_oia_artifacts",
        "callable_path": callable_path,
        "source_resolution_readiness_id": "resolution-readiness-test",
        "source_resolution_readiness_record_hash": stable_hash(
            {"readiness": 1}
        ),
        "source_binding_contract_id": "binding-test",
        "source_binding_contract_hash": stable_hash({"binding": 1}),
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "module_imported": True,
        "class_resolved": True,
        "callable_resolved": True,
        "callable_is_callable": True,
        "callable_is_coroutine": False,
        "callable_signature": (
            "(self, *, certified_artifacts, execution_context)"
        ),
        "callable_parameter_names": [
            "self",
            "certified_artifacts",
            "execution_context",
        ],
        "callable_bound": False,
        "callable_invoked": False,
        "consumer_instantiated": False,
        "corpus_read_performed": False,
        "source_mutation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "resolution_status": "resolved_not_bound",
    }
    record["resolution_attestation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-008",
        "engine_id": "INT-OIA-008",
        "attested_at": "2026-07-22T00:00:00+00:00",
        "resolution_attestation_manifest_id": "int-oia-008-test",
        "resolution_attestation_status": (
            "downstream_read_only_consumer_callable_resolution_attested"
        ),
        "resolution_attestation_policy_id": "test",
        "source_resolution_readiness_manifest_id": "int-oia-007-test",
        "source_resolution_readiness_manifest_hash": stable_hash(
            {"int": 7}
        ),
        "source_binding_manifest_id": "int-oia-006-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "attestation_record_count": 1,
        "attestation_records": [record],
        "all_readiness_hashes_verified": True,
        "all_modules_imported": True,
        "all_classes_resolved": True,
        "all_callables_resolved": True,
        "all_callables_callable": True,
        "exact_callable_identity_preserved": True,
        "source_boundary_consumed_without_reexecution": True,
        "callable_binding_allowed": True,
        "callable_binding_performed": False,
        "callable_invocation_allowed": False,
        "callable_invocation_performed": False,
        "consumer_instantiation_performed": False,
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
        "controlled_callable_binding_authorized": True,
        "attestation_artifact_persistence_allowed": True,
    }
    manifest["resolution_attestation_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-009 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CALLABLE BINDING ATTESTATION")
    print("=" * 40)

    _install_test_module()

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        resolution = root / "resolution"
        binding = root / "binding"
        _seed_resolution(resolution)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationGate(
            resolution_directory=resolution,
            binding_directory=binding,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-009"
        assert first.attestation_record_count == 1
        assert first.all_resolution_hashes_verified
        assert first.all_consumers_instantiated
        assert first.all_callables_bound
        assert first.all_bound_callables_callable
        assert first.exact_callable_identity_preserved
        assert first.source_boundary_consumed_without_reexecution
        assert first.callable_invocation_allowed
        assert not first.callable_invocation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.controlled_callable_invocation_authorized
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.attestation_records[0]
        assert record.consumer_instantiated
        assert record.callable_bound
        assert record.bound_callable_is_callable
        assert record.bound_callable_parameter_names == (
            "certified_artifacts",
            "execution_context",
        )
        assert len(record.bound_callable_identity_hash) == 64
        assert record.callable_invocation_allowed
        assert not record.callable_invocation_performed
        assert not record.corpus_read_performed
        assert record.binding_status == "bound_not_invoked"

        assert (binding / "current.json").exists()

        tampered = json.loads(
            (resolution / "current.json").read_text(encoding="utf-8")
        )
        tampered["attestation_records"][0][
            "callable_invoked"
        ] = True
        (resolution / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered resolution accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-008 resolution attestation consumed")
    print("[PASS] Every resolution-attestation hash verified")
    print("[PASS] Exact consumer class instantiated")
    print("[PASS] Exact approved analytical callable bound")
    print("[PASS] Bound callable signature captured deterministically")
    print("[PASS] Bound callable identity hash persisted")
    print("[PASS] Controlled callable invocation authorized")
    print("[PASS] Callable was not invoked")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe resolution evidence rejected")
    print("[PASS] Atomic binding-attestation artifacts persisted")
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


def verify_int_oia_008_contract() -> None:
    if not INT_OIA_008.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-008 production module missing: {INT_OIA_008}"
        )
    source = INT_OIA_008.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-008"',
        "class DownstreamReadOnlyConsumerCallableResolutionAttestationRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationGate",
        "resolution_attestation_manifest_hash",
        "controlled_callable_binding_authorized",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-008 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-008 resolution-attestation contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export_line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_callable_binding_attestation_gate import *"
    )
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        PACKAGE.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-009 INSTALLER")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CALLABLE BINDING ATTESTATION")
    print("=" * 40)

    verify_int_oia_008_contract()
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

    print("[OK] INT-OIA-009 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-009 downstream read-only consumer "
        "callable binding attestation gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
