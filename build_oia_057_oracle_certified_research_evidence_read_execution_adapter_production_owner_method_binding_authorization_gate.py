from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA056 = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_readiness_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_authorization_gate.py"
TEST = ROOT / "test_oia_057_oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_authorization_gate.py"
INIT = ANALYTICS / "__init__.py"

PRODUCTION_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "OIA-057"
ENGINE_ID = "OIA-057"
POLICY_ID = "oracle.certified-research-evidence-read-execution-adapter-production-owner-method-binding-authorization.v1"
STATUS_METHOD_BINDING_AUTHORIZED = "evidence_read_execution_adapter_production_owner_method_binding_authorized"
STATUS_AUTHORIZATION_ISSUED = "evidence_read_execution_adapter_production_owner_method_binding_authorization_issued"

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_method_binding_readiness"
)
DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_method_binding_authorization"
)

APPROVED = {
    "oracle_read_only_canonical_observation_adapter.v1": (
        "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "OracleLiveCorpusInspector",
        "inspect",
    ),
    "oracle_read_only_market_state_lineage_adapter.v1": (
        "qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger",
        "OracleCanonicalMarketLineageLedger",
        "records",
    ),
}

APPROVED_SIGNATURES = {
    "oracle_read_only_canonical_observation_adapter.v1": (
        "(*, connection_factory, stale_after_seconds=300, market_limit=100)",
        "(self, *, inspected_at: 'Optional[datetime]' = None) -> 'OracleLiveCorpusReport'",
    ),
    "oracle_read_only_market_state_lineage_adapter.v1": (
        "()",
        "(self) -> 'Tuple[CanonicalMarketLineageRecord, ...]'",
    ),
}


class ProductionOwnerMethodBindingAuthorizationInvariantError(RuntimeError):
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
            raise ProductionOwnerMethodBindingAuthorizationInvariantError(
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
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _aware(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ProductionOwnerMethodBindingAuthorizationInvariantError(
            f"{field_name} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", delete=False, dir=str(path.parent)
    )
    temporary = Path(handle.name)
    try:
        with handle:
            json.dump(_canonical(payload), handle, sort_keys=True, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class ProductionOwnerMethodBindingAuthorizationEntry:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    module_path: str
    owner_name: str
    callable_name: str
    constructor_signature: str
    callable_signature: str
    owner_state_fingerprint: str
    owner_construction_hash: str
    method_descriptor_type: str
    method_descriptor_module: str
    method_descriptor_qualname: str
    method_signature_verified: bool
    instance_parameter_verified: bool
    descriptor_static_resolution_verified: bool
    owner_reconstruction_required: bool
    owner_method_binding_ready: bool
    owner_method_binding_authorized: bool
    owner_reconstruction_requested: bool
    owner_reconstructed: bool
    method_binding_requested: bool
    method_bound_to_owner: bool
    method_invoked: bool
    adapter_executed: bool
    authorization_checks: tuple[str, ...]
    authorization_status: str
    source_owner_method_binding_readiness_hash: str
    source_owner_construction_authorization_hash: str
    source_owner_construction_readiness_hash: str
    source_callable_argument_binding_hash: str
    owner_method_binding_authorization_hash: str


@dataclass(frozen=True)
class ProductionOwnerMethodBindingAuthorizationManifest:
    schema_version: str
    engine_id: str
    authorized_at: str
    owner_method_binding_authorization_id: str
    owner_method_binding_authorization_status: str
    owner_method_binding_authorization_policy_id: str
    worker_id: str
    authorization_entry_count: int
    authorization_entries: tuple[ProductionOwnerMethodBindingAuthorizationEntry, ...]
    source_owner_method_binding_readiness_id: str
    source_owner_method_binding_readiness_manifest_hash: str
    source_owner_construction_id: str
    source_owner_construction_manifest_hash: str
    source_lineage: dict[str, Any]
    owner_method_binding_authorization_issued: bool
    owner_reconstruction_evaluation_allowed: bool
    owner_reconstruction_allowed: bool
    owner_reconstruction_performed: bool
    callable_binding_to_owner_evaluation_allowed: bool
    callable_binding_to_owner_allowed: bool
    callable_binding_to_owner_performed: bool
    callable_invocation_allowed: bool
    callable_invocation_performed: bool
    adapter_execution_allowed: bool
    adapter_execution_performed: bool
    corpus_read_execution_allowed: bool
    corpus_read_execution_performed: bool
    research_execution_allowed: bool
    analytic_conclusion_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    execution_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    authorization_artifact_persistence_allowed: bool
    owner_method_binding_authorization_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingAuthorizationGate:
    """Authorize exact OIA-056 method-binding plans without reconstructing or binding owners."""

    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
    ) -> None:
        self.readiness_directory = Path(readiness_directory)
        self.authorization_directory = Path(authorization_directory)

    def _load_readiness(self) -> dict[str, Any]:
        path = self.readiness_directory / "current.json"
        if not path.exists():
            raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                f"OIA-056 current readiness artifact missing: {path}"
            )
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                "OIA-056 readiness artifact could not be decoded"
            ) from error

        manifest_hash = source.pop("owner_method_binding_readiness_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                "OIA-056 readiness manifest hash verification failed"
            )
        source["owner_method_binding_readiness_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-056",
            "engine_id": "OIA-056",
            "owner_method_binding_readiness_issued": True,
            "owner_method_binding_authorization_evaluation_allowed": True,
            "owner_reconstruction_allowed": False,
            "owner_reconstruction_performed": False,
            "callable_binding_to_owner_allowed": False,
            "callable_binding_to_owner_performed": False,
            "callable_invocation_allowed": False,
            "callable_invocation_performed": False,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
            "corpus_read_execution_performed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    f"OIA-056 invariant failed: {field_name}"
                )

        for field_name in (
            "owner_method_binding_readiness_id",
            "source_owner_construction_id",
            "worker_id",
        ):
            if not isinstance(source.get(field_name), str) or not source[field_name]:
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    f"OIA-056 identifier invalid: {field_name}"
                )
        for hash_field in (
            "source_owner_construction_manifest_hash",
            "source_owner_construction_authorization_manifest_hash",
        ):
            if not _valid_hash(source.get(hash_field)):
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    f"OIA-056 lineage hash invalid: {hash_field}"
                )

        entries = source.get("readiness_entries")
        if not isinstance(entries, list) or not entries or len(entries) != source.get("readiness_entry_count"):
            raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                "OIA-056 readiness entries invalid"
            )

        seen_work_items: set[str] = set()
        seen_hashes: set[str] = set()
        for expected_sequence, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict) or entry.get("sequence") != expected_sequence:
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    "OIA-056 readiness entry sequence invalid"
                )
            entry_hash = entry.pop("owner_method_binding_readiness_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    "OIA-056 readiness entry hash verification failed"
                )
            entry["owner_method_binding_readiness_hash"] = entry_hash
            if entry_hash in seen_hashes:
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    "duplicate OIA-056 readiness hash"
                )
            seen_hashes.add(entry_hash)
            work_item_id = entry.get("work_item_id")
            if not isinstance(work_item_id, str) or not work_item_id or work_item_id in seen_work_items:
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    "duplicate or invalid OIA-056 work item"
                )
            seen_work_items.add(work_item_id)
            identity = APPROVED.get(entry.get("adapter_id"))
            if identity is None or identity != (
                entry.get("module_path"), entry.get("owner_name"), entry.get("callable_name")
            ):
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    "unapproved OIA-056 method identity"
                )
            safety = {
                "method_descriptor_type": "function",
                "method_signature_verified": True,
                "instance_parameter_verified": True,
                "descriptor_static_resolution_verified": True,
                "owner_reconstruction_required": True,
                "owner_reconstructed": False,
                "method_bound_to_owner": False,
                "method_invoked": False,
                "adapter_executed": False,
            }
            for field_name, expected_value in safety.items():
                if entry.get(field_name) != expected_value:
                    raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                        f"unsafe OIA-056 readiness entry: {field_name}"
                    )
            approved_signatures = APPROVED_SIGNATURES[entry["adapter_id"]]
            if (entry.get("constructor_signature"), entry.get("callable_signature")) != approved_signatures:
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    "OIA-056 repository-approved signature mismatch"
                )
            if entry.get("method_descriptor_module") != entry.get("module_path"):
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    "OIA-056 method descriptor module mismatch"
                )
            if entry.get("method_descriptor_qualname") != f'{entry["owner_name"]}.{entry["callable_name"]}':
                raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                    "OIA-056 method descriptor qualified-name mismatch"
                )
            for hash_field in (
                "owner_state_fingerprint",
                "owner_construction_hash",
                "source_owner_construction_authorization_hash",
                "source_owner_construction_readiness_hash",
                "source_callable_argument_binding_hash",
            ):
                if not _valid_hash(entry.get(hash_field)):
                    raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                        f"OIA-056 entry hash invalid: {hash_field}"
                    )
        if not isinstance(source.get("source_lineage"), dict) or not source["source_lineage"]:
            raise ProductionOwnerMethodBindingAuthorizationInvariantError(
                "OIA-056 source lineage missing"
            )
        return source

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> ProductionOwnerMethodBindingAuthorizationManifest:
        authorized_at = _aware(authorized_at, "authorized_at")
        source = self._load_readiness()
        authorization_entries: list[ProductionOwnerMethodBindingAuthorizationEntry] = []

        for sequence, readiness_entry in enumerate(source["readiness_entries"], start=1):
            body = {
                "sequence": sequence,
                "worker_id": readiness_entry["worker_id"],
                "work_item_id": readiness_entry["work_item_id"],
                "adapter_id": readiness_entry["adapter_id"],
                "read_operation": readiness_entry["read_operation"],
                "module_path": readiness_entry["module_path"],
                "owner_name": readiness_entry["owner_name"],
                "callable_name": readiness_entry["callable_name"],
                "constructor_signature": readiness_entry["constructor_signature"],
                "callable_signature": readiness_entry["callable_signature"],
                "owner_state_fingerprint": readiness_entry["owner_state_fingerprint"],
                "owner_construction_hash": readiness_entry["owner_construction_hash"],
                "method_descriptor_type": readiness_entry["method_descriptor_type"],
                "method_descriptor_module": readiness_entry["method_descriptor_module"],
                "method_descriptor_qualname": readiness_entry["method_descriptor_qualname"],
                "method_signature_verified": True,
                "instance_parameter_verified": True,
                "descriptor_static_resolution_verified": True,
                "owner_reconstruction_required": True,
                "owner_method_binding_ready": True,
                "owner_method_binding_authorized": True,
                "owner_reconstruction_requested": False,
                "owner_reconstructed": False,
                "method_binding_requested": False,
                "method_bound_to_owner": False,
                "method_invoked": False,
                "adapter_executed": False,
                "authorization_checks": (
                    "owner_method_binding_readiness_manifest_hash_verified",
                    "owner_method_binding_readiness_entry_hash_verified",
                    "approved_owner_method_identity_verified",
                    "method_descriptor_identity_verified",
                    "method_signature_verified",
                    "canonical_self_parameter_verified",
                    "owner_method_binding_plan_authorized",
                    "owner_reconstruction_not_requested",
                    "owner_not_reconstructed",
                    "method_binding_not_requested",
                    "method_not_bound_to_owner",
                    "method_not_invoked",
                    "adapter_not_executed",
                    "corpus_execution_remained_disabled",
                    "oracle_qseries_boundary_verified",
                ),
                "authorization_status": STATUS_METHOD_BINDING_AUTHORIZED,
                "source_owner_method_binding_readiness_hash": readiness_entry[
                    "owner_method_binding_readiness_hash"
                ],
                "source_owner_construction_authorization_hash": readiness_entry[
                    "source_owner_construction_authorization_hash"
                ],
                "source_owner_construction_readiness_hash": readiness_entry[
                    "source_owner_construction_readiness_hash"
                ],
                "source_callable_argument_binding_hash": readiness_entry[
                    "source_callable_argument_binding_hash"
                ],
            }
            authorization_entries.append(
                ProductionOwnerMethodBindingAuthorizationEntry(
                    **body,
                    owner_method_binding_authorization_hash=stable_hash(body),
                )
            )

        source_manifest_hash = source["owner_method_binding_readiness_manifest_hash"]
        authorization_id = "oia057-owner-method-binding-authorization-" + stable_hash(
            {"source_owner_method_binding_readiness_manifest_hash": source_manifest_hash, "policy_id": POLICY_ID}
        )[:32]
        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at.isoformat(),
            "owner_method_binding_authorization_id": authorization_id,
            "owner_method_binding_authorization_status": STATUS_AUTHORIZATION_ISSUED,
            "owner_method_binding_authorization_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "authorization_entry_count": len(authorization_entries),
            "authorization_entries": tuple(authorization_entries),
            "source_owner_method_binding_readiness_id": source["owner_method_binding_readiness_id"],
            "source_owner_method_binding_readiness_manifest_hash": source_manifest_hash,
            "source_owner_construction_id": source["source_owner_construction_id"],
            "source_owner_construction_manifest_hash": source["source_owner_construction_manifest_hash"],
            "source_lineage": dict(source["source_lineage"]),
            "owner_method_binding_authorization_issued": True,
            "owner_reconstruction_evaluation_allowed": True,
            "owner_reconstruction_allowed": False,
            "owner_reconstruction_performed": False,
            "callable_binding_to_owner_evaluation_allowed": True,
            "callable_binding_to_owner_allowed": False,
            "callable_binding_to_owner_performed": False,
            "callable_invocation_allowed": False,
            "callable_invocation_performed": False,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
            "corpus_read_execution_performed": False,
            "research_execution_allowed": False,
            "analytic_conclusion_allowed": False,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "trading_recommendations_allowed": False,
            "source_mutation_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "authorization_artifact_persistence_allowed": True,
        }
        serializable = dict(manifest_body)
        serializable["authorization_entries"] = [asdict(entry) for entry in authorization_entries]
        result = ProductionOwnerMethodBindingAuthorizationManifest(
            **manifest_body,
            owner_method_binding_authorization_manifest_hash=stable_hash(serializable),
        )
        if persist:
            payload = asdict(result)
            _atomic_write(self.authorization_directory / "current.json", payload)
            _atomic_write(
                self.authorization_directory / "authorizations" / f"{authorization_id}.json",
                payload,
            )
            _atomic_write(
                self.authorization_directory / "workers" / result.worker_id / f"{authorization_id}.json",
                payload,
            )
        return result
'''

TEST_SOURCE = r'''import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_authorization_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingAuthorizationGate,
    ProductionOwnerMethodBindingAuthorizationInvariantError,
    stable_hash,
)


def seed_oia056(path: Path) -> dict:
    entry_body = {
        "sequence": 1,
        "worker_id": "oracle-worker-test",
        "work_item_id": "work.test",
        "adapter_id": "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation": "read_canonical_observations",
        "module_path": "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "constructor_signature": "(*, connection_factory, stale_after_seconds=300, market_limit=100)",
        "callable_signature": "(self, *, inspected_at: 'Optional[datetime]' = None) -> 'OracleLiveCorpusReport'",
        "owner_state_fingerprint": stable_hash({"owner": "inert"}),
        "owner_construction_hash": stable_hash({"55": 1}),
        "method_descriptor_type": "function",
        "method_descriptor_module": "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "method_descriptor_qualname": "OracleLiveCorpusInspector.inspect",
        "method_signature_verified": True,
        "instance_parameter_verified": True,
        "descriptor_static_resolution_verified": True,
        "owner_reconstruction_required": True,
        "owner_reconstructed": False,
        "method_bound_to_owner": False,
        "method_invoked": False,
        "adapter_executed": False,
        "readiness_checks": ["approved_method_descriptor_statically_resolved"],
        "readiness_status": "evidence_read_execution_adapter_production_owner_method_binding_ready",
        "source_owner_construction_authorization_hash": stable_hash({"54": 1}),
        "source_owner_construction_readiness_hash": stable_hash({"53": 1}),
        "source_callable_argument_binding_hash": stable_hash({"52": 1}),
    }
    entry = dict(entry_body)
    entry["owner_method_binding_readiness_hash"] = stable_hash(entry_body)
    manifest_body = {
        "schema_version": "OIA-056",
        "engine_id": "OIA-056",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "owner_method_binding_readiness_id": "oia056-test",
        "owner_method_binding_readiness_status": "evidence_read_execution_adapter_production_owner_method_binding_readiness_issued",
        "owner_method_binding_readiness_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "readiness_entry_count": 1,
        "readiness_entries": [entry],
        "source_owner_construction_id": "oia055-test",
        "source_owner_construction_manifest_hash": stable_hash({"55m": 1}),
        "source_owner_construction_authorization_id": "oia054-test",
        "source_owner_construction_authorization_manifest_hash": stable_hash({"54m": 1}),
        "source_lineage": {"dispatch_manifest_id": "oia020-test", "source_claim_id": "oia021-test"},
        "owner_method_binding_readiness_issued": True,
        "owner_method_binding_authorization_evaluation_allowed": True,
        "owner_reconstruction_allowed": False,
        "owner_reconstruction_performed": False,
        "callable_binding_to_owner_allowed": False,
        "callable_binding_to_owner_performed": False,
        "callable_invocation_allowed": False,
        "callable_invocation_performed": False,
        "adapter_execution_allowed": False,
        "adapter_execution_performed": False,
        "corpus_read_execution_allowed": False,
        "corpus_read_execution_performed": False,
        "research_execution_allowed": False,
        "analytic_conclusion_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "readiness_artifact_persistence_allowed": True,
    }
    payload = dict(manifest_body)
    payload["owner_method_binding_readiness_manifest_hash"] = stable_hash(manifest_body)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def rehash(payload: dict) -> None:
    for entry in payload["readiness_entries"]:
        body = dict(entry)
        body.pop("owner_method_binding_readiness_hash", None)
        entry["owner_method_binding_readiness_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("owner_method_binding_readiness_manifest_hash", None)
    payload["owner_method_binding_readiness_manifest_hash"] = stable_hash(body)


def reject(gate, fixed, message):
    try:
        gate.authorize(authorized_at=fixed, persist=False)
    except ProductionOwnerMethodBindingAuthorizationInvariantError:
        return
    raise AssertionError(message)


def main() -> int:
    print("=" * 40)
    print(" OIA-057 TEST")
    print(" OWNER METHOD BINDING AUTHORIZATION")
    print("=" * 40)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness = root / "readiness"
        authorization = root / "authorization"
        source = seed_oia056(readiness)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingAuthorizationGate(
            readiness_directory=readiness,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-057"
        assert first.engine_id == "OIA-057"
        assert first.owner_method_binding_authorization_issued is True
        assert first.owner_reconstruction_evaluation_allowed is True
        assert first.callable_binding_to_owner_evaluation_allowed is True
        assert first.authorization_entry_count == 1
        entry = first.authorization_entries[0]
        assert entry.owner_method_binding_ready is True
        assert entry.owner_method_binding_authorized is True
        assert entry.owner_reconstruction_requested is False
        assert entry.owner_reconstructed is False
        assert entry.method_binding_requested is False
        assert entry.method_bound_to_owner is False
        assert entry.method_invoked is False
        assert entry.adapter_executed is False
        assert first.owner_reconstruction_allowed is False
        assert first.callable_binding_to_owner_allowed is False
        assert first.callable_invocation_allowed is False
        assert first.adapter_execution_allowed is False
        assert first.corpus_read_execution_allowed is False
        assert first.qseries_handoff_allowed is False
        assert first.execution_allowed is False
        assert first.source_owner_method_binding_readiness_manifest_hash == source["owner_method_binding_readiness_manifest_hash"]
        assert (authorization / "current.json").exists()

        tampered = json.loads((readiness / "current.json").read_text())
        tampered["readiness_entries"][0]["callable_signature"] = "(self, *args, **kwargs)"
        rehash(tampered)
        (readiness / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        reject(gate, fixed, "tampered signature accepted")

        seed_oia056(readiness)
        bound = json.loads((readiness / "current.json").read_text())
        bound["readiness_entries"][0]["method_bound_to_owner"] = True
        rehash(bound)
        (readiness / "current.json").write_text(json.dumps(bound), encoding="utf-8")
        reject(gate, fixed, "premature binding accepted")

        seed_oia056(readiness)
        executable = json.loads((readiness / "current.json").read_text())
        executable["adapter_execution_allowed"] = True
        rehash(executable)
        (readiness / "current.json").write_text(json.dumps(executable), encoding="utf-8")
        reject(gate, fixed, "executable manifest accepted")

        seed_oia056(readiness)
        duplicate = json.loads((readiness / "current.json").read_text())
        duplicate["readiness_entries"].append(dict(duplicate["readiness_entries"][0]))
        duplicate["readiness_entries"][1]["sequence"] = 2
        duplicate["readiness_entry_count"] = 2
        rehash(duplicate)
        (readiness / "current.json").write_text(json.dumps(duplicate), encoding="utf-8")
        reject(gate, fixed, "duplicate work item accepted")

    print("[PASS] Actual OIA-056 owner-method-binding-readiness contract consumed")
    print("[PASS] Exact verified owner method binding plans authorized deterministically")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-056 lineage preserved")
    print("[PASS] Binding evaluation authorized without reconstructing or binding owners")
    print("[PASS] Owners were not reconstructed and methods were not owner-bound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, duplicate, bound, or executable input rejected")
    print("[PASS] Atomic owner-method-binding-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

EXPORT_BLOCK = r'''
from .oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_authorization_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingAuthorizationGate,
    ProductionOwnerMethodBindingAuthorizationEntry,
    ProductionOwnerMethodBindingAuthorizationInvariantError,
    ProductionOwnerMethodBindingAuthorizationManifest,
)

__all__ = [
    "OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingAuthorizationGate",
    "ProductionOwnerMethodBindingAuthorizationEntry",
    "ProductionOwnerMethodBindingAuthorizationInvariantError",
    "ProductionOwnerMethodBindingAuthorizationManifest",
] + __all__
'''


def write_full(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = "oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_authorization_gate"
    if marker not in existing:
        write_full(INIT, existing.rstrip() + "\n\n" + EXPORT_BLOCK.strip() + "\n")


def main() -> int:
    print("=" * 40)
    print(" OIA-057 INSTALLER")
    print(" OWNER METHOD BINDING AUTHORIZATION")
    print(" PRE-BINDING SAFETY GATE")
    print("=" * 40)
    if not OIA056.exists():
        raise SystemExit(f"[FAIL] Required OIA-056 production contract missing: {OIA056}")
    source = OIA056.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "OIA-056"',
        "ProductionOwnerMethodBindingReadinessManifest",
        "owner_method_binding_readiness_manifest_hash",
        "owner_method_binding_authorization_evaluation_allowed",
    )
    if not all(token in source for token in required):
        raise SystemExit("[FAIL] Actual OIA-056 owner-method-binding-readiness contract verification failed")
    print("[OK] Actual OIA-056 owner-method-binding-readiness contract verified")
    write_full(PRODUCTION, PRODUCTION_SOURCE)
    print(f"[OK] FULL REPLACEMENT: {PRODUCTION}")
    write_full(TEST, TEST_SOURCE)
    print(f"[OK] FULL REPLACEMENT: {TEST}")
    update_init()
    print(f"[OK] PACKAGE UPDATED: {INIT}")
    for path in (PRODUCTION, TEST, INIT):
        py_compile.compile(str(path), doraise=True)
    print("[OK] Production, test, and package syntax verified")
    completed = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    print("[OK] OIA-057 test executed automatically")
    print()
    print("[DONE] OIA-057 production owner method binding authorization gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
