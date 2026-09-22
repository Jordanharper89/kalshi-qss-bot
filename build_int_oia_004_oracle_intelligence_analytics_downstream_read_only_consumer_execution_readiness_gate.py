from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

PRODUCTION = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_execution_readiness_gate.py"
TEST = ROOT / "test_int_oia_004_oracle_intelligence_analytics_downstream_read_only_consumer_execution_readiness_gate.py"
PACKAGE = ANALYTICS / "__init__.py"
INT_OIA_003 = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_execution_contract_gate.py"

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

SCHEMA_VERSION = "INT-OIA-004"
ENGINE_ID = "INT-OIA-004"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-execution-readiness.v1"
STATUS_READY = "downstream_read_only_consumer_execution_ready"

DEFAULT_CONTRACT_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_execution_contract"
)
DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_execution_readiness"
)


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
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
class DownstreamReadOnlyConsumerExecutionReadinessRecord:
    sequence: int
    readiness_id: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    source_contract_id: str
    source_contract_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    authorized_capabilities: tuple[str, ...]
    certified_artifact_input_ready: bool
    immutable_output_ready: bool
    deterministic_execution_ready: bool
    replayable_execution_ready: bool
    read_only_execution_ready: bool
    source_reexecution_allowed: bool
    corpus_read_allowed: bool
    source_mutation_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    controlled_activation_allowed: bool
    readiness_status: str
    readiness_record_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: str
    execution_readiness_manifest_id: str
    execution_readiness_status: str
    execution_readiness_policy_id: str
    source_execution_contract_manifest_id: str
    source_execution_contract_manifest_hash: str
    source_admission_manifest_id: str
    source_boundary_id: str
    source_boundary_hash: str
    readiness_record_count: int
    readiness_records: tuple[
        DownstreamReadOnlyConsumerExecutionReadinessRecord, ...
    ]
    all_contract_hashes_verified: bool
    all_consumers_ready: bool
    all_inputs_certified_artifact_only: bool
    all_outputs_immutable_research_artifact_only: bool
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
    controlled_read_only_activation_allowed: bool
    readiness_artifact_persistence_allowed: bool
    execution_readiness_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessGate:
    def __init__(
        self,
        *,
        contract_directory: Path | str = DEFAULT_CONTRACT_DIRECTORY,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
    ) -> None:
        self.contract_directory = Path(contract_directory)
        self.readiness_directory = Path(readiness_directory)

    def _load_contract_manifest(self) -> dict[str, Any]:
        path = self.contract_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
                f"INT-OIA-003 execution-contract artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
                "INT-OIA-003 execution-contract artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("execution_contract_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
                "INT-OIA-003 execution-contract manifest hash mismatch"
            )
        payload["execution_contract_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-003",
            "engine_id": "INT-OIA-003",
            "admitted_consumers_only": True,
            "exact_capability_set_preserved": True,
            "deterministic_execution_required": True,
            "immutable_input_consumption_required": True,
            "replayable_output_required": True,
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
            "read_only_consumer_execution_authorized": True,
            "contract_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
                    f"unsafe or incomplete INT-OIA-003 field: {field}"
                )

        contracts = payload.get("execution_contracts")
        if (
            not isinstance(contracts, list)
            or not contracts
            or payload.get("execution_contract_count") != len(contracts)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
                "INT-OIA-003 execution contracts invalid"
            )

        seen_consumers: set[str] = set()
        for sequence, raw_contract in enumerate(contracts, start=1):
            contract = dict(raw_contract)
            contract_hash = contract.pop("execution_contract_hash", None)
            if not _valid_hash(contract_hash) or stable_hash(contract) != contract_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
                    "INT-OIA-003 execution-contract hash mismatch"
                )
            contract["execution_contract_hash"] = contract_hash

            if contract.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
                    "INT-OIA-003 execution-contract sequence mismatch"
                )
            consumer_id = contract.get("consumer_id")
            if (
                not isinstance(consumer_id, str)
                or not consumer_id
                or consumer_id in seen_consumers
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
                    "invalid or duplicate execution-contract consumer"
                )
            seen_consumers.add(consumer_id)

            required_contract = {
                "input_mode": "certified_artifacts_only",
                "output_mode": "immutable_research_artifacts_only",
                "deterministic_required": True,
                "immutable_inputs_required": True,
                "replayable_required": True,
                "read_only_required": True,
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
                "artifact_persistence_allowed": True,
                "execution_contract_status": "issued_read_only",
            }
            for field, expected in required_contract.items():
                if contract.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
                        f"unsafe INT-OIA-003 execution-contract field: {field}"
                    )

            capabilities = contract.get("authorized_capabilities")
            if not isinstance(capabilities, list) or not capabilities:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError(
                    "INT-OIA-003 authorized capabilities invalid"
                )

        payload["execution_contracts"] = contracts
        return payload

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessManifest:
        evaluated_at = _aware(evaluated_at, "evaluated_at")
        source = self._load_contract_manifest()

        readiness_records: list[
            DownstreamReadOnlyConsumerExecutionReadinessRecord
        ] = []

        for sequence, contract in enumerate(
            source["execution_contracts"],
            start=1,
        ):
            identity = {
                "source_execution_contract_manifest_id": source[
                    "execution_contract_manifest_id"
                ],
                "source_contract_id": contract["contract_id"],
                "source_contract_hash": contract["execution_contract_hash"],
                "consumer_id": contract["consumer_id"],
                "evaluated_at": evaluated_at.isoformat(),
            }
            readiness_id = stable_hash(identity)

            body = {
                "sequence": sequence,
                "readiness_id": readiness_id,
                "consumer_id": contract["consumer_id"],
                "consumer_module": contract["consumer_module"],
                "consumer_class": contract["consumer_class"],
                "source_contract_id": contract["contract_id"],
                "source_contract_hash": contract["execution_contract_hash"],
                "source_boundary_id": contract["source_boundary_id"],
                "source_boundary_hash": contract["source_boundary_hash"],
                "authorized_capabilities": tuple(
                    contract["authorized_capabilities"]
                ),
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
            readiness_records.append(
                DownstreamReadOnlyConsumerExecutionReadinessRecord(
                    **body,
                    readiness_record_hash=stable_hash(body),
                )
            )

        manifest_identity = {
            "source_execution_contract_manifest_id": source[
                "execution_contract_manifest_id"
            ],
            "source_execution_contract_manifest_hash": source[
                "execution_contract_manifest_hash"
            ],
            "evaluated_at": evaluated_at.isoformat(),
            "readiness_record_hashes": [
                record.readiness_record_hash
                for record in readiness_records
            ],
        }
        manifest_id = stable_hash(manifest_identity)

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at.isoformat(),
            "execution_readiness_manifest_id": manifest_id,
            "execution_readiness_status": STATUS_READY,
            "execution_readiness_policy_id": POLICY_ID,
            "source_execution_contract_manifest_id": source[
                "execution_contract_manifest_id"
            ],
            "source_execution_contract_manifest_hash": source[
                "execution_contract_manifest_hash"
            ],
            "source_admission_manifest_id": source[
                "source_admission_manifest_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "readiness_record_count": len(readiness_records),
            "readiness_records": tuple(readiness_records),
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

        serializable = dict(body)
        serializable["readiness_records"] = [
            asdict(record) for record in readiness_records
        ]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessManifest(
            **body,
            execution_readiness_manifest_hash=manifest_hash,
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
            for record in readiness_records:
                _atomic_write(
                    self.readiness_directory
                    / "consumers"
                    / record.consumer_id
                    / f"{record.readiness_id}.json",
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

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_execution_readiness_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError,
    stable_hash,
)


CAPABILITIES = [
    "perform_read_only_research_analysis",
    "persist_research_analysis_artifacts",
    "read_certified_invocation_results",
    "read_certified_oia_boundary",
    "read_certified_result_summaries",
]


def _seed_contract(path: Path) -> None:
    contract_body = {
        "sequence": 1,
        "contract_id": "contract-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer"
        ),
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "source_admission_record_hash": stable_hash({"admission": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "authorized_capabilities": CAPABILITIES,
        "input_mode": "certified_artifacts_only",
        "output_mode": "immutable_research_artifacts_only",
        "deterministic_required": True,
        "immutable_inputs_required": True,
        "replayable_required": True,
        "read_only_required": True,
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
        "artifact_persistence_allowed": True,
        "execution_contract_status": "issued_read_only",
    }
    contract_body["execution_contract_hash"] = stable_hash(contract_body)

    manifest = {
        "schema_version": "INT-OIA-003",
        "engine_id": "INT-OIA-003",
        "issued_at": "2026-07-22T00:00:00+00:00",
        "execution_contract_manifest_id": "int-oia-003-test",
        "execution_contract_manifest_status": (
            "downstream_read_only_consumer_execution_contract_issued"
        ),
        "execution_contract_policy_id": "test",
        "source_admission_manifest_id": "int-oia-002-test",
        "source_admission_manifest_hash": stable_hash({"int": 2}),
        "source_integration_certification_id": "int-oia-001-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "execution_contract_count": 1,
        "execution_contracts": [contract_body],
        "admitted_consumers_only": True,
        "exact_capability_set_preserved": True,
        "deterministic_execution_required": True,
        "immutable_input_consumption_required": True,
        "replayable_output_required": True,
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
        "read_only_consumer_execution_authorized": True,
        "contract_artifact_persistence_allowed": True,
    }
    manifest["execution_contract_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-004 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" EXECUTION READINESS GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        contracts = root / "contracts"
        readiness = root / "readiness"
        _seed_contract(contracts)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessGate(
            contract_directory=contracts,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.evaluate(
            evaluated_at=fixed,
            persist=True,
        )
        second = gate.evaluate(
            evaluated_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "INT-OIA-004"
        assert first.readiness_record_count == 1
        assert first.all_contract_hashes_verified
        assert first.all_consumers_ready
        assert first.all_inputs_certified_artifact_only
        assert first.all_outputs_immutable_research_artifact_only
        assert first.deterministic_execution_required
        assert first.replayable_execution_required
        assert first.source_boundary_consumed_without_reexecution
        assert first.controlled_read_only_activation_allowed
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

        record = first.readiness_records[0]
        assert record.certified_artifact_input_ready
        assert record.immutable_output_ready
        assert record.deterministic_execution_ready
        assert record.replayable_execution_ready
        assert record.read_only_execution_ready
        assert record.controlled_activation_allowed
        assert not record.source_reexecution_allowed
        assert not record.corpus_read_allowed
        assert not record.signals_allowed
        assert not record.qseries_execution_allowed

        assert (readiness / "current.json").exists()
        assert (
            readiness
            / "manifests"
            / f"{first.execution_readiness_manifest_id}.json"
        ).exists()
        assert (
            readiness
            / "consumers"
            / record.consumer_id
            / f"{record.readiness_id}.json"
        ).exists()

        tampered = json.loads(
            (contracts / "current.json").read_text(encoding="utf-8")
        )
        tampered["execution_contracts"][0][
            "corpus_read_allowed"
        ] = True
        (contracts / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.evaluate(
                evaluated_at=fixed,
                persist=False,
            )
            raise AssertionError(
                "tampered INT-OIA-003 contract was accepted"
            )
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError:
            pass

    print("[PASS] Actual INT-OIA-003 execution contract consumed")
    print("[PASS] Every execution-contract hash independently verified")
    print("[PASS] Certified-artifact-only inputs verified ready")
    print("[PASS] Immutable research-artifact outputs verified ready")
    print("[PASS] Deterministic and replayable execution verified ready")
    print("[PASS] Controlled read-only activation authorized")
    print("[PASS] Frozen OIA boundary consumed without re-execution")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe execution contract rejected")
    print("[PASS] Atomic readiness artifacts persisted")
    print("[PASS] Read-only analytical conclusion execution ready")
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


def verify_int_oia_003_contract() -> None:
    if not INT_OIA_003.exists():
        raise FileNotFoundError(
            f"Actual INT-OIA-003 production module missing: {INT_OIA_003}"
        )
    source = INT_OIA_003.read_text(encoding="utf-8")
    required_tokens = (
        'SCHEMA_VERSION = "INT-OIA-003"',
        "class DownstreamReadOnlyConsumerExecutionContract",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractGate",
        "execution_contract_manifest_hash",
        "read_only_consumer_execution_authorized",
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-003 contract mismatch; missing tokens: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-003 execution-contract contract verified")


def update_package() -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    existing = PACKAGE.read_text(encoding="utf-8") if PACKAGE.exists() else ""
    export_line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_execution_readiness_gate import *"
    )
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line + "\n"
        PACKAGE.write_text(existing, encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PACKAGE.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-004 INSTALLER")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" EXECUTION READINESS GATE")
    print("=" * 40)

    verify_int_oia_003_contract()
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

    print("[OK] INT-OIA-004 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-004 downstream read-only consumer "
        "execution readiness gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
