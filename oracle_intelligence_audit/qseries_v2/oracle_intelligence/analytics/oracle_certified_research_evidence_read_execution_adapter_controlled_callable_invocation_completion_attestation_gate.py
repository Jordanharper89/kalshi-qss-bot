from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "OIA-067"
ENGINE_ID = "OIA-067"
POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "controlled-callable-invocation-completion-attestation.v1"
)
STATUS_ATTESTED = (
    "evidence_read_execution_adapter_controlled_callable_invocation_completed"
)

DEFAULT_INVOCATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_controlled_callable_invocation"
)
DEFAULT_ATTESTATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_"
    "controlled_callable_invocation_completion_attestation"
)

APPROVED_ADAPTERS = frozenset(
    {
        "oracle_read_only_canonical_observation_adapter.v1",
        "oracle_read_only_market_state_lineage_adapter.v1",
    }
)


class ControlledCallableInvocationCompletionAttestationInvariantError(
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
            raise ControlledCallableInvocationCompletionAttestationInvariantError(
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
        raise ControlledCallableInvocationCompletionAttestationInvariantError(
            f"{name} must be timezone-aware"
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
class ControlledCallableInvocationCompletionEntry:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    source_invocation_hash: str
    activation_nonce: str
    consumption_attempt_nonce: str
    result_type: str
    result_hash: str
    result_summary_hash: str
    callable_invoked: bool
    adapter_executed: bool
    corpus_read_executed: bool
    source_mutation_performed: bool
    completion_validated: bool
    completion_status: str
    controlled_callable_invocation_completion_entry_hash: str


@dataclass(frozen=True)
class ControlledCallableInvocationCompletionAttestation:
    schema_version: str
    engine_id: str
    attested_at: str
    controlled_callable_invocation_completion_attestation_id: str
    controlled_callable_invocation_completion_attestation_status: str
    controlled_callable_invocation_completion_attestation_policy_id: str
    worker_id: str
    completion_entry_count: int
    completion_entries: tuple[
        ControlledCallableInvocationCompletionEntry, ...
    ]
    source_invocation_id: str
    source_invocation_manifest_hash: str
    source_readiness_id: str
    source_readiness_manifest_hash: str
    source_lineage: dict[str, Any]
    invocation_results_validated: bool
    all_approved_invocations_completed: bool
    all_result_hashes_verified: bool
    all_nonce_pairs_unique: bool
    source_invocation_reexecuted: bool
    owner_reconstruction_performed: bool
    callable_binding_performed: bool
    callable_invocation_performed: bool
    adapter_execution_performed: bool
    corpus_read_execution_performed: bool
    source_mutation_allowed: bool
    source_mutation_performed: bool
    analytic_conclusion_allowed: bool
    forecast_creation_allowed: bool
    signals_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    execution_allowed: bool
    trading_recommendations_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    oia_subsystem_complete: bool
    attestation_artifact_persistence_allowed: bool
    controlled_callable_invocation_completion_attestation_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterControlledCallableInvocationCompletionAttestationGate:
    def __init__(
        self,
        *,
        invocation_directory: Path | str = DEFAULT_INVOCATION_DIRECTORY,
        attestation_directory: Path | str = DEFAULT_ATTESTATION_DIRECTORY,
    ) -> None:
        self.invocation_directory = Path(invocation_directory)
        self.attestation_directory = Path(attestation_directory)

    def _load_source(self) -> dict[str, Any]:
        path = self.invocation_directory / "current.json"
        if not path.exists():
            raise ControlledCallableInvocationCompletionAttestationInvariantError(
                f"OIA-066 current invocation artifact missing: {path}"
            )

        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ControlledCallableInvocationCompletionAttestationInvariantError(
                "OIA-066 invocation artifact could not be decoded"
            ) from exc

        manifest_hash = source.pop(
            "controlled_callable_invocation_manifest_hash",
            None,
        )
        if not _valid_hash(manifest_hash) or stable_hash(source) != manifest_hash:
            raise ControlledCallableInvocationCompletionAttestationInvariantError(
                "OIA-066 invocation manifest hash mismatch"
            )
        source["controlled_callable_invocation_manifest_hash"] = manifest_hash

        required_flags = {
            "schema_version": "OIA-066",
            "readiness_consumed": True,
            "owner_reconstruction_performed": True,
            "callable_binding_to_owner_performed": True,
            "callable_invocation_performed": True,
            "adapter_execution_performed": True,
            "corpus_read_execution_performed": True,
            "research_execution_allowed": False,
            "analytic_conclusion_allowed": False,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "trading_recommendations_allowed": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "owner_instances_retained": False,
            "bound_methods_retained": False,
        }
        for field, expected in required_flags.items():
            if source.get(field) != expected:
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    f"unsafe or invalid OIA-066 field: {field}"
                )

        entries = source.get("invocation_entries")
        if (
            not isinstance(entries, list)
            or not entries
            or source.get("invocation_entry_count") != len(entries)
        ):
            raise ControlledCallableInvocationCompletionAttestationInvariantError(
                "OIA-066 invocation entries invalid"
            )

        return source

    def attest(
        self,
        *,
        attested_at: datetime,
        persist: bool = True,
    ) -> ControlledCallableInvocationCompletionAttestation:
        attested_at = _aware(attested_at, "attested_at")
        source = self._load_source()

        seen_adapters: set[str] = set()
        seen_nonce_pairs: set[tuple[str, str]] = set()
        completion_entries: list[
            ControlledCallableInvocationCompletionEntry
        ] = []

        for expected_sequence, source_entry in enumerate(
            source["invocation_entries"],
            start=1,
        ):
            entry = dict(source_entry)
            invocation_hash = entry.pop(
                "controlled_callable_invocation_hash",
                None,
            )
            if (
                not _valid_hash(invocation_hash)
                or stable_hash(entry) != invocation_hash
            ):
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    "OIA-066 invocation entry hash mismatch"
                )
            entry[
                "controlled_callable_invocation_hash"
            ] = invocation_hash

            if entry.get("sequence") != expected_sequence:
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    "OIA-066 invocation sequence mismatch"
                )

            adapter_id = entry.get("adapter_id")
            if adapter_id not in APPROVED_ADAPTERS:
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    "unapproved OIA-066 adapter"
                )
            if adapter_id in seen_adapters:
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    "duplicate OIA-066 adapter"
                )
            seen_adapters.add(adapter_id)

            nonce_pair = (
                entry.get("activation_nonce"),
                entry.get("consumption_attempt_nonce"),
            )
            if (
                not all(
                    isinstance(value, str) and value
                    for value in nonce_pair
                )
                or nonce_pair in seen_nonce_pairs
            ):
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    "invalid or duplicate OIA-066 nonce pair"
                )
            seen_nonce_pairs.add(nonce_pair)

            if not _valid_hash(entry.get("source_readiness_hash")):
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    "invalid OIA-066 source readiness hash"
                )
            if not _valid_hash(entry.get("invocation_argument_hash")):
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    "invalid OIA-066 invocation argument hash"
                )
            if (
                stable_hash(entry.get("invocation_arguments", {}))
                != entry["invocation_argument_hash"]
            ):
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    "OIA-066 invocation argument hash mismatch"
                )
            if not _valid_hash(entry.get("result_hash")):
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    "invalid OIA-066 result hash"
                )
            if not isinstance(entry.get("result_summary"), dict):
                raise ControlledCallableInvocationCompletionAttestationInvariantError(
                    "invalid OIA-066 result summary"
                )

            required_entry_flags = {
                "owner_reconstructed": True,
                "method_bound_to_owner": True,
                "callable_invoked": True,
                "adapter_executed": True,
                "corpus_read_executed": True,
                "source_mutation_performed": False,
            }
            for field, expected in required_entry_flags.items():
                if entry.get(field) != expected:
                    raise ControlledCallableInvocationCompletionAttestationInvariantError(
                        f"unsafe or incomplete OIA-066 invocation entry: {field}"
                    )

            completion_body = {
                "sequence": expected_sequence,
                "worker_id": entry["worker_id"],
                "work_item_id": entry["work_item_id"],
                "adapter_id": adapter_id,
                "source_invocation_hash": invocation_hash,
                "activation_nonce": entry["activation_nonce"],
                "consumption_attempt_nonce": entry[
                    "consumption_attempt_nonce"
                ],
                "result_type": entry["result_type"],
                "result_hash": entry["result_hash"],
                "result_summary_hash": stable_hash(
                    entry["result_summary"]
                ),
                "callable_invoked": True,
                "adapter_executed": True,
                "corpus_read_executed": True,
                "source_mutation_performed": False,
                "completion_validated": True,
                "completion_status": "validated",
            }
            completion_entries.append(
                ControlledCallableInvocationCompletionEntry(
                    **completion_body,
                    controlled_callable_invocation_completion_entry_hash=stable_hash(
                        completion_body
                    ),
                )
            )

        if seen_adapters != APPROVED_ADAPTERS:
            raise ControlledCallableInvocationCompletionAttestationInvariantError(
                "complete approved OIA-066 adapter set was not executed"
            )

        source_manifest_hash = source[
            "controlled_callable_invocation_manifest_hash"
        ]
        attestation_identity = {
            "source_invocation_id": source[
                "controlled_callable_invocation_id"
            ],
            "source_invocation_manifest_hash": source_manifest_hash,
            "attested_at": attested_at.isoformat(),
            "completion_entry_hashes": [
                item.controlled_callable_invocation_completion_entry_hash
                for item in completion_entries
            ],
        }
        attestation_id = stable_hash(attestation_identity)

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "attested_at": attested_at.isoformat(),
            "controlled_callable_invocation_completion_attestation_id": attestation_id,
            "controlled_callable_invocation_completion_attestation_status": STATUS_ATTESTED,
            "controlled_callable_invocation_completion_attestation_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "completion_entry_count": len(completion_entries),
            "completion_entries": tuple(completion_entries),
            "source_invocation_id": source[
                "controlled_callable_invocation_id"
            ],
            "source_invocation_manifest_hash": source_manifest_hash,
            "source_readiness_id": source["source_readiness_id"],
            "source_readiness_manifest_hash": source[
                "source_readiness_manifest_hash"
            ],
            "source_lineage": dict(source["source_lineage"]),
            "invocation_results_validated": True,
            "all_approved_invocations_completed": True,
            "all_result_hashes_verified": True,
            "all_nonce_pairs_unique": True,
            "source_invocation_reexecuted": False,
            "owner_reconstruction_performed": False,
            "callable_binding_performed": False,
            "callable_invocation_performed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_performed": False,
            "source_mutation_allowed": False,
            "source_mutation_performed": False,
            "analytic_conclusion_allowed": False,
            "forecast_creation_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "trading_recommendations_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "oia_subsystem_complete": True,
            "attestation_artifact_persistence_allowed": True,
        }

        serializable = dict(body)
        serializable["completion_entries"] = [
            asdict(item) for item in completion_entries
        ]
        manifest_hash = stable_hash(serializable)

        attestation = ControlledCallableInvocationCompletionAttestation(
            **body,
            controlled_callable_invocation_completion_attestation_manifest_hash=manifest_hash,
        )

        if persist:
            payload = asdict(attestation)
            _atomic_write(
                self.attestation_directory / "current.json",
                payload,
            )
            _atomic_write(
                self.attestation_directory
                / "attestations"
                / f"{attestation_id}.json",
                payload,
            )
            _atomic_write(
                self.attestation_directory
                / "workers"
                / attestation.worker_id
                / f"{attestation_id}.json",
                payload,
            )

        return attestation
