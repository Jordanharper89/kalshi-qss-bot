from __future__ import annotations
import hashlib, json, os, tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "INT-OIA-012"
ENGINE_ID = "INT-OIA-012"
STATUS_ATTESTED = "downstream_read_only_consumer_controlled_invocation_result_attested"
DEFAULT_EXECUTION_DIRECTORY = Path("runtime/oracle_intelligence/analytics_downstream_read_only_consumer_controlled_invocation_execution")
DEFAULT_ATTESTATION_DIRECTORY = Path("runtime/oracle_intelligence/analytics_downstream_read_only_consumer_controlled_invocation_result_attestation")

class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError(RuntimeError):
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
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("unsupported value type")

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)

def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_canonical(payload), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", delete=False, dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(text); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()

@dataclass(frozen=True)
class ControlledInvocationResultAttestationRecord:
    sequence: int
    result_attestation_id: str
    consumer_id: str
    invocation_execution_id: str
    invocation_nonce: str
    source_invocation_execution_record_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    result_type: str
    result_hash: str
    recomputed_result_hash: str
    result_payload: Any
    result_hash_verified: bool
    invocation_count_verified: bool
    one_time_invocation_verified: bool
    immutable_result_verified: bool
    execution_lineage_verified: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_performed: bool
    source_mutation_performed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    result_admission_authorized: bool
    downstream_release_performed: bool
    attestation_status: str
    result_attestation_record_hash: str

@dataclass(frozen=True)
class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationManifest:
    schema_version: str
    engine_id: str
    attested_at: str
    result_attestation_manifest_id: str
    result_attestation_status: str
    source_invocation_execution_manifest_id: str
    source_invocation_execution_manifest_hash: str
    source_boundary_id: str
    source_boundary_hash: str
    attestation_record_count: int
    attestation_records: tuple[ControlledInvocationResultAttestationRecord, ...]
    all_execution_hashes_verified: bool
    all_result_hashes_verified: bool
    all_execution_lineage_verified: bool
    all_one_time_invocations_verified: bool
    all_results_immutable: bool
    source_boundary_consumed_without_reexecution: bool
    invocation_reexecution_performed: bool
    database_connection_performed: bool
    corpus_read_execution_repeated: bool
    source_mutation_performed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_execution_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    controlled_result_admission_authorized: bool
    downstream_release_performed: bool
    result_attestation_manifest_hash: str

class OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationGate:
    def __init__(self, *, execution_directory=DEFAULT_EXECUTION_DIRECTORY, attestation_directory=DEFAULT_ATTESTATION_DIRECTORY):
        self.execution_directory = Path(execution_directory)
        self.attestation_directory = Path(attestation_directory)

    def _load(self) -> dict[str, Any]:
        path = self.execution_directory / "current.json"
        if not path.exists():
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError(f"INT-OIA-011 execution artifact missing: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest_hash = payload.pop("invocation_execution_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(payload) != manifest_hash:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("INT-OIA-011 execution manifest hash mismatch")
        payload["invocation_execution_manifest_hash"] = manifest_hash
        required = {
            "schema_version": "INT-OIA-011",
            "engine_id": "INT-OIA-011",
            "controlled_invocation_performed": True,
            "one_time_invocation_enforced": True,
            "all_results_deterministically_hashable": True,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_performed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        for field, expected in required.items():
            if payload.get(field) != expected:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError(f"unsafe INT-OIA-011 field: {field}")
        records = payload.get("execution_records")
        if not isinstance(records, list) or not records or payload.get("execution_record_count") != len(records):
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("INT-OIA-011 execution records invalid")
        for sequence, raw in enumerate(records, 1):
            record = dict(raw)
            record_hash = record.pop("invocation_execution_record_hash", None)
            if not _valid_hash(record_hash) or stable_hash(record) != record_hash:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("execution-record hash mismatch")
            raw["invocation_execution_record_hash"] = record_hash
            if raw.get("sequence") != sequence or raw.get("invocation_count") != 1 or raw.get("invocation_performed") is not True:
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("one-time invocation contract mismatch")
            if stable_hash(raw.get("result_payload")) != raw.get("result_hash"):
                raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("result hash mismatch")
            for field in ("database_connection_performed", "corpus_read_performed", "source_mutation_performed", "signals_allowed", "alerts_allowed", "qseries_execution_allowed", "market_order_creation_allowed", "funds_movement_allowed", "portfolio_mutation_allowed"):
                if raw.get(field) is not False:
                    raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError(f"unsafe execution-record field: {field}")
        return payload

    def attest(self, *, attested_at: datetime, persist: bool = True):
        if attested_at.tzinfo is None or attested_at.utcoffset() is None:
            raise OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError("attested_at must be timezone-aware")
        attested_at = attested_at.astimezone(timezone.utc)
        source = self._load()
        records = []
        for sequence, execution in enumerate(source["execution_records"], 1):
            recomputed = stable_hash(execution["result_payload"])
            attestation_id = stable_hash({
                "source_manifest": source["invocation_execution_manifest_id"],
                "execution_id": execution["invocation_execution_id"],
                "execution_record_hash": execution["invocation_execution_record_hash"],
                "result_hash": recomputed,
                "attested_at": attested_at.isoformat(),
            })
            body = {
                "sequence": sequence,
                "result_attestation_id": attestation_id,
                "consumer_id": execution["consumer_id"],
                "invocation_execution_id": execution["invocation_execution_id"],
                "invocation_nonce": execution["invocation_nonce"],
                "source_invocation_execution_record_hash": execution["invocation_execution_record_hash"],
                "source_boundary_id": execution["source_boundary_id"],
                "source_boundary_hash": execution["source_boundary_hash"],
                "result_type": execution["result_type"],
                "result_hash": execution["result_hash"],
                "recomputed_result_hash": recomputed,
                "result_payload": execution["result_payload"],
                "result_hash_verified": True,
                "invocation_count_verified": True,
                "one_time_invocation_verified": True,
                "immutable_result_verified": True,
                "execution_lineage_verified": True,
                "invocation_reexecution_performed": False,
                "database_connection_performed": False,
                "corpus_read_performed": False,
                "source_mutation_performed": False,
                "signals_allowed": False,
                "alerts_allowed": False,
                "qseries_execution_allowed": False,
                "market_order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "result_admission_authorized": True,
                "downstream_release_performed": False,
                "attestation_status": "result_verified_not_released",
            }
            records.append(ControlledInvocationResultAttestationRecord(**body, result_attestation_record_hash=stable_hash(body)))
        manifest_id = stable_hash({
            "source_manifest": source["invocation_execution_manifest_id"],
            "source_hash": source["invocation_execution_manifest_hash"],
            "attested_at": attested_at.isoformat(),
            "records": [r.result_attestation_record_hash for r in records],
        })
        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "result_attestation_manifest_id": manifest_id,
            "result_attestation_status": STATUS_ATTESTED,
            "source_invocation_execution_manifest_id": source["invocation_execution_manifest_id"],
            "source_invocation_execution_manifest_hash": source["invocation_execution_manifest_hash"],
            "source_boundary_id": source["source_boundary_id"],
            "source_boundary_hash": source["source_boundary_hash"],
            "attestation_record_count": len(records),
            "attestation_records": tuple(records),
            "all_execution_hashes_verified": True,
            "all_result_hashes_verified": True,
            "all_execution_lineage_verified": True,
            "all_one_time_invocations_verified": True,
            "all_results_immutable": True,
            "source_boundary_consumed_without_reexecution": True,
            "invocation_reexecution_performed": False,
            "database_connection_performed": False,
            "corpus_read_execution_repeated": False,
            "source_mutation_performed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "controlled_result_admission_authorized": True,
            "downstream_release_performed": False,
        }
        serializable = dict(body)
        serializable["attestation_records"] = [asdict(r) for r in records]
        manifest = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationManifest(**body, result_attestation_manifest_hash=stable_hash(serializable))
        if persist:
            payload = asdict(manifest)
            _atomic_write(self.attestation_directory / "current.json", payload)
            _atomic_write(self.attestation_directory / "manifests" / f"{manifest_id}.json", payload)
        return manifest
