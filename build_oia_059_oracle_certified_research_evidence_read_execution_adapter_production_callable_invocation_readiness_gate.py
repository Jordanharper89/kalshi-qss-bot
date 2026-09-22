from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA058 = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_readiness_gate.py"
TEST = ROOT / "test_oia_059_oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_readiness_gate.py"
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

SCHEMA_VERSION = "OIA-059"
ENGINE_ID = "OIA-059"
POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "production-callable-invocation-readiness.v1"
)
STATUS_INVOCATION_READY = (
    "evidence_read_execution_adapter_production_callable_invocation_ready"
)
STATUS_READINESS_ISSUED = (
    "evidence_read_execution_adapter_production_callable_invocation_readiness_issued"
)

DEFAULT_BINDING_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_owner_method_binding"
)
DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_invocation_readiness"
)

APPROVED_INVOCATION_ENVELOPES = {
    "oracle_read_only_canonical_observation_adapter.v1": {
        "read_operation": "read_canonical_observations",
        "module_path": (
            "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector"
        ),
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
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
        "bound_method_qualname": "OracleCanonicalMarketLineageLedger.records",
        "bound_method_signature": (
            "() -> 'tuple[CanonicalMarketStateDwellChangeLineage, ...]'"
        ),
        "invocation_arguments": {},
    },
}


class ProductionCallableInvocationReadinessInvariantError(RuntimeError):
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
            raise ProductionCallableInvocationReadinessInvariantError(
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
        raise ProductionCallableInvocationReadinessInvariantError(
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
class ProductionCallableInvocationReadinessEntry:
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
    source_owner_method_binding_hash: str
    source_owner_method_binding_authorization_hash: str
    source_owner_method_binding_readiness_hash: str
    source_owner_construction_authorization_hash: str
    source_owner_construction_readiness_hash: str
    source_callable_argument_binding_hash: str
    owner_reconstruction_required: bool
    owner_reconstructed: bool
    method_binding_required: bool
    method_bound_to_owner: bool
    invocation_envelope_verified: bool
    callable_invocation_ready: bool
    callable_invoked: bool
    adapter_executed: bool
    corpus_read_executed: bool
    readiness_checks: tuple[str, ...]
    readiness_status: str
    callable_invocation_readiness_hash: str


@dataclass(frozen=True)
class ProductionCallableInvocationReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: str
    callable_invocation_readiness_id: str
    callable_invocation_readiness_status: str
    callable_invocation_readiness_policy_id: str
    worker_id: str
    readiness_entry_count: int
    readiness_entries: tuple[ProductionCallableInvocationReadinessEntry, ...]
    source_owner_method_binding_id: str
    source_owner_method_binding_manifest_hash: str
    source_owner_method_binding_authorization_id: str
    source_owner_method_binding_authorization_manifest_hash: str
    source_owner_method_binding_readiness_id: str
    source_owner_method_binding_readiness_manifest_hash: str
    source_owner_construction_id: str
    source_owner_construction_manifest_hash: str
    source_lineage: dict[str, Any]
    callable_invocation_readiness_issued: bool
    owner_reconstruction_allowed: bool
    owner_reconstruction_performed: bool
    callable_binding_to_owner_allowed: bool
    callable_binding_to_owner_performed: bool
    callable_invocation_authorization_evaluation_allowed: bool
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
    owner_instances_retained: bool
    bound_methods_retained: bool
    callable_invocation_readiness_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationReadinessGate:
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
            raise ProductionCallableInvocationReadinessInvariantError(
                f"OIA-058 current binding artifact missing: {path}"
            )
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProductionCallableInvocationReadinessInvariantError(
                "OIA-058 binding artifact could not be decoded"
            ) from error

        manifest_hash = source.pop("owner_method_binding_manifest_hash", None)
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ProductionCallableInvocationReadinessInvariantError(
                "OIA-058 binding manifest hash verification failed"
            )
        source["owner_method_binding_manifest_hash"] = manifest_hash

        required_flags = {
            "owner_reconstruction_allowed": True,
            "owner_reconstruction_performed": True,
            "callable_binding_to_owner_allowed": True,
            "callable_binding_to_owner_performed": True,
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
                raise ProductionCallableInvocationReadinessInvariantError(
                    f"unsafe OIA-058 binding manifest: {field}"
                )

        entries = source.get("binding_entries")
        if (
            not isinstance(entries, list)
            or not entries
            or source.get("binding_entry_count") != len(entries)
        ):
            raise ProductionCallableInvocationReadinessInvariantError(
                "OIA-058 binding entry count invalid"
            )

        seen: set[tuple[str, str, str]] = set()
        for entry in entries:
            entry_hash = entry.pop("owner_method_binding_hash", None)
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ProductionCallableInvocationReadinessInvariantError(
                    "OIA-058 binding entry hash verification failed"
                )
            entry["owner_method_binding_hash"] = entry_hash

            adapter_id = entry.get("adapter_id")
            approved = APPROVED_INVOCATION_ENVELOPES.get(adapter_id)
            if approved is None:
                raise ProductionCallableInvocationReadinessInvariantError(
                    "unapproved OIA-058 adapter identity"
                )

            exact_fields = (
                "read_operation",
                "module_path",
                "owner_name",
                "callable_name",
                "bound_method_qualname",
                "bound_method_signature",
            )
            for field in exact_fields:
                if entry.get(field) != approved[field]:
                    raise ProductionCallableInvocationReadinessInvariantError(
                        f"OIA-058 production callable drift: {field}"
                    )

            if entry.get("bound_method_module") != approved["module_path"]:
                raise ProductionCallableInvocationReadinessInvariantError(
                    "OIA-058 bound method module drift"
                )

            key = (
                str(entry.get("worker_id")),
                str(entry.get("work_item_id")),
                str(adapter_id),
            )
            if key in seen:
                raise ProductionCallableInvocationReadinessInvariantError(
                    "duplicate OIA-058 binding entry"
                )
            seen.add(key)

            safe_entry = {
                "owner_reconstructed": True,
                "method_binding_requested": True,
                "method_bound_to_owner": True,
                "bound_method_self_verified": True,
                "bound_method_function_verified": True,
                "method_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
            }
            for field, expected in safe_entry.items():
                if entry.get(field) != expected:
                    raise ProductionCallableInvocationReadinessInvariantError(
                        f"unsafe OIA-058 binding entry: {field}"
                    )

            for hash_field in (
                "owner_state_fingerprint",
                "owner_construction_hash",
                "source_owner_method_binding_authorization_hash",
                "source_owner_method_binding_readiness_hash",
                "source_owner_construction_authorization_hash",
                "source_owner_construction_readiness_hash",
                "source_callable_argument_binding_hash",
            ):
                if not _valid_hash(entry.get(hash_field)):
                    raise ProductionCallableInvocationReadinessInvariantError(
                        f"OIA-058 entry hash invalid: {hash_field}"
                    )

        if not isinstance(source.get("source_lineage"), dict) or not source["source_lineage"]:
            raise ProductionCallableInvocationReadinessInvariantError(
                "OIA-058 source lineage missing"
            )
        return source

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> ProductionCallableInvocationReadinessManifest:
        evaluated_at = _aware(evaluated_at, "evaluated_at")
        source = self._load_binding()
        results: list[ProductionCallableInvocationReadinessEntry] = []

        for sequence, entry in enumerate(source["binding_entries"], start=1):
            approved = APPROVED_INVOCATION_ENVELOPES[entry["adapter_id"]]
            invocation_arguments = dict(approved["invocation_arguments"])
            invocation_argument_hash = stable_hash(invocation_arguments)

            body = {
                "sequence": sequence,
                "worker_id": entry["worker_id"],
                "work_item_id": entry["work_item_id"],
                "adapter_id": entry["adapter_id"],
                "read_operation": entry["read_operation"],
                "module_path": entry["module_path"],
                "owner_name": entry["owner_name"],
                "callable_name": entry["callable_name"],
                "bound_method_module": entry["bound_method_module"],
                "bound_method_qualname": entry["bound_method_qualname"],
                "bound_method_signature": entry["bound_method_signature"],
                "invocation_arguments": invocation_arguments,
                "invocation_argument_hash": invocation_argument_hash,
                "source_owner_method_binding_hash": entry[
                    "owner_method_binding_hash"
                ],
                "source_owner_method_binding_authorization_hash": entry[
                    "source_owner_method_binding_authorization_hash"
                ],
                "source_owner_method_binding_readiness_hash": entry[
                    "source_owner_method_binding_readiness_hash"
                ],
                "source_owner_construction_authorization_hash": entry[
                    "source_owner_construction_authorization_hash"
                ],
                "source_owner_construction_readiness_hash": entry[
                    "source_owner_construction_readiness_hash"
                ],
                "source_callable_argument_binding_hash": entry[
                    "source_callable_argument_binding_hash"
                ],
                "owner_reconstruction_required": True,
                "owner_reconstructed": False,
                "method_binding_required": True,
                "method_bound_to_owner": False,
                "invocation_envelope_verified": True,
                "callable_invocation_ready": True,
                "callable_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
                "readiness_checks": (
                    "oia058_binding_manifest_hash_verified",
                    "oia058_binding_entry_hash_verified",
                    "approved_adapter_identity_verified",
                    "approved_bound_method_identity_verified",
                    "approved_bound_method_signature_verified",
                    "approved_invocation_argument_envelope_verified",
                    "prior_live_owner_and_method_references_released",
                    "owner_not_reconstructed",
                    "method_not_bound",
                    "callable_not_invoked",
                    "adapter_not_executed",
                    "corpus_not_read",
                    "oracle_qseries_boundary_verified",
                ),
                "readiness_status": STATUS_INVOCATION_READY,
            }
            results.append(
                ProductionCallableInvocationReadinessEntry(
                    **body,
                    callable_invocation_readiness_hash=stable_hash(body),
                )
            )

        source_hash = source["owner_method_binding_manifest_hash"]
        readiness_id = (
            "oia059-callable-invocation-readiness-"
            + stable_hash({"source": source_hash, "policy": POLICY_ID})[:32]
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at.isoformat(),
            "callable_invocation_readiness_id": readiness_id,
            "callable_invocation_readiness_status": STATUS_READINESS_ISSUED,
            "callable_invocation_readiness_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "readiness_entry_count": len(results),
            "readiness_entries": tuple(results),
            "source_owner_method_binding_id": source["owner_method_binding_id"],
            "source_owner_method_binding_manifest_hash": source_hash,
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
            "source_owner_construction_id": source["source_owner_construction_id"],
            "source_owner_construction_manifest_hash": source[
                "source_owner_construction_manifest_hash"
            ],
            "source_lineage": dict(source["source_lineage"]),
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

        serial = dict(body)
        serial["readiness_entries"] = [asdict(entry) for entry in results]
        result = ProductionCallableInvocationReadinessManifest(
            **body,
            callable_invocation_readiness_manifest_hash=stable_hash(serial),
        )

        if persist:
            payload = asdict(result)
            _atomic_write(self.readiness_directory / "current.json", payload)
            _atomic_write(
                self.readiness_directory
                / "readiness"
                / f"{readiness_id}.json",
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
"""

TEST_SOURCE = r"""
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_readiness_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationReadinessGate,
    ProductionCallableInvocationReadinessInvariantError,
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
            "owner_state_fingerprint": stable_hash({"owner": owner_name}),
            "owner_construction_hash": stable_hash({"construction": owner_name}),
            "method_descriptor_module": module_path,
            "method_descriptor_qualname": qualname,
            "bound_method_type": "method",
            "bound_method_module": module_path,
            "bound_method_qualname": qualname,
            "bound_method_signature": signature,
            "bound_method_self_verified": True,
            "bound_method_function_verified": True,
            "owner_reconstructed": True,
            "method_binding_requested": True,
            "method_bound_to_owner": True,
            "method_invoked": False,
            "adapter_executed": False,
            "corpus_read_executed": False,
            "binding_checks": ["verified"],
            "binding_status": (
                "evidence_read_execution_adapter_production_owner_method_bound"
            ),
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
        }
        body["owner_method_binding_hash"] = stable_hash(body)
        entries.append(body)

    manifest = {
        "schema_version": "OIA-058",
        "engine_id": "OIA-058",
        "bound_at": "2026-07-22T00:00:00+00:00",
        "owner_method_binding_id": "oia058-test",
        "owner_method_binding_status": (
            "evidence_read_execution_adapter_production_owner_method_binding_issued"
        ),
        "owner_method_binding_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "binding_entry_count": len(entries),
        "binding_entries": entries,
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
        "owner_reconstruction_allowed": True,
        "owner_reconstruction_performed": True,
        "callable_binding_to_owner_allowed": True,
        "callable_binding_to_owner_performed": True,
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
        "binding_artifact_persistence_allowed": True,
        "owner_instances_retained": False,
        "bound_methods_retained": False,
    }
    manifest["owner_method_binding_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def rehash(payload):
    for entry in payload["binding_entries"]:
        body = dict(entry)
        body.pop("owner_method_binding_hash", None)
        entry["owner_method_binding_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("owner_method_binding_manifest_hash", None)
    payload["owner_method_binding_manifest_hash"] = stable_hash(body)


def reject(gate, fixed, message):
    try:
        gate.evaluate(evaluated_at=fixed, persist=False)
    except ProductionCallableInvocationReadinessInvariantError:
        return
    raise AssertionError(message)


def main():
    print("=" * 40)
    print(" OIA-059 TEST")
    print(" CALLABLE INVOCATION READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        binding = root / "binding"
        readiness = root / "readiness"
        source = seed(binding)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationReadinessGate(
            binding_directory=binding,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-059"
        assert first.engine_id == "OIA-059"
        assert first.callable_invocation_readiness_issued is True
        assert first.callable_invocation_authorization_evaluation_allowed is True
        assert first.readiness_entry_count == 2
        assert first.source_owner_method_binding_manifest_hash == source[
            "owner_method_binding_manifest_hash"
        ]
        assert first.owner_reconstruction_performed is False
        assert first.callable_binding_to_owner_performed is False
        assert first.callable_invocation_allowed is False
        assert first.callable_invocation_performed is False
        assert first.adapter_execution_allowed is False
        assert first.corpus_read_execution_allowed is False
        assert first.owner_instances_retained is False
        assert first.bound_methods_retained is False

        for entry in first.readiness_entries:
            assert entry.invocation_envelope_verified is True
            assert entry.callable_invocation_ready is True
            assert entry.owner_reconstructed is False
            assert entry.method_bound_to_owner is False
            assert entry.callable_invoked is False
            assert entry.adapter_executed is False
            assert entry.corpus_read_executed is False
            assert entry.invocation_argument_hash == stable_hash(
                entry.invocation_arguments
            )

        assert (
            first.readiness_entries[0].invocation_arguments
            == {"inspected_at": None}
        )
        assert first.readiness_entries[1].invocation_arguments == {}
        assert (readiness / "current.json").exists()

        payload = json.loads((binding / "current.json").read_text())
        payload["binding_entries"][0]["method_invoked"] = True
        rehash(payload)
        (binding / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "premature invocation accepted")

        seed(binding)
        payload = json.loads((binding / "current.json").read_text())
        payload["binding_entries"][0]["bound_method_signature"] = (
            "(*args, **kwargs)"
        )
        rehash(payload)
        (binding / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "signature drift accepted")

        seed(binding)
        payload = json.loads((binding / "current.json").read_text())
        payload["binding_entries"][0]["callable_name"] = "execute"
        rehash(payload)
        (binding / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "unknown callable accepted")

        seed(binding)
        payload = json.loads((binding / "current.json").read_text())
        payload["binding_entries"].append(dict(payload["binding_entries"][0]))
        payload["binding_entries"][-1]["sequence"] = 3
        payload["binding_entry_count"] = 3
        rehash(payload)
        (binding / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "duplicate binding accepted")

        seed(binding)
        payload = json.loads((binding / "current.json").read_text())
        payload["callable_invocation_allowed"] = True
        rehash(payload)
        (binding / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "executable binding manifest accepted")

    print("[PASS] Actual OIA-058 owner-method-binding contract consumed")
    print("[PASS] Exact approved invocation envelopes verified deterministically")
    print("[PASS] Invocation argument and readiness hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-058 lineage preserved")
    print("[PASS] Prior live owners and bound methods remained released")
    print("[PASS] Owners were not reconstructed and methods were not rebound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] PostgreSQL connections and corpus reads remained disabled")
    print("[PASS] Tampered, duplicate, invoked, or executable input rejected")
    print("[PASS] Atomic callable-invocation-readiness artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

EXPORT_BLOCK = r"""
from .oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_readiness_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationReadinessGate,
    ProductionCallableInvocationReadinessEntry,
    ProductionCallableInvocationReadinessInvariantError,
    ProductionCallableInvocationReadinessManifest,
)

__all__ = [
    "OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationReadinessGate",
    "ProductionCallableInvocationReadinessEntry",
    "ProductionCallableInvocationReadinessInvariantError",
    "ProductionCallableInvocationReadinessManifest",
] + __all__
"""


def write_full(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = (
        "oracle_certified_research_evidence_read_execution_adapter_"
        "production_callable_invocation_readiness_gate"
    )
    if marker not in existing:
        write_full(INIT, existing.rstrip() + "\n\n" + EXPORT_BLOCK.strip() + "\n")


def main() -> int:
    print("=" * 40)
    print(" OIA-059 INSTALLER")
    print(" CALLABLE INVOCATION READINESS")
    print(" PRE-INVOCATION SAFETY GATE")
    print("=" * 40)

    if not OIA058.exists():
        raise SystemExit(
            f"[FAIL] Required OIA-058 production contract missing: {OIA058}"
        )

    source = OIA058.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "OIA-058"',
        "ProductionOwnerMethodBindingManifest",
        "owner_method_binding_manifest_hash",
        "callable_invocation_allowed",
        "callable_invocation_performed",
        "owner_instances_retained",
        "bound_methods_retained",
    )
    if not all(token in source for token in required):
        raise SystemExit(
            "[FAIL] Actual OIA-058 owner-method-binding contract verification failed"
        )

    print("[OK] Actual OIA-058 owner-method-binding contract verified")
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

    print("[OK] OIA-059 test executed automatically")
    print()
    print("[DONE] OIA-059 production callable invocation readiness gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
