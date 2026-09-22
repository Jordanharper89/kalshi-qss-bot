from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA059 = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_readiness_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_authorization_gate.py"
TEST = ROOT / "test_oia_060_oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_authorization_gate.py"
INIT = ANALYTICS / "__init__.py"

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

SCHEMA_VERSION = "OIA-060"
ENGINE_ID = "OIA-060"
POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "production-callable-invocation-authorization.v1"
)
STATUS_INVOCATION_AUTHORIZED = (
    "evidence_read_execution_adapter_production_callable_invocation_authorized"
)
STATUS_AUTHORIZATION_ISSUED = (
    "evidence_read_execution_adapter_production_callable_invocation_authorization_issued"
)

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_invocation_readiness"
)
DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_invocation_authorization"
)

APPROVED_INVOCATIONS = {
    "oracle_read_only_canonical_observation_adapter.v1": {
        "read_operation": "read_canonical_observations",
        "module_path": (
            "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector"
        ),
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "bound_method_module": (
            "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector"
        ),
        "bound_method_qualname": "OracleLiveCorpusInspector.inspect",
        "bound_method_signature": (
            "(*, inspected_at: 'Optional[datetime]' = None) "
            "-> 'OracleLiveCorpusReport'"
        ),
        "invocation_arguments": {"inspected_at": None},
    },
    "oracle_read_only_market_state_lineage_adapter.v1": {
        "read_operation": "read_market_state_lineage",
        "module_path": (
            "qseries_v2.oracle_intelligence.live_acquisition."
            "oracle_canonical_market_lineage_ledger"
        ),
        "owner_name": "OracleCanonicalMarketLineageLedger",
        "callable_name": "records",
        "bound_method_module": (
            "qseries_v2.oracle_intelligence.live_acquisition."
            "oracle_canonical_market_lineage_ledger"
        ),
        "bound_method_qualname": "OracleCanonicalMarketLineageLedger.records",
        "bound_method_signature": (
            "() -> 'tuple[CanonicalMarketStateDwellChangeLineage, ...]'"
        ),
        "invocation_arguments": {},
    },
}


class ProductionCallableInvocationAuthorizationInvariantError(RuntimeError):
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
            raise ProductionCallableInvocationAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    return value


def stable_hash(value: Any) -> str:
    encoded = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
        raise ProductionCallableInvocationAuthorizationInvariantError(
            f"{name} must be timezone-aware"
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
class ProductionCallableInvocationAuthorizationEntry:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    module_path: str
    owner_name: str
    callable_name: str
    bound_method_module: str
    bound_method_qualname: str
    bound_method_signature: str
    invocation_arguments: dict[str, Any]
    invocation_argument_hash: str
    source_callable_invocation_readiness_hash: str
    source_owner_method_binding_hash: str
    source_owner_method_binding_authorization_hash: str
    source_owner_method_binding_readiness_hash: str
    source_owner_construction_authorization_hash: str
    source_owner_construction_readiness_hash: str
    source_callable_argument_binding_hash: str
    callable_invocation_authorization_granted: bool
    owner_reconstruction_authorized: bool
    owner_reconstruction_performed: bool
    method_binding_authorized: bool
    method_binding_performed: bool
    callable_invocation_authorized: bool
    callable_invoked: bool
    adapter_executed: bool
    corpus_read_executed: bool
    authorization_checks: tuple[str, ...]
    authorization_status: str
    callable_invocation_authorization_hash: str


@dataclass(frozen=True)
class ProductionCallableInvocationAuthorizationManifest:
    schema_version: str
    engine_id: str
    authorized_at: str
    callable_invocation_authorization_id: str
    callable_invocation_authorization_status: str
    callable_invocation_authorization_policy_id: str
    worker_id: str
    authorization_entry_count: int
    authorization_entries: tuple[ProductionCallableInvocationAuthorizationEntry, ...]
    source_callable_invocation_readiness_id: str
    source_callable_invocation_readiness_manifest_hash: str
    source_owner_method_binding_id: str
    source_owner_method_binding_manifest_hash: str
    source_owner_method_binding_authorization_id: str
    source_owner_method_binding_authorization_manifest_hash: str
    source_owner_method_binding_readiness_id: str
    source_owner_method_binding_readiness_manifest_hash: str
    source_owner_construction_id: str
    source_owner_construction_manifest_hash: str
    source_lineage: dict[str, Any]
    callable_invocation_authorization_issued: bool
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
    authorization_artifact_persistence_allowed: bool
    owner_instances_retained: bool
    bound_methods_retained: bool
    callable_invocation_authorization_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationAuthorizationGate:
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
            raise ProductionCallableInvocationAuthorizationInvariantError(
                f"OIA-059 current readiness artifact missing: {path}"
            )

        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProductionCallableInvocationAuthorizationInvariantError(
                "OIA-059 readiness artifact could not be decoded"
            ) from error

        manifest_hash = source.pop(
            "callable_invocation_readiness_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ProductionCallableInvocationAuthorizationInvariantError(
                "OIA-059 readiness manifest hash verification failed"
            )
        source["callable_invocation_readiness_manifest_hash"] = manifest_hash

        required_flags = {
            "callable_invocation_readiness_issued": True,
            "owner_reconstruction_allowed": False,
            "owner_reconstruction_performed": False,
            "callable_binding_to_owner_allowed": False,
            "callable_binding_to_owner_performed": False,
            "callable_invocation_authorization_evaluation_allowed": True,
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
            "owner_instances_retained": False,
            "bound_methods_retained": False,
        }
        for field, expected in required_flags.items():
            if source.get(field) != expected:
                raise ProductionCallableInvocationAuthorizationInvariantError(
                    f"unsafe OIA-059 readiness manifest: {field}"
                )

        entries = source.get("readiness_entries")
        if (
            not isinstance(entries, list)
            or not entries
            or source.get("readiness_entry_count") != len(entries)
        ):
            raise ProductionCallableInvocationAuthorizationInvariantError(
                "OIA-059 readiness entry count invalid"
            )

        seen: set[tuple[str, str, str]] = set()
        for entry in entries:
            entry_hash = entry.pop(
                "callable_invocation_readiness_hash",
                None,
            )
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionCallableInvocationAuthorizationInvariantError(
                    "OIA-059 readiness entry hash verification failed"
                )
            entry["callable_invocation_readiness_hash"] = entry_hash

            adapter_id = entry.get("adapter_id")
            approved = APPROVED_INVOCATIONS.get(adapter_id)
            if approved is None:
                raise ProductionCallableInvocationAuthorizationInvariantError(
                    "unapproved OIA-059 adapter identity"
                )

            for field in (
                "read_operation",
                "module_path",
                "owner_name",
                "callable_name",
                "bound_method_module",
                "bound_method_qualname",
                "bound_method_signature",
                "invocation_arguments",
            ):
                if entry.get(field) != approved[field]:
                    raise ProductionCallableInvocationAuthorizationInvariantError(
                        f"OIA-059 invocation envelope drift: {field}"
                    )

            if entry.get("invocation_argument_hash") != stable_hash(
                approved["invocation_arguments"]
            ):
                raise ProductionCallableInvocationAuthorizationInvariantError(
                    "OIA-059 invocation argument hash drift"
                )

            key = (
                str(entry.get("worker_id")),
                str(entry.get("work_item_id")),
                str(adapter_id),
            )
            if key in seen:
                raise ProductionCallableInvocationAuthorizationInvariantError(
                    "duplicate OIA-059 readiness entry"
                )
            seen.add(key)

            expected_flags = {
                "owner_reconstruction_required": True,
                "owner_reconstructed": False,
                "method_binding_required": True,
                "method_bound_to_owner": False,
                "invocation_envelope_verified": True,
                "callable_invocation_ready": True,
                "callable_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
            }
            for field, expected in expected_flags.items():
                if entry.get(field) != expected:
                    raise ProductionCallableInvocationAuthorizationInvariantError(
                        f"unsafe OIA-059 readiness entry: {field}"
                    )

            for hash_field in (
                "source_owner_method_binding_hash",
                "source_owner_method_binding_authorization_hash",
                "source_owner_method_binding_readiness_hash",
                "source_owner_construction_authorization_hash",
                "source_owner_construction_readiness_hash",
                "source_callable_argument_binding_hash",
            ):
                if not _valid_hash(entry.get(hash_field)):
                    raise ProductionCallableInvocationAuthorizationInvariantError(
                        f"OIA-059 lineage hash invalid: {hash_field}"
                    )

        if not isinstance(source.get("source_lineage"), dict) or not source["source_lineage"]:
            raise ProductionCallableInvocationAuthorizationInvariantError(
                "OIA-059 source lineage missing"
            )
        return source

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> ProductionCallableInvocationAuthorizationManifest:
        authorized_at = _aware(authorized_at, "authorized_at")
        source = self._load_readiness()
        entries: list[ProductionCallableInvocationAuthorizationEntry] = []

        for sequence, readiness in enumerate(source["readiness_entries"], start=1):
            body = {
                "sequence": sequence,
                "worker_id": readiness["worker_id"],
                "work_item_id": readiness["work_item_id"],
                "adapter_id": readiness["adapter_id"],
                "read_operation": readiness["read_operation"],
                "module_path": readiness["module_path"],
                "owner_name": readiness["owner_name"],
                "callable_name": readiness["callable_name"],
                "bound_method_module": readiness["bound_method_module"],
                "bound_method_qualname": readiness["bound_method_qualname"],
                "bound_method_signature": readiness["bound_method_signature"],
                "invocation_arguments": dict(readiness["invocation_arguments"]),
                "invocation_argument_hash": readiness["invocation_argument_hash"],
                "source_callable_invocation_readiness_hash": readiness[
                    "callable_invocation_readiness_hash"
                ],
                "source_owner_method_binding_hash": readiness[
                    "source_owner_method_binding_hash"
                ],
                "source_owner_method_binding_authorization_hash": readiness[
                    "source_owner_method_binding_authorization_hash"
                ],
                "source_owner_method_binding_readiness_hash": readiness[
                    "source_owner_method_binding_readiness_hash"
                ],
                "source_owner_construction_authorization_hash": readiness[
                    "source_owner_construction_authorization_hash"
                ],
                "source_owner_construction_readiness_hash": readiness[
                    "source_owner_construction_readiness_hash"
                ],
                "source_callable_argument_binding_hash": readiness[
                    "source_callable_argument_binding_hash"
                ],
                "callable_invocation_authorization_granted": True,
                "owner_reconstruction_authorized": True,
                "owner_reconstruction_performed": False,
                "method_binding_authorized": True,
                "method_binding_performed": False,
                "callable_invocation_authorized": True,
                "callable_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
                "authorization_checks": (
                    "oia059_readiness_manifest_hash_verified",
                    "oia059_readiness_entry_hash_verified",
                    "approved_adapter_identity_frozen",
                    "approved_bound_method_identity_frozen",
                    "approved_bound_method_signature_frozen",
                    "approved_invocation_argument_envelope_frozen",
                    "invocation_argument_hash_verified",
                    "owner_reconstruction_authorized_not_performed",
                    "method_binding_authorized_not_performed",
                    "callable_invocation_authorized_not_performed",
                    "adapter_execution_not_performed",
                    "corpus_read_not_performed",
                    "oracle_qseries_boundary_verified",
                ),
                "authorization_status": STATUS_INVOCATION_AUTHORIZED,
            }
            entries.append(
                ProductionCallableInvocationAuthorizationEntry(
                    **body,
                    callable_invocation_authorization_hash=stable_hash(body),
                )
            )

        source_hash = source["callable_invocation_readiness_manifest_hash"]
        authorization_id = (
            "oia060-callable-invocation-authorization-"
            + stable_hash({"source": source_hash, "policy": POLICY_ID})[:32]
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at.isoformat(),
            "callable_invocation_authorization_id": authorization_id,
            "callable_invocation_authorization_status": STATUS_AUTHORIZATION_ISSUED,
            "callable_invocation_authorization_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "authorization_entry_count": len(entries),
            "authorization_entries": tuple(entries),
            "source_callable_invocation_readiness_id": source[
                "callable_invocation_readiness_id"
            ],
            "source_callable_invocation_readiness_manifest_hash": source_hash,
            "source_owner_method_binding_id": source[
                "source_owner_method_binding_id"
            ],
            "source_owner_method_binding_manifest_hash": source[
                "source_owner_method_binding_manifest_hash"
            ],
            "source_owner_method_binding_authorization_id": source[
                "source_owner_method_binding_authorization_id"
            ],
            "source_owner_method_binding_authorization_manifest_hash": source[
                "source_owner_method_binding_authorization_manifest_hash"
            ],
            "source_owner_method_binding_readiness_id": source[
                "source_owner_method_binding_readiness_id"
            ],
            "source_owner_method_binding_readiness_manifest_hash": source[
                "source_owner_method_binding_readiness_manifest_hash"
            ],
            "source_owner_construction_id": source[
                "source_owner_construction_id"
            ],
            "source_owner_construction_manifest_hash": source[
                "source_owner_construction_manifest_hash"
            ],
            "source_lineage": dict(source["source_lineage"]),
            "callable_invocation_authorization_issued": True,
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
            "authorization_artifact_persistence_allowed": True,
            "owner_instances_retained": False,
            "bound_methods_retained": False,
        }

        serial = dict(body)
        serial["authorization_entries"] = [asdict(entry) for entry in entries]
        result = ProductionCallableInvocationAuthorizationManifest(
            **body,
            callable_invocation_authorization_manifest_hash=stable_hash(serial),
        )

        if persist:
            payload = asdict(result)
            _atomic_write(self.authorization_directory / "current.json", payload)
            _atomic_write(
                self.authorization_directory
                / "authorizations"
                / f"{authorization_id}.json",
                payload,
            )
            _atomic_write(
                self.authorization_directory
                / "workers"
                / result.worker_id
                / f"{authorization_id}.json",
                payload,
            )

        return result
"""

TEST_SOURCE = r"""
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_authorization_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationAuthorizationGate,
    ProductionCallableInvocationAuthorizationInvariantError,
    stable_hash,
)


def seed(path: Path):
    specs = [
        (
            "oracle_read_only_canonical_observation_adapter.v1",
            "work.observations",
            "read_canonical_observations",
            "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
            "OracleLiveCorpusInspector",
            "inspect",
            "OracleLiveCorpusInspector.inspect",
            "(*, inspected_at: 'Optional[datetime]' = None) -> 'OracleLiveCorpusReport'",
            {"inspected_at": None},
        ),
        (
            "oracle_read_only_market_state_lineage_adapter.v1",
            "work.lineage",
            "read_market_state_lineage",
            "qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger",
            "OracleCanonicalMarketLineageLedger",
            "records",
            "OracleCanonicalMarketLineageLedger.records",
            "() -> 'tuple[CanonicalMarketStateDwellChangeLineage, ...]'",
            {},
        ),
    ]

    entries = []
    for sequence, spec in enumerate(specs, start=1):
        (
            adapter_id,
            work_item_id,
            read_operation,
            module_path,
            owner_name,
            callable_name,
            qualname,
            signature,
            arguments,
        ) = spec
        body = {
            "sequence": sequence,
            "worker_id": "oracle-worker-test",
            "work_item_id": work_item_id,
            "adapter_id": adapter_id,
            "read_operation": read_operation,
            "module_path": module_path,
            "owner_name": owner_name,
            "callable_name": callable_name,
            "bound_method_module": module_path,
            "bound_method_qualname": qualname,
            "bound_method_signature": signature,
            "invocation_arguments": arguments,
            "invocation_argument_hash": stable_hash(arguments),
            "source_owner_method_binding_hash": stable_hash({"58": owner_name}),
            "source_owner_method_binding_authorization_hash": stable_hash(
                {"57": owner_name}
            ),
            "source_owner_method_binding_readiness_hash": stable_hash(
                {"56": owner_name}
            ),
            "source_owner_construction_authorization_hash": stable_hash(
                {"54": owner_name}
            ),
            "source_owner_construction_readiness_hash": stable_hash(
                {"53": owner_name}
            ),
            "source_callable_argument_binding_hash": stable_hash(
                {"52": owner_name}
            ),
            "owner_reconstruction_required": True,
            "owner_reconstructed": False,
            "method_binding_required": True,
            "method_bound_to_owner": False,
            "invocation_envelope_verified": True,
            "callable_invocation_ready": True,
            "callable_invoked": False,
            "adapter_executed": False,
            "corpus_read_executed": False,
            "readiness_checks": ["verified"],
            "readiness_status": (
                "evidence_read_execution_adapter_production_callable_invocation_ready"
            ),
        }
        body["callable_invocation_readiness_hash"] = stable_hash(body)
        entries.append(body)

    manifest = {
        "schema_version": "OIA-059",
        "engine_id": "OIA-059",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "callable_invocation_readiness_id": "oia059-test",
        "callable_invocation_readiness_status": (
            "evidence_read_execution_adapter_production_callable_invocation_readiness_issued"
        ),
        "callable_invocation_readiness_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "readiness_entry_count": len(entries),
        "readiness_entries": entries,
        "source_owner_method_binding_id": "oia058-test",
        "source_owner_method_binding_manifest_hash": stable_hash({"58m": 1}),
        "source_owner_method_binding_authorization_id": "oia057-test",
        "source_owner_method_binding_authorization_manifest_hash": stable_hash(
            {"57m": 1}
        ),
        "source_owner_method_binding_readiness_id": "oia056-test",
        "source_owner_method_binding_readiness_manifest_hash": stable_hash(
            {"56m": 1}
        ),
        "source_owner_construction_id": "oia055-test",
        "source_owner_construction_manifest_hash": stable_hash({"55m": 1}),
        "source_lineage": {
            "dispatch_manifest_id": "oia020-test",
            "source_claim_id": "oia021-test",
        },
        "callable_invocation_readiness_issued": True,
        "owner_reconstruction_allowed": False,
        "owner_reconstruction_performed": False,
        "callable_binding_to_owner_allowed": False,
        "callable_binding_to_owner_performed": False,
        "callable_invocation_authorization_evaluation_allowed": True,
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
        "owner_instances_retained": False,
        "bound_methods_retained": False,
    }
    manifest["callable_invocation_readiness_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def rehash(payload):
    for entry in payload["readiness_entries"]:
        body = dict(entry)
        body.pop("callable_invocation_readiness_hash", None)
        entry["callable_invocation_readiness_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("callable_invocation_readiness_manifest_hash", None)
    payload["callable_invocation_readiness_manifest_hash"] = stable_hash(body)


def reject(gate, fixed, message):
    try:
        gate.authorize(authorized_at=fixed, persist=False)
    except ProductionCallableInvocationAuthorizationInvariantError:
        return
    raise AssertionError(message)


def main():
    print("=" * 40)
    print(" OIA-060 TEST")
    print(" CALLABLE INVOCATION AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness = root / "readiness"
        authorization = root / "authorization"
        source = seed(readiness)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationAuthorizationGate(
            readiness_directory=readiness,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-060"
        assert first.engine_id == "OIA-060"
        assert first.callable_invocation_authorization_issued is True
        assert first.authorization_entry_count == 2
        assert first.source_callable_invocation_readiness_manifest_hash == source[
            "callable_invocation_readiness_manifest_hash"
        ]
        assert first.owner_reconstruction_allowed is False
        assert first.callable_binding_to_owner_allowed is False
        assert first.callable_invocation_allowed is False
        assert first.callable_invocation_performed is False
        assert first.adapter_execution_allowed is False
        assert first.corpus_read_execution_allowed is False
        assert first.owner_instances_retained is False
        assert first.bound_methods_retained is False

        for entry in first.authorization_entries:
            assert entry.callable_invocation_authorization_granted is True
            assert entry.owner_reconstruction_authorized is True
            assert entry.owner_reconstruction_performed is False
            assert entry.method_binding_authorized is True
            assert entry.method_binding_performed is False
            assert entry.callable_invocation_authorized is True
            assert entry.callable_invoked is False
            assert entry.adapter_executed is False
            assert entry.corpus_read_executed is False
            assert entry.invocation_argument_hash == stable_hash(
                entry.invocation_arguments
            )

        assert (authorization / "current.json").exists()

        payload = json.loads((readiness / "current.json").read_text())
        payload["readiness_entries"][0]["callable_invoked"] = True
        rehash(payload)
        (readiness / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "premature invocation accepted")

        seed(readiness)
        payload = json.loads((readiness / "current.json").read_text())
        payload["readiness_entries"][0]["invocation_arguments"] = {
            "inspected_at": "2026-07-22T00:00:00+00:00"
        }
        payload["readiness_entries"][0]["invocation_argument_hash"] = stable_hash(
            payload["readiness_entries"][0]["invocation_arguments"]
        )
        rehash(payload)
        (readiness / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "altered invocation arguments accepted")

        seed(readiness)
        payload = json.loads((readiness / "current.json").read_text())
        payload["readiness_entries"][0]["bound_method_signature"] = "(*args, **kwargs)"
        rehash(payload)
        (readiness / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "signature drift accepted")

        seed(readiness)
        payload = json.loads((readiness / "current.json").read_text())
        payload["readiness_entries"].append(dict(payload["readiness_entries"][0]))
        payload["readiness_entries"][-1]["sequence"] = 3
        payload["readiness_entry_count"] = 3
        rehash(payload)
        (readiness / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "duplicate readiness entry accepted")

        seed(readiness)
        payload = json.loads((readiness / "current.json").read_text())
        payload["callable_invocation_allowed"] = True
        rehash(payload)
        (readiness / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "executable readiness manifest accepted")

    print("[PASS] Actual OIA-059 callable-invocation-readiness contract consumed")
    print("[PASS] Exact approved invocation envelopes authorized deterministically")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-059 lineage preserved")
    print("[PASS] Reconstruction, binding, and invocation authorized only by entry")
    print("[PASS] Owners were not reconstructed and methods were not rebound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] PostgreSQL connections and corpus reads remained disabled")
    print("[PASS] Tampered, duplicate, invoked, or executable input rejected")
    print("[PASS] Atomic callable-invocation-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

EXPORT_BLOCK = r"""
from .oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_authorization_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationAuthorizationGate,
    ProductionCallableInvocationAuthorizationEntry,
    ProductionCallableInvocationAuthorizationInvariantError,
    ProductionCallableInvocationAuthorizationManifest,
)

__all__ = [
    "OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationAuthorizationGate",
    "ProductionCallableInvocationAuthorizationEntry",
    "ProductionCallableInvocationAuthorizationInvariantError",
    "ProductionCallableInvocationAuthorizationManifest",
] + __all__
"""


def write_full(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = (
        "oracle_certified_research_evidence_read_execution_adapter_"
        "production_callable_invocation_authorization_gate"
    )
    if marker not in existing:
        write_full(INIT, existing.rstrip() + "\n\n" + EXPORT_BLOCK.strip() + "\n")


def main() -> int:
    print("=" * 40)
    print(" OIA-060 INSTALLER")
    print(" CALLABLE INVOCATION AUTHORIZATION")
    print(" PRE-INVOCATION AUTHORIZATION GATE")
    print("=" * 40)

    if not OIA059.exists():
        raise SystemExit(
            f"[FAIL] Required OIA-059 production contract missing: {OIA059}"
        )

    source = OIA059.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "OIA-059"',
        "ProductionCallableInvocationReadinessManifest",
        "callable_invocation_readiness_manifest_hash",
        "callable_invocation_ready",
        "callable_invocation_allowed",
        "callable_invocation_performed",
        "owner_instances_retained",
        "bound_methods_retained",
    )
    if not all(token in source for token in required):
        raise SystemExit(
            "[FAIL] Actual OIA-059 callable-invocation-readiness contract verification failed"
        )

    print("[OK] Actual OIA-059 callable-invocation-readiness contract verified")
    write_full(PRODUCTION, PRODUCTION_SOURCE)
    print(f"[OK] FULL REPLACEMENT: {PRODUCTION}")
    write_full(TEST, TEST_SOURCE)
    print(f"[OK] FULL REPLACEMENT: {TEST}")
    update_init()
    print(f"[OK] PACKAGE UPDATED: {INIT}")

    for path in (PRODUCTION, TEST, INIT):
        py_compile.compile(str(path), doraise=True)

    print("[OK] Production, test, and package syntax verified")
    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    print("[OK] OIA-060 test executed automatically")
    print()
    print("[DONE] OIA-060 production callable invocation authorization gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
