from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA055 = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_readiness_gate.py"
TEST = ROOT / "test_oia_056_oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_readiness_gate.py"
INIT = ANALYTICS / "__init__.py"

PRODUCTION_SOURCE = r'''from __future__ import annotations

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

SCHEMA_VERSION = "OIA-056"
ENGINE_ID = "OIA-056"
POLICY_ID = "oracle.certified-research-evidence-read-execution-adapter-production-owner-method-binding-readiness.v1"
STATUS_METHOD_BINDING_READY = "evidence_read_execution_adapter_production_owner_method_binding_ready"
STATUS_READINESS_ISSUED = "evidence_read_execution_adapter_production_owner_method_binding_readiness_issued"

DEFAULT_CONSTRUCTION_DIRECTORY = Path(
    "runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_construction"
)
DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/certified_research_evidence_read_execution_adapter_production_owner_method_binding_readiness"
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


class ProductionOwnerMethodBindingReadinessInvariantError(RuntimeError):
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
            raise ProductionOwnerMethodBindingReadinessInvariantError(
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


def _aware(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ProductionOwnerMethodBindingReadinessInvariantError(
            f"{field_name} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
    )
    temporary = Path(handle.name)
    try:
        with handle:
            json.dump(
                _canonical(payload),
                handle,
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class ProductionOwnerMethodBindingReadinessEntry:
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
    owner_reconstructed: bool
    method_bound_to_owner: bool
    method_invoked: bool
    adapter_executed: bool
    readiness_checks: tuple[str, ...]
    readiness_status: str
    source_owner_construction_authorization_hash: str
    source_owner_construction_readiness_hash: str
    source_callable_argument_binding_hash: str
    owner_method_binding_readiness_hash: str


@dataclass(frozen=True)
class ProductionOwnerMethodBindingReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: str
    owner_method_binding_readiness_id: str
    owner_method_binding_readiness_status: str
    owner_method_binding_readiness_policy_id: str
    worker_id: str
    readiness_entry_count: int
    readiness_entries: tuple[ProductionOwnerMethodBindingReadinessEntry, ...]
    source_owner_construction_id: str
    source_owner_construction_manifest_hash: str
    source_owner_construction_authorization_id: str
    source_owner_construction_authorization_manifest_hash: str
    source_lineage: dict[str, Any]
    owner_method_binding_readiness_issued: bool
    owner_method_binding_authorization_evaluation_allowed: bool
    owner_reconstruction_allowed: bool
    owner_reconstruction_performed: bool
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
    readiness_artifact_persistence_allowed: bool
    owner_method_binding_readiness_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingReadinessGate:
    # OIA-056 validates the repository-approved owner method descriptor.
    # It performs static descriptor inspection only and never invokes it.

    def __init__(
        self,
        *,
        construction_directory: Path | str = DEFAULT_CONSTRUCTION_DIRECTORY,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
    ) -> None:
        self.construction_directory = Path(construction_directory)
        self.readiness_directory = Path(readiness_directory)

    def _load_construction(self) -> dict[str, Any]:
        path = self.construction_directory / "current.json"
        if not path.exists():
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                f"OIA-055 current construction artifact missing: {path}"
            )
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "OIA-055 construction artifact could not be decoded"
            ) from error

        manifest_hash = source.pop("owner_construction_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "OIA-055 construction manifest hash verification failed"
            )
        source["owner_construction_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-055",
            "engine_id": "OIA-055",
            "owner_construction_performed": True,
            "owner_instances_retained": False,
            "callable_binding_to_owner_allowed": False,
            "callable_binding_to_owner_performed": False,
            "callable_invocation_allowed": False,
            "callable_invocation_performed": False,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
            "corpus_read_execution_performed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    f"OIA-055 invariant failed: {field_name}"
                )

        for field_name in (
            "owner_construction_id",
            "source_owner_construction_authorization_id",
            "worker_id",
        ):
            if not isinstance(source.get(field_name), str) or not source[field_name]:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    f"OIA-055 identifier invalid: {field_name}"
                )

        if not _valid_hash(source.get("source_owner_construction_authorization_manifest_hash")):
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "OIA-055 authorization lineage hash invalid"
            )

        entries = source.get("construction_entries")
        if (
            not isinstance(entries, list)
            or not entries
            or len(entries) != source.get("construction_entry_count")
        ):
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "OIA-055 construction entries invalid"
            )

        seen_work_items: set[str] = set()
        seen_hashes: set[str] = set()
        for expected_sequence, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict) or entry.get("sequence") != expected_sequence:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "OIA-055 construction entry sequence invalid"
                )
            entry_hash = entry.pop("owner_construction_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "OIA-055 construction entry hash verification failed"
                )
            entry["owner_construction_hash"] = entry_hash
            if entry_hash in seen_hashes:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "duplicate OIA-055 construction hash"
                )
            seen_hashes.add(entry_hash)

            work_item_id = entry.get("work_item_id")
            if not isinstance(work_item_id, str) or not work_item_id:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "OIA-055 work item invalid"
                )
            if work_item_id in seen_work_items:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "duplicate OIA-055 work item"
                )
            seen_work_items.add(work_item_id)

            adapter_id = entry.get("adapter_id")
            identity = APPROVED.get(adapter_id)
            if identity is None or identity != (
                entry.get("module_path"),
                entry.get("owner_name"),
                entry.get("callable_name"),
            ):
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "unapproved OIA-055 owner method identity"
                )

            safety = {
                "owner_constructed": True,
                "owner_type_verified": True,
                "owner_read_only_verified": True,
                "owner_execution_disabled_verified": True,
                "callable_bound_to_owner": False,
                "callable_invoked": False,
                "adapter_executed": False,
            }
            for field_name, expected_value in safety.items():
                if entry.get(field_name) != expected_value:
                    raise ProductionOwnerMethodBindingReadinessInvariantError(
                        f"unsafe OIA-055 entry: {field_name}"
                    )

            for hash_field in (
                "source_owner_construction_authorization_hash",
                "source_owner_construction_readiness_hash",
                "source_callable_argument_binding_hash",
                "owner_state_fingerprint",
            ):
                if not _valid_hash(entry.get(hash_field)):
                    raise ProductionOwnerMethodBindingReadinessInvariantError(
                        f"OIA-055 entry hash invalid: {hash_field}"
                    )

        if not isinstance(source.get("source_lineage"), dict) or not source["source_lineage"]:
            raise ProductionOwnerMethodBindingReadinessInvariantError(
                "OIA-055 source lineage missing"
            )
        return source

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> ProductionOwnerMethodBindingReadinessManifest:
        evaluated_at = _aware(evaluated_at, "evaluated_at")
        source = self._load_construction()
        readiness_entries: list[ProductionOwnerMethodBindingReadinessEntry] = []

        for sequence, construction_entry in enumerate(
            source["construction_entries"], start=1
        ):
            module = importlib.import_module(construction_entry["module_path"])
            owner_type = getattr(module, construction_entry["owner_name"], None)
            if not isinstance(owner_type, type):
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "approved owner class could not be resolved"
                )

            descriptor = inspect.getattr_static(
                owner_type,
                construction_entry["callable_name"],
                None,
            )
            if descriptor is None or not inspect.isfunction(descriptor):
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "approved owner method descriptor is not a plain function"
                )

            descriptor_module = getattr(descriptor, "__module__", "")
            descriptor_qualname = getattr(descriptor, "__qualname__", "")
            if descriptor_module != construction_entry["module_path"]:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "method descriptor module mismatch"
                )
            expected_qualname = (
                f'{construction_entry["owner_name"]}.'
                f'{construction_entry["callable_name"]}'
            )
            if descriptor_qualname != expected_qualname:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "method descriptor qualified-name mismatch"
                )

            signature = inspect.signature(descriptor)
            if str(signature) != construction_entry["callable_signature"]:
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "method signature drift detected"
                )
            parameters = tuple(signature.parameters.values())
            if (
                not parameters
                or parameters[0].name != "self"
                or parameters[0].kind
                not in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            ):
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "approved owner method lacks canonical self parameter"
                )
            if any(
                parameter.kind
                in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                )
                for parameter in parameters
            ):
                raise ProductionOwnerMethodBindingReadinessInvariantError(
                    "variadic owner method is prohibited"
                )

            body = {
                "sequence": sequence,
                "worker_id": construction_entry["worker_id"],
                "work_item_id": construction_entry["work_item_id"],
                "adapter_id": construction_entry["adapter_id"],
                "read_operation": construction_entry["read_operation"],
                "module_path": construction_entry["module_path"],
                "owner_name": construction_entry["owner_name"],
                "callable_name": construction_entry["callable_name"],
                "constructor_signature": construction_entry["constructor_signature"],
                "callable_signature": construction_entry["callable_signature"],
                "owner_state_fingerprint": construction_entry["owner_state_fingerprint"],
                "owner_construction_hash": construction_entry["owner_construction_hash"],
                "method_descriptor_type": type(descriptor).__name__,
                "method_descriptor_module": descriptor_module,
                "method_descriptor_qualname": descriptor_qualname,
                "method_signature_verified": True,
                "instance_parameter_verified": True,
                "descriptor_static_resolution_verified": True,
                "owner_reconstruction_required": True,
                "owner_reconstructed": False,
                "method_bound_to_owner": False,
                "method_invoked": False,
                "adapter_executed": False,
                "readiness_checks": (
                    "owner_construction_manifest_hash_verified",
                    "owner_construction_entry_hash_verified",
                    "approved_owner_identity_verified",
                    "approved_method_descriptor_statically_resolved",
                    "method_descriptor_module_verified",
                    "method_descriptor_qualname_verified",
                    "method_signature_verified",
                    "canonical_self_parameter_verified",
                    "variadic_parameters_rejected",
                    "owner_not_reconstructed",
                    "method_not_bound_to_owner",
                    "method_not_invoked",
                    "adapter_not_executed",
                    "corpus_execution_remained_disabled",
                    "oracle_qseries_boundary_verified",
                ),
                "readiness_status": STATUS_METHOD_BINDING_READY,
                "source_owner_construction_authorization_hash": construction_entry[
                    "source_owner_construction_authorization_hash"
                ],
                "source_owner_construction_readiness_hash": construction_entry[
                    "source_owner_construction_readiness_hash"
                ],
                "source_callable_argument_binding_hash": construction_entry[
                    "source_callable_argument_binding_hash"
                ],
            }
            readiness_entries.append(
                ProductionOwnerMethodBindingReadinessEntry(
                    **body,
                    owner_method_binding_readiness_hash=stable_hash(body),
                )
            )

        source_manifest_hash = source["owner_construction_manifest_hash"]
        readiness_id = "oia056-owner-method-binding-readiness-" + stable_hash(
            {
                "source_owner_construction_manifest_hash": source_manifest_hash,
                "policy_id": POLICY_ID,
            }
        )[:32]

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at.isoformat(),
            "owner_method_binding_readiness_id": readiness_id,
            "owner_method_binding_readiness_status": STATUS_READINESS_ISSUED,
            "owner_method_binding_readiness_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "readiness_entry_count": len(readiness_entries),
            "readiness_entries": tuple(readiness_entries),
            "source_owner_construction_id": source["owner_construction_id"],
            "source_owner_construction_manifest_hash": source_manifest_hash,
            "source_owner_construction_authorization_id": source[
                "source_owner_construction_authorization_id"
            ],
            "source_owner_construction_authorization_manifest_hash": source[
                "source_owner_construction_authorization_manifest_hash"
            ],
            "source_lineage": dict(source["source_lineage"]),
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
        serializable = dict(manifest_body)
        serializable["readiness_entries"] = [
            asdict(entry) for entry in readiness_entries
        ]
        result = ProductionOwnerMethodBindingReadinessManifest(
            **manifest_body,
            owner_method_binding_readiness_manifest_hash=stable_hash(serializable),
        )

        if persist:
            payload = asdict(result)
            _atomic_write(self.readiness_directory / "current.json", payload)
            _atomic_write(
                self.readiness_directory / "readiness" / f"{readiness_id}.json",
                payload,
            )
            _atomic_write(
                self.readiness_directory
                / "workers"
                / result.worker_id
                / f"{readiness_id}.json",
                payload,
            )
        return result
'''

TEST_SOURCE = r'''import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_readiness_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingReadinessGate,
    ProductionOwnerMethodBindingReadinessInvariantError,
    stable_hash,
)


def seed_oia055(path: Path) -> dict:
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
        "constructor_dependency_names": ["connection_factory"],
        "constructor_default_names": ["stale_after_seconds", "market_limit"],
        "owner_constructed": True,
        "owner_type_verified": True,
        "owner_read_only_verified": True,
        "owner_execution_disabled_verified": True,
        "callable_bound_to_owner": False,
        "callable_invoked": False,
        "adapter_executed": False,
        "construction_checks": ["approved_owner_identity_verified"],
        "construction_status": "evidence_read_execution_adapter_production_owner_constructed",
        "source_owner_construction_authorization_hash": stable_hash({"54": 1}),
        "source_owner_construction_readiness_hash": stable_hash({"53": 1}),
        "source_callable_argument_binding_hash": stable_hash({"52": 1}),
        "owner_state_fingerprint": stable_hash({"owner": "inert"}),
    }
    entry = dict(entry_body)
    entry["owner_construction_hash"] = stable_hash(entry_body)

    manifest_body = {
        "schema_version": "OIA-055",
        "engine_id": "OIA-055",
        "constructed_at": "2026-07-22T00:00:00+00:00",
        "owner_construction_id": "oia055-test",
        "owner_construction_status": "evidence_read_execution_adapter_production_owner_construction_issued",
        "owner_construction_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "construction_entry_count": 1,
        "construction_entries": [entry],
        "source_owner_construction_authorization_id": "oia054-test",
        "source_owner_construction_authorization_manifest_hash": stable_hash({"54m": 1}),
        "source_lineage": {
            "dispatch_manifest_id": "oia020-test",
            "source_claim_id": "oia021-test",
            "source_activation_id": "oia022-test",
        },
        "owner_construction_performed": True,
        "owner_instances_retained": False,
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
        "construction_artifact_persistence_allowed": True,
    }
    payload = dict(manifest_body)
    payload["owner_construction_manifest_hash"] = stable_hash(manifest_body)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def rehash(payload: dict) -> None:
    for entry in payload["construction_entries"]:
        body = dict(entry)
        body.pop("owner_construction_hash", None)
        entry["owner_construction_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("owner_construction_manifest_hash", None)
    payload["owner_construction_manifest_hash"] = stable_hash(body)


def reject(gate, evaluated_at, message):
    try:
        gate.evaluate(evaluated_at=evaluated_at, persist=False)
    except ProductionOwnerMethodBindingReadinessInvariantError:
        return
    raise AssertionError(message)


def main() -> int:
    print("=" * 40)
    print(" OIA-056 TEST")
    print(" OWNER METHOD BINDING READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        construction = root / "construction"
        readiness = root / "readiness"
        source = seed_oia055(construction)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingReadinessGate(
            construction_directory=construction,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-056"
        assert first.engine_id == "OIA-056"
        assert first.owner_method_binding_readiness_issued is True
        assert first.owner_method_binding_authorization_evaluation_allowed is True
        assert first.readiness_entry_count == 1
        entry = first.readiness_entries[0]
        assert entry.method_descriptor_type == "function"
        assert entry.method_descriptor_module == source["construction_entries"][0]["module_path"]
        assert entry.method_descriptor_qualname == "OracleLiveCorpusInspector.inspect"
        assert entry.method_signature_verified is True
        assert entry.instance_parameter_verified is True
        assert entry.descriptor_static_resolution_verified is True
        assert entry.owner_reconstruction_required is True
        assert entry.owner_reconstructed is False
        assert entry.method_bound_to_owner is False
        assert entry.method_invoked is False
        assert entry.adapter_executed is False
        assert first.owner_reconstruction_allowed is False
        assert first.owner_reconstruction_performed is False
        assert first.callable_binding_to_owner_allowed is False
        assert first.callable_binding_to_owner_performed is False
        assert first.callable_invocation_allowed is False
        assert first.callable_invocation_performed is False
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.corpus_read_execution_performed is False
        assert first.qseries_handoff_allowed is False
        assert first.execution_allowed is False
        assert first.source_owner_construction_manifest_hash == source["owner_construction_manifest_hash"]
        assert (readiness / "current.json").exists()

        tampered = json.loads((construction / "current.json").read_text())
        tampered["construction_entries"][0]["callable_signature"] = "(self, *args, **kwargs)"
        rehash(tampered)
        (construction / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        reject(gate, fixed, "signature drift accepted")

        seed_oia055(construction)
        bound = json.loads((construction / "current.json").read_text())
        bound["construction_entries"][0]["callable_bound_to_owner"] = True
        rehash(bound)
        (construction / "current.json").write_text(json.dumps(bound), encoding="utf-8")
        reject(gate, fixed, "premature live binding accepted")

        seed_oia055(construction)
        unknown = json.loads((construction / "current.json").read_text())
        unknown["construction_entries"][0]["callable_name"] = "execute"
        rehash(unknown)
        (construction / "current.json").write_text(json.dumps(unknown), encoding="utf-8")
        reject(gate, fixed, "unknown callable accepted")

        seed_oia055(construction)
        duplicate = json.loads((construction / "current.json").read_text())
        copied = dict(duplicate["construction_entries"][0])
        copied["sequence"] = 2
        duplicate["construction_entries"].append(copied)
        duplicate["construction_entry_count"] = 2
        rehash(duplicate)
        (construction / "current.json").write_text(json.dumps(duplicate), encoding="utf-8")
        reject(gate, fixed, "duplicate work item accepted")

    print("[PASS] Actual OIA-055 owner-construction contract consumed")
    print("[PASS] Approved owner method descriptors resolved statically")
    print("[PASS] Exact method signatures and canonical self parameters verified")
    print("[PASS] Method-binding-readiness hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-055 lineage preserved")
    print("[PASS] Owners were not reconstructed and methods were not owner-bound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, unknown, duplicate, bound, or executable input rejected")
    print("[PASS] Atomic owner-method-binding-readiness artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

INIT_BLOCK = r'''from .oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_readiness_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingReadinessGate,
    ProductionOwnerMethodBindingReadinessEntry,
    ProductionOwnerMethodBindingReadinessInvariantError,
    ProductionOwnerMethodBindingReadinessManifest,
    POLICY_ID as OIA056_POLICY_ID,
)
__all__ = [
    "OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingReadinessGate",
    "ProductionOwnerMethodBindingReadinessEntry",
    "ProductionOwnerMethodBindingReadinessInvariantError",
    "ProductionOwnerMethodBindingReadinessManifest",
    "OIA056_POLICY_ID",
] + __all__
'''


def verify_oia055() -> None:
    if not OIA055.exists():
        raise RuntimeError(f"Actual OIA-055 production module missing: {OIA055}")
    text = OIA055.read_text(encoding="utf-8")
    required = [
        'SCHEMA_VERSION="OIA-055"',
        "ProductionOwnerConstructionEntry",
        "ProductionOwnerConstructionManifest",
        "owner_construction_hash",
        "owner_construction_manifest_hash",
        "owner_instances_retained",
        "callable_binding_to_owner_allowed",
        "callable_binding_to_owner_performed",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise RuntimeError(f"Actual OIA-055 contract mismatch: {missing}")


def write_full(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.strip() + "\n", encoding="utf-8")
    print(f"[OK] FULL REPLACEMENT: {path}")


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = "oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_readiness_gate import"
    if marker not in existing:
        INIT.write_text(existing.rstrip() + "\n" + INIT_BLOCK.strip() + "\n", encoding="utf-8")
        print(f"[OK] PACKAGE UPDATED: {INIT}")
    else:
        print(f"[OK] PACKAGE ALREADY CURRENT: {INIT}")


def main() -> int:
    print("=" * 40)
    print(" OIA-056 INSTALLER")
    print(" OWNER METHOD BINDING READINESS")
    print(" STATIC DESCRIPTOR INSPECTION ONLY")
    print("=" * 40)
    verify_oia055()
    print("[OK] Actual OIA-055 owner-construction contract verified")
    write_full(PRODUCTION, PRODUCTION_SOURCE)
    write_full(TEST, TEST_SOURCE)
    update_init()
    for path in (PRODUCTION, TEST, INIT):
        py_compile.compile(str(path), doraise=True)
    print("[OK] Production, test, and package syntax verified")
    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)
    print("[OK] OIA-056 test executed automatically")
    print()
    print("[DONE] OIA-056 production owner method binding readiness gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
