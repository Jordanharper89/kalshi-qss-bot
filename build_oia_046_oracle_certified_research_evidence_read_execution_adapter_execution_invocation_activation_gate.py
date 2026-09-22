from pathlib import Path
import py_compile
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

OIA045 = (
    ANALYTICS
    / "oracle_certified_research_evidence_read_execution_adapter_execution_invocation_manifest_builder.py"
)

PRODUCTION = (
    ANALYTICS
    / "oracle_certified_research_evidence_read_execution_adapter_execution_invocation_activation_gate.py"
)

TEST = (
    ROOT
    / "test_oia_046_oracle_certified_research_evidence_read_execution_adapter_execution_invocation_activation_gate.py"
)

INIT = ANALYTICS / "__init__.py"


PRODUCTION_SOURCE = r'''
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "OIA-046"
ENGINE_ID = "OIA-046"

POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "execution-invocation-activation.v1"
)

STATUS_INVOCATION_ACTIVE = (
    "evidence_read_execution_adapter_execution_invocation_active"
)

STATUS_ACTIVATION_ISSUED = (
    "evidence_read_execution_adapter_execution_invocation_activation_issued"
)

DEFAULT_INVOCATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_invocations"
)

DEFAULT_ACTIVATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_invocation_activation"
)


class AdapterExecutionInvocationActivationInvariantError(RuntimeError):
    """Raised when the OIA-045 invocation manifest is invalid or unsafe."""


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def valid_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def aware_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise AdapterExecutionInvocationActivationInvariantError(
            f"{field_name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=path.parent,
    )
    temporary_path = Path(handle.name)

    try:
        with handle:
            json.dump(
                payload,
                handle,
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


@dataclass(frozen=True)
class ActiveAdapterExecutionInvocation:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    active_invocation_arguments: dict[str, Any]
    activation_checks: tuple[str, ...]
    activation_status: str
    source_execution_invocation_hash: str
    source_authorization_entry_hash: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    active_execution_invocation_hash: str


@dataclass(frozen=True)
class AdapterExecutionInvocationActivationManifest:
    schema_version: str
    engine_id: str
    activated_at: str
    activation_id: str
    activation_status: str
    activation_policy_id: str
    worker_id: str
    active_invocation_count: int
    active_invocations: tuple[ActiveAdapterExecutionInvocation, ...]
    source_execution_invocation_manifest_id: str
    source_execution_invocation_manifest_hash: str
    source_execution_authorization_id: str
    source_execution_authorization_manifest_hash: str
    source_execution_readiness_id: str
    source_execution_readiness_manifest_hash: str
    source_activation_hash: str
    source_lineage: dict[str, Any]
    invocation_activation_issued: bool
    execution_readiness_evaluation_allowed: bool
    callable_resolution_allowed: bool
    adapter_execution_allowed: bool
    adapter_execution_performed: bool
    corpus_read_execution_allowed: bool
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
    activation_artifact_persistence_allowed: bool
    activation_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationActivationGate:
    """
    OIA-046 exact invocation activation boundary.

    This gate activates the canonical invocation produced by OIA-045 so that a
    later certified component may evaluate execution readiness.

    Activation is not execution.

    This component does not:
    - import an adapter,
    - resolve a callable,
    - bind a callable,
    - connect to PostgreSQL,
    - perform a network request,
    - read the certified corpus,
    - produce research conclusions,
    - create signals,
    - create alerts,
    - communicate with Q Series,
    - create orders,
    - move funds,
    - mutate a portfolio.
    """

    def __init__(
        self,
        *,
        invocation_directory: Path | str = DEFAULT_INVOCATION_DIRECTORY,
        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,
    ) -> None:
        self.invocation_directory = Path(invocation_directory)
        self.activation_directory = Path(activation_directory)

    def _load_invocation_manifest(self) -> dict[str, Any]:
        current = self.invocation_directory / "current.json"

        if not current.exists():
            raise AdapterExecutionInvocationActivationInvariantError(
                f"OIA-045 current invocation artifact missing: {current}"
            )

        try:
            source = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation artifact could not be decoded."
            ) from error

        if not isinstance(source, dict):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation artifact must be a JSON object."
            )

        manifest_hash = source.pop(
            "invocation_manifest_hash",
            None,
        )

        if (
            not valid_hash(manifest_hash)
            or stable_hash(source) != manifest_hash
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation manifest hash verification failed."
            )

        source["invocation_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-045",
            "engine_id": "OIA-045",
            "invocation_manifest_status":
                "evidence_read_execution_adapter_execution_invocation_manifest_issued",
            "invocation_manifest_created": True,
            "invocation_activation_allowed": True,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
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
            "invocation_artifact_persistence_allowed": True,
        }

        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise AdapterExecutionInvocationActivationInvariantError(
                    f"OIA-045 invariant failed: {field_name}."
                )

        invocation_manifest_id = source.get(
            "invocation_manifest_id"
        )
        invocation_policy_id = source.get(
            "invocation_policy_id"
        )
        worker_id = source.get("worker_id")
        invocation_count = source.get("invocation_count")
        invocations = source.get("invocations")

        if (
            not isinstance(invocation_manifest_id, str)
            or not invocation_manifest_id
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation manifest ID is invalid."
            )

        if (
            invocation_policy_id
            != (
                "oracle.certified-research-evidence-read-execution-adapter-"
                "execution-invocation-manifest.v1"
            )
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation policy mismatch."
            )

        if not isinstance(worker_id, str) or not worker_id:
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 worker ID is invalid."
            )

        if (
            not isinstance(invocation_count, int)
            or isinstance(invocation_count, bool)
            or invocation_count < 1
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation count is invalid."
            )

        if (
            not isinstance(invocations, list)
            or len(invocations) != invocation_count
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 invocation collection is invalid."
            )

        hash_fields = {
            "source_execution_authorization_manifest_hash",
            "source_execution_readiness_manifest_hash",
            "source_activation_hash",
        }

        for field_name in hash_fields:
            if not valid_hash(source.get(field_name)):
                raise AdapterExecutionInvocationActivationInvariantError(
                    f"OIA-045 hash field is invalid: {field_name}."
                )

        identifier_fields = {
            "source_execution_authorization_id",
            "source_execution_readiness_id",
        }

        for field_name in identifier_fields:
            value = source.get(field_name)

            if not isinstance(value, str) or not value:
                raise AdapterExecutionInvocationActivationInvariantError(
                    f"OIA-045 identifier is invalid: {field_name}."
                )

        source_lineage = source.get("source_lineage")

        if not isinstance(source_lineage, dict) or not source_lineage:
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 source lineage is missing."
            )

        required_lineage_fields = {
            "source_evidence_read_execution_adapter_invocation_manifest_id",
            "source_evidence_read_execution_adapter_authorization_manifest_id",
            "source_evidence_read_execution_adapter_readiness_manifest_id",
            "source_evidence_read_execution_adapter_binding_manifest_id",
            "source_evidence_read_execution_invocation_activation_id",
            "source_evidence_read_execution_invocation_manifest_id",
            "source_evidence_read_execution_authorization_id",
            "source_evidence_read_execution_readiness_id",
            "source_evidence_read_request_activation_id",
            "source_evidence_read_request_manifest_id",
            "source_evidence_task_activation_id",
            "source_evidence_task_manifest_id",
            "source_evidence_batch_activation_id",
            "source_evidence_batch_id",
            "source_evidence_session_id",
            "source_evidence_manifest_id",
            "source_certification_id",
            "source_readiness_id",
            "source_session_id",
            "source_activation_id",
            "source_claim_id",
            "dispatch_manifest_id",
            "selected_batch_id",
            "selected_batch_number",
        }

        missing_lineage = required_lineage_fields - set(
            source_lineage
        )

        if missing_lineage:
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 lineage is incomplete: "
                f"{sorted(missing_lineage)}"
            )

        for field_name in (
            required_lineage_fields - {"selected_batch_number"}
        ):
            value = source_lineage.get(field_name)

            if not isinstance(value, str) or not value:
                raise AdapterExecutionInvocationActivationInvariantError(
                    f"OIA-045 lineage field is invalid: {field_name}."
                )

        selected_batch_number = source_lineage.get(
            "selected_batch_number"
        )

        if (
            not isinstance(selected_batch_number, int)
            or isinstance(selected_batch_number, bool)
            or selected_batch_number < 1
        ):
            raise AdapterExecutionInvocationActivationInvariantError(
                "OIA-045 selected batch number is invalid."
            )

        required_invocation_checks = {
            "authorization_manifest_hash_verified",
            "authorization_entry_hash_verified",
            "readiness_entry_lineage_verified",
            "active_invocation_lineage_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_argument_allowlist_verified",
            "invocation_remained_non_executing",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }

        seen_work_item_ids: set[str] = set()
        seen_invocation_hashes: set[str] = set()

        for expected_sequence, invocation in enumerate(
            invocations,
            start=1,
        ):
            if not isinstance(invocation, dict):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation must be an object."
                )

            invocation_hash = invocation.pop(
                "execution_invocation_hash",
                None,
            )

            if (
                not valid_hash(invocation_hash)
                or stable_hash(invocation) != invocation_hash
            ):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 execution invocation hash verification failed."
                )

            invocation["execution_invocation_hash"] = invocation_hash

            if invocation_hash in seen_invocation_hashes:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 contains a duplicate invocation hash."
                )

            seen_invocation_hashes.add(invocation_hash)

            if invocation.get("sequence") != expected_sequence:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation sequence is non-canonical."
                )

            if invocation.get("worker_id") != worker_id:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation worker identity mismatch."
                )

            if (
                invocation.get("invocation_status")
                != "evidence_read_execution_adapter_execution_invocation_ready"
            ):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation is not ready for activation."
                )

            work_item_id = invocation.get("work_item_id")
            adapter_id = invocation.get("adapter_id")
            read_operation = invocation.get("read_operation")
            arguments = invocation.get("invocation_arguments")
            checks = invocation.get("invocation_checks")

            if not isinstance(work_item_id, str) or not work_item_id:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 work-item identity is invalid."
                )

            if work_item_id in seen_work_item_ids:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 contains duplicate work-item identities."
                )

            seen_work_item_ids.add(work_item_id)

            if (
                not isinstance(adapter_id, str)
                or not adapter_id.startswith("oracle_read_only_")
                or "write" in adapter_id.lower()
                or "mutation" in adapter_id.lower()
                or "order" in adapter_id.lower()
                or "fund" in adapter_id.lower()
                or "portfolio" in adapter_id.lower()
            ):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 adapter identity is not approved read-only."
                )

            if (
                not isinstance(read_operation, str)
                or not read_operation.startswith("read_")
                or "write" in read_operation.lower()
                or "delete" in read_operation.lower()
                or "update" in read_operation.lower()
                or "insert" in read_operation.lower()
                or "order" in read_operation.lower()
            ):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 operation is not a bounded read operation."
                )

            if not isinstance(arguments, dict):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation arguments are invalid."
                )

            if set(arguments) != {
                "activated",
                "read_only",
                "execute",
            }:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation argument allowlist mismatch."
                )

            if arguments.get("activated") is not True:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation lacks prior activation."
                )

            if arguments.get("read_only") is not True:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation is not read-only."
                )

            if arguments.get("execute") is not False:
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation crossed the execution boundary."
                )

            if (
                not isinstance(checks, list)
                or not required_invocation_checks.issubset(set(checks))
            ):
                raise AdapterExecutionInvocationActivationInvariantError(
                    "OIA-045 invocation checks are incomplete."
                )

            lineage_hash_fields = {
                "source_authorization_entry_hash",
                "source_readiness_entry_hash",
                "source_active_adapter_invocation_hash",
            }

            for field_name in lineage_hash_fields:
                if not valid_hash(invocation.get(field_name)):
                    raise AdapterExecutionInvocationActivationInvariantError(
                        f"OIA-045 invocation lineage hash is invalid: "
                        f"{field_name}."
                    )

        return source

    def activate(
        self,
        *,
        activated_at: datetime,
        persist: bool = True,
    ) -> AdapterExecutionInvocationActivationManifest:
        activated_at = aware_utc(activated_at, "activated_at")
        source = self._load_invocation_manifest()

        active_invocations: list[
            ActiveAdapterExecutionInvocation
        ] = []

        for sequence, invocation in enumerate(
            source["invocations"],
            start=1,
        ):
            active_arguments = dict(
                invocation["invocation_arguments"]
            )

            # OIA-046 activates the invocation identity for later readiness
            # evaluation. The actual execution bit remains closed.
            active_arguments["activated"] = True
            active_arguments["read_only"] = True
            active_arguments["execute"] = False

            body = {
                "sequence": sequence,
                "worker_id": invocation["worker_id"],
                "work_item_id": invocation["work_item_id"],
                "adapter_id": invocation["adapter_id"],
                "read_operation": invocation["read_operation"],
                "active_invocation_arguments": active_arguments,
                "activation_checks": (
                    "invocation_manifest_hash_verified",
                    "execution_invocation_hash_verified",
                    "authorization_lineage_verified",
                    "readiness_lineage_verified",
                    "prior_activation_lineage_verified",
                    "adapter_read_only_identity_verified",
                    "operation_read_only_verified",
                    "invocation_argument_allowlist_verified",
                    "active_invocation_remained_non_executing",
                    "callable_resolution_remained_disabled",
                    "corpus_execution_remained_disabled",
                    "oracle_qseries_boundary_verified",
                ),
                "activation_status": STATUS_INVOCATION_ACTIVE,
                "source_execution_invocation_hash":
                    invocation["execution_invocation_hash"],
                "source_authorization_entry_hash":
                    invocation["source_authorization_entry_hash"],
                "source_readiness_entry_hash":
                    invocation["source_readiness_entry_hash"],
                "source_active_adapter_invocation_hash":
                    invocation[
                        "source_active_adapter_invocation_hash"
                    ],
            }

            active_invocations.append(
                ActiveAdapterExecutionInvocation(
                    **body,
                    active_execution_invocation_hash=stable_hash(
                        body
                    ),
                )
            )

        source_manifest_hash = source[
            "invocation_manifest_hash"
        ]

        activation_id = (
            "oia046-adapter-execution-invocation-activation-"
            + stable_hash(
                {
                    "source_execution_invocation_manifest_hash":
                        source_manifest_hash,
                    "activation_policy_id": POLICY_ID,
                }
            )[:32]
        )

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "activated_at": activated_at.isoformat(),
            "activation_id": activation_id,
            "activation_status": STATUS_ACTIVATION_ISSUED,
            "activation_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "active_invocation_count": len(active_invocations),
            "active_invocations": tuple(active_invocations),
            "source_execution_invocation_manifest_id":
                source["invocation_manifest_id"],
            "source_execution_invocation_manifest_hash":
                source_manifest_hash,
            "source_execution_authorization_id":
                source["source_execution_authorization_id"],
            "source_execution_authorization_manifest_hash":
                source[
                    "source_execution_authorization_manifest_hash"
                ],
            "source_execution_readiness_id":
                source["source_execution_readiness_id"],
            "source_execution_readiness_manifest_hash":
                source[
                    "source_execution_readiness_manifest_hash"
                ],
            "source_activation_hash":
                source["source_activation_hash"],
            "source_lineage": dict(source["source_lineage"]),
            "invocation_activation_issued": True,
            "execution_readiness_evaluation_allowed": True,
            "callable_resolution_allowed": False,
            "adapter_execution_allowed": False,
            "adapter_execution_performed": False,
            "corpus_read_execution_allowed": False,
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
        }

        serializable_body = dict(manifest_body)
        serializable_body["active_invocations"] = [
            asdict(invocation)
            for invocation in active_invocations
        ]

        result = AdapterExecutionInvocationActivationManifest(
            **manifest_body,
            activation_manifest_hash=stable_hash(
                serializable_body
            ),
        )

        if persist:
            payload = asdict(result)

            atomic_write(
                self.activation_directory / "current.json",
                payload,
            )

            atomic_write(
                self.activation_directory
                / "activations"
                / f"{activation_id}.json",
                payload,
            )

            atomic_write(
                self.activation_directory
                / "workers"
                / result.worker_id
                / f"{activation_id}.json",
                payload,
            )

        return result
'''


TEST_SOURCE = r'''
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_execution_invocation_activation_gate import (
    AdapterExecutionInvocationActivationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationActivationGate,
    POLICY_ID,
    STATUS_ACTIVATION_ISSUED,
    STATUS_INVOCATION_ACTIVE,
    stable_hash,
)


def seed_oia045(directory: Path) -> dict:
    source_lineage = {
        "source_evidence_read_execution_adapter_invocation_manifest_id":
            "oia041-test",
        "source_evidence_read_execution_adapter_authorization_manifest_id":
            "oia040-test",
        "source_evidence_read_execution_adapter_readiness_manifest_id":
            "oia039-test",
        "source_evidence_read_execution_adapter_binding_manifest_id":
            "oia038-test",
        "source_evidence_read_execution_invocation_activation_id":
            "oia037-test",
        "source_evidence_read_execution_invocation_manifest_id":
            "oia036-test",
        "source_evidence_read_execution_authorization_id":
            "oia035-test",
        "source_evidence_read_execution_readiness_id":
            "oia034-test",
        "source_evidence_read_request_activation_id":
            "oia033-test",
        "source_evidence_read_request_manifest_id":
            "oia032-test",
        "source_evidence_task_activation_id":
            "oia031-test",
        "source_evidence_task_manifest_id":
            "oia030-test",
        "source_evidence_batch_activation_id":
            "oia029-test",
        "source_evidence_batch_id":
            "oia028-test",
        "source_evidence_session_id":
            "oia027-test",
        "source_evidence_manifest_id":
            "oia026-test",
        "source_certification_id":
            "oia025-test",
        "source_readiness_id":
            "oia024-test",
        "source_session_id":
            "oia023-test",
        "source_activation_id":
            "oia022-test",
        "source_claim_id":
            "oia021-test",
        "dispatch_manifest_id":
            "oia020-test",
        "selected_batch_id":
            "oia020-batch",
        "selected_batch_number": 1,
    }

    invocation_body = {
        "sequence": 1,
        "worker_id": "oracle-worker-test",
        "work_item_id": "work.test",
        "adapter_id":
            "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation": "read_canonical_observations",
        "invocation_arguments": {
            "activated": True,
            "read_only": True,
            "execute": False,
        },
        "invocation_checks": [
            "authorization_manifest_hash_verified",
            "authorization_entry_hash_verified",
            "readiness_entry_lineage_verified",
            "active_invocation_lineage_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_argument_allowlist_verified",
            "invocation_remained_non_executing",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        ],
        "invocation_status":
            "evidence_read_execution_adapter_execution_invocation_ready",
        "source_authorization_entry_hash": stable_hash(
            {"source": "oia044-entry"}
        ),
        "source_readiness_entry_hash": stable_hash(
            {"source": "oia043-entry"}
        ),
        "source_active_adapter_invocation_hash": stable_hash(
            {"source": "oia042-active-invocation"}
        ),
    }

    invocation = dict(invocation_body)
    invocation["execution_invocation_hash"] = stable_hash(
        invocation_body
    )

    manifest_body = {
        "schema_version": "OIA-045",
        "engine_id": "OIA-045",
        "created_at": "2026-07-22T03:00:00+00:00",
        "invocation_manifest_id":
            "oia045-test-invocation-manifest",
        "invocation_manifest_status":
            "evidence_read_execution_adapter_execution_invocation_manifest_issued",
        "invocation_policy_id":
            "oracle.certified-research-evidence-read-execution-adapter-"
            "execution-invocation-manifest.v1",
        "worker_id": "oracle-worker-test",
        "invocation_count": 1,
        "invocations": [invocation],
        "source_execution_authorization_id":
            "oia044-test-authorization",
        "source_execution_authorization_manifest_hash":
            stable_hash({"source": "oia044-manifest"}),
        "source_execution_readiness_id":
            "oia043-test-readiness",
        "source_execution_readiness_manifest_hash":
            stable_hash({"source": "oia043-manifest"}),
        "source_activation_hash":
            stable_hash({"source": "oia042-activation"}),
        "source_lineage": source_lineage,
        "invocation_manifest_created": True,
        "invocation_activation_allowed": True,
        "adapter_execution_allowed": False,
        "adapter_execution_performed": False,
        "corpus_read_execution_allowed": False,
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
        "invocation_artifact_persistence_allowed": True,
    }

    payload = dict(manifest_body)
    payload["invocation_manifest_hash"] = stable_hash(
        manifest_body
    )

    directory.mkdir(parents=True, exist_ok=True)

    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-046 TEST")
    print(" EXECUTION INVOCATION ACTIVATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        invocation_directory = root / "invocations"
        activation_directory = root / "activation"

        source = seed_oia045(invocation_directory)

        gate = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationActivationGate(
                invocation_directory=invocation_directory,
                activation_directory=activation_directory,
            )
        )

        fixed = datetime(
            2026,
            7,
            22,
            4,
            0,
            tzinfo=timezone.utc,
        )

        first = gate.activate(
            activated_at=fixed,
            persist=True,
        )

        second = gate.activate(
            activated_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "OIA-046"
        assert first.engine_id == "OIA-046"
        assert first.activation_status == STATUS_ACTIVATION_ISSUED
        assert first.activation_policy_id == POLICY_ID
        assert first.active_invocation_count == 1

        active = first.active_invocations[0]

        assert active.activation_status == STATUS_INVOCATION_ACTIVE

        assert (
            active.adapter_id
            == "oracle_read_only_canonical_observation_adapter.v1"
        )

        assert (
            active.read_operation
            == "read_canonical_observations"
        )

        assert active.active_invocation_arguments == {
            "activated": True,
            "read_only": True,
            "execute": False,
        }

        assert active.source_execution_invocation_hash == (
            source["invocations"][0][
                "execution_invocation_hash"
            ]
        )

        assert active.source_authorization_entry_hash == (
            source["invocations"][0][
                "source_authorization_entry_hash"
            ]
        )

        assert active.source_readiness_entry_hash == (
            source["invocations"][0][
                "source_readiness_entry_hash"
            ]
        )

        assert active.source_active_adapter_invocation_hash == (
            source["invocations"][0][
                "source_active_adapter_invocation_hash"
            ]
        )

        assert {
            "invocation_manifest_hash_verified",
            "execution_invocation_hash_verified",
            "authorization_lineage_verified",
            "readiness_lineage_verified",
            "prior_activation_lineage_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_argument_allowlist_verified",
            "active_invocation_remained_non_executing",
            "callable_resolution_remained_disabled",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }.issubset(set(active.activation_checks))

        assert first.source_execution_invocation_manifest_id == (
            source["invocation_manifest_id"]
        )

        assert (
            first.source_execution_invocation_manifest_hash
            == source["invocation_manifest_hash"]
        )

        assert first.source_execution_authorization_id == (
            source["source_execution_authorization_id"]
        )

        assert (
            first.source_execution_authorization_manifest_hash
            == source[
                "source_execution_authorization_manifest_hash"
            ]
        )

        assert first.source_execution_readiness_id == (
            source["source_execution_readiness_id"]
        )

        assert (
            first.source_execution_readiness_manifest_hash
            == source[
                "source_execution_readiness_manifest_hash"
            ]
        )

        assert first.source_activation_hash == (
            source["source_activation_hash"]
        )

        assert first.source_lineage == source["source_lineage"]

        assert first.invocation_activation_issued is True
        assert first.execution_readiness_evaluation_allowed is True
        assert first.callable_resolution_allowed is False
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.activation_artifact_persistence_allowed is True

        prohibited_values = (
            first.research_execution_allowed,
            first.analytic_conclusion_allowed,
            first.forecast_creation_allowed,
            first.signals_allowed,
            first.alerts_allowed,
            first.qseries_handoff_allowed,
            first.execution_allowed,
            first.trading_recommendations_allowed,
            first.source_mutation_allowed,
            first.market_order_creation_allowed,
            first.funds_movement_allowed,
            first.portfolio_mutation_allowed,
        )

        assert all(value is False for value in prohibited_values)

        manifest_body = dict(first.__dict__)
        manifest_hash = manifest_body.pop(
            "activation_manifest_hash"
        )

        manifest_body["active_invocations"] = [
            dict(item.__dict__)
            for item in first.active_invocations
        ]

        assert manifest_hash == stable_hash(manifest_body)

        active_body = dict(active.__dict__)
        active_hash = active_body.pop(
            "active_execution_invocation_hash"
        )

        assert active_hash == stable_hash(active_body)

        assert (
            activation_directory / "current.json"
        ).exists()

        assert list(
            (
                activation_directory / "activations"
            ).glob("*.json")
        )

        assert list(
            (
                activation_directory
                / "workers"
                / first.worker_id
            ).glob("*.json")
        )

        current = json.loads(
            (
                activation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        assert current["callable_resolution_allowed"] is False
        assert current["adapter_execution_allowed"] is False
        assert current["adapter_execution_performed"] is False
        assert current["execution_allowed"] is False
        assert current["qseries_handoff_allowed"] is False

        tampered = json.loads(
            (
                invocation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered["invocations"][0][
            "invocation_arguments"
        ]["execute"] = True

        (
            invocation_directory / "current.json"
        ).write_text(
            json.dumps(tampered, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.activate(
                activated_at=fixed,
                persist=False,
            )
        except AdapterExecutionInvocationActivationInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered executable OIA-045 invocation accepted."
            )

        seed_oia045(invocation_directory)

        tampered_adapter = json.loads(
            (
                invocation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered_adapter["invocations"][0]["adapter_id"] = (
            "oracle_write_capable_observation_adapter.v1"
        )

        invocation_payload = dict(
            tampered_adapter["invocations"][0]
        )
        invocation_payload.pop("execution_invocation_hash")

        tampered_adapter["invocations"][0][
            "execution_invocation_hash"
        ] = stable_hash(invocation_payload)

        manifest_payload = dict(tampered_adapter)
        manifest_payload.pop("invocation_manifest_hash")

        tampered_adapter[
            "invocation_manifest_hash"
        ] = stable_hash(manifest_payload)

        (
            invocation_directory / "current.json"
        ).write_text(
            json.dumps(tampered_adapter, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.activate(
                activated_at=fixed,
                persist=False,
            )
        except AdapterExecutionInvocationActivationInvariantError:
            pass
        else:
            raise AssertionError(
                "Write-capable adapter invocation was activated."
            )

        seed_oia045(invocation_directory)

        duplicate_work_item = json.loads(
            (
                invocation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        duplicate = dict(
            duplicate_work_item["invocations"][0]
        )
        duplicate["sequence"] = 2
        duplicate.pop("execution_invocation_hash")
        duplicate["execution_invocation_hash"] = stable_hash(
            {
                key: value
                for key, value in duplicate.items()
                if key != "execution_invocation_hash"
            }
        )

        duplicate_work_item["invocations"].append(duplicate)
        duplicate_work_item["invocation_count"] = 2

        duplicate_manifest_body = dict(duplicate_work_item)
        duplicate_manifest_body.pop("invocation_manifest_hash")

        duplicate_work_item[
            "invocation_manifest_hash"
        ] = stable_hash(duplicate_manifest_body)

        (
            invocation_directory / "current.json"
        ).write_text(
            json.dumps(duplicate_work_item, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.activate(
                activated_at=fixed,
                persist=False,
            )
        except AdapterExecutionInvocationActivationInvariantError:
            pass
        else:
            raise AssertionError(
                "Duplicate work-item invocation was activated."
            )

    print("[PASS] Actual OIA-045 execution-invocation contract consumed")
    print("[PASS] Activation manifest and active-invocation hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-045 lineage preserved")
    print("[PASS] Exact authorized read-only invocation activated")
    print("[PASS] Active invocation arguments remained non-executing")
    print("[PASS] Callable resolution remained disabled")
    print("[PASS] No adapter was imported, resolved, invoked, or executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, duplicate, or write-capable invocation rejected")
    print("[PASS] Atomic invocation-activation artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


INIT_BLOCK = r'''
from .oracle_certified_research_evidence_read_execution_adapter_execution_invocation_activation_gate import (
    ActiveAdapterExecutionInvocation,
    AdapterExecutionInvocationActivationInvariantError,
    AdapterExecutionInvocationActivationManifest,
    OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationActivationGate,
    POLICY_ID as OIA046_POLICY_ID,
    STATUS_ACTIVATION_ISSUED as OIA046_STATUS_ACTIVATION_ISSUED,
    STATUS_INVOCATION_ACTIVE as OIA046_STATUS_INVOCATION_ACTIVE,
)

__all__ = [
    "ActiveAdapterExecutionInvocation",
    "AdapterExecutionInvocationActivationInvariantError",
    "AdapterExecutionInvocationActivationManifest",
    "OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationActivationGate",
    "OIA046_POLICY_ID",
    "OIA046_STATUS_ACTIVATION_ISSUED",
    "OIA046_STATUS_INVOCATION_ACTIVE",
] + __all__
'''


def verify_oia045() -> None:
    if not OIA045.exists():
        raise RuntimeError(
            f"Actual OIA-045 production module missing: {OIA045}"
        )

    text = OIA045.read_text(encoding="utf-8")

    required_tokens = [
        'SCHEMA_VERSION = "OIA-045"',
        'ENGINE_ID = "OIA-045"',
        "AdapterExecutionInvocation",
        "AdapterExecutionInvocationManifest",
        "OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationManifestBuilder",
        "evidence_read_execution_adapter_execution_invocation_ready",
        "evidence_read_execution_adapter_execution_invocation_manifest_issued",
        "execution_invocation_hash",
        "invocation_manifest_hash",
        "source_authorization_entry_hash",
        "source_readiness_entry_hash",
        "source_active_adapter_invocation_hash",
        "source_execution_authorization_manifest_hash",
        "source_execution_readiness_manifest_hash",
        "source_activation_hash",
        "source_lineage",
        "invocation_manifest_created",
        "invocation_activation_allowed",
        "adapter_execution_allowed",
        "adapter_execution_performed",
        "corpus_read_execution_allowed",
        "qseries_handoff_allowed",
        "execution_allowed",
        "market_order_creation_allowed",
        "funds_movement_allowed",
        "portfolio_mutation_allowed",
    ]

    missing = [
        token
        for token in required_tokens
        if token not in text
    ]

    if missing:
        raise RuntimeError(
            "Actual OIA-045 production contract mismatch: "
            f"{missing}"
        )


def write_full(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        source.strip() + "\n",
        encoding="utf-8",
    )

    print(f"[OK] FULL REPLACEMENT: {path}")


def update_init() -> None:
    existing = (
        INIT.read_text(encoding="utf-8")
        if INIT.exists()
        else "__all__ = []\n"
    )

    marker = (
        "from .oracle_certified_research_evidence_read_execution_"
        "adapter_execution_invocation_activation_gate import ("
    )

    if marker not in existing:
        INIT.write_text(
            existing.rstrip()
            + "\n"
            + INIT_BLOCK.strip()
            + "\n",
            encoding="utf-8",
        )

        print(f"[OK] PACKAGE UPDATED: {INIT}")
    else:
        print(f"[OK] PACKAGE ALREADY CURRENT: {INIT}")


def main() -> int:
    print("=" * 40)
    print(" OIA-046 INSTALLER")
    print(" EXECUTION INVOCATION ACTIVATION")
    print(" NON-EXECUTING ACTIVE INVOCATION")
    print("=" * 40)

    verify_oia045()

    print(
        "[OK] Actual OIA-045 execution-invocation contract verified"
    )

    write_full(PRODUCTION, PRODUCTION_SOURCE)
    write_full(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(
        str(PRODUCTION),
        doraise=True,
    )

    py_compile.compile(
        str(TEST),
        doraise=True,
    )

    py_compile.compile(
        str(INIT),
        doraise=True,
    )

    print("[OK] Production, test, and package syntax verified")

    result = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )

    if result.returncode:
        raise SystemExit(result.returncode)

    print("[OK] OIA-046 test executed automatically")
    print()
    print(
        "[DONE] OIA-046 certified research evidence read execution "
        "adapter execution invocation activation gate installed"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())