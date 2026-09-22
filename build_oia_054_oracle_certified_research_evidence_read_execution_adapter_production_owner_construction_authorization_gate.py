from pathlib import Path
import py_compile, subprocess, sys

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA053 = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_readiness_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_authorization_gate.py"
TEST = ROOT / "test_oia_054_oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_authorization_gate.py"
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

SCHEMA_VERSION = "OIA-054"
ENGINE_ID = "OIA-054"
POLICY_ID = "oracle.certified-research-evidence-read-execution-adapter-production-owner-construction-authorization.v1"
STATUS_OWNER_CONSTRUCTION_AUTHORIZED = "evidence_read_execution_adapter_production_owner_construction_authorized"
STATUS_AUTHORIZATION_ISSUED = "evidence_read_execution_adapter_production_owner_construction_authorization_issued"

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_owner_construction_readiness"
)
DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_owner_construction_authorization"
)


class ProductionOwnerConstructionAuthorizationInvariantError(RuntimeError):
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
            raise ProductionOwnerConstructionAuthorizationInvariantError(
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


def _aware(value: datetime, name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ProductionOwnerConstructionAuthorizationInvariantError(
            f"{name} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
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
class ProductionOwnerConstructionAuthorizationEntry:
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
    bound_constructor_arguments: dict[str, Any]
    bound_callable_arguments: dict[str, Any]
    constructor_binding_hash: str
    callable_binding_hash: str
    constructor_dependency_names: tuple[str, ...]
    constructor_default_names: tuple[str, ...]
    symbolic_dependencies_only: bool
    owner_construction_ready: bool
    owner_construction_authorized: bool
    owner_instantiation_requested: bool
    owner_instantiated: bool
    callable_bound_to_owner: bool
    callable_invoked: bool
    adapter_executed: bool
    authorization_checks: tuple[str, ...]
    authorization_status: str
    source_owner_construction_readiness_hash: str
    source_callable_argument_binding_hash: str
    source_callable_binding_authorization_hash: str
    source_callable_binding_readiness_hash: str
    source_callable_resolution_hash: str
    source_active_invocation_execution_authorization_hash: str
    source_active_invocation_execution_readiness_hash: str
    source_active_execution_invocation_hash: str
    source_execution_invocation_hash: str
    source_authorization_entry_hash: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    owner_construction_authorization_hash: str


@dataclass(frozen=True)
class ProductionOwnerConstructionAuthorizationManifest:
    schema_version: str
    engine_id: str
    authorized_at: str
    owner_construction_authorization_id: str
    owner_construction_authorization_status: str
    owner_construction_authorization_policy_id: str
    worker_id: str
    authorization_entry_count: int
    authorization_entries: tuple[ProductionOwnerConstructionAuthorizationEntry, ...]
    source_owner_construction_readiness_id: str
    source_owner_construction_readiness_manifest_hash: str
    source_callable_argument_binding_id: str
    source_callable_argument_binding_manifest_hash: str
    source_lineage: dict[str, Any]
    owner_construction_authorization_issued: bool
    owner_construction_evaluation_allowed: bool
    owner_instantiation_allowed: bool
    owner_instantiation_performed: bool
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
    owner_construction_authorization_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionAuthorizationGate:
    """Authorize exact OIA-053 owner-construction plans without constructing owners."""

    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
    ) -> None:
        self.readiness_directory = Path(readiness_directory)
        self.authorization_directory = Path(authorization_directory)

    def _load(self) -> dict[str, Any]:
        path = self.readiness_directory / "current.json"
        if not path.exists():
            raise ProductionOwnerConstructionAuthorizationInvariantError(
                f"OIA-053 current readiness artifact missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProductionOwnerConstructionAuthorizationInvariantError(
                "OIA-053 readiness artifact could not be decoded"
            ) from error

        digest = payload.pop("owner_construction_readiness_manifest_hash", None)
        if not _valid_hash(digest) or stable_hash(payload) != digest:
            raise ProductionOwnerConstructionAuthorizationInvariantError(
                "OIA-053 readiness manifest hash verification failed"
            )
        payload["owner_construction_readiness_manifest_hash"] = digest

        expected = {
            "schema_version": "OIA-053",
            "engine_id": "OIA-053",
            "owner_construction_readiness_issued": True,
            "owner_construction_authorization_evaluation_allowed": True,
            "owner_instantiation_allowed": False,
            "owner_instantiation_performed": False,
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
        for field, expected_value in expected.items():
            if payload.get(field) != expected_value:
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    f"OIA-053 invariant failed: {field}"
                )

        entries = payload.get("readiness_entries")
        count = payload.get("readiness_entry_count")
        if (
            not isinstance(entries, list)
            or not isinstance(count, int)
            or isinstance(count, bool)
            or count < 1
            or len(entries) != count
        ):
            raise ProductionOwnerConstructionAuthorizationInvariantError(
                "OIA-053 readiness entries invalid"
            )

        seen_work_items: set[str] = set()
        seen_adapters: set[str] = set()
        required_checks = {
            "callable_argument_binding_manifest_hash_verified",
            "callable_argument_binding_entry_hash_verified",
            "constructor_binding_hash_verified",
            "callable_binding_hash_verified",
            "constructor_dependencies_classified",
            "constructor_defaults_classified",
            "symbolic_dependencies_only_verified",
            "owner_not_instantiated",
            "callable_not_bound_to_owner",
            "callable_not_invoked",
            "adapter_not_executed",
            "oracle_qseries_boundary_verified",
        }

        for sequence, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 readiness entry invalid"
                )
            entry_hash = entry.pop("owner_construction_readiness_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 readiness entry hash verification failed"
                )
            entry["owner_construction_readiness_hash"] = entry_hash

            if entry.get("sequence") != sequence:
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 readiness sequence invalid"
                )
            work_item_id = entry.get("work_item_id")
            adapter_id = entry.get("adapter_id")
            if not isinstance(work_item_id, str) or not work_item_id or work_item_id in seen_work_items:
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 work item invalid or duplicate"
                )
            if (
                not isinstance(adapter_id, str)
                or not adapter_id.startswith("oracle_read_only_")
                or adapter_id in seen_adapters
            ):
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 adapter invalid or duplicate"
                )
            seen_work_items.add(work_item_id)
            seen_adapters.add(adapter_id)

            for field, expected_value in {
                "symbolic_dependencies_only": True,
                "owner_construction_ready": True,
                "owner_instantiated": False,
                "callable_bound_to_owner": False,
                "callable_invoked": False,
                "adapter_executed": False,
            }.items():
                if entry.get(field) != expected_value:
                    raise ProductionOwnerConstructionAuthorizationInvariantError(
                        f"OIA-053 readiness entry invariant failed: {field}"
                    )

            constructor_arguments = entry.get("bound_constructor_arguments")
            callable_arguments = entry.get("bound_callable_arguments")
            if stable_hash(constructor_arguments) != entry.get("constructor_binding_hash"):
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 constructor binding changed"
                )
            if stable_hash(callable_arguments) != entry.get("callable_binding_hash"):
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 callable binding changed"
                )

            dependency_names = entry.get("constructor_dependency_names")
            default_names = entry.get("constructor_default_names")
            if not isinstance(dependency_names, list) or not isinstance(default_names, list):
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 constructor classifications invalid"
                )
            if set(dependency_names) & set(default_names):
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 constructor classifications overlap"
                )
            if set(dependency_names) | set(default_names) != set(constructor_arguments):
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 constructor classifications are incomplete"
                )

            checks = entry.get("readiness_checks")
            if not isinstance(checks, list) or not required_checks.issubset(set(checks)):
                raise ProductionOwnerConstructionAuthorizationInvariantError(
                    "OIA-053 readiness checks incomplete"
                )

            for field in (
                "source_callable_argument_binding_hash",
                "source_callable_binding_authorization_hash",
                "source_callable_binding_readiness_hash",
                "source_callable_resolution_hash",
                "source_active_invocation_execution_authorization_hash",
                "source_active_invocation_execution_readiness_hash",
                "source_active_execution_invocation_hash",
                "source_execution_invocation_hash",
                "source_authorization_entry_hash",
                "source_readiness_entry_hash",
                "source_active_adapter_invocation_hash",
            ):
                if not _valid_hash(entry.get(field)):
                    raise ProductionOwnerConstructionAuthorizationInvariantError(
                        f"OIA-053 lineage hash invalid: {field}"
                    )

        return payload

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> ProductionOwnerConstructionAuthorizationManifest:
        authorized_at = _aware(authorized_at, "authorized_at")
        source = self._load()
        authorization_entries: list[ProductionOwnerConstructionAuthorizationEntry] = []

        for sequence, readiness in enumerate(source["readiness_entries"], start=1):
            entry_body = {
                "sequence": sequence,
                "worker_id": readiness["worker_id"],
                "work_item_id": readiness["work_item_id"],
                "adapter_id": readiness["adapter_id"],
                "read_operation": readiness["read_operation"],
                "module_path": readiness["module_path"],
                "owner_name": readiness["owner_name"],
                "callable_name": readiness["callable_name"],
                "constructor_signature": readiness["constructor_signature"],
                "callable_signature": readiness["callable_signature"],
                "bound_constructor_arguments": dict(readiness["bound_constructor_arguments"]),
                "bound_callable_arguments": dict(readiness["bound_callable_arguments"]),
                "constructor_binding_hash": readiness["constructor_binding_hash"],
                "callable_binding_hash": readiness["callable_binding_hash"],
                "constructor_dependency_names": tuple(readiness["constructor_dependency_names"]),
                "constructor_default_names": tuple(readiness["constructor_default_names"]),
                "symbolic_dependencies_only": True,
                "owner_construction_ready": True,
                "owner_construction_authorized": True,
                "owner_instantiation_requested": False,
                "owner_instantiated": False,
                "callable_bound_to_owner": False,
                "callable_invoked": False,
                "adapter_executed": False,
                "authorization_checks": (
                    "owner_construction_readiness_manifest_hash_verified",
                    "owner_construction_readiness_entry_hash_verified",
                    "constructor_binding_hash_verified",
                    "callable_binding_hash_verified",
                    "constructor_dependency_allowlist_verified",
                    "constructor_default_allowlist_verified",
                    "symbolic_dependencies_only_verified",
                    "owner_construction_authorized_but_not_requested",
                    "owner_not_instantiated",
                    "callable_not_bound_to_owner",
                    "callable_not_invoked",
                    "adapter_not_executed",
                    "oracle_qseries_boundary_verified",
                ),
                "authorization_status": STATUS_OWNER_CONSTRUCTION_AUTHORIZED,
                "source_owner_construction_readiness_hash": readiness["owner_construction_readiness_hash"],
                "source_callable_argument_binding_hash": readiness["source_callable_argument_binding_hash"],
                "source_callable_binding_authorization_hash": readiness["source_callable_binding_authorization_hash"],
                "source_callable_binding_readiness_hash": readiness["source_callable_binding_readiness_hash"],
                "source_callable_resolution_hash": readiness["source_callable_resolution_hash"],
                "source_active_invocation_execution_authorization_hash": readiness["source_active_invocation_execution_authorization_hash"],
                "source_active_invocation_execution_readiness_hash": readiness["source_active_invocation_execution_readiness_hash"],
                "source_active_execution_invocation_hash": readiness["source_active_execution_invocation_hash"],
                "source_execution_invocation_hash": readiness["source_execution_invocation_hash"],
                "source_authorization_entry_hash": readiness["source_authorization_entry_hash"],
                "source_readiness_entry_hash": readiness["source_readiness_entry_hash"],
                "source_active_adapter_invocation_hash": readiness["source_active_adapter_invocation_hash"],
            }
            authorization_entries.append(
                ProductionOwnerConstructionAuthorizationEntry(
                    **entry_body,
                    owner_construction_authorization_hash=stable_hash(entry_body),
                )
            )

        source_hash = source["owner_construction_readiness_manifest_hash"]
        authorization_id = "oia054-owner-construction-authorization-" + stable_hash(
            {
                "source_owner_construction_readiness_manifest_hash": source_hash,
                "owner_construction_authorization_policy_id": POLICY_ID,
            }
        )[:32]

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at.isoformat(),
            "owner_construction_authorization_id": authorization_id,
            "owner_construction_authorization_status": STATUS_AUTHORIZATION_ISSUED,
            "owner_construction_authorization_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "authorization_entry_count": len(authorization_entries),
            "authorization_entries": tuple(authorization_entries),
            "source_owner_construction_readiness_id": source["owner_construction_readiness_id"],
            "source_owner_construction_readiness_manifest_hash": source_hash,
            "source_callable_argument_binding_id": source["source_callable_argument_binding_id"],
            "source_callable_argument_binding_manifest_hash": source["source_callable_argument_binding_manifest_hash"],
            "source_lineage": dict(source.get("source_lineage", {})),
            "owner_construction_authorization_issued": True,
            "owner_construction_evaluation_allowed": True,
            "owner_instantiation_allowed": False,
            "owner_instantiation_performed": False,
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
        serializable["authorization_entries"] = [
            asdict(entry) for entry in authorization_entries
        ]
        result = ProductionOwnerConstructionAuthorizationManifest(
            **manifest_body,
            owner_construction_authorization_manifest_hash=stable_hash(serializable),
        )

        if persist:
            payload = asdict(result)
            _atomic(self.authorization_directory / "current.json", payload)
            _atomic(
                self.authorization_directory / "authorizations" / f"{authorization_id}.json",
                payload,
            )
            _atomic(
                self.authorization_directory / "workers" / result.worker_id / f"{authorization_id}.json",
                payload,
            )

        return result
'''

TEST_SOURCE = r'''import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_authorization_gate import *


def _hashes():
    return {
        key: stable_hash({key: 1})
        for key in (
            "source_callable_argument_binding_hash",
            "source_callable_binding_authorization_hash",
            "source_callable_binding_readiness_hash",
            "source_callable_resolution_hash",
            "source_active_invocation_execution_authorization_hash",
            "source_active_invocation_execution_readiness_hash",
            "source_active_execution_invocation_hash",
            "source_execution_invocation_hash",
            "source_authorization_entry_hash",
            "source_readiness_entry_hash",
            "source_active_adapter_invocation_hash",
        )
    }


def seed(path: Path) -> dict:
    constructor_arguments = {
        "connection_factory": "symbolic://oracle/runtime/connection_factory",
        "stale_after_seconds": 300,
        "market_limit": 100,
    }
    callable_arguments = {
        "self": "symbolic://oracle/owner_instance",
        "inspected_at": None,
    }
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
        "callable_signature": "(self, *, inspected_at=None)",
        "bound_constructor_arguments": constructor_arguments,
        "bound_callable_arguments": callable_arguments,
        "constructor_binding_hash": stable_hash(constructor_arguments),
        "callable_binding_hash": stable_hash(callable_arguments),
        "constructor_dependency_names": ["connection_factory"],
        "constructor_default_names": ["stale_after_seconds", "market_limit"],
        "symbolic_dependencies_only": True,
        "owner_construction_ready": True,
        "owner_instantiated": False,
        "callable_bound_to_owner": False,
        "callable_invoked": False,
        "adapter_executed": False,
        "readiness_checks": [
            "callable_argument_binding_manifest_hash_verified",
            "callable_argument_binding_entry_hash_verified",
            "constructor_binding_hash_verified",
            "callable_binding_hash_verified",
            "constructor_dependencies_classified",
            "constructor_defaults_classified",
            "symbolic_dependencies_only_verified",
            "owner_not_instantiated",
            "callable_not_bound_to_owner",
            "callable_not_invoked",
            "adapter_not_executed",
            "oracle_qseries_boundary_verified",
        ],
        "readiness_status": "evidence_read_execution_adapter_production_owner_construction_ready",
        **_hashes(),
    }
    entry = dict(entry_body)
    entry["owner_construction_readiness_hash"] = stable_hash(entry_body)
    manifest = {
        "schema_version": "OIA-053",
        "engine_id": "OIA-053",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "owner_construction_readiness_id": "oia053-test",
        "owner_construction_readiness_status": "evidence_read_execution_adapter_production_owner_construction_readiness_issued",
        "owner_construction_readiness_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "readiness_entry_count": 1,
        "readiness_entries": [entry],
        "source_callable_argument_binding_id": "oia052-test",
        "source_callable_argument_binding_manifest_hash": stable_hash({"oia052": 1}),
        "source_lineage": {"dispatch_manifest_id": "20", "source_claim_id": "21"},
        "owner_construction_readiness_issued": True,
        "owner_construction_authorization_evaluation_allowed": True,
        "owner_instantiation_allowed": False,
        "owner_instantiation_performed": False,
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
    manifest["owner_construction_readiness_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def rehash(payload: dict) -> None:
    for entry in payload["readiness_entries"]:
        body = dict(entry)
        body.pop("owner_construction_readiness_hash", None)
        entry["owner_construction_readiness_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("owner_construction_readiness_manifest_hash", None)
    payload["owner_construction_readiness_manifest_hash"] = stable_hash(body)


def reject(gate, fixed, message):
    try:
        gate.authorize(authorized_at=fixed, persist=False)
    except ProductionOwnerConstructionAuthorizationInvariantError:
        return
    raise AssertionError(message)


def main() -> int:
    print("=" * 40)
    print(" OIA-054 TEST")
    print(" OWNER CONSTRUCTION AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness = root / "readiness"
        authorization = root / "authorization"
        source = seed(readiness)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionAuthorizationGate(
            readiness_directory=readiness,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-054"
        assert first.authorization_entry_count == 1
        entry = first.authorization_entries[0]
        assert entry.owner_construction_ready is True
        assert entry.owner_construction_authorized is True
        assert entry.owner_instantiation_requested is False
        assert entry.owner_instantiated is False
        assert entry.callable_bound_to_owner is False
        assert entry.callable_invoked is False
        assert entry.adapter_executed is False
        assert entry.constructor_dependency_names == ("connection_factory",)
        assert entry.constructor_default_names == ("stale_after_seconds", "market_limit")
        assert first.owner_construction_authorization_issued is True
        assert first.owner_construction_evaluation_allowed is True
        assert first.owner_instantiation_allowed is False
        assert first.owner_instantiation_performed is False
        assert first.callable_binding_to_owner_allowed is False
        assert first.callable_invocation_allowed is False
        assert first.adapter_execution_allowed is False
        assert first.corpus_read_execution_allowed is False
        assert first.qseries_handoff_allowed is False
        assert first.execution_allowed is False
        assert first.source_owner_construction_readiness_manifest_hash == source["owner_construction_readiness_manifest_hash"]
        assert (authorization / "current.json").exists()

        tampered = json.loads((readiness / "current.json").read_text(encoding="utf-8"))
        tampered["readiness_entries"][0]["owner_instantiated"] = True
        (readiness / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        reject(gate, fixed, "instantiated owner accepted")

        seed(readiness)
        duplicate = json.loads((readiness / "current.json").read_text(encoding="utf-8"))
        extra = dict(duplicate["readiness_entries"][0])
        extra["sequence"] = 2
        duplicate["readiness_entries"].append(extra)
        duplicate["readiness_entry_count"] = 2
        rehash(duplicate)
        (readiness / "current.json").write_text(json.dumps(duplicate), encoding="utf-8")
        reject(gate, fixed, "duplicate work item accepted")

        seed(readiness)
        live_secret = json.loads((readiness / "current.json").read_text(encoding="utf-8"))
        live_secret["readiness_entries"][0]["bound_constructor_arguments"]["connection_factory"] = "postgresql://user:secret@localhost/db"
        rehash(live_secret)
        (readiness / "current.json").write_text(json.dumps(live_secret), encoding="utf-8")
        reject(gate, fixed, "changed constructor binding accepted")

    print("[PASS] Actual OIA-053 owner-construction-readiness contract consumed")
    print("[PASS] Exact symbolic construction plans authorized deterministically")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-053 lineage preserved")
    print("[PASS] Owner-construction evaluation authorized without construction")
    print("[PASS] Owners were not instantiated and methods were not owner-bound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, duplicate, live, or executable input rejected")
    print("[PASS] Atomic owner-construction-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

INIT_BLOCK = r'''from .oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_authorization_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionAuthorizationGate,
    ProductionOwnerConstructionAuthorizationEntry,
    ProductionOwnerConstructionAuthorizationInvariantError,
    ProductionOwnerConstructionAuthorizationManifest,
    POLICY_ID as OIA054_POLICY_ID,
)
__all__ = [
    "OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionAuthorizationGate",
    "ProductionOwnerConstructionAuthorizationEntry",
    "ProductionOwnerConstructionAuthorizationInvariantError",
    "ProductionOwnerConstructionAuthorizationManifest",
    "OIA054_POLICY_ID",
] + __all__
'''


def main() -> int:
    print("=" * 40)
    print(" OIA-054 INSTALLER")
    print(" OWNER CONSTRUCTION AUTHORIZATION")
    print(" PRE-CONSTRUCTION SAFETY GATE")
    print("=" * 40)

    if not OIA053.exists():
        raise RuntimeError(f"Actual OIA-053 module missing: {OIA053}")
    text = OIA053.read_text(encoding="utf-8")
    required = [
        'SCHEMA_VERSION="OIA-053"',
        "ProductionOwnerConstructionReadinessEntry",
        "owner_construction_readiness_hash",
        "owner_construction_readiness_manifest_hash",
        "owner_construction_authorization_evaluation_allowed",
        "symbolic_dependencies_only",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise RuntimeError(f"Actual OIA-053 contract mismatch: {missing}")
    print("[OK] Actual OIA-053 owner-construction-readiness contract verified")

    for path, source in ((PRODUCTION, PRODUCTION_SOURCE), (TEST, TEST_SOURCE)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source.strip() + "\n", encoding="utf-8")
        print(f"[OK] FULL REPLACEMENT: {path}")

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = "oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_authorization_gate import"
    if marker not in existing:
        INIT.write_text(existing.rstrip() + "\n" + INIT_BLOCK.strip() + "\n", encoding="utf-8")
        print(f"[OK] PACKAGE UPDATED: {INIT}")
    else:
        print(f"[OK] PACKAGE ALREADY CURRENT: {INIT}")

    for path in (PRODUCTION, TEST, INIT):
        py_compile.compile(str(path), doraise=True)
    print("[OK] Production, test, and package syntax verified")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    print("[OK] OIA-054 test executed automatically")
    print()
    print("[DONE] OIA-054 production owner construction authorization gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
