from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-003"
ENGINE_ID = "INT-OIA-003"
POLICY_ID = "oracle.intelligence.analytics.downstream-read-only-consumer-execution-contract.v1"
STATUS_ISSUED = "downstream_read_only_consumer_execution_contract_issued"

DEFAULT_ADMISSION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_admission"
)
DEFAULT_CONTRACT_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "analytics_downstream_read_only_consumer_execution_contract"
)

REQUIRED_CAPABILITIES = frozenset(
    {
        "read_certified_oia_boundary",
        "read_certified_invocation_results",
        "read_certified_result_summaries",
        "perform_read_only_research_analysis",
        "persist_research_analysis_artifacts",
    }
)


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
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
        raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
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
class DownstreamReadOnlyConsumerExecutionContract:
    sequence: int
    contract_id: str
    consumer_id: str
    consumer_module: str
    consumer_class: str
    source_admission_record_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    authorized_capabilities: tuple[str, ...]
    input_mode: str
    output_mode: str
    deterministic_required: bool
    immutable_inputs_required: bool
    replayable_required: bool
    read_only_required: bool
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
    artifact_persistence_allowed: bool
    execution_contract_status: str
    execution_contract_hash: str


@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractManifest:
    schema_version: str
    engine_id: str
    issued_at: str
    execution_contract_manifest_id: str
    execution_contract_manifest_status: str
    execution_contract_policy_id: str
    source_admission_manifest_id: str
    source_admission_manifest_hash: str
    source_integration_certification_id: str
    source_boundary_id: str
    source_boundary_hash: str
    execution_contract_count: int
    execution_contracts: tuple[DownstreamReadOnlyConsumerExecutionContract, ...]
    admitted_consumers_only: bool
    exact_capability_set_preserved: bool
    deterministic_execution_required: bool
    immutable_input_consumption_required: bool
    replayable_output_required: bool
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
    read_only_consumer_execution_authorized: bool
    contract_artifact_persistence_allowed: bool
    execution_contract_manifest_hash: str


class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractGate:
    def __init__(
        self,
        *,
        admission_directory: Path | str = DEFAULT_ADMISSION_DIRECTORY,
        contract_directory: Path | str = DEFAULT_CONTRACT_DIRECTORY,
    ) -> None:
        self.admission_directory = Path(admission_directory)
        self.contract_directory = Path(contract_directory)

    def _load_admission(self) -> dict[str, Any]:
        path = self.admission_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
                f"INT-OIA-002 admission artifact missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
                "INT-OIA-002 admission artifact could not be decoded"
            ) from exc

        manifest_hash = payload.pop("admission_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
                "INT-OIA-002 admission manifest hash mismatch"
            )
        payload["admission_manifest_hash"] = manifest_hash

        required = {
            "schema_version": "INT-OIA-002",
            "engine_id": "INT-OIA-002",
            "all_consumers_read_only": True,
            "all_capabilities_allowlisted": True,
            "duplicate_consumers_rejected": True,
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
            "downstream_read_only_research_allowed": True,
            "admission_artifact_persistence_allowed": True,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
                    f"unsafe or incomplete INT-OIA-002 field: {field}"
                )

        records = payload.get("admission_records")
        if (
            not isinstance(records, list)
            or not records
            or payload.get("admission_record_count") != len(records)
        ):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
                "INT-OIA-002 admission records invalid"
            )

        seen_consumers: set[str] = set()
        for sequence, raw_record in enumerate(records, start=1):
            record = dict(raw_record)
            record_hash = record.pop("admission_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
                    "INT-OIA-002 admission record hash mismatch"
                )
            record["admission_record_hash"] = record_hash

            if record.get("sequence") != sequence:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
                    "INT-OIA-002 admission sequence mismatch"
                )
            consumer_id = record.get("consumer_id")
            if not isinstance(consumer_id, str) or not consumer_id or consumer_id in seen_consumers:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
                    "invalid or duplicate admitted consumer"
                )
            seen_consumers.add(consumer_id)

            capabilities = record.get("requested_capabilities")
            if (
                not isinstance(capabilities, list)
                or set(capabilities) != REQUIRED_CAPABILITIES
            ):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
                    "INT-OIA-002 consumer capability set mismatch"
                )

            required_record = {
                "read_only": True,
                "execution_allowed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_handoff_allowed": False,
                "order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "source_mutation_allowed": False,
                "admitted": True,
                "admission_status": "admitted_read_only",
            }
            for field, expected in required_record.items():
                if record.get(field) != expected:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError(
                        f"unsafe INT-OIA-002 admission record field: {field}"
                    )

        payload["admission_records"] = records
        return payload

    def issue(
        self,
        *,
        issued_at: datetime,
        persist: bool = True,
    ) -> OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractManifest:
        issued_at = _aware(issued_at, "issued_at")
        source = self._load_admission()

        contracts: list[DownstreamReadOnlyConsumerExecutionContract] = []
        for sequence, record in enumerate(source["admission_records"], start=1):
            capabilities = tuple(sorted(record["requested_capabilities"]))
            identity = {
                "source_admission_manifest_id": source["admission_manifest_id"],
                "consumer_id": record["consumer_id"],
                "source_admission_record_hash": record["admission_record_hash"],
                "source_boundary_id": record["source_boundary_id"],
                "source_boundary_hash": record["source_boundary_hash"],
                "authorized_capabilities": capabilities,
            }
            contract_id = stable_hash(identity)

            contract_body = {
                "sequence": sequence,
                "contract_id": contract_id,
                "consumer_id": record["consumer_id"],
                "consumer_module": record["consumer_module"],
                "consumer_class": record["consumer_class"],
                "source_admission_record_hash": record["admission_record_hash"],
                "source_boundary_id": record["source_boundary_id"],
                "source_boundary_hash": record["source_boundary_hash"],
                "authorized_capabilities": capabilities,
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
            contracts.append(
                DownstreamReadOnlyConsumerExecutionContract(
                    **contract_body,
                    execution_contract_hash=stable_hash(contract_body),
                )
            )

        manifest_identity = {
            "source_admission_manifest_id": source["admission_manifest_id"],
            "source_admission_manifest_hash": source["admission_manifest_hash"],
            "issued_at": issued_at.isoformat(),
            "execution_contract_hashes": [
                contract.execution_contract_hash for contract in contracts
            ],
        }
        manifest_id = stable_hash(manifest_identity)

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "issued_at": issued_at.isoformat(),
            "execution_contract_manifest_id": manifest_id,
            "execution_contract_manifest_status": STATUS_ISSUED,
            "execution_contract_policy_id": POLICY_ID,
            "source_admission_manifest_id": source["admission_manifest_id"],
            "source_admission_manifest_hash": source["admission_manifest_hash"],
            "source_integration_certification_id": source[
                "source_integration_certification_id"
            ],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "execution_contract_count": len(contracts),
            "execution_contracts": tuple(contracts),
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

        serializable = dict(body)
        serializable["execution_contracts"] = [asdict(contract) for contract in contracts]
        manifest_hash = stable_hash(serializable)

        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractManifest(
            **body,
            execution_contract_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(manifest)
            _atomic_write(self.contract_directory / "current.json", payload)
            _atomic_write(
                self.contract_directory
                / "manifests"
                / f"{manifest_id}.json",
                payload,
            )
            for contract in contracts:
                _atomic_write(
                    self.contract_directory
                    / "consumers"
                    / contract.consumer_id
                    / f"{contract.contract_id}.json",
                    asdict(contract),
                )

        return manifest
