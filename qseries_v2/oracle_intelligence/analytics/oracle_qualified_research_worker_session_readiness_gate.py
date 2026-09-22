from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .oracle_qualified_research_priority_ranking_engine import RANKING_POLICY_ID
from .oracle_qualified_research_priority_tier_assignment_gate import TIER_POLICY_ID
from .oracle_qualified_research_queue_admission_gate import QUEUE_POLICY_ID
from .oracle_qualified_research_work_item_materialization_engine import WORK_ITEM_POLICY_ID
from .oracle_qualified_research_dispatch_manifest_builder import DISPATCH_POLICY_ID
from .oracle_qualified_research_dispatch_claim_gate import CLAIM_POLICY_ID
from .oracle_qualified_research_claim_activation_gate import ACTIVATION_POLICY_ID
from .oracle_qualified_research_worker_session_manifest_builder import (
    SESSION_POLICY_ID,
    SESSION_READY,
    SESSION_ENTRY_READY,
    DEFAULT_SESSION_DIRECTORY,
    stable_hash as session_stable_hash,
)

SCHEMA_VERSION = "OIA-024"
ENGINE_ID = "OIA-024"
READINESS_POLICY_ID = "oracle.qualified-research-worker-session-readiness.v1"

READINESS_VERIFIED = "readiness_verified"
ENTRY_READINESS_VERIFIED = "entry_readiness_verified"

READ_ONLY_CORPUS = True
RESEARCH_EXECUTION_ALLOWED = False
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
MARKET_ORDER_CREATION_ALLOWED = False
FUNDS_MOVEMENT_ALLOWED = False
PORTFOLIO_MUTATION_ALLOWED = False
READINESS_ARTIFACT_PERSISTENCE_ALLOWED = True

DEFAULT_READINESS_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "qualified_research_worker_session_readiness"
)


class QualifiedResearchWorkerSessionReadinessError(RuntimeError):
    pass


class QualifiedResearchWorkerSessionReadinessInvariantError(
    QualifiedResearchWorkerSessionReadinessError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise QualifiedResearchWorkerSessionReadinessInvariantError(
            f"{field_name} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        return _aware_utc(value, "datetime").isoformat()
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


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _valid_hash(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


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


def _readiness_id(source_session_hash: str, worker_id: str) -> str:
    digest = stable_hash(
        {
            "source_session_hash": source_session_hash,
            "worker_id": worker_id,
            "readiness_policy_id": READINESS_POLICY_ID,
        }
    )
    return f"oia024-readiness-{digest[:32]}"


@dataclass(frozen=True)
class OracleQualifiedResearchWorkerSessionReadinessEntry:
    readiness_sequence: int
    session_sequence: int
    activation_sequence: int
    claim_sequence: int
    dispatch_sequence: int
    batch_number: int
    batch_position: int
    work_item_id: str
    queue_position: int
    source_rank: int
    dimension: str
    key: str
    tier: str
    priority_score: str
    research_objective: str
    required_operations: tuple[str, ...]
    prohibited_operations: tuple[str, ...]
    completion_requirements: tuple[str, ...]
    readiness_status: str
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    dispatch_policy_id: str
    claim_policy_id: str
    activation_policy_id: str
    session_policy_id: str
    readiness_policy_id: str
    source_eligibility_decision_hash: str
    source_ranking_record_hash: str
    source_tier_record_hash: str
    source_queue_record_hash: str
    source_work_item_hash: str
    source_dispatch_entry_hash: str
    source_claim_entry_hash: str
    source_activation_entry_hash: str
    source_session_entry_hash: str
    readiness_entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleQualifiedResearchWorkerSessionReadinessAttestation:
    schema_version: str
    engine_id: str
    generated_at: datetime
    readiness_id: str
    readiness_status: str
    worker_id: str
    session_directory: str
    readiness_directory: str
    source_session_id: str
    source_activation_id: str
    source_claim_id: str
    manifest_id: str
    selected_batch_id: str
    selected_batch_number: int
    readiness_entry_count: int
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    dispatch_policy_id: str
    claim_policy_id: str
    activation_policy_id: str
    session_policy_id: str
    readiness_policy_id: str
    entries: tuple[OracleQualifiedResearchWorkerSessionReadinessEntry, ...]
    source_session_hash: str
    source_activation_hash: str
    source_claim_hash: str
    source_manifest_hash: str
    source_batch_hash: str
    read_only_corpus: bool
    research_execution_allowed: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    market_order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    readiness_artifact_persistence_allowed: bool
    readiness_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleQualifiedResearchWorkerSessionReadinessGate:
    def __init__(
        self,
        *,
        session_directory: Path | str = DEFAULT_SESSION_DIRECTORY,
        readiness_directory: Path | str = DEFAULT_READINESS_DIRECTORY,
    ) -> None:
        self._session_directory = Path(session_directory)
        self._readiness_directory = Path(readiness_directory)

    def _load_session(self) -> dict[str, Any]:
        path = self._session_directory / "current.json"
        if not path.exists():
            raise QualifiedResearchWorkerSessionReadinessInvariantError(
                f"OIA-023 current session is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise QualifiedResearchWorkerSessionReadinessInvariantError(
                f"OIA-023 current session is invalid JSON: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise QualifiedResearchWorkerSessionReadinessInvariantError(
                "OIA-023 session must be a JSON object."
            )

        session_hash = payload.pop("session_hash", None)
        expected = {
            "schema_version": "OIA-023",
            "engine_id": "OIA-023",
            "session_status": SESSION_READY,
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "work_item_policy_id": WORK_ITEM_POLICY_ID,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
            "claim_policy_id": CLAIM_POLICY_ID,
            "activation_policy_id": ACTIVATION_POLICY_ID,
            "session_policy_id": SESSION_POLICY_ID,
        }
        for field_name, expected_value in expected.items():
            if payload.get(field_name) != expected_value:
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    f"OIA-023 identity mismatch: {field_name}."
                )

        if session_hash != session_stable_hash(payload):
            raise QualifiedResearchWorkerSessionReadinessInvariantError(
                "OIA-023 session hash verification failed."
            )
        if not _valid_hash(session_hash):
            raise QualifiedResearchWorkerSessionReadinessInvariantError(
                "OIA-023 session hash is malformed."
            )

        if payload.get("read_only_corpus") is not True:
            raise QualifiedResearchWorkerSessionReadinessInvariantError(
                "OIA-023 read-only corpus invariant failed."
            )

        for field_name in (
            "research_execution_allowed",
            "execution_allowed",
            "alerts_allowed",
            "qseries_handoff_allowed",
            "signals_allowed",
            "trading_recommendations_allowed",
            "source_mutation_allowed",
            "market_order_creation_allowed",
            "funds_movement_allowed",
            "portfolio_mutation_allowed",
        ):
            if payload.get(field_name) is not False:
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    f"OIA-023 safety boundary mismatch: {field_name}."
                )

        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            raise QualifiedResearchWorkerSessionReadinessInvariantError(
                "OIA-023 session entries must be a non-empty list."
            )
        if int(payload.get("session_entry_count", -1)) != len(entries):
            raise QualifiedResearchWorkerSessionReadinessInvariantError(
                "OIA-023 session entry count mismatch."
            )

        verified: list[dict[str, Any]] = []
        seen_work_items: set[str] = set()
        seen_hashes: set[str] = set()
        previous_dispatch: int | None = None

        for index, raw in enumerate(entries, start=1):
            if not isinstance(raw, dict):
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    f"OIA-023 session entry {index} must be an object."
                )
            entry = dict(raw)
            entry_hash = entry.pop("session_entry_hash", None)
            if entry_hash != session_stable_hash(entry):
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    f"OIA-023 session-entry hash failed at index {index}."
                )
            if not _valid_hash(entry_hash):
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    "OIA-023 session-entry hash is malformed."
                )
            if int(entry.get("session_sequence", -1)) != index:
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    "OIA-023 session sequences must be contiguous."
                )
            if entry.get("session_entry_status") != SESSION_ENTRY_READY:
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    "OIA-023 session entry is not ready."
                )

            dispatch_sequence = int(entry.get("dispatch_sequence", -1))
            if (
                previous_dispatch is not None
                and dispatch_sequence != previous_dispatch + 1
            ):
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    "OIA-023 dispatch sequence is not contiguous."
                )
            previous_dispatch = dispatch_sequence

            work_item_id = str(entry.get("work_item_id", ""))
            if not work_item_id.startswith("oia019-"):
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    "OIA-023 work-item ID is malformed."
                )
            if work_item_id in seen_work_items or entry_hash in seen_hashes:
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    "Duplicate OIA-023 session lineage."
                )

            for field_name, expected_value in (
                ("ranking_policy_id", RANKING_POLICY_ID),
                ("tier_policy_id", TIER_POLICY_ID),
                ("queue_policy_id", QUEUE_POLICY_ID),
                ("work_item_policy_id", WORK_ITEM_POLICY_ID),
                ("dispatch_policy_id", DISPATCH_POLICY_ID),
                ("claim_policy_id", CLAIM_POLICY_ID),
                ("activation_policy_id", ACTIVATION_POLICY_ID),
                ("session_policy_id", SESSION_POLICY_ID),
            ):
                if entry.get(field_name) != expected_value:
                    raise QualifiedResearchWorkerSessionReadinessInvariantError(
                        f"OIA-023 entry policy mismatch: {field_name}."
                    )

            for field_name in (
                "source_eligibility_decision_hash",
                "source_ranking_record_hash",
                "source_tier_record_hash",
                "source_queue_record_hash",
                "source_work_item_hash",
                "source_dispatch_entry_hash",
                "source_claim_entry_hash",
                "source_activation_entry_hash",
            ):
                if not _valid_hash(entry.get(field_name)):
                    raise QualifiedResearchWorkerSessionReadinessInvariantError(
                        f"OIA-023 {field_name} is malformed."
                    )

            for field_name in (
                "required_operations",
                "prohibited_operations",
                "completion_requirements",
            ):
                value = entry.get(field_name)
                if not isinstance(value, list) or not value:
                    raise QualifiedResearchWorkerSessionReadinessInvariantError(
                        f"OIA-023 {field_name} must be a non-empty list."
                    )

            required_prohibitions = {
                "create_trading_signal",
                "create_trading_recommendation",
                "publish_operator_alert",
                "handoff_to_qseries_execution",
                "create_market_order",
                "move_funds",
                "mutate_portfolio",
                "mutate_source_corpus",
            }
            if not required_prohibitions.issubset(
                set(entry["prohibited_operations"])
            ):
                raise QualifiedResearchWorkerSessionReadinessInvariantError(
                    "OIA-023 prohibited-operation boundary is incomplete."
                )

            entry["session_entry_hash"] = entry_hash
            verified.append(entry)
            seen_work_items.add(work_item_id)
            seen_hashes.add(entry_hash)

        payload["entries"] = verified
        payload["session_hash"] = session_hash
        return payload

    def attest(
        self,
        *,
        generated_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleQualifiedResearchWorkerSessionReadinessAttestation:
        generated_at = _aware_utc(
            generated_at or datetime.now(timezone.utc),
            "generated_at",
        )
        session = self._load_session()
        source_session_hash = str(session["session_hash"])
        worker_id = str(session["worker_id"])
        readiness_id = _readiness_id(source_session_hash, worker_id)

        entries: list[OracleQualifiedResearchWorkerSessionReadinessEntry] = []
        for sequence, source in enumerate(session["entries"], start=1):
            body = {
                "readiness_sequence": sequence,
                "session_sequence": int(source["session_sequence"]),
                "activation_sequence": int(source["activation_sequence"]),
                "claim_sequence": int(source["claim_sequence"]),
                "dispatch_sequence": int(source["dispatch_sequence"]),
                "batch_number": int(source["batch_number"]),
                "batch_position": int(source["batch_position"]),
                "work_item_id": str(source["work_item_id"]),
                "queue_position": int(source["queue_position"]),
                "source_rank": int(source["source_rank"]),
                "dimension": str(source["dimension"]),
                "key": str(source["key"]),
                "tier": str(source["tier"]),
                "priority_score": str(source["priority_score"]),
                "research_objective": str(source["research_objective"]),
                "required_operations": tuple(source["required_operations"]),
                "prohibited_operations": tuple(source["prohibited_operations"]),
                "completion_requirements": tuple(
                    source["completion_requirements"]
                ),
                "readiness_status": ENTRY_READINESS_VERIFIED,
                "ranking_policy_id": RANKING_POLICY_ID,
                "tier_policy_id": TIER_POLICY_ID,
                "queue_policy_id": QUEUE_POLICY_ID,
                "work_item_policy_id": WORK_ITEM_POLICY_ID,
                "dispatch_policy_id": DISPATCH_POLICY_ID,
                "claim_policy_id": CLAIM_POLICY_ID,
                "activation_policy_id": ACTIVATION_POLICY_ID,
                "session_policy_id": SESSION_POLICY_ID,
                "readiness_policy_id": READINESS_POLICY_ID,
                "source_eligibility_decision_hash": str(
                    source["source_eligibility_decision_hash"]
                ),
                "source_ranking_record_hash": str(
                    source["source_ranking_record_hash"]
                ),
                "source_tier_record_hash": str(
                    source["source_tier_record_hash"]
                ),
                "source_queue_record_hash": str(
                    source["source_queue_record_hash"]
                ),
                "source_work_item_hash": str(
                    source["source_work_item_hash"]
                ),
                "source_dispatch_entry_hash": str(
                    source["source_dispatch_entry_hash"]
                ),
                "source_claim_entry_hash": str(
                    source["source_claim_entry_hash"]
                ),
                "source_activation_entry_hash": str(
                    source["source_activation_entry_hash"]
                ),
                "source_session_entry_hash": str(
                    source["session_entry_hash"]
                ),
            }
            entries.append(
                OracleQualifiedResearchWorkerSessionReadinessEntry(
                    **body,
                    readiness_entry_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "readiness_id": readiness_id,
            "readiness_status": READINESS_VERIFIED,
            "worker_id": worker_id,
            "session_directory": str(self._session_directory),
            "readiness_directory": str(self._readiness_directory),
            "source_session_id": str(session["session_id"]),
            "source_activation_id": str(session["source_activation_id"]),
            "source_claim_id": str(session["source_claim_id"]),
            "manifest_id": str(session["manifest_id"]),
            "selected_batch_id": str(session["selected_batch_id"]),
            "selected_batch_number": int(session["selected_batch_number"]),
            "readiness_entry_count": len(entries),
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "work_item_policy_id": WORK_ITEM_POLICY_ID,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
            "claim_policy_id": CLAIM_POLICY_ID,
            "activation_policy_id": ACTIVATION_POLICY_ID,
            "session_policy_id": SESSION_POLICY_ID,
            "readiness_policy_id": READINESS_POLICY_ID,
            "entries": tuple(entries),
            "source_session_hash": source_session_hash,
            "source_activation_hash": str(session["source_activation_hash"]),
            "source_claim_hash": str(session["source_claim_hash"]),
            "source_manifest_hash": str(session["source_manifest_hash"]),
            "source_batch_hash": str(session["source_batch_hash"]),
            "read_only_corpus": READ_ONLY_CORPUS,
            "research_execution_allowed": RESEARCH_EXECUTION_ALLOWED,
            "execution_allowed": EXECUTION_ALLOWED,
            "alerts_allowed": ALERTS_ALLOWED,
            "qseries_handoff_allowed": QSERIES_HANDOFF_ALLOWED,
            "signals_allowed": SIGNALS_ALLOWED,
            "trading_recommendations_allowed": TRADING_RECOMMENDATIONS_ALLOWED,
            "source_mutation_allowed": SOURCE_MUTATION_ALLOWED,
            "market_order_creation_allowed": MARKET_ORDER_CREATION_ALLOWED,
            "funds_movement_allowed": FUNDS_MOVEMENT_ALLOWED,
            "portfolio_mutation_allowed": PORTFOLIO_MUTATION_ALLOWED,
            "readiness_artifact_persistence_allowed": (
                READINESS_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }
        readiness = OracleQualifiedResearchWorkerSessionReadinessAttestation(
            **body,
            readiness_hash=stable_hash(body),
        )

        if persist:
            payload = dict(readiness.to_dict())
            _atomic_write(self._readiness_directory / "current.json", payload)
            _atomic_write(
                self._readiness_directory
                / "attestations"
                / f"{readiness.readiness_id}-{readiness.readiness_hash}.json",
                payload,
            )
            _atomic_write(
                self._readiness_directory
                / "workers"
                / worker_id
                / f"{readiness.readiness_id}.json",
                payload,
            )
        return readiness


def format_readiness(
    readiness: OracleQualifiedResearchWorkerSessionReadinessAttestation,
) -> str:
    lines = [
        "=" * 154,
        "ORACLE QUALIFIED RESEARCH WORKER SESSION READINESS",
        "=" * 154,
        f"Generated at:     {readiness.generated_at.isoformat()}",
        f"Readiness ID:     {readiness.readiness_id}",
        f"Readiness status: {readiness.readiness_status}",
        f"Worker ID:        {readiness.worker_id}",
        f"Source session:   {readiness.source_session_id}",
        f"Verified entries: {readiness.readiness_entry_count}",
        "-" * 154,
    ]
    for entry in readiness.entries:
        lines.append(
            f"{entry.readiness_sequence:>4} | "
            f"session={entry.session_sequence:>4} | "
            f"dispatch={entry.dispatch_sequence:>4} | "
            f"tier={entry.tier:<10} | "
            f"{entry.dimension}:{entry.key} | "
            f"{entry.readiness_status}"
        )
    lines.extend(
        [
            "-" * 154,
            f"Readiness hash: {readiness.readiness_hash}",
            (
                "READINESS ATTESTATION ONLY — NO RESEARCH EXECUTION, "
                "SIGNALS, ALERTS, RECOMMENDATIONS, QSERIES HANDOFFS, "
                "ORDERS, FUNDS MOVEMENT, PORTFOLIO MUTATION, "
                "OR SOURCE MUTATION"
            ),
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="OIA-024 qualified research worker session readiness gate"
    )
    parser.add_argument(
        "--session-directory",
        default=str(DEFAULT_SESSION_DIRECTORY),
    )
    parser.add_argument(
        "--readiness-directory",
        default=str(DEFAULT_READINESS_DIRECTORY),
    )
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args(argv)
    readiness = OracleQualifiedResearchWorkerSessionReadinessGate(
        session_directory=args.session_directory,
        readiness_directory=args.readiness_directory,
    ).attest(persist=not args.no_persist)
    print(format_readiness(readiness))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
