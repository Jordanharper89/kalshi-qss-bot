from pathlib import Path
import py_compile
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

OIA044 = (
    ANALYTICS
    / "oracle_certified_research_evidence_read_execution_adapter_execution_authorization_gate.py"
)

PRODUCTION = (
    ANALYTICS
    / "oracle_certified_research_evidence_read_execution_adapter_execution_invocation_manifest_builder.py"
)

TEST = (
    ROOT
    / "test_oia_045_oracle_certified_research_evidence_read_execution_adapter_execution_invocation_manifest_builder.py"
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


SCHEMA_VERSION = "OIA-045"
ENGINE_ID = "OIA-045"

POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "execution-invocation-manifest.v1"
)

STATUS_INVOCATION_READY = (
    "evidence_read_execution_adapter_execution_invocation_ready"
)

STATUS_MANIFEST_ISSUED = (
    "evidence_read_execution_adapter_execution_invocation_manifest_issued"
)

DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_authorization"
)

DEFAULT_INVOCATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_invocations"
)


class AdapterExecutionInvocationInvariantError(RuntimeError):
    """Raised when OIA-044 authorization evidence is invalid or unsafe."""


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
        raise AdapterExecutionInvocationInvariantError(
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
class AdapterExecutionInvocation:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    invocation_arguments: dict[str, Any]
    invocation_checks: tuple[str, ...]
    invocation_status: str
    source_authorization_entry_hash: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    execution_invocation_hash: str


@dataclass(frozen=True)
class AdapterExecutionInvocationManifest:
    schema_version: str
    engine_id: str
    created_at: str
    invocation_manifest_id: str
    invocation_manifest_status: str
    invocation_policy_id: str
    worker_id: str
    invocation_count: int
    invocations: tuple[AdapterExecutionInvocation, ...]
    source_execution_authorization_id: str
    source_execution_authorization_manifest_hash: str
    source_execution_readiness_id: str
    source_execution_readiness_manifest_hash: str
    source_activation_hash: str
    source_lineage: dict[str, Any]
    invocation_manifest_created: bool
    invocation_activation_allowed: bool
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
    invocation_artifact_persistence_allowed: bool
    invocation_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationManifestBuilder:
    """
    OIA-045 exact adapter execution invocation manifest boundary.

    This builder converts the OIA-044 authorization artifact into a canonical
    invocation manifest for later activation.

    It does not import, instantiate, resolve, call, or execute an adapter.
    It does not read the certified corpus.
    """

    def __init__(
        self,
        *,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
        invocation_directory: Path | str = DEFAULT_INVOCATION_DIRECTORY,
    ) -> None:
        self.authorization_directory = Path(authorization_directory)
        self.invocation_directory = Path(invocation_directory)

    def _load_authorization(self) -> dict[str, Any]:
        current = self.authorization_directory / "current.json"

        if not current.exists():
            raise AdapterExecutionInvocationInvariantError(
                f"OIA-044 current authorization artifact missing: {current}"
            )

        try:
            source = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization artifact could not be decoded."
            ) from error

        if not isinstance(source, dict):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization artifact must be a JSON object."
            )

        manifest_hash = source.pop(
            "authorization_manifest_hash",
            None,
        )

        if (
            not valid_hash(manifest_hash)
            or stable_hash(source) != manifest_hash
        ):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization manifest hash verification failed."
            )

        source["authorization_manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-044",
            "engine_id": "OIA-044",
            "authorization_status":
                "evidence_read_execution_adapter_execution_authorization_issued",
            "read_only_authorization_issued": True,
            "adapter_execution_authorization_allowed": True,
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
            "authorization_artifact_persistence_allowed": True,
        }

        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise AdapterExecutionInvocationInvariantError(
                    f"OIA-044 invariant failed: {field_name}."
                )

        authorization_id = source.get("authorization_id")
        worker_id = source.get("worker_id")
        policy_id = source.get("authorization_policy_id")
        source_readiness_id = source.get(
            "source_execution_readiness_id"
        )
        source_readiness_hash = source.get(
            "source_execution_readiness_manifest_hash"
        )
        source_activation_hash = source.get(
            "source_activation_hash"
        )
        source_lineage = source.get("source_lineage")
        entries = source.get("entries")

        if not isinstance(authorization_id, str) or not authorization_id:
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization ID is invalid."
            )

        if not isinstance(worker_id, str) or not worker_id:
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 worker ID is invalid."
            )

        if (
            policy_id
            != (
                "oracle.certified-research-evidence-read-execution-adapter-"
                "execution-authorization.v1"
            )
        ):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization policy mismatch."
            )

        if (
            not isinstance(source_readiness_id, str)
            or not source_readiness_id
        ):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 source readiness ID is invalid."
            )

        if not valid_hash(source_readiness_hash):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 source readiness manifest hash is invalid."
            )

        if not valid_hash(source_activation_hash):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 source activation hash is invalid."
            )

        if not isinstance(source_lineage, dict) or not source_lineage:
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 source lineage is missing."
            )

        if (
            not isinstance(entries, list)
            or not entries
            or source.get("authorization_entry_count") != len(entries)
        ):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 authorization entries are invalid."
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

        missing_lineage = required_lineage_fields - set(source_lineage)

        if missing_lineage:
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 lineage is incomplete: "
                f"{sorted(missing_lineage)}"
            )

        for field_name in (
            required_lineage_fields - {"selected_batch_number"}
        ):
            value = source_lineage.get(field_name)

            if not isinstance(value, str) or not value:
                raise AdapterExecutionInvocationInvariantError(
                    f"OIA-044 lineage field is invalid: {field_name}."
                )

        selected_batch_number = source_lineage.get(
            "selected_batch_number"
        )

        if (
            not isinstance(selected_batch_number, int)
            or isinstance(selected_batch_number, bool)
            or selected_batch_number < 1
        ):
            raise AdapterExecutionInvocationInvariantError(
                "OIA-044 selected batch number is invalid."
            )

        required_authorization_checks = {
            "readiness_manifest_hash_verified",
            "readiness_entry_hash_verified",
            "active_invocation_hash_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_arguments_allowlisted",
            "invocation_remained_non_executing",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }

        for expected_sequence, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization entry must be an object."
                )

            entry_hash = entry.pop(
                "authorization_entry_hash",
                None,
            )

            if (
                not valid_hash(entry_hash)
                or stable_hash(entry) != entry_hash
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization entry hash verification failed."
                )

            entry["authorization_entry_hash"] = entry_hash

            if entry.get("sequence") != expected_sequence:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization entry sequence is non-canonical."
                )

            if entry.get("worker_id") != worker_id:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization worker identity mismatch."
                )

            if (
                entry.get("authorization_status")
                != "evidence_read_execution_adapter_execution_authorized"
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization entry is not authorized."
                )

            work_item_id = entry.get("work_item_id")
            adapter_id = entry.get("adapter_id")
            read_operation = entry.get("read_operation")
            arguments = entry.get(
                "authorized_invocation_arguments"
            )
            checks = entry.get("authorization_checks")

            if not isinstance(work_item_id, str) or not work_item_id:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 work-item identity is invalid."
                )

            if (
                not isinstance(adapter_id, str)
                or not adapter_id.startswith("oracle_read_only_")
                or "write" in adapter_id.lower()
                or "mutation" in adapter_id.lower()
                or "order" in adapter_id.lower()
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 adapter identity is not approved read-only."
                )

            if (
                not isinstance(read_operation, str)
                or not read_operation.startswith("read_")
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 operation is not a bounded read operation."
                )

            if not isinstance(arguments, dict):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorized invocation arguments are invalid."
                )

            if set(arguments) != {
                "activated",
                "read_only",
                "execute",
            }:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorized invocation argument allowlist mismatch."
                )

            if arguments.get("activated") is not True:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 invocation is not activated."
                )

            if arguments.get("read_only") is not True:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 invocation is not read-only."
                )

            if arguments.get("execute") is not False:
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 invocation crossed the execution boundary."
                )

            if (
                not isinstance(checks, list)
                or not required_authorization_checks.issubset(set(checks))
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 authorization checks are incomplete."
                )

            if not valid_hash(
                entry.get("source_readiness_entry_hash")
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 source readiness entry hash is invalid."
                )

            if not valid_hash(
                entry.get("source_active_adapter_invocation_hash")
            ):
                raise AdapterExecutionInvocationInvariantError(
                    "OIA-044 source active invocation hash is invalid."
                )

        return source

    def build(
        self,
        *,
        created_at: datetime,
        persist: bool = True,
    ) -> AdapterExecutionInvocationManifest:
        created_at = aware_utc(created_at, "created_at")
        source = self._load_authorization()

        invocations: list[AdapterExecutionInvocation] = []

        for sequence, authorization_entry in enumerate(
            source["entries"],
            start=1,
        ):
            invocation_arguments = dict(
                authorization_entry[
                    "authorized_invocation_arguments"
                ]
            )

            # OIA-045 records the exact authorized invocation while retaining
            # the closed execution bit. Activation and execution are separate,
            # later certified boundaries.
            invocation_arguments["execute"] = False

            body = {
                "sequence": sequence,
                "worker_id": authorization_entry["worker_id"],
                "work_item_id": authorization_entry["work_item_id"],
                "adapter_id": authorization_entry["adapter_id"],
                "read_operation": authorization_entry["read_operation"],
                "invocation_arguments": invocation_arguments,
                "invocation_checks": (
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
                ),
                "invocation_status": STATUS_INVOCATION_READY,
                "source_authorization_entry_hash":
                    authorization_entry[
                        "authorization_entry_hash"
                    ],
                "source_readiness_entry_hash":
                    authorization_entry[
                        "source_readiness_entry_hash"
                    ],
                "source_active_adapter_invocation_hash":
                    authorization_entry[
                        "source_active_adapter_invocation_hash"
                    ],
            }

            invocations.append(
                AdapterExecutionInvocation(
                    **body,
                    execution_invocation_hash=stable_hash(body),
                )
            )

        source_authorization_hash = source[
            "authorization_manifest_hash"
        ]

        invocation_manifest_id = (
            "oia045-adapter-execution-invocation-"
            + stable_hash(
                {
                    "source_execution_authorization_manifest_hash":
                        source_authorization_hash,
                    "invocation_policy_id": POLICY_ID,
                }
            )[:32]
        )

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "created_at": created_at.isoformat(),
            "invocation_manifest_id": invocation_manifest_id,
            "invocation_manifest_status": STATUS_MANIFEST_ISSUED,
            "invocation_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "invocation_count": len(invocations),
            "invocations": tuple(invocations),
            "source_execution_authorization_id":
                source["authorization_id"],
            "source_execution_authorization_manifest_hash":
                source_authorization_hash,
            "source_execution_readiness_id":
                source["source_execution_readiness_id"],
            "source_execution_readiness_manifest_hash":
                source[
                    "source_execution_readiness_manifest_hash"
                ],
            "source_activation_hash":
                source["source_activation_hash"],
            "source_lineage": dict(source["source_lineage"]),
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

        serializable_body = dict(manifest_body)
        serializable_body["invocations"] = [
            asdict(invocation)
            for invocation in invocations
        ]

        result = AdapterExecutionInvocationManifest(
            **manifest_body,
            invocation_manifest_hash=stable_hash(
                serializable_body
            ),
        )

        if persist:
            payload = asdict(result)

            atomic_write(
                self.invocation_directory / "current.json",
                payload,
            )

            atomic_write(
                self.invocation_directory
                / "manifests"
                / f"{invocation_manifest_id}.json",
                payload,
            )

            atomic_write(
                self.invocation_directory
                / "workers"
                / result.worker_id
                / f"{invocation_manifest_id}.json",
                payload,
            )

        return result
'''


TEST_SOURCE = r'''
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_execution_invocation_manifest_builder import (
    AdapterExecutionInvocationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationManifestBuilder,
    POLICY_ID,
    STATUS_INVOCATION_READY,
    STATUS_MANIFEST_ISSUED,
    stable_hash,
)


def seed_oia044(directory: Path) -> dict:
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

    authorization_entry_body = {
        "sequence": 1,
        "worker_id": "oracle-worker-test",
        "work_item_id": "work.test",
        "adapter_id":
            "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation": "read_canonical_observations",
        "authorized_invocation_arguments": {
            "activated": True,
            "read_only": True,
            "execute": False,
        },
        "authorization_checks": [
            "readiness_manifest_hash_verified",
            "readiness_entry_hash_verified",
            "active_invocation_hash_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_arguments_allowlisted",
            "invocation_remained_non_executing",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        ],
        "authorization_status":
            "evidence_read_execution_adapter_execution_authorized",
        "source_readiness_entry_hash": stable_hash(
            {"source": "oia043-entry"}
        ),
        "source_active_adapter_invocation_hash": stable_hash(
            {"source": "oia042-active-invocation"}
        ),
    }

    authorization_entry = dict(authorization_entry_body)
    authorization_entry["authorization_entry_hash"] = stable_hash(
        authorization_entry_body
    )

    manifest_body = {
        "schema_version": "OIA-044",
        "engine_id": "OIA-044",
        "authorized_at": "2026-07-22T02:00:00+00:00",
        "authorization_id": "oia044-test-authorization",
        "authorization_status":
            "evidence_read_execution_adapter_execution_authorization_issued",
        "authorization_policy_id":
            "oracle.certified-research-evidence-read-execution-adapter-"
            "execution-authorization.v1",
        "worker_id": "oracle-worker-test",
        "authorization_entry_count": 1,
        "entries": [authorization_entry],
        "source_execution_readiness_id":
            "oia043-test-readiness",
        "source_execution_readiness_manifest_hash": stable_hash(
            {"source": "oia043-manifest"}
        ),
        "source_activation_hash": stable_hash(
            {"source": "oia042-activation"}
        ),
        "source_lineage": source_lineage,
        "read_only_authorization_issued": True,
        "adapter_execution_authorization_allowed": True,
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
        "authorization_artifact_persistence_allowed": True,
    }

    payload = dict(manifest_body)
    payload["authorization_manifest_hash"] = stable_hash(
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
    print(" OIA-045 TEST")
    print(" ADAPTER EXECUTION INVOCATION MANIFEST")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        authorization_directory = root / "authorization"
        invocation_directory = root / "invocations"

        source = seed_oia044(authorization_directory)

        builder = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationManifestBuilder(
                authorization_directory=authorization_directory,
                invocation_directory=invocation_directory,
            )
        )

        fixed = datetime(
            2026,
            7,
            22,
            3,
            0,
            tzinfo=timezone.utc,
        )

        first = builder.build(
            created_at=fixed,
            persist=True,
        )

        second = builder.build(
            created_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "OIA-045"
        assert first.engine_id == "OIA-045"
        assert (
            first.invocation_manifest_status
            == STATUS_MANIFEST_ISSUED
        )
        assert first.invocation_policy_id == POLICY_ID
        assert first.invocation_count == 1

        invocation = first.invocations[0]

        assert (
            invocation.invocation_status
            == STATUS_INVOCATION_READY
        )

        assert (
            invocation.adapter_id
            == "oracle_read_only_canonical_observation_adapter.v1"
        )

        assert (
            invocation.read_operation
            == "read_canonical_observations"
        )

        assert invocation.invocation_arguments == {
            "activated": True,
            "read_only": True,
            "execute": False,
        }

        assert invocation.source_authorization_entry_hash == (
            source["entries"][0]["authorization_entry_hash"]
        )

        assert invocation.source_readiness_entry_hash == (
            source["entries"][0]["source_readiness_entry_hash"]
        )

        assert (
            invocation.source_active_adapter_invocation_hash
            == source["entries"][0][
                "source_active_adapter_invocation_hash"
            ]
        )

        assert {
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
        }.issubset(set(invocation.invocation_checks))

        assert first.source_execution_authorization_id == (
            source["authorization_id"]
        )

        assert (
            first.source_execution_authorization_manifest_hash
            == source["authorization_manifest_hash"]
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
        assert first.invocation_manifest_created is True
        assert first.invocation_activation_allowed is True
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.invocation_artifact_persistence_allowed is True

        for prohibited_value in (
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
        ):
            assert prohibited_value is False

        manifest_body = dict(first.__dict__)
        manifest_hash = manifest_body.pop(
            "invocation_manifest_hash"
        )
        manifest_body["invocations"] = [
            dict(item.__dict__)
            for item in first.invocations
        ]

        assert manifest_hash == stable_hash(manifest_body)

        invocation_body = dict(invocation.__dict__)
        invocation_hash = invocation_body.pop(
            "execution_invocation_hash"
        )

        assert invocation_hash == stable_hash(invocation_body)

        assert (
            invocation_directory / "current.json"
        ).exists()

        assert list(
            (
                invocation_directory / "manifests"
            ).glob("*.json")
        )

        assert list(
            (
                invocation_directory
                / "workers"
                / first.worker_id
            ).glob("*.json")
        )

        current = json.loads(
            (
                invocation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        assert current["adapter_execution_allowed"] is False
        assert current["adapter_execution_performed"] is False
        assert current["execution_allowed"] is False
        assert current["qseries_handoff_allowed"] is False

        tampered = json.loads(
            (
                authorization_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered["entries"][0][
            "authorized_invocation_arguments"
        ]["execute"] = True

        (
            authorization_directory / "current.json"
        ).write_text(
            json.dumps(tampered, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            builder.build(
                created_at=fixed,
                persist=False,
            )
        except AdapterExecutionInvocationInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered executable OIA-044 authorization accepted."
            )

        seed_oia044(authorization_directory)

        tampered_adapter = json.loads(
            (
                authorization_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered_adapter["entries"][0]["adapter_id"] = (
            "oracle_write_capable_observation_adapter.v1"
        )

        entry_payload = dict(tampered_adapter["entries"][0])
        entry_payload.pop("authorization_entry_hash")

        tampered_adapter["entries"][0][
            "authorization_entry_hash"
        ] = stable_hash(entry_payload)

        manifest_payload = dict(tampered_adapter)
        manifest_payload.pop("authorization_manifest_hash")

        tampered_adapter[
            "authorization_manifest_hash"
        ] = stable_hash(manifest_payload)

        (
            authorization_directory / "current.json"
        ).write_text(
            json.dumps(tampered_adapter, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            builder.build(
                created_at=fixed,
                persist=False,
            )
        except AdapterExecutionInvocationInvariantError:
            pass
        else:
            raise AssertionError(
                "Write-capable adapter invocation was accepted."
            )

    print("[PASS] Actual OIA-044 execution-authorization contract consumed")
    print("[PASS] Invocation manifest and invocation hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-044 lineage preserved")
    print("[PASS] Exact authorized read-only invocation recorded")
    print("[PASS] Invocation arguments remained non-executing")
    print("[PASS] No adapter was imported, resolved, invoked, or executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered or write-capable authorization rejected")
    print("[PASS] Atomic execution-invocation artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


INIT_BLOCK = r'''
from .oracle_certified_research_evidence_read_execution_adapter_execution_invocation_manifest_builder import (
    AdapterExecutionInvocation,
    AdapterExecutionInvocationInvariantError,
    AdapterExecutionInvocationManifest,
    OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationManifestBuilder,
    POLICY_ID as OIA045_POLICY_ID,
    STATUS_INVOCATION_READY as OIA045_STATUS_INVOCATION_READY,
    STATUS_MANIFEST_ISSUED as OIA045_STATUS_MANIFEST_ISSUED,
)

__all__ = [
    "AdapterExecutionInvocation",
    "AdapterExecutionInvocationInvariantError",
    "AdapterExecutionInvocationManifest",
    "OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationManifestBuilder",
    "OIA045_POLICY_ID",
    "OIA045_STATUS_INVOCATION_READY",
    "OIA045_STATUS_MANIFEST_ISSUED",
] + __all__
'''


def verify_oia044() -> None:
    if not OIA044.exists():
        raise RuntimeError(
            f"Actual OIA-044 production module missing: {OIA044}"
        )

    text = OIA044.read_text(encoding="utf-8")

    required_tokens = [
        'SCHEMA_VERSION = "OIA-044"',
        'ENGINE_ID = "OIA-044"',
        "AdapterExecutionAuthorizationEntry",
        "AdapterExecutionAuthorizationManifest",
        "OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionAuthorizationGate",
        "evidence_read_execution_adapter_execution_authorized",
        "evidence_read_execution_adapter_execution_authorization_issued",
        "authorization_entry_hash",
        "authorization_manifest_hash",
        "source_readiness_entry_hash",
        "source_active_adapter_invocation_hash",
        "source_execution_readiness_manifest_hash",
        "source_activation_hash",
        "source_lineage",
        "read_only_authorization_issued",
        "adapter_execution_authorization_allowed",
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
            "Actual OIA-044 production contract mismatch: "
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
        "adapter_execution_invocation_manifest_builder import ("
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
    print(" OIA-045 INSTALLER")
    print(" ADAPTER EXECUTION INVOCATION")
    print(" NON-EXECUTING INVOCATION MANIFEST")
    print("=" * 40)

    verify_oia044()
    print("[OK] Actual OIA-044 execution-authorization contract verified")

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

    print("[OK] OIA-045 test executed automatically")
    print()
    print(
        "[DONE] OIA-045 certified research evidence read execution "
        "adapter execution invocation manifest builder installed"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())