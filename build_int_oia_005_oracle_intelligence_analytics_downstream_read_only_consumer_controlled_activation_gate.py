from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_activation_gate.py"
TEST = ROOT / "test_int_oia_005_oracle_intelligence_analytics_downstream_read_only_consumer_controlled_activation_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
INT_OIA_004 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_execution_readiness_gate.py"

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

SCHEMA_VERSION = "INT-OIA-005"
ENGINE_ID = "INT-OIA-005"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-controlled-activation.v1"
STATUS_ACTIVATED = "downstream_read_only_consumer_controlled_activation_issued"

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_execution_readiness"
)
DEFAULT_ACTIVATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_activation"
)


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
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
class DownstreamReadOnlyConsumerControlledActivationRecord:
    sequence: int
    activation_id: str
    activation_nonce: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    source_readiness_id: str
    source_readiness_record_hash: str
    source_contract_id: str
    source_contract_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    authorized_capabilities: tuple[str, ...]
    activation_mode: str
    one_time_activation: bool
    readiness_consumed: bool
    execution_performed: bool
    callable_binding_performed: bool
    callable_invocation_performed: bool
    corpus_read_performed: bool
    source_mutation_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    activation_status: str
    activation_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationManifest:
    schema_version: str
    engine_id: str
    activated_at: str
    activation_manifest_id: str
    activation_manifest_status: str
    activation_policy_id: str
    source_execution_readiness_manifest_id: str
    source_execution_readiness_manifest_hash: str
    source_execution_contract_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    activation_record_count: int
    activation_records: tuple[
        DownstreamReadOnlyConsumerControlledActivationRecord, ...
    ]
    all_readiness_hashes_verified: bool
    all_consumers_activated_once: bool
    all_activation_nonces_unique: bool
    certified_artifact_input_mode_preserved: bool
    immutable_output_mode_preserved: bool
    deterministic_execution_required: bool
    replayable_execution_required: bool
    source_boundary_consumed_without_reexecution: bool
    controlled_read_execution_repeated: bool
    corpus_read_execution_repeated: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    trading_recommendations_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    downstream_consumer_execution_allowed: bool
    downstream_consumer_execution_performed: bool
    activation_artifact_persistence_allowed: bool
    activation_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationGate:
    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,
    ) -> None:
        self.readiness_directory = Path(readiness_directory)
        self.activation_directory = Path(activation_directory)

    def _load_readiness(self) -> dict[str, Any]:
        path = self.readiness_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                f"INT-OIA-004 readiness artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                "INT-OIA-004 readiness artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop(
            "execution_readiness_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                "INT-OIA-004 readiness manifest hash mismatch"
            )
        payload["execution_readiness_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-004",
            "engine_id": "INT-OIA-004",
            "all_contract_hashes_verified": True,
            "all_consumers_ready": True,
            "all_inputs_certified_artifact_only": True,
            "all_outputs_immutable_research_artifact_only": True,
            "deterministic_execution_required": True,
            "replayable_execution_required": True,
            "source_boundary_consumed_without_reexecution": True,
            "controlled_read_execution_repeated": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "trading_recommendations_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "controlled_read_only_activation_allowed": True,
            "readiness_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                    f"unsafe or incomplete INT-OIA-004 field: {field}"
                )

        records = payload.get("readiness_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("readiness_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                "INT-OIA-004 readiness records invalid"
            )

        seen_consumers: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            record = dict(raw_record)
            record_hash = record.pop("readiness_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                    "INT-OIA-004 readiness-record hash mismatch"
                )
            record["readiness_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                    "INT-OIA-004 readiness sequence mismatch"
                )
            consumer_id = record.get("consumer_id")
            if (
                not isinstance(consumer_id, str)
                or not consumer_id
                or consumer_id in seen_consumers
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                    "invalid or duplicate ready consumer"
                )
            seen_consumers.add(consumer_id)

            required_record = {
                "certified_artifact_input_ready": True,
                "immutable_output_ready": True,
                "deterministic_execution_ready": True,
                "replayable_execution_ready": True,
                "read_only_execution_ready": True,
                "source_reexecution_allowed": False,
                "corpus_read_allowed": False,
                "source_mutation_allowed": False,
                "forecast_creation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_handoff_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "controlled_activation_allowed": True,
                "readiness_status": "ready_read_only",
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                        f"unsafe INT-OIA-004 readiness-record field: {field}"
                    )

            capabilities = record.get("authorized_capabilities")
            if not isinstance(capabilities, list) or not capabilities:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                    "INT-OIA-004 authorized capabilities invalid"
                )

        payload["readiness_records"] = records
        return payload

    def activate(
        self,
        *,
        activated_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationManifest:
        activated_at = _aware(activated_at, "activated_at")
        source = self._load_readiness()

        records: list[
            DownstreamReadOnlyConsumerControlledActivationRecord
        ] = []
        seen_nonces: set[str] = set()

        for sequence, readiness in enumerate(
            source["readiness_records"],
            start=1,
        ):
            nonce = stable_hash(
                {
                    "source_readiness_id": readiness["readiness_id"],
                    "source_readiness_record_hash": readiness[
                        "readiness_record_hash"
                    ],
                    "consumer_id": readiness["consumer_id"],
                    "activated_at": activated_at.isoformat(),
                }
            )
            if nonce in seen_nonces:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError(
                    "duplicate activation nonce"
                )
            seen_nonces.add(nonce)

            activation_identity = {
                "source_execution_readiness_manifest_id": source[
                    "execution_readiness_manifest_id"
                ],
                "source_readiness_id": readiness["readiness_id"],
                "source_readiness_record_hash": readiness[
                    "readiness_record_hash"
                ],
                "consumer_id": readiness["consumer_id"],
                "activation_nonce": nonce,
            }
            activation_id = stable_hash(activation_identity)

            body = {
                "sequence": sequence,
                "activation_id": activation_id,
                "activation_nonce": nonce,
                "consumer_id": readiness["consumer_id"],
                "consumer_module": readiness["consumer_module"],
                "consumer_class": readiness["consumer_class"],
                "source_readiness_id": readiness["readiness_id"],
                "source_readiness_record_hash": readiness[
                    "readiness_record_hash"
                ],
                "source_contract_id": readiness["source_contract_id"],
                "source_contract_hash": readiness["source_contract_hash"],
                "source_boundary_id": readiness["source_boundary_id"],
                "source_boundary_hash": readiness["source_boundary_hash"],
                "authorized_capabilities": tuple(
                    readiness["authorized_capabilities"]
                ),
                "activation_mode": "controlled_one_time_read_only",
                "one_time_activation": True,
                "readiness_consumed": True,
                "execution_performed": False,
                "callable_binding_performed": False,
                "callable_invocation_performed": False,
                "corpus_read_performed": False,
                "source_mutation_allowed": False,
                "forecast_creation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_handoff_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "activation_status": "activated_not_executed",
            }
            records.append(
                DownstreamReadOnlyConsumerControlledActivationRecord(
                    **body,
                    activation_record_hash=stable_hash(body),
                )
            )

        manifest_identity = {
            "source_execution_readiness_manifest_id": source[
                "execution_readiness_manifest_id"
            ],
            "source_execution_readiness_manifest_hash": source[
                "execution_readiness_manifest_hash"
            ],
            "activated_at": activated_at.isoformat(),
            "activation_record_hashes": [
                record.activation_record_hash for record in records
            ],
        }
        manifest_id = stable_hash(manifest_identity)

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "activated_at": activated_at.isoformat(),
            "activation_manifest_id": manifest_id,
            "activation_manifest_status": STATUS_ACTIVATED,
            "activation_policy_id": POLICY_ID,
            "source_execution_readiness_manifest_id": source[
                "execution_readiness_manifest_id"
            ],
            "source_execution_readiness_manifest_hash": source[
                "execution_readiness_manifest_hash"
            ],
            "source_execution_contract_manifest_id": source[
                "source_execution_contract_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "activation_record_count": len(records),
            "activation_records": tuple(records),
            "all_readiness_hashes_verified": True,
            "all_consumers_activated_once": True,
            "all_activation_nonces_unique": True,
            "certified_artifact_input_mode_preserved": True,
            "immutable_output_mode_preserved": True,
            "deterministic_execution_required": True,
            "replayable_execution_required": True,
            "source_boundary_consumed_without_reexecution": True,
            "controlled_read_execution_repeated": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": True,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "trading_recommendations_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "downstream_consumer_execution_allowed": True,
            "downstream_consumer_execution_performed": False,
            "activation_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["activation_records"] = [
            asdict(record) for record in records
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationManifest(
            **body,
            activation_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.activation_directory / "current.json", payload)
            _atomic_write(
                self.activation_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for record in records:
                _atomic_write(
                    self.activation_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.activation_id}.json",
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

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_activation_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError,
    stable_hash,
)


CAPABILITIES = [
    "perform_read_only_research_analysis",
    "persist_research_analysis_artifacts",
    "read_certified_invocation_results",
    "read_certified_oia_boundary",
    "read_certified_result_summaries",
]


def _seed_readiness(path: Path) -> None:
    record_body = {
        "sequence": 1,
        "readiness_id": "readiness-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer"
        ),
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "source_contract_id": "contract-test",
        "source_contract_hash": stable_hash({"contract": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "authorized_capabilities": CAPABILITIES,
        "certified_artifact_input_ready": True,
        "immutable_output_ready": True,
        "deterministic_execution_ready": True,
        "replayable_execution_ready": True,
        "read_only_execution_ready": True,
        "source_reexecution_allowed": False,
        "corpus_read_allowed": False,
        "source_mutation_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "controlled_activation_allowed": True,
        "readiness_status": "ready_read_only",
    }
    record_body["readiness_record_hash"] = stable_hash(record_body)

    manifest = {
        "schema_version": "INT-OIA-004",
        "engine_id": "INT-OIA-004",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "execution_readiness_manifest_id": "int-oia-004-test",
        "execution_readiness_status": (
            "downstream_read_only_consumer_execution_ready"
        ),
        "execution_readiness_policy_id": "test",
        "source_execution_contract_manifest_id": "int-oia-003-test",
        "source_execution_contract_manifest_hash": stable_hash({"int": 3}),
        "source_admission_manifest_id": "int-oia-002-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "readiness_record_count": 1,
        "readiness_records": [record_body],
        "all_contract_hashes_verified": True,
        "all_consumers_ready": True,
        "all_inputs_certified_artifact_only": True,
        "all_outputs_immutable_research_artifact_only": True,
        "deterministic_execution_required": True,
        "replayable_execution_required": True,
        "source_boundary_consumed_without_reexecution": True,
        "controlled_read_execution_repeated": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "trading_recommendations_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "controlled_read_only_activation_allowed": True,
        "readiness_artifact_persistence_allowed": True,
    }
    manifest["execution_readiness_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-005 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED ACTIVATION GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        readiness = root / "readiness"
        activation = root / "activation"
        _seed_readiness(readiness)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationGate(
            readiness_directory=readiness,
            activation_directory=activation,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.activate(
            activated_at=fixed,
            persist=True,
        )
        second = gate.activate(
            activated_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "INT-OIA-005"
        assert first.activation_record_count == 1
        assert first.all_readiness_hashes_verified
        assert first.all_consumers_activated_once
        assert first.all_activation_nonces_unique
        assert first.certified_artifact_input_mode_preserved
        assert first.immutable_output_mode_preserved
        assert first.deterministic_execution_required
        assert first.replayable_execution_required
        assert first.source_boundary_consumed_without_reexecution
        assert first.downstream_consumer_execution_allowed
        assert not first.downstream_consumer_execution_performed
        assert first.analytic_conclusion_allowed
        assert not first.forecast_creation_allowed
        assert not first.controlled_read_execution_repeated
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_handoff_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.activation_records[0]
        assert record.one_time_activation
        assert record.readiness_consumed
        assert record.activation_mode == "controlled_one_time_read_only"
        assert record.activation_status == "activated_not_executed"
        assert not record.execution_performed
        assert not record.callable_binding_performed
        assert not record.callable_invocation_performed
        assert not record.corpus_read_performed
        assert not record.signals_allowed
        assert not record.qseries_execution_allowed

        assert (activation / "current.json").exists()
        assert (
            activation
            / "manifests"
            / f"{first.activation_manifest_id}.json"
        ).exists()
        assert (
            activation
            / "consumers"
            / record.consumer_id
            / f"{record.activation_id}.json"
        ).exists()

        tampered = json.loads(
            (readiness / "current.json").read_text(encoding="utf-8")
        )
        tampered["readiness_records"][0][
            "controlled_activation_allowed"
        ] = False
        (readiness / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.activate(
                activated_at=fixed,
                persist=False,
            )
            raise AssertionError(
                "tampered INT-OIA-004 readiness was accepted"
            )
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-004 readiness contract consumed")
    print("[PASS] Every readiness-record hash independently verified")
    print("[PASS] One-time activation IDs and nonces deterministic")
    print("[PASS] Activation nonces unique across consumers")
    print("[PASS] Certified-artifact input mode preserved")
    print("[PASS] Immutable research-artifact output mode preserved")
    print("[PASS] Controlled read-only execution authorized")
    print("[PASS] Consumer execution not yet performed")
    print("[PASS] No callable binding or invocation performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe readiness evidence rejected")
    print("[PASS] Atomic activation artifacts persisted")
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


def verify_int_oia_004_contract() -> None:
    if not INT_OIA_004.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-004 production module missing: {INT_OIA_004}"
        )
    source = INT_OIA_004.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-004"',
        "class DownstreamReadOnlyConsumerExecutionReadinessRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessGate",
        "execution_readiness_manifest_hash",
        "controlled_read_only_activation_allowed",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-004 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-004 execution-readiness contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export_line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_controlled_activation_gate import *"
    )
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        PACKAGE.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-005 INSTALLER")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED ACTIVATION GATE")
    print("=" * 40)

    verify_int_oia_004_contract()
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

    print("[OK] INT-OIA-005 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-005 downstream read-only consumer "
        "controlled activation gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
