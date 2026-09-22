from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_callable_resolution_readiness_gate.py"
TEST = ROOT / "test_int_oia_007_oracle_intelligence_analytics_downstream_read_only_consumer_callable_resolution_readiness_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
INT_OIA_006 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_callable_binding_contract_gate.py"

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

SCHEMA_VERSION = "INT-OIA-007"
ENGINE_ID = "INT-OIA-007"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-callable-resolution-readiness.v1"
STATUS_READY = "downstream_read_only_consumer_callable_resolution_ready"

DEFAULT_BINDING_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_binding_contract"
)
DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_resolution_readiness"
)

APPROVED_CALLABLE_NAME = "analyze_certified_oia_artifacts"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
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
class DownstreamReadOnlyConsumerCallableResolutionReadinessRecord:
    sequence: int
    resolution_readiness_id: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    callable_name: str
    callable_path: str
    source_binding_contract_id: str
    source_binding_contract_hash: str
    source_activation_id: str
    source_activation_nonce: str
    source_boundary_id: str
    source_boundary_hash: str
    module_identity_valid: bool
    class_identity_valid: bool
    callable_identity_valid: bool
    callable_path_consistent: bool
    exact_identity_hash_verified: bool
    dynamic_import_allowed: bool
    module_import_performed: bool
    callable_resolution_allowed: bool
    callable_resolution_performed: bool
    callable_binding_allowed: bool
    callable_binding_performed: bool
    callable_invocation_allowed: bool
    callable_invocation_performed: bool
    corpus_read_allowed: bool
    source_mutation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    controlled_resolution_authorized: bool
    readiness_status: str
    resolution_readiness_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: str
    resolution_readiness_manifest_id: str
    resolution_readiness_status: str
    resolution_readiness_policy_id: str
    source_binding_manifest_id: str
    source_binding_manifest_hash: str
    source_activation_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    readiness_record_count: int
    readiness_records: tuple[
        DownstreamReadOnlyConsumerCallableResolutionReadinessRecord, ...
    ]
    all_binding_hashes_verified: bool
    all_callable_paths_consistent: bool
    exact_callable_identity_preserved: bool
    source_boundary_consumed_without_reexecution: bool
    dynamic_import_allowed: bool
    module_import_performed: bool
    callable_resolution_allowed: bool
    callable_resolution_performed: bool
    callable_binding_allowed: bool
    callable_binding_performed: bool
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
    controlled_callable_resolution_authorized: bool
    readiness_artifact_persistence_allowed: bool
    resolution_readiness_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessGate:
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
                f"INT-OIA-006 binding artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
                "INT-OIA-006 binding artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("binding_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
                "INT-OIA-006 binding manifest hash mismatch"
            )
        payload["binding_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-006",
            "engine_id": "INT-OIA-006",
            "all_activation_hashes_verified": True,
            "all_activation_nonces_unique": True,
            "exact_consumer_identity_preserved": True,
            "exact_callable_identity_frozen": True,
            "source_boundary_consumed_without_reexecution": True,
            "corpus_read_execution_repeated": False,
            "callable_resolution_allowed": False,
            "callable_binding_allowed": False,
            "callable_invocation_allowed": False,
            "callable_resolution_performed": False,
            "callable_binding_performed": False,
            "callable_invocation_performed": False,
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
            "binding_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
                    f"unsafe or incomplete INT-OIA-006 field: {field}"
                )

        contracts = payload.get("binding_contracts")
        if (
            not isinstance(contracts, list)
            or not contracts
            or payload.get("binding_contract_count") != len(contracts)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
                "INT-OIA-006 binding contracts invalid"
            )

        seen_consumers: set[str] = set()
        for sequence, raw_contract in enumerate(contracts, start=1):
            contract = dict(raw_contract)
            contract_hash = contract.pop("binding_contract_hash", None)
            if not _valid_hash(contract_hash) or stable_hash(contract) != contract_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
                    "INT-OIA-006 binding-contract hash mismatch"
                )
            contract["binding_contract_hash"] = contract_hash

            if contract.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
                    "INT-OIA-006 binding sequence mismatch"
                )

            consumer_id = contract.get("consumer_id")
            if (
                not isinstance(consumer_id, str)
                or not consumer_id
                or consumer_id in seen_consumers
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
                    "invalid or duplicate bound consumer"
                )
            seen_consumers.add(consumer_id)

            module_name = contract.get("consumer_module")
            class_name = contract.get("consumer_class")
            callable_name = contract.get("callable_name")
            callable_path = contract.get("callable_path")
            if (
                not isinstance(module_name, str)
                or not module_name.strip()
                or not isinstance(class_name, str)
                or not class_name.strip()
                or callable_name != APPROVED_CALLABLE_NAME
                or callable_path
                != f"{module_name}.{class_name}.{APPROVED_CALLABLE_NAME}"
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
                    "INT-OIA-006 callable identity inconsistent"
                )

            required_contract = {
                "exact_callable_identity_required": True,
                "dynamic_import_allowed": False,
                "callable_resolution_allowed": False,
                "callable_binding_allowed": False,
                "callable_invocation_allowed": False,
                "callable_resolution_performed": False,
                "callable_binding_performed": False,
                "callable_invocation_performed": False,
                "corpus_read_allowed": False,
                "source_mutation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "binding_status": "contract_issued_not_resolved",
            }
            for field, expected in required_contract.items():
                if contract.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError(
                        f"unsafe INT-OIA-006 binding-contract field: {field}"
                    )

        payload["binding_contracts"] = contracts
        return payload

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessManifest:
        evaluated_at = _aware(evaluated_at, "evaluated_at")
        source = self._load_binding()

        records: list[
            DownstreamReadOnlyConsumerCallableResolutionReadinessRecord
        ] = []

        for sequence, contract in enumerate(
            source["binding_contracts"],
            start=1,
        ):
            identity = {
                "source_binding_manifest_id": source["binding_manifest_id"],
                "source_binding_contract_id": contract[
                    "binding_contract_id"
                ],
                "source_binding_contract_hash": contract[
                    "binding_contract_hash"
                ],
                "consumer_id": contract["consumer_id"],
                "callable_path": contract["callable_path"],
                "evaluated_at": evaluated_at.isoformat(),
            }
            readiness_id = stable_hash(identity)

            body = {
                "sequence": sequence,
                "resolution_readiness_id": readiness_id,
                "consumer_id": contract["consumer_id"],
                "consumer_module": contract["consumer_module"],
                "consumer_class": contract["consumer_class"],
                "callable_name": contract["callable_name"],
                "callable_path": contract["callable_path"],
                "source_binding_contract_id": contract[
                    "binding_contract_id"
                ],
                "source_binding_contract_hash": contract[
                    "binding_contract_hash"
                ],
                "source_activation_id": contract["source_activation_id"],
                "source_activation_nonce": contract[
                    "source_activation_nonce"
                ],
                "source_boundary_id": contract["source_boundary_id"],
                "source_boundary_hash": contract["source_boundary_hash"],
                "module_identity_valid": True,
                "class_identity_valid": True,
                "callable_identity_valid": True,
                "callable_path_consistent": True,
                "exact_identity_hash_verified": True,
                "dynamic_import_allowed": False,
                "module_import_performed": False,
                "callable_resolution_allowed": True,
                "callable_resolution_performed": False,
                "callable_binding_allowed": False,
                "callable_binding_performed": False,
                "callable_invocation_allowed": False,
                "callable_invocation_performed": False,
                "corpus_read_allowed": False,
                "source_mutation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "controlled_resolution_authorized": True,
                "readiness_status": "ready_for_controlled_resolution",
            }
            records.append(
                DownstreamReadOnlyConsumerCallableResolutionReadinessRecord(
                    **body,
                    resolution_readiness_record_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_binding_manifest_id": source["binding_manifest_id"],
                "source_binding_manifest_hash": source[
                    "binding_manifest_hash"
                ],
                "evaluated_at": evaluated_at.isoformat(),
                "readiness_record_hashes": [
                    record.resolution_readiness_record_hash
                    for record in records
                ],
            }
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at.isoformat(),
            "resolution_readiness_manifest_id": manifest_id,
            "resolution_readiness_status": STATUS_READY,
            "resolution_readiness_policy_id": POLICY_ID,
            "source_binding_manifest_id": source["binding_manifest_id"],
            "source_binding_manifest_hash": source[
                "binding_manifest_hash"
            ],
            "source_activation_manifest_id": source[
                "source_activation_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "readiness_record_count": len(records),
            "readiness_records": tuple(records),
            "all_binding_hashes_verified": True,
            "all_callable_paths_consistent": True,
            "exact_callable_identity_preserved": True,
            "source_boundary_consumed_without_reexecution": True,
            "dynamic_import_allowed": False,
            "module_import_performed": False,
            "callable_resolution_allowed": True,
            "callable_resolution_performed": False,
            "callable_binding_allowed": False,
            "callable_binding_performed": False,
            "callable_invocation_allowed": False,
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
            "controlled_callable_resolution_authorized": True,
            "readiness_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["readiness_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessManifest(
            **body,
            resolution_readiness_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.readiness_directory / "current.json", payload)
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
                    / f"{record.resolution_readiness_id}.json",
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

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_callable_resolution_readiness_gate import (
    APPROVED_CALLABLE_NAME,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError,
    stable_hash,
)


def _seed_binding(path: Path) -> None:
    contract = {
        "sequence": 1,
        "binding_contract_id": "binding-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer"
        ),
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": APPROVED_CALLABLE_NAME,
        "callable_path": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer."
            "OracleResearchAnalyticsConsumer."
            "analyze_certified_oia_artifacts"
        ),
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"nonce": 1}),
        "source_activation_record_hash": stable_hash({"activation": 1}),
        "source_contract_id": "contract-test",
        "source_contract_hash": stable_hash({"contract": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "authorized_capabilities": [
            "perform_read_only_research_analysis",
            "persist_research_analysis_artifacts",
            "read_certified_invocation_results",
            "read_certified_oia_boundary",
            "read_certified_result_summaries",
        ],
        "exact_callable_identity_required": True,
        "dynamic_import_allowed": False,
        "callable_resolution_allowed": False,
        "callable_binding_allowed": False,
        "callable_invocation_allowed": False,
        "callable_resolution_performed": False,
        "callable_binding_performed": False,
        "callable_invocation_performed": False,
        "corpus_read_allowed": False,
        "source_mutation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "binding_status": "contract_issued_not_resolved",
    }
    contract["binding_contract_hash"] = stable_hash(contract)

    manifest = {
        "schema_version": "INT-OIA-006",
        "engine_id": "INT-OIA-006",
        "issued_at": "2026-07-22T00:00:00+00:00",
        "binding_manifest_id": "int-oia-006-test",
        "source_activation_manifest_id": "int-oia-005-test",
        "source_activation_manifest_hash": stable_hash({"int": 5}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "binding_contract_count": 1,
        "binding_contracts": [contract],
        "all_activation_hashes_verified": True,
        "all_activation_nonces_unique": True,
        "exact_consumer_identity_preserved": True,
        "exact_callable_identity_frozen": True,
        "source_boundary_consumed_without_reexecution": True,
        "corpus_read_execution_repeated": False,
        "callable_resolution_allowed": False,
        "callable_binding_allowed": False,
        "callable_invocation_allowed": False,
        "callable_resolution_performed": False,
        "callable_binding_performed": False,
        "callable_invocation_performed": False,
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
        "binding_artifact_persistence_allowed": True,
    }
    manifest["binding_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-007 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CALLABLE RESOLUTION READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        binding = root / "binding"
        readiness = root / "readiness"
        _seed_binding(binding)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessGate(
            binding_directory=binding,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-007"
        assert first.readiness_record_count == 1
        assert first.all_binding_hashes_verified
        assert first.all_callable_paths_consistent
        assert first.exact_callable_identity_preserved
        assert first.source_boundary_consumed_without_reexecution
        assert not first.dynamic_import_allowed
        assert not first.module_import_performed
        assert first.callable_resolution_allowed
        assert not first.callable_resolution_performed
        assert not first.callable_binding_allowed
        assert not first.callable_binding_performed
        assert not first.callable_invocation_allowed
        assert not first.callable_invocation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.controlled_callable_resolution_authorized
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.readiness_records[0]
        assert record.module_identity_valid
        assert record.class_identity_valid
        assert record.callable_identity_valid
        assert record.callable_path_consistent
        assert record.exact_identity_hash_verified
        assert record.controlled_resolution_authorized
        assert not record.module_import_performed
        assert not record.callable_resolution_performed
        assert not record.callable_binding_performed
        assert not record.callable_invocation_performed

        assert (readiness / "current.json").exists()

        tampered = json.loads(
            (binding / "current.json").read_text(encoding="utf-8")
        )
        tampered["binding_contracts"][0][
            "callable_path"
        ] = "unsafe.module.UnsafeClass.execute"
        (binding / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.evaluate(evaluated_at=fixed, persist=False)
            raise AssertionError("tampered binding accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError:
            pass

    print("[PASS] Actual INT-OIA-006 binding contract consumed")
    print("[PASS] Every binding-contract hash independently verified")
    print("[PASS] Exact module, class, callable, and path identity verified")
    print("[PASS] Callable path consistency verified")
    print("[PASS] Controlled callable resolution authorized")
    print("[PASS] No dynamic import or module import performed")
    print("[PASS] No callable resolution, binding, or invocation performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe binding evidence rejected")
    print("[PASS] Atomic resolution-readiness artifacts persisted")
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
    path.write_text(source.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def verify_int_oia_006_contract() -> None:
    if not INT_OIA_006.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-006 production module missing: {INT_OIA_006}"
        )
    source = INT_OIA_006.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-006"',
        "class DownstreamReadOnlyConsumerCallableBindingContract",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingContractGate",
        "binding_manifest_hash",
        "exact_callable_identity_frozen",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-006 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-006 callable-binding contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export_line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_callable_resolution_readiness_gate import *"
    )
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        PACKAGE.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-007 INSTALLER")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CALLABLE RESOLUTION READINESS")
    print("=" * 40)

    verify_int_oia_006_contract()
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

    print("[OK] INT-OIA-007 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-007 downstream read-only consumer "
        "callable resolution readiness gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
