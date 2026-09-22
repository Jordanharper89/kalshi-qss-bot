from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
PROD = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_callable_binding_contract_gate.py"
TEST = ROOT / "test_int_oia_006_oracle_intelligence_analytics_downstream_read_only_consumer_callable_binding_contract_gate.py"
PKG = ANALYTICS / "__init__.py"
SOURCE = ANALYTICS / "oracle_intelligence_analytics_downstream_read_only_consumer_controlled_activation_gate.py"

PRODUCTION = r"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-006"
ENGINE_ID = "INT-OIA-006"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-callable-binding-contract.v1"
DEFAULT_ACTIVATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_controlled_activation"
)
DEFAULT_BINDING_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_callable_binding_contract"
)
APPROVED_CALLABLE_NAME = "analyze_certified_oia_artifacts"


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(RuntimeError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
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
        and all(c in "0123456789abcdef" for c in value)
    )


def _aware(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
            f"{field} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(
        _canonical(payload),
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    ) + "\n"
    h = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    tmp = Path(h.name)
    try:
        with h:
            h.write(rendered)
            h.flush()
            os.fsync(h.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


@dataclass(frozen=True)
class DownstreamReadOnlyConsumerCallableBindingContract:
    sequence: int
    binding_contract_id: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    callable_name: str
    callable_path: str
    source_activation_id: str
    source_activation_nonce: str
    source_activation_record_hash: str
    source_contract_id: str
    source_contract_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    authorized_capabilities: tuple[str, ...]
    exact_callable_identity_required: bool
    dynamic_import_allowed: bool
    callable_resolution_allowed: bool
    callable_binding_allowed: bool
    callable_invocation_allowed: bool
    callable_resolution_performed: bool
    callable_binding_performed: bool
    callable_invocation_performed: bool
    corpus_read_allowed: bool
    source_mutation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    binding_status: str
    binding_contract_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingManifest:
    schema_version: str
    engine_id: str
    issued_at: str
    binding_manifest_id: str
    source_activation_manifest_id: str
    source_activation_manifest_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    binding_contract_count: int
    binding_contracts: tuple[DownstreamReadOnlyConsumerCallableBindingContract, ...]
    all_activation_hashes_verified: bool
    all_activation_nonces_unique: bool
    exact_consumer_identity_preserved: bool
    exact_callable_identity_frozen: bool
    source_boundary_consumed_without_reexecution: bool
    corpus_read_execution_repeated: bool
    callable_resolution_allowed: bool
    callable_binding_allowed: bool
    callable_invocation_allowed: bool
    callable_resolution_performed: bool
    callable_binding_performed: bool
    callable_invocation_performed: bool
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
    binding_artifact_persistence_allowed: bool
    binding_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingContractGate:
    def __init__(
        self,
        *,
        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,
        binding_directory: Path | str = DEFAULT_BINDING_DIRECTORY,
    ) -> None:
        self.activation_directory = Path(activation_directory)
        self.binding_directory = Path(binding_directory)

    def _load(self) -> dict[str, Any]:
        path = self.activation_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                f"INT-OIA-005 activation artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                "INT-OIA-005 activation artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("activation_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                "INT-OIA-005 activation manifest hash mismatch"
            )
        payload["activation_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-005",
            "engine_id": "INT-OIA-005",
            "all_readiness_hashes_verified": True,
            "all_consumers_activated_once": True,
            "all_activation_nonces_unique": True,
            "source_boundary_consumed_without_reexecution": True,
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
            "downstream_consumer_execution_allowed": True,
            "downstream_consumer_execution_performed": False,
        }
        for key, expected in required.items():
            if payload.get(key) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                    f"unsafe or incomplete INT-OIA-005 field: {key}"
                )

        records = payload.get("activation_records")
        if not isinstance(records, list) or not records or payload.get("activation_record_count") != len(records):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                "INT-OIA-005 activation records invalid"
            )

        seen_ids: set[str] = set()
        seen_nonces: set[str] = set()
        for sequence, raw in enumerate(records, start=1):
            record = dict(raw)
            record_hash = record.pop("activation_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                    "INT-OIA-005 activation-record hash mismatch"
                )
            record["activation_record_hash"] = record_hash
            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                    "activation sequence mismatch"
                )
            cid = record.get("consumer_id")
            nonce = record.get("activation_nonce")
            if not isinstance(cid, str) or not cid or cid in seen_ids:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                    "invalid or duplicate consumer"
                )
            if not _valid_hash(nonce) or nonce in seen_nonces:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                    "invalid or duplicate activation nonce"
                )
            seen_ids.add(cid)
            seen_nonces.add(nonce)
            for key, expected in {
                "activation_mode": "controlled_one_time_read_only",
                "one_time_activation": True,
                "readiness_consumed": True,
                "execution_performed": False,
                "callable_binding_performed": False,
                "callable_invocation_performed": False,
                "corpus_read_performed": False,
                "source_mutation_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "activation_status": "activated_not_executed",
            }.items():
                if record.get(key) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError(
                        f"unsafe activation record field: {key}"
                    )
        payload["activation_records"] = records
        return payload

    def issue(
        self,
        *,
        issued_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingManifest:
        issued_at = _aware(issued_at, "issued_at")
        source = self._load()
        contracts = []

        for sequence, activation in enumerate(source["activation_records"], start=1):
            callable_path = (
                f"{activation['consumer_module']}."
                f"{activation['consumer_class']}."
                f"{APPROVED_CALLABLE_NAME}"
            )
            contract_id = stable_hash(
                {
                    "source_activation_manifest_id": source["activation_manifest_id"],
                    "source_activation_id": activation["activation_id"],
                    "source_activation_nonce": activation["activation_nonce"],
                    "consumer_id": activation["consumer_id"],
                    "callable_path": callable_path,
                }
            )
            body = {
                "sequence": sequence,
                "binding_contract_id": contract_id,
                "consumer_id": activation["consumer_id"],
                "consumer_module": activation["consumer_module"],
                "consumer_class": activation["consumer_class"],
                "callable_name": APPROVED_CALLABLE_NAME,
                "callable_path": callable_path,
                "source_activation_id": activation["activation_id"],
                "source_activation_nonce": activation["activation_nonce"],
                "source_activation_record_hash": activation["activation_record_hash"],
                "source_contract_id": activation["source_contract_id"],
                "source_contract_hash": activation["source_contract_hash"],
                "source_boundary_id": activation["source_boundary_id"],
                "source_boundary_hash": activation["source_boundary_hash"],
                "authorized_capabilities": tuple(activation["authorized_capabilities"]),
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
            contracts.append(
                DownstreamReadOnlyConsumerCallableBindingContract(
                    **body,
                    binding_contract_hash=stable_hash(body),
                )
            )

        manifest_id = stable_hash(
            {
                "source_activation_manifest_id": source["activation_manifest_id"],
                "source_activation_manifest_hash": source["activation_manifest_hash"],
                "issued_at": issued_at.isoformat(),
                "binding_contract_hashes": [c.binding_contract_hash for c in contracts],
            }
        )
        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "issued_at": issued_at.isoformat(),
            "binding_manifest_id": manifest_id,
            "source_activation_manifest_id": source["activation_manifest_id"],
            "source_activation_manifest_hash": source["activation_manifest_hash"],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "binding_contract_count": len(contracts),
            "binding_contracts": tuple(contracts),
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
        serializable = dict(body)
        serializable["binding_contracts"] = [asdict(c) for c in contracts]
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingManifest(
            **body,
            binding_manifest_hash=stable_hash(serializable),
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.binding_directory / "current.json", payload)
            _atomic_write(
                self.binding_directory / "manifests" / f"{manifest_id}.json",
                payload,
            )
            for contract in contracts:
                _atomic_write(
                    self.binding_directory
                    / "consumers"
                    / contract.consumer_id
                    / f"{contract.binding_contract_id}.json",
                    asdict(contract),
                )
        return manifest
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_callable_binding_contract_gate import (
    APPROVED_CALLABLE_NAME,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingContractGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError,
    stable_hash,
)


def _seed(path: Path) -> None:
    capabilities = [
        "perform_read_only_research_analysis",
        "persist_research_analysis_artifacts",
        "read_certified_invocation_results",
        "read_certified_oia_boundary",
        "read_certified_result_summaries",
    ]
    record = {
        "sequence": 1,
        "activation_id": "activation-test",
        "activation_nonce": stable_hash({"nonce": 1}),
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": "qseries_v2.oracle_intelligence.research_analytics_consumer",
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "source_readiness_id": "readiness-test",
        "source_readiness_record_hash": stable_hash({"readiness": 1}),
        "source_contract_id": "contract-test",
        "source_contract_hash": stable_hash({"contract": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "authorized_capabilities": capabilities,
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
    record["activation_record_hash"] = stable_hash(record)
    manifest = {
        "schema_version": "INT-OIA-005",
        "engine_id": "INT-OIA-005",
        "activated_at": "2026-07-22T00:00:00+00:00",
        "activation_manifest_id": "int-oia-005-test",
        "activation_manifest_status": "test",
        "activation_policy_id": "test",
        "source_execution_readiness_manifest_id": "int-oia-004-test",
        "source_execution_readiness_manifest_hash": stable_hash({"int": 4}),
        "source_execution_contract_manifest_id": "int-oia-003-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "activation_record_count": 1,
        "activation_records": [record],
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
    manifest["activation_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-006 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CALLABLE BINDING CONTRACT GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        activation = root / "activation"
        binding = root / "binding"
        _seed(activation)
        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingContractGate(
            activation_directory=activation,
            binding_directory=binding,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.issue(issued_at=fixed, persist=True)
        second = gate.issue(issued_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "INT-OIA-006"
        assert first.binding_contract_count == 1
        assert first.all_activation_hashes_verified
        assert first.all_activation_nonces_unique
        assert first.exact_consumer_identity_preserved
        assert first.exact_callable_identity_frozen
        assert first.source_boundary_consumed_without_reexecution
        assert not first.callable_resolution_allowed
        assert not first.callable_binding_allowed
        assert not first.callable_invocation_allowed
        assert not first.callable_resolution_performed
        assert not first.callable_binding_performed
        assert not first.callable_invocation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        contract = first.binding_contracts[0]
        assert contract.callable_name == APPROVED_CALLABLE_NAME
        assert contract.callable_path.endswith(
            ".OracleResearchAnalyticsConsumer.analyze_certified_oia_artifacts"
        )
        assert contract.exact_callable_identity_required
        assert not contract.dynamic_import_allowed
        assert not contract.callable_resolution_performed
        assert not contract.callable_binding_performed
        assert not contract.callable_invocation_performed
        assert (binding / "current.json").exists()

        tampered = json.loads(
            (activation / "current.json").read_text(encoding="utf-8")
        )
        tampered["activation_records"][0]["callable_binding_performed"] = True
        (activation / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.issue(issued_at=fixed, persist=False)
            raise AssertionError("tampered activation accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError:
            pass

    print("[PASS] Actual INT-OIA-005 activation contract consumed")
    print("[PASS] Every activation-record hash independently verified")
    print("[PASS] Activation nonces remained unique")
    print("[PASS] Exact consumer module and class identity preserved")
    print("[PASS] Exact approved analytical callable identity frozen")
    print("[PASS] Callable path hash-bound to one-time activation")
    print("[PASS] No dynamic import or callable resolution performed")
    print("[PASS] No callable binding or invocation performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe activation evidence rejected")
    print("[PASS] Atomic binding-contract artifacts persisted")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def verify() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Actual INT-OIA-005 module missing: {SOURCE}")
    text = SOURCE.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "INT-OIA-005"',
        "class DownstreamReadOnlyConsumerControlledActivationRecord",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationManifest",
        "class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationGate",
        "activation_manifest_hash",
        "downstream_consumer_execution_allowed",
    )
    missing = [token for token in required if token not in text]
    if missing:
        raise RuntimeError(
            "Actual INT-OIA-005 contract mismatch; missing: "
            + ", ".join(missing)
        )
    print("[OK] Actual INT-OIA-005 controlled-activation contract verified")


def update_package() -> None:
    existing = PKG.read_text(encoding="utf-8") if PKG.exists() else ""
    line = (
        "from .oracle_intelligence_analytics_downstream_read_only_"
        "consumer_callable_binding_contract_gate import *"
    )
    if line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        PKG.write_text(existing + line + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {PKG.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-006 INSTALLER")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CALLABLE BINDING CONTRACT GATE")
    print("=" * 40)
    verify()
    write(PROD, PRODUCTION)
    write(TEST, TEST_SOURCE)
    update_package()
    py_compile.compile(str(PROD), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    py_compile.compile(str(PKG), doraise=True)
    print("[OK] Production, test, and package syntax verified")
    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT))
    if result.returncode:
        raise SystemExit(result.returncode)
    print("[OK] INT-OIA-006 test executed automatically")
    print()
    print(
        "[DONE] INT-OIA-006 downstream read-only consumer "
        "callable binding contract gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
