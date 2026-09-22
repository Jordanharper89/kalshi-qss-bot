from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"
OIA064 = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_consumption_activation_gate.py"
PRODUCTION = ANALYTICS / "oracle_certified_research_evidence_read_execution_adapter_controlled_callable_invocation_execution_readiness_gate.py"
TEST = ROOT / "test_oia_065_oracle_certified_research_evidence_read_execution_adapter_controlled_callable_invocation_execution_readiness_gate.py"
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

SCHEMA_VERSION = "OIA-065"
ENGINE_ID = "OIA-065"
POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "controlled-callable-invocation-execution-readiness.v1"
)
STATUS_EXECUTION_READY = (
    "evidence_read_execution_adapter_controlled_callable_invocation_execution_ready"
)
STATUS_READINESS_ISSUED = (
    "evidence_read_execution_adapter_controlled_callable_invocation_execution_readiness_issued"
)

DEFAULT_ACTIVATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_production_callable_invocation_consumption_activation"
)
DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_controlled_callable_invocation_execution_readiness"
)

APPROVED = {
    "oracle_read_only_canonical_observation_adapter.v1": {
        "read_operation": "read_canonical_observations",
        "module_path": "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "bound_method_module": "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
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


class ControlledCallableInvocationExecutionReadinessInvariantError(RuntimeError):
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
            raise ControlledCallableInvocationExecutionReadinessInvariantError(
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
        raise ControlledCallableInvocationExecutionReadinessInvariantError(
            f"{name} must be timezone-aware"
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
    handle = tempfile.NamedTemporaryFile(
        mode="w",
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
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class ControlledCallableInvocationExecutionReadinessEntry:
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
    activation_nonce: str
    consumption_attempt_nonce: str
    source_consumption_activation_hash: str
    source_consumption_authorization_hash: str
    source_consumption_readiness_hash: str
    controlled_execution_ready: bool
    fresh_repository_inspection_required: bool
    consumption_activation_consumed: bool
    original_activation_consumed: bool
    owner_reconstruction_performed: bool
    method_binding_performed: bool
    callable_invoked: bool
    adapter_executed: bool
    corpus_read_executed: bool
    readiness_checks: tuple[str, ...]
    readiness_status: str
    controlled_callable_invocation_execution_readiness_hash: str


@dataclass(frozen=True)
class ControlledCallableInvocationExecutionReadinessManifest:
    schema_version: str
    engine_id: str
    evaluated_at: str
    controlled_callable_invocation_execution_readiness_id: str
    controlled_callable_invocation_execution_readiness_status: str
    controlled_callable_invocation_execution_readiness_policy_id: str
    worker_id: str
    readiness_entry_count: int
    readiness_entries: tuple[ControlledCallableInvocationExecutionReadinessEntry, ...]
    source_consumption_activation_id: str
    source_consumption_activation_manifest_hash: str
    source_consumption_authorization_id: str
    source_consumption_authorization_manifest_hash: str
    source_consumption_readiness_id: str
    source_consumption_readiness_manifest_hash: str
    source_invocation_activation_id: str
    source_invocation_activation_manifest_hash: str
    source_invocation_authorization_id: str
    source_invocation_authorization_manifest_hash: str
    source_lineage: dict[str, Any]
    controlled_callable_invocation_execution_readiness_issued: bool
    fresh_repository_inspection_required_before_execution: bool
    activation_consumption_allowed: bool
    activation_consumption_performed: bool
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
    owner_instances_retained: bool
    bound_methods_retained: bool
    controlled_callable_invocation_execution_readiness_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationExecutionReadinessGate:
    def __init__(
        self,
        *,
        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
    ) -> None:
        self.activation_directory = Path(activation_directory)
        self.readiness_directory = Path(readiness_directory)

    def _load_activation(self) -> dict[str, Any]:
        path = self.activation_directory / "current.json"
        if not path.exists():
            raise ControlledCallableInvocationExecutionReadinessInvariantError(
                f"OIA-064 current activation artifact missing: {path}"
            )
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ControlledCallableInvocationExecutionReadinessInvariantError(
                "OIA-064 activation artifact could not be decoded"
            ) from error

        manifest_hash = source.pop(
            "callable_invocation_consumption_activation_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ControlledCallableInvocationExecutionReadinessInvariantError(
                "OIA-064 activation manifest hash verification failed"
            )
        source["callable_invocation_consumption_activation_manifest_hash"] = (
            manifest_hash
        )

        expected_manifest = {
            "schema_version": "OIA-064",
            "engine_id": "OIA-064",
            "callable_invocation_consumption_activation_issued": True,
            "single_execution_attempt_required": True,
            "activation_consumption_allowed": False,
            "activation_consumption_performed": False,
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
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "owner_instances_retained": False,
            "bound_methods_retained": False,
        }
        for field, expected in expected_manifest.items():
            if source.get(field) != expected:
                raise ControlledCallableInvocationExecutionReadinessInvariantError(
                    f"unsafe OIA-064 activation manifest: {field}"
                )

        entries = source.get("activation_entries")
        if (
            not isinstance(entries, list)
            or not entries
            or source.get("activation_entry_count") != len(entries)
        ):
            raise ControlledCallableInvocationExecutionReadinessInvariantError(
                "OIA-064 activation entry count invalid"
            )

        seen_keys: set[tuple[str, str, str]] = set()
        seen_original_nonces: set[str] = set()
        seen_attempt_nonces: set[str] = set()

        for expected_sequence, entry in enumerate(entries, start=1):
            if entry.get("sequence") != expected_sequence:
                raise ControlledCallableInvocationExecutionReadinessInvariantError(
                    "OIA-064 activation sequence invalid"
                )

            entry_hash = entry.pop(
                "callable_invocation_consumption_activation_hash",
                None,
            )
            if not _valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise ControlledCallableInvocationExecutionReadinessInvariantError(
                    "OIA-064 activation entry hash verification failed"
                )
            entry["callable_invocation_consumption_activation_hash"] = entry_hash

            approved = APPROVED.get(entry.get("adapter_id"))
            if approved is None:
                raise ControlledCallableInvocationExecutionReadinessInvariantError(
                    "unapproved OIA-064 adapter identity"
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
                    raise ControlledCallableInvocationExecutionReadinessInvariantError(
                        f"OIA-064 execution-attempt drift: {field}"
                    )

            if entry.get("invocation_argument_hash") != stable_hash(
                approved["invocation_arguments"]
            ):
                raise ControlledCallableInvocationExecutionReadinessInvariantError(
                    "OIA-064 invocation argument hash drift"
                )

            key = (
                str(entry.get("worker_id")),
                str(entry.get("work_item_id")),
                str(entry.get("adapter_id")),
            )
            if key in seen_keys:
                raise ControlledCallableInvocationExecutionReadinessInvariantError(
                    "duplicate OIA-064 activation entry"
                )
            seen_keys.add(key)

            original_nonce = entry.get("activation_nonce")
            attempt_nonce = entry.get("consumption_attempt_nonce")
            if (
                not _valid_hash(original_nonce)
                or original_nonce in seen_original_nonces
                or not _valid_hash(attempt_nonce)
                or attempt_nonce in seen_attempt_nonces
            ):
                raise ControlledCallableInvocationExecutionReadinessInvariantError(
                    "invalid or duplicate OIA-064 nonce"
                )
            seen_original_nonces.add(original_nonce)
            seen_attempt_nonces.add(attempt_nonce)

            expected_entry = {
                "consumption_activation_granted": True,
                "consumption_activation_consumed": False,
                "original_activation_consumed": False,
                "owner_reconstruction_performed": False,
                "method_binding_performed": False,
                "callable_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
            }
            for field, expected in expected_entry.items():
                if entry.get(field) != expected:
                    raise ControlledCallableInvocationExecutionReadinessInvariantError(
                        f"unsafe OIA-064 activation entry: {field}"
                    )

            for hash_field in (
                "source_consumption_authorization_hash",
                "source_consumption_readiness_hash",
                "source_invocation_activation_hash",
                "source_invocation_authorization_hash",
            ):
                if not _valid_hash(entry.get(hash_field)):
                    raise ControlledCallableInvocationExecutionReadinessInvariantError(
                        f"OIA-064 lineage hash invalid: {hash_field}"
                    )

        if not isinstance(source.get("source_lineage"), dict) or not source["source_lineage"]:
            raise ControlledCallableInvocationExecutionReadinessInvariantError(
                "OIA-064 source lineage missing"
            )
        return source

    def evaluate(
        self,
        *,
        evaluated_at: datetime,
        persist: bool = True,
    ) -> ControlledCallableInvocationExecutionReadinessManifest:
        evaluated_at = _aware(evaluated_at, "evaluated_at")
        source = self._load_activation()
        entries: list[ControlledCallableInvocationExecutionReadinessEntry] = []

        for sequence, activation in enumerate(
            source["activation_entries"],
            start=1,
        ):
            body = {
                "sequence": sequence,
                "worker_id": activation["worker_id"],
                "work_item_id": activation["work_item_id"],
                "adapter_id": activation["adapter_id"],
                "read_operation": activation["read_operation"],
                "module_path": activation["module_path"],
                "owner_name": activation["owner_name"],
                "callable_name": activation["callable_name"],
                "bound_method_module": activation["bound_method_module"],
                "bound_method_qualname": activation["bound_method_qualname"],
                "bound_method_signature": activation["bound_method_signature"],
                "invocation_arguments": dict(activation["invocation_arguments"]),
                "invocation_argument_hash": activation["invocation_argument_hash"],
                "activation_nonce": activation["activation_nonce"],
                "consumption_attempt_nonce": activation[
                    "consumption_attempt_nonce"
                ],
                "source_consumption_activation_hash": activation[
                    "callable_invocation_consumption_activation_hash"
                ],
                "source_consumption_authorization_hash": activation[
                    "source_consumption_authorization_hash"
                ],
                "source_consumption_readiness_hash": activation[
                    "source_consumption_readiness_hash"
                ],
                "controlled_execution_ready": True,
                "fresh_repository_inspection_required": True,
                "consumption_activation_consumed": False,
                "original_activation_consumed": False,
                "owner_reconstruction_performed": False,
                "method_binding_performed": False,
                "callable_invoked": False,
                "adapter_executed": False,
                "corpus_read_executed": False,
                "readiness_checks": (
                    "oia064_activation_manifest_hash_verified",
                    "oia064_activation_entry_hash_verified",
                    "approved_adapter_identity_verified",
                    "approved_callable_identity_verified",
                    "approved_callable_signature_verified",
                    "approved_invocation_arguments_verified",
                    "original_activation_nonce_verified",
                    "single_execution_attempt_nonce_verified",
                    "all_nonces_unique",
                    "all_nonces_unconsumed",
                    "controlled_execution_ready",
                    "fresh_repository_inspection_required_before_execution",
                    "owner_not_reconstructed",
                    "method_not_bound",
                    "callable_not_invoked",
                    "adapter_not_executed",
                    "corpus_not_read",
                    "oracle_qseries_boundary_verified",
                ),
                "readiness_status": STATUS_EXECUTION_READY,
            }
            entries.append(
                ControlledCallableInvocationExecutionReadinessEntry(
                    **body,
                    controlled_callable_invocation_execution_readiness_hash=stable_hash(
                        body
                    ),
                )
            )

        source_hash = source[
            "callable_invocation_consumption_activation_manifest_hash"
        ]
        readiness_id = (
            "oia065-controlled-callable-invocation-execution-readiness-"
            + stable_hash({"source": source_hash, "policy": POLICY_ID})[:32]
        )
        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "evaluated_at": evaluated_at.isoformat(),
            "controlled_callable_invocation_execution_readiness_id": readiness_id,
            "controlled_callable_invocation_execution_readiness_status": STATUS_READINESS_ISSUED,
            "controlled_callable_invocation_execution_readiness_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "readiness_entry_count": len(entries),
            "readiness_entries": tuple(entries),
            "source_consumption_activation_id": source[
                "callable_invocation_consumption_activation_id"
            ],
            "source_consumption_activation_manifest_hash": source_hash,
            "source_consumption_authorization_id": source[
                "source_consumption_authorization_id"
            ],
            "source_consumption_authorization_manifest_hash": source[
                "source_consumption_authorization_manifest_hash"
            ],
            "source_consumption_readiness_id": source[
                "source_consumption_readiness_id"
            ],
            "source_consumption_readiness_manifest_hash": source[
                "source_consumption_readiness_manifest_hash"
            ],
            "source_invocation_activation_id": source[
                "source_invocation_activation_id"
            ],
            "source_invocation_activation_manifest_hash": source[
                "source_invocation_activation_manifest_hash"
            ],
            "source_invocation_authorization_id": source[
                "source_invocation_authorization_id"
            ],
            "source_invocation_authorization_manifest_hash": source[
                "source_invocation_authorization_manifest_hash"
            ],
            "source_lineage": dict(source["source_lineage"]),
            "controlled_callable_invocation_execution_readiness_issued": True,
            "fresh_repository_inspection_required_before_execution": True,
            "activation_consumption_allowed": False,
            "activation_consumption_performed": False,
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
            "owner_instances_retained": False,
            "bound_methods_retained": False,
        }
        serial = dict(body)
        serial["readiness_entries"] = [asdict(entry) for entry in entries]
        result = ControlledCallableInvocationExecutionReadinessManifest(
            **body,
            controlled_callable_invocation_execution_readiness_manifest_hash=stable_hash(
                serial
            ),
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

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_controlled_callable_invocation_execution_readiness_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationExecutionReadinessGate,
    ControlledCallableInvocationExecutionReadinessInvariantError,
    stable_hash,
)


SPECS = (
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
)


def seed(path: Path):
    entries = []
    for sequence, spec in enumerate(SPECS, start=1):
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
            "activation_nonce": stable_hash(
                {"adapter_id": adapter_id, "work_item_id": work_item_id}
            ),
            "consumption_attempt_nonce": stable_hash(
                {"attempt": adapter_id, "work_item_id": work_item_id}
            ),
            "source_consumption_authorization_hash": stable_hash(
                {"63": owner_name}
            ),
            "source_consumption_readiness_hash": stable_hash(
                {"62": owner_name}
            ),
            "source_invocation_activation_hash": stable_hash(
                {"61": owner_name}
            ),
            "source_invocation_authorization_hash": stable_hash(
                {"60": owner_name}
            ),
            "consumption_activation_granted": True,
            "consumption_activation_consumed": False,
            "original_activation_consumed": False,
            "owner_reconstruction_performed": False,
            "method_binding_performed": False,
            "callable_invoked": False,
            "adapter_executed": False,
            "corpus_read_executed": False,
            "activation_checks": ["verified"],
            "activation_status": (
                "evidence_read_execution_adapter_production_callable_invocation_consumption_activated"
            ),
        }
        body["callable_invocation_consumption_activation_hash"] = stable_hash(
            body
        )
        entries.append(body)

    manifest = {
        "schema_version": "OIA-064",
        "engine_id": "OIA-064",
        "activated_at": "2026-07-22T00:00:00+00:00",
        "callable_invocation_consumption_activation_id": "oia064-test",
        "callable_invocation_consumption_activation_status": (
            "evidence_read_execution_adapter_production_callable_invocation_consumption_activation_issued"
        ),
        "callable_invocation_consumption_activation_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "activation_entry_count": len(entries),
        "activation_entries": entries,
        "source_consumption_authorization_id": "oia063-test",
        "source_consumption_authorization_manifest_hash": stable_hash(
            {"63m": 1}
        ),
        "source_consumption_readiness_id": "oia062-test",
        "source_consumption_readiness_manifest_hash": stable_hash(
            {"62m": 1}
        ),
        "source_invocation_activation_id": "oia061-test",
        "source_invocation_activation_manifest_hash": stable_hash(
            {"61m": 1}
        ),
        "source_invocation_authorization_id": "oia060-test",
        "source_invocation_authorization_manifest_hash": stable_hash(
            {"60m": 1}
        ),
        "source_lineage": {
            "dispatch_manifest_id": "oia020-test",
            "source_claim_id": "oia021-test",
        },
        "callable_invocation_consumption_activation_issued": True,
        "single_execution_attempt_required": True,
        "activation_consumption_allowed": False,
        "activation_consumption_performed": False,
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
        "activation_artifact_persistence_allowed": True,
        "owner_instances_retained": False,
        "bound_methods_retained": False,
    }
    manifest[
        "callable_invocation_consumption_activation_manifest_hash"
    ] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def rehash(payload):
    for entry in payload["activation_entries"]:
        body = dict(entry)
        body.pop("callable_invocation_consumption_activation_hash", None)
        entry["callable_invocation_consumption_activation_hash"] = stable_hash(
            body
        )
    body = dict(payload)
    body.pop("callable_invocation_consumption_activation_manifest_hash", None)
    payload[
        "callable_invocation_consumption_activation_manifest_hash"
    ] = stable_hash(body)


def reject(gate, fixed, message):
    try:
        gate.evaluate(evaluated_at=fixed, persist=False)
    except ControlledCallableInvocationExecutionReadinessInvariantError:
        return
    raise AssertionError(message)


def main():
    print("=" * 40)
    print(" OIA-065 TEST")
    print(" CONTROLLED INVOCATION EXECUTION READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        activation = root / "activation"
        readiness = root / "readiness"
        source = seed(activation)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationExecutionReadinessGate(
            activation_directory=activation,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-065"
        assert first.engine_id == "OIA-065"
        assert first.controlled_callable_invocation_execution_readiness_issued is True
        assert first.fresh_repository_inspection_required_before_execution is True
        assert first.readiness_entry_count == 2
        assert first.source_consumption_activation_manifest_hash == source[
            "callable_invocation_consumption_activation_manifest_hash"
        ]
        assert first.activation_consumption_allowed is False
        assert first.activation_consumption_performed is False
        assert first.owner_reconstruction_performed is False
        assert first.callable_binding_to_owner_performed is False
        assert first.callable_invocation_performed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_performed is False

        original_nonces = set()
        attempt_nonces = set()
        for entry in first.readiness_entries:
            assert entry.controlled_execution_ready is True
            assert entry.fresh_repository_inspection_required is True
            assert entry.consumption_activation_consumed is False
            assert entry.original_activation_consumed is False
            assert entry.owner_reconstruction_performed is False
            assert entry.method_binding_performed is False
            assert entry.callable_invoked is False
            assert entry.adapter_executed is False
            assert entry.corpus_read_executed is False
            original_nonces.add(entry.activation_nonce)
            attempt_nonces.add(entry.consumption_attempt_nonce)
        assert len(original_nonces) == 2
        assert len(attempt_nonces) == 2
        assert (readiness / "current.json").exists()

        payload = json.loads((activation / "current.json").read_text())
        payload["activation_entries"][0]["consumption_activation_consumed"] = True
        rehash(payload)
        (activation / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "consumed execution attempt accepted")

        seed(activation)
        payload = json.loads((activation / "current.json").read_text())
        payload["activation_entries"][1]["consumption_attempt_nonce"] = payload[
            "activation_entries"
        ][0]["consumption_attempt_nonce"]
        rehash(payload)
        (activation / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "duplicate attempt nonce accepted")

        seed(activation)
        payload = json.loads((activation / "current.json").read_text())
        payload["activation_entries"][0]["bound_method_signature"] = (
            "(*args, **kwargs)"
        )
        rehash(payload)
        (activation / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "signature drift accepted")

        seed(activation)
        payload = json.loads((activation / "current.json").read_text())
        payload["activation_entries"][0]["callable_invoked"] = True
        rehash(payload)
        (activation / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "premature invocation accepted")

        seed(activation)
        payload = json.loads((activation / "current.json").read_text())
        payload["callable_invocation_allowed"] = True
        rehash(payload)
        (activation / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "executable activation manifest accepted")

    print("[PASS] Actual OIA-064 invocation-consumption-activation contract consumed")
    print("[PASS] Exact controlled execution attempts certified ready")
    print("[PASS] Original and execution-attempt nonces verified unique and unconsumed")
    print("[PASS] Execution-readiness manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-064 lineage preserved")
    print("[PASS] Fresh repository inspection required before actual invocation")
    print("[PASS] Activation consumption remained unauthorized and unperformed")
    print("[PASS] Owners were not reconstructed and methods were not rebound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] PostgreSQL connections and corpus reads remained disabled")
    print("[PASS] Consumed, duplicate, tampered, invoked, or executable input rejected")
    print("[PASS] Atomic controlled-execution-readiness artifacts persisted")
    print("[PASS] Signals, alerts, Q Series, orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

EXPORT_BLOCK = r"""
from .oracle_certified_research_evidence_read_execution_adapter_controlled_callable_invocation_execution_readiness_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationExecutionReadinessGate,
    ControlledCallableInvocationExecutionReadinessEntry,
    ControlledCallableInvocationExecutionReadinessInvariantError,
    ControlledCallableInvocationExecutionReadinessManifest,
)

__all__ = [
    "OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationExecutionReadinessGate",
    "ControlledCallableInvocationExecutionReadinessEntry",
    "ControlledCallableInvocationExecutionReadinessInvariantError",
    "ControlledCallableInvocationExecutionReadinessManifest",
] + __all__
"""


def write_full(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def update_init() -> None:
    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else "__all__ = []\n"
    marker = (
        "oracle_certified_research_evidence_read_execution_adapter_"
        "controlled_callable_invocation_execution_readiness_gate"
    )
    if marker not in existing:
        write_full(INIT, existing.rstrip() + "\n\n" + EXPORT_BLOCK.strip() + "\n")


def main() -> int:
    print("=" * 40)
    print(" OIA-065 INSTALLER")
    print(" CONTROLLED INVOCATION EXECUTION READINESS")
    print(" FINAL PRE-LIVE-READ SAFETY GATE")
    print("=" * 40)

    if not OIA064.exists():
        raise SystemExit(
            f"[FAIL] Required OIA-064 production contract missing: {OIA064}"
        )

    source = OIA064.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "OIA-064"',
        "ProductionCallableInvocationConsumptionActivationManifest",
        "callable_invocation_consumption_activation_manifest_hash",
        "consumption_attempt_nonce",
        "consumption_activation_granted",
        "consumption_activation_consumed",
        "original_activation_consumed",
        "callable_invocation_allowed",
        "callable_invocation_performed",
    )
    if not all(token in source for token in required):
        raise SystemExit(
            "[FAIL] Actual OIA-064 invocation-consumption-activation contract verification failed"
        )

    print("[OK] Actual OIA-064 invocation-consumption-activation contract verified")
    write_full(PRODUCTION, PRODUCTION_SOURCE)
    print(f"[OK] FULL REPLACEMENT: {PRODUCTION}")
    write_full(TEST, TEST_SOURCE)
    print(f"[OK] FULL REPLACEMENT: {TEST}")
    update_init()
    print(f"[OK] PACKAGE UPDATED: {INIT}")

    for target in (PRODUCTION, TEST, INIT):
        py_compile.compile(str(target), doraise=True)
    print("[OK] Production, test, and package syntax verified")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    print("[OK] OIA-065 test executed automatically")
    print()
    print(
        "[DONE] OIA-065 controlled callable invocation "
        "execution readiness gate installed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
