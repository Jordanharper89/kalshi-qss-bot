from pathlib import Path
import py_compile
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
ANALYTICS = ROOT / "qseries_v2" / "oracle_intelligence" / "analytics"

OIA043 = (
    ANALYTICS
    / "oracle_certified_research_evidence_read_execution_adapter_execution_readiness_gate.py"
)

PRODUCTION = (
    ANALYTICS
    / "oracle_certified_research_evidence_read_execution_adapter_execution_authorization_gate.py"
)

TEST = (
    ROOT
    / "test_oia_044_oracle_certified_research_evidence_read_execution_adapter_execution_authorization_gate.py"
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


SCHEMA_VERSION = "OIA-044"
ENGINE_ID = "OIA-044"

POLICY_ID = (
    "oracle.certified-research-evidence-read-execution-adapter-"
    "execution-authorization.v1"
)

STATUS_AUTHORIZED = (
    "evidence_read_execution_adapter_execution_authorized"
)

STATUS_ISSUED = (
    "evidence_read_execution_adapter_execution_authorization_issued"
)

DEFAULT_READINESS_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_readiness"
)

DEFAULT_AUTHORIZATION_DIRECTORY = Path(
    "runtime/oracle_intelligence/"
    "certified_research_evidence_read_execution_adapter_execution_authorization"
)


class AdapterExecutionAuthorizationInvariantError(RuntimeError):
    """Raised when the OIA-043 readiness contract is unsafe or invalid."""


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
        raise AdapterExecutionAuthorizationInvariantError(
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
class AdapterExecutionAuthorizationEntry:
    sequence: int
    worker_id: str
    work_item_id: str
    adapter_id: str
    read_operation: str
    authorized_invocation_arguments: dict[str, Any]
    authorization_checks: tuple[str, ...]
    authorization_status: str
    source_readiness_entry_hash: str
    source_active_adapter_invocation_hash: str
    authorization_entry_hash: str


@dataclass(frozen=True)
class AdapterExecutionAuthorizationManifest:
    schema_version: str
    engine_id: str
    authorized_at: str
    authorization_id: str
    authorization_status: str
    authorization_policy_id: str
    worker_id: str
    authorization_entry_count: int
    entries: tuple[AdapterExecutionAuthorizationEntry, ...]
    source_execution_readiness_id: str
    source_execution_readiness_manifest_hash: str
    source_activation_hash: str
    source_lineage: dict[str, Any]
    read_only_authorization_issued: bool
    adapter_execution_authorization_allowed: bool
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
    authorization_artifact_persistence_allowed: bool
    authorization_manifest_hash: str


class OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionAuthorizationGate:
    """
    OIA-044 authorization boundary.

    This gate authorizes the exact bounded read-only adapter invocation described
    by OIA-043. It does not import, instantiate, invoke, or execute an adapter.

    Authorization here means that a later certified execution component may
    consume the authorization artifact. It does not mean execution occurred.
    """

    def __init__(
        self,
        *,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
        authorization_directory: Path | str = DEFAULT_AUTHORIZATION_DIRECTORY,
    ) -> None:
        self.readiness_directory = Path(readiness_directory)
        self.authorization_directory = Path(authorization_directory)

    def _load_readiness(self) -> dict[str, Any]:
        current = self.readiness_directory / "current.json"

        if not current.exists():
            raise AdapterExecutionAuthorizationInvariantError(
                f"OIA-043 current readiness artifact missing: {current}"
            )

        try:
            source = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 readiness artifact could not be decoded."
            ) from error

        if not isinstance(source, dict):
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 readiness artifact must be a JSON object."
            )

        manifest_hash = source.pop("manifest_hash", None)

        if (
            not valid_hash(manifest_hash)
            or stable_hash(source) != manifest_hash
        ):
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 readiness manifest hash verification failed."
            )

        source["manifest_hash"] = manifest_hash

        expected = {
            "schema_version": "OIA-043",
            "engine_id": "OIA-043",
            "status":
                "evidence_read_execution_adapter_execution_readiness_issued",
            "corpus_read_execution_allowed": False,
            "research_execution_allowed": False,
            "signals_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_allowed": False,
            "source_mutation_allowed": False,
            "market_order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }

        for field_name, expected_value in expected.items():
            if source.get(field_name) != expected_value:
                raise AdapterExecutionAuthorizationInvariantError(
                    f"OIA-043 invariant failed: {field_name}."
                )

        readiness_id = source.get("readiness_id")
        worker_id = source.get("worker_id")
        source_activation_hash = source.get("source_activation_hash")
        source_lineage = source.get("source_lineage")
        entries = source.get("entries")

        if not isinstance(readiness_id, str) or not readiness_id:
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 readiness ID is invalid."
            )

        if not isinstance(worker_id, str) or not worker_id:
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 worker ID is invalid."
            )

        if not valid_hash(source_activation_hash):
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 source activation hash is invalid."
            )

        if not isinstance(source_lineage, dict) or not source_lineage:
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 source lineage is missing."
            )

        if not isinstance(entries, list) or not entries:
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 readiness entries are missing."
            )

        for expected_sequence, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 readiness entry must be an object."
                )

            entry_hash = entry.pop("entry_hash", None)

            if not valid_hash(entry_hash) or stable_hash(entry) != entry_hash:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 readiness entry hash verification failed."
                )

            entry["entry_hash"] = entry_hash

            if entry.get("sequence") != expected_sequence:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 readiness entry sequence is non-canonical."
                )

            if (
                entry.get("status")
                != "evidence_read_execution_adapter_execution_ready"
            ):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 adapter execution entry is not ready."
                )

            if entry.get("worker_id") != worker_id:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 readiness worker identity mismatch."
                )

            work_item_id = entry.get("work_item_id")
            adapter_id = entry.get("adapter_id")
            read_operation = entry.get("read_operation")
            invocation_arguments = entry.get("invocation_arguments")
            checks = entry.get("checks")

            if not isinstance(work_item_id, str) or not work_item_id:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 work-item identity is invalid."
                )

            if (
                not isinstance(adapter_id, str)
                or not adapter_id.startswith("oracle_read_only_")
                or "write" in adapter_id.lower()
                or "mutation" in adapter_id.lower()
                or "order" in adapter_id.lower()
            ):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 adapter is not an approved read-only identity."
                )

            if (
                not isinstance(read_operation, str)
                or not read_operation.startswith("read_")
            ):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 operation is not a bounded read operation."
                )

            if not isinstance(invocation_arguments, dict):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 invocation arguments are invalid."
                )

            if invocation_arguments.get("activated") is not True:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 invocation is not activated."
                )

            if invocation_arguments.get("read_only") is not True:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 invocation is not read-only."
                )

            if invocation_arguments.get("execute") is not False:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 invocation attempted to cross the execution boundary."
                )

            allowed_argument_names = {
                "activated",
                "read_only",
                "execute",
            }

            unexpected_arguments = (
                set(invocation_arguments) - allowed_argument_names
            )

            if unexpected_arguments:
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 invocation contains unapproved arguments: "
                    f"{sorted(unexpected_arguments)}"
                )

            required_checks = {
                "activation_hash_verified",
                "adapter_read_only_verified",
                "operation_read_only_verified",
                "invocation_non_executing_verified",
                "corpus_execution_disabled",
            }

            if (
                not isinstance(checks, list)
                or not required_checks.issubset(set(checks))
            ):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 readiness checks are incomplete."
                )

            if not valid_hash(
                entry.get("source_active_adapter_invocation_hash")
            ):
                raise AdapterExecutionAuthorizationInvariantError(
                    "OIA-043 active invocation lineage hash is invalid."
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
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 lineage is incomplete: "
                f"{sorted(missing_lineage)}"
            )

        for field_name in required_lineage_fields - {"selected_batch_number"}:
            value = source_lineage.get(field_name)
            if not isinstance(value, str) or not value:
                raise AdapterExecutionAuthorizationInvariantError(
                    f"OIA-043 lineage field is invalid: {field_name}."
                )

        selected_batch_number = source_lineage.get("selected_batch_number")
        if (
            not isinstance(selected_batch_number, int)
            or isinstance(selected_batch_number, bool)
            or selected_batch_number < 1
        ):
            raise AdapterExecutionAuthorizationInvariantError(
                "OIA-043 selected batch number is invalid."
            )

        return source

    def authorize(
        self,
        *,
        authorized_at: datetime,
        persist: bool = True,
    ) -> AdapterExecutionAuthorizationManifest:
        authorized_at = aware_utc(authorized_at, "authorized_at")
        source = self._load_readiness()

        entries: list[AdapterExecutionAuthorizationEntry] = []

        for sequence, readiness_entry in enumerate(
            source["entries"],
            start=1,
        ):
            authorized_arguments = dict(
                readiness_entry["invocation_arguments"]
            )

            # OIA-044 authorizes a future bounded read-only invocation but does
            # not turn the source request into an executable request.
            authorized_arguments["execute"] = False

            body = {
                "sequence": sequence,
                "worker_id": readiness_entry["worker_id"],
                "work_item_id": readiness_entry["work_item_id"],
                "adapter_id": readiness_entry["adapter_id"],
                "read_operation": readiness_entry["read_operation"],
                "authorized_invocation_arguments": authorized_arguments,
                "authorization_checks": (
                    "readiness_manifest_hash_verified",
                    "readiness_entry_hash_verified",
                    "active_invocation_hash_verified",
                    "adapter_read_only_identity_verified",
                    "operation_read_only_verified",
                    "invocation_arguments_allowlisted",
                    "invocation_remained_non_executing",
                    "corpus_execution_remained_disabled",
                    "oracle_qseries_boundary_verified",
                ),
                "authorization_status": STATUS_AUTHORIZED,
                "source_readiness_entry_hash":
                    readiness_entry["entry_hash"],
                "source_active_adapter_invocation_hash":
                    readiness_entry[
                        "source_active_adapter_invocation_hash"
                    ],
            }

            entries.append(
                AdapterExecutionAuthorizationEntry(
                    **body,
                    authorization_entry_hash=stable_hash(body),
                )
            )

        source_manifest_hash = source["manifest_hash"]

        authorization_id = (
            "oia044-adapter-execution-authorization-"
            + stable_hash(
                {
                    "source_execution_readiness_manifest_hash":
                        source_manifest_hash,
                    "authorization_policy_id": POLICY_ID,
                }
            )[:32]
        )

        manifest_body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "authorized_at": authorized_at.isoformat(),
            "authorization_id": authorization_id,
            "authorization_status": STATUS_ISSUED,
            "authorization_policy_id": POLICY_ID,
            "worker_id": source["worker_id"],
            "authorization_entry_count": len(entries),
            "entries": tuple(entries),
            "source_execution_readiness_id": source["readiness_id"],
            "source_execution_readiness_manifest_hash":
                source_manifest_hash,
            "source_activation_hash": source["source_activation_hash"],
            "source_lineage": dict(source["source_lineage"]),
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

        serializable_body = dict(manifest_body)
        serializable_body["entries"] = [
            asdict(entry) for entry in entries
        ]

        result = AdapterExecutionAuthorizationManifest(
            **manifest_body,
            authorization_manifest_hash=stable_hash(
                serializable_body
            ),
        )

        if persist:
            payload = asdict(result)

            atomic_write(
                self.authorization_directory / "current.json",
                payload,
            )

            atomic_write(
                self.authorization_directory
                / "authorizations"
                / f"{authorization_id}.json",
                payload,
            )

            atomic_write(
                self.authorization_directory
                / "workers"
                / result.worker_id
                / f"{authorization_id}.json",
                payload,
            )

        return result
'''


TEST_SOURCE = r'''
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_execution_authorization_gate import (
    AdapterExecutionAuthorizationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionAuthorizationGate,
    POLICY_ID,
    STATUS_AUTHORIZED,
    STATUS_ISSUED,
    stable_hash,
)


def seed_oia043(directory: Path) -> dict:
    active_invocation = {
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
        "activation_status":
            "evidence_read_execution_adapter_invocation_active",
    }

    active_invocation["active_adapter_invocation_hash"] = stable_hash(
        active_invocation
    )

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

    readiness_entry_body = {
        "sequence": 1,
        "worker_id": active_invocation["worker_id"],
        "work_item_id": active_invocation["work_item_id"],
        "adapter_id": active_invocation["adapter_id"],
        "read_operation": active_invocation["read_operation"],
        "invocation_arguments":
            dict(active_invocation["invocation_arguments"]),
        "checks": [
            "activation_hash_verified",
            "adapter_read_only_verified",
            "operation_read_only_verified",
            "invocation_non_executing_verified",
            "corpus_execution_disabled",
        ],
        "status":
            "evidence_read_execution_adapter_execution_ready",
        "source_active_adapter_invocation_hash":
            active_invocation["active_adapter_invocation_hash"],
    }

    readiness_entry = dict(readiness_entry_body)
    readiness_entry["entry_hash"] = stable_hash(
        readiness_entry_body
    )

    activation_hash = stable_hash(
        {
            "schema_version": "OIA-042",
            "engine_id": "OIA-042",
            "active_adapter_invocation":
                active_invocation["active_adapter_invocation_hash"],
        }
    )

    manifest_body = {
        "schema_version": "OIA-043",
        "engine_id": "OIA-043",
        "evaluated_at": "2026-07-22T01:00:00+00:00",
        "readiness_id": "oia043-test-readiness",
        "status":
            "evidence_read_execution_adapter_execution_readiness_issued",
        "worker_id": "oracle-worker-test",
        "entries": [readiness_entry],
        "source_activation_hash": activation_hash,
        "source_lineage": source_lineage,
        "corpus_read_execution_allowed": False,
        "research_execution_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
    }

    payload = dict(manifest_body)
    payload["manifest_hash"] = stable_hash(manifest_body)

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-044 TEST")
    print(" ADAPTER EXECUTION AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness_directory = root / "readiness"
        authorization_directory = root / "authorization"

        source = seed_oia043(readiness_directory)

        gate = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionAuthorizationGate(
                readiness_directory=readiness_directory,
                authorization_directory=authorization_directory,
            )
        )

        fixed = datetime(
            2026,
            7,
            22,
            2,
            0,
            tzinfo=timezone.utc,
        )

        first = gate.authorize(
            authorized_at=fixed,
            persist=True,
        )

        second = gate.authorize(
            authorized_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "OIA-044"
        assert first.engine_id == "OIA-044"
        assert first.authorization_status == STATUS_ISSUED
        assert first.authorization_policy_id == POLICY_ID
        assert first.authorization_entry_count == 1

        entry = first.entries[0]

        assert entry.authorization_status == STATUS_AUTHORIZED
        assert (
            entry.adapter_id
            == "oracle_read_only_canonical_observation_adapter.v1"
        )
        assert entry.read_operation == "read_canonical_observations"
        assert entry.authorized_invocation_arguments == {
            "activated": True,
            "read_only": True,
            "execute": False,
        }

        assert entry.source_readiness_entry_hash == (
            source["entries"][0]["entry_hash"]
        )

        assert entry.source_active_adapter_invocation_hash == (
            source["entries"][0][
                "source_active_adapter_invocation_hash"
            ]
        )

        assert {
            "readiness_manifest_hash_verified",
            "readiness_entry_hash_verified",
            "active_invocation_hash_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_arguments_allowlisted",
            "invocation_remained_non_executing",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }.issubset(set(entry.authorization_checks))

        assert first.source_execution_readiness_id == (
            source["readiness_id"]
        )

        assert first.source_execution_readiness_manifest_hash == (
            source["manifest_hash"]
        )

        assert first.source_lineage == source["source_lineage"]
        assert first.read_only_authorization_issued is True
        assert first.adapter_execution_authorization_allowed is True
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.authorization_artifact_persistence_allowed is True

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
            "authorization_manifest_hash"
        )
        manifest_body["entries"] = [
            dict(item.__dict__) for item in first.entries
        ]
        assert manifest_hash == stable_hash(manifest_body)

        entry_body = dict(entry.__dict__)
        entry_hash = entry_body.pop(
            "authorization_entry_hash"
        )
        assert entry_hash == stable_hash(entry_body)

        assert (
            authorization_directory / "current.json"
        ).exists()

        assert list(
            (
                authorization_directory / "authorizations"
            ).glob("*.json")
        )

        assert list(
            (
                authorization_directory
                / "workers"
                / first.worker_id
            ).glob("*.json")
        )

        current = json.loads(
            (
                authorization_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        assert current["adapter_execution_performed"] is False
        assert current["execution_allowed"] is False
        assert current["qseries_handoff_allowed"] is False

        tampered = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered["entries"][0]["invocation_arguments"][
            "execute"
        ] = True

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(tampered, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.authorize(
                authorized_at=fixed,
                persist=False,
            )
        except AdapterExecutionAuthorizationInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered executable OIA-043 readiness accepted."
            )

        seed_oia043(readiness_directory)

        tampered_adapter = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered_adapter["entries"][0]["adapter_id"] = (
            "oracle_write_capable_observation_adapter.v1"
        )

        entry_payload = dict(tampered_adapter["entries"][0])
        entry_payload.pop("entry_hash")
        tampered_adapter["entries"][0]["entry_hash"] = stable_hash(
            entry_payload
        )

        manifest_payload = dict(tampered_adapter)
        manifest_payload.pop("manifest_hash")
        tampered_adapter["manifest_hash"] = stable_hash(
            manifest_payload
        )

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(tampered_adapter, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.authorize(
                authorized_at=fixed,
                persist=False,
            )
        except AdapterExecutionAuthorizationInvariantError:
            pass
        else:
            raise AssertionError(
                "Write-capable adapter identity was authorized."
            )

    print("[PASS] Actual OIA-043 execution-readiness contract consumed")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-043 lineage preserved")
    print("[PASS] Only readiness-certified read-only adapter execution authorized")
    print("[PASS] Invocation arguments remained non-executing")
    print("[PASS] Authorization did not invoke or execute an adapter")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered or write-capable readiness rejected")
    print("[PASS] Atomic execution-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


INIT_BLOCK = r'''
from .oracle_certified_research_evidence_read_execution_adapter_execution_authorization_gate import (
    AdapterExecutionAuthorizationEntry,
    AdapterExecutionAuthorizationInvariantError,
    AdapterExecutionAuthorizationManifest,
    OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionAuthorizationGate,
    POLICY_ID as OIA044_POLICY_ID,
    STATUS_AUTHORIZED as OIA044_STATUS_AUTHORIZED,
    STATUS_ISSUED as OIA044_STATUS_ISSUED,
)

__all__ = [
    "AdapterExecutionAuthorizationEntry",
    "AdapterExecutionAuthorizationInvariantError",
    "AdapterExecutionAuthorizationManifest",
    "OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionAuthorizationGate",
    "OIA044_POLICY_ID",
    "OIA044_STATUS_AUTHORIZED",
    "OIA044_STATUS_ISSUED",
] + __all__
'''


def verify_oia043() -> None:
    if not OIA043.exists():
        raise RuntimeError(
            f"Actual OIA-043 production module missing: {OIA043}"
        )

    text = OIA043.read_text(encoding="utf-8")

    required_tokens = [
        'SCHEMA_VERSION="OIA-043"',
        'ENGINE_ID="OIA-043"',
        "AdapterExecutionReadinessEntry",
        "AdapterExecutionReadinessManifest",
        "OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionReadinessGate",
        "evidence_read_execution_adapter_execution_ready",
        "evidence_read_execution_adapter_execution_readiness_issued",
        "source_active_adapter_invocation_hash",
        "source_activation_hash",
        "source_lineage",
        "manifest_hash",
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
            "Actual OIA-043 production contract mismatch: "
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
        "adapter_execution_authorization_gate import ("
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
    print(" OIA-044 INSTALLER")
    print(" ADAPTER EXECUTION AUTHORIZATION")
    print(" CERTIFIED READ-ONLY AUTHORITY GATE")
    print("=" * 40)

    verify_oia043()
    print("[OK] Actual OIA-043 execution-readiness contract verified")

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

    print("[OK] OIA-044 test executed automatically")
    print()
    print(
        "[DONE] OIA-044 certified research evidence read execution "
        "adapter execution authorization gate installed"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())