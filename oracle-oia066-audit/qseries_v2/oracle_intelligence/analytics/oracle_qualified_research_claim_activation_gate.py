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
from .oracle_qualified_research_dispatch_claim_gate import (
    CLAIM_POLICY_ID,
    CLAIM_READY,
    CLAIMED,
    DEFAULT_CLAIM_DIRECTORY,
    stable_hash as claim_stable_hash,
)

SCHEMA_VERSION = "OIA-022"
ENGINE_ID = "OIA-022"
ACTIVATION_POLICY_ID = "oracle.qualified-research-claim-activation.v1"
ACTIVATION_READY = "activation_ready"
ENTRY_ACTIVATED = "entry_activated"

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
ACTIVATION_ARTIFACT_PERSISTENCE_ALLOWED = True

DEFAULT_ACTIVATION_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "qualified_research_claim_activations"
)


class QualifiedResearchClaimActivationError(RuntimeError):
    pass


class QualifiedResearchClaimActivationInvariantError(
    QualifiedResearchClaimActivationError
):
    pass


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise QualifiedResearchClaimActivationInvariantError(
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


def _activation_id(
    source_claim_hash: str,
    worker_id: str,
    selected_batch_id: str,
) -> str:
    digest = stable_hash(
        {
            "source_claim_hash": source_claim_hash,
            "worker_id": worker_id,
            "selected_batch_id": selected_batch_id,
            "activation_policy_id": ACTIVATION_POLICY_ID,
        }
    )
    return f"oia022-activation-{digest[:32]}"


@dataclass(frozen=True)
class OracleQualifiedResearchClaimActivationEntry:
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
    activation_status: str
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    dispatch_policy_id: str
    claim_policy_id: str
    activation_policy_id: str
    source_eligibility_decision_hash: str
    source_ranking_record_hash: str
    source_tier_record_hash: str
    source_queue_record_hash: str
    source_work_item_hash: str
    source_dispatch_entry_hash: str
    source_claim_entry_hash: str
    activation_entry_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleQualifiedResearchClaimActivation:
    schema_version: str
    engine_id: str
    generated_at: datetime
    activation_id: str
    activation_status: str
    worker_id: str
    claim_directory: str
    activation_directory: str
    source_claim_id: str
    manifest_id: str
    selected_batch_id: str
    selected_batch_number: int
    activated_entry_count: int
    ranking_policy_id: str
    tier_policy_id: str
    queue_policy_id: str
    work_item_policy_id: str
    dispatch_policy_id: str
    claim_policy_id: str
    activation_policy_id: str
    entries: tuple[OracleQualifiedResearchClaimActivationEntry, ...]
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
    activation_artifact_persistence_allowed: bool
    activation_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleQualifiedResearchClaimActivationGate:
    def __init__(
        self,
        *,
        claim_directory: Path | str = DEFAULT_CLAIM_DIRECTORY,
        activation_directory: Path | str = DEFAULT_ACTIVATION_DIRECTORY,
    ) -> None:
        self._claim_directory = Path(claim_directory)
        self._activation_directory = Path(activation_directory)

    def _load_claim(self) -> dict[str, Any]:
        path = self._claim_directory / "current.json"
        if not path.exists():
            raise QualifiedResearchClaimActivationInvariantError(
                f"OIA-021 current claim is missing: {path}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise QualifiedResearchClaimActivationInvariantError(
                f"OIA-021 current claim is invalid JSON: {path}"
            ) from exc
        if not isinstance(payload, dict):
            raise QualifiedResearchClaimActivationInvariantError(
                "OIA-021 current claim must be a JSON object."
            )

        claim_hash = payload.pop("claim_hash", None)
        expected = {
            "schema_version": "OIA-021",
            "engine_id": "OIA-021",
            "claim_status": CLAIM_READY,
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "work_item_policy_id": WORK_ITEM_POLICY_ID,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
            "claim_policy_id": CLAIM_POLICY_ID,
        }
        for field_name, expected_value in expected.items():
            if payload.get(field_name) != expected_value:
                raise QualifiedResearchClaimActivationInvariantError(
                    f"OIA-021 identity mismatch: {field_name}."
                )

        if claim_hash != claim_stable_hash(payload):
            raise QualifiedResearchClaimActivationInvariantError(
                "OIA-021 claim hash verification failed."
            )
        if not _valid_hash(claim_hash):
            raise QualifiedResearchClaimActivationInvariantError(
                "OIA-021 claim hash is malformed."
            )

        if payload.get("read_only_corpus") is not True:
            raise QualifiedResearchClaimActivationInvariantError(
                "OIA-021 read-only corpus invariant failed."
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
                raise QualifiedResearchClaimActivationInvariantError(
                    f"OIA-021 safety boundary mismatch: {field_name}."
                )

        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            raise QualifiedResearchClaimActivationInvariantError(
                "OIA-021 claim entries must be a non-empty list."
            )
        if int(payload.get("selected_batch_entry_count", -1)) != len(entries):
            raise QualifiedResearchClaimActivationInvariantError(
                "OIA-021 selected batch entry count mismatch."
            )

        verified: list[dict[str, Any]] = []
        previous_dispatch: int | None = None
        seen_work_items: set[str] = set()
        seen_hashes: set[str] = set()

        for index, raw in enumerate(entries, start=1):
            if not isinstance(raw, dict):
                raise QualifiedResearchClaimActivationInvariantError(
                    f"OIA-021 claim entry {index} must be an object."
                )
            entry = dict(raw)
            entry_hash = entry.pop("claim_entry_hash", None)
            if entry_hash != claim_stable_hash(entry):
                raise QualifiedResearchClaimActivationInvariantError(
                    f"OIA-021 claim-entry hash failed at index {index}."
                )
            if not _valid_hash(entry_hash):
                raise QualifiedResearchClaimActivationInvariantError(
                    "OIA-021 claim-entry hash is malformed."
                )
            if int(entry.get("claim_sequence", -1)) != index:
                raise QualifiedResearchClaimActivationInvariantError(
                    "OIA-021 claim sequences must be contiguous."
                )
            if entry.get("claim_status") != CLAIMED:
                raise QualifiedResearchClaimActivationInvariantError(
                    "OIA-021 claim entry is not claimed."
                )
            if int(entry.get("batch_number", -1)) != int(
                payload["selected_batch_number"]
            ):
                raise QualifiedResearchClaimActivationInvariantError(
                    "OIA-021 claim entry batch mismatch."
                )

            dispatch_sequence = int(entry.get("dispatch_sequence", -1))
            if (
                previous_dispatch is not None
                and dispatch_sequence != previous_dispatch + 1
            ):
                raise QualifiedResearchClaimActivationInvariantError(
                    "OIA-021 dispatch sequence is not contiguous."
                )
            previous_dispatch = dispatch_sequence

            work_item_id = str(entry.get("work_item_id", ""))
            if not work_item_id.startswith("oia019-"):
                raise QualifiedResearchClaimActivationInvariantError(
                    "OIA-021 work-item ID is malformed."
                )
            if work_item_id in seen_work_items or entry_hash in seen_hashes:
                raise QualifiedResearchClaimActivationInvariantError(
                    "Duplicate OIA-021 claim lineage."
                )

            for field_name, expected_value in (
                ("ranking_policy_id", RANKING_POLICY_ID),
                ("tier_policy_id", TIER_POLICY_ID),
                ("queue_policy_id", QUEUE_POLICY_ID),
                ("work_item_policy_id", WORK_ITEM_POLICY_ID),
                ("dispatch_policy_id", DISPATCH_POLICY_ID),
                ("claim_policy_id", CLAIM_POLICY_ID),
            ):
                if entry.get(field_name) != expected_value:
                    raise QualifiedResearchClaimActivationInvariantError(
                        f"OIA-021 entry policy mismatch: {field_name}."
                    )

            for field_name in (
                "source_eligibility_decision_hash",
                "source_ranking_record_hash",
                "source_tier_record_hash",
                "source_queue_record_hash",
                "source_work_item_hash",
                "source_dispatch_entry_hash",
            ):
                if not _valid_hash(entry.get(field_name)):
                    raise QualifiedResearchClaimActivationInvariantError(
                        f"OIA-021 {field_name} is malformed."
                    )

            for field_name in (
                "required_operations",
                "prohibited_operations",
                "completion_requirements",
            ):
                value = entry.get(field_name)
                if not isinstance(value, list) or not value:
                    raise QualifiedResearchClaimActivationInvariantError(
                        f"OIA-021 {field_name} must be a non-empty list."
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
                raise QualifiedResearchClaimActivationInvariantError(
                    "OIA-021 prohibited-operation boundary is incomplete."
                )

            entry["claim_entry_hash"] = entry_hash
            verified.append(entry)
            seen_work_items.add(work_item_id)
            seen_hashes.add(entry_hash)

        payload["entries"] = verified
        payload["claim_hash"] = claim_hash
        return payload

    def activate(
        self,
        *,
        generated_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleQualifiedResearchClaimActivation:
        generated_at = _aware_utc(
            generated_at or datetime.now(timezone.utc),
            "generated_at",
        )
        claim = self._load_claim()
        source_claim_hash = str(claim["claim_hash"])
        worker_id = str(claim["worker_id"])
        selected_batch_id = str(claim["selected_batch_id"])
        activation_id = _activation_id(
            source_claim_hash,
            worker_id,
            selected_batch_id,
        )

        entries: list[OracleQualifiedResearchClaimActivationEntry] = []
        for sequence, source in enumerate(claim["entries"], start=1):
            body = {
                "activation_sequence": sequence,
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
                "activation_status": ENTRY_ACTIVATED,
                "ranking_policy_id": RANKING_POLICY_ID,
                "tier_policy_id": TIER_POLICY_ID,
                "queue_policy_id": QUEUE_POLICY_ID,
                "work_item_policy_id": WORK_ITEM_POLICY_ID,
                "dispatch_policy_id": DISPATCH_POLICY_ID,
                "claim_policy_id": CLAIM_POLICY_ID,
                "activation_policy_id": ACTIVATION_POLICY_ID,
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
                "source_claim_entry_hash": str(source["claim_entry_hash"]),
            }
            entries.append(
                OracleQualifiedResearchClaimActivationEntry(
                    **body,
                    activation_entry_hash=stable_hash(body),
                )
            )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "activation_id": activation_id,
            "activation_status": ACTIVATION_READY,
            "worker_id": worker_id,
            "claim_directory": str(self._claim_directory),
            "activation_directory": str(self._activation_directory),
            "source_claim_id": str(claim["claim_id"]),
            "manifest_id": str(claim["manifest_id"]),
            "selected_batch_id": selected_batch_id,
            "selected_batch_number": int(claim["selected_batch_number"]),
            "activated_entry_count": len(entries),
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "queue_policy_id": QUEUE_POLICY_ID,
            "work_item_policy_id": WORK_ITEM_POLICY_ID,
            "dispatch_policy_id": DISPATCH_POLICY_ID,
            "claim_policy_id": CLAIM_POLICY_ID,
            "activation_policy_id": ACTIVATION_POLICY_ID,
            "entries": tuple(entries),
            "source_claim_hash": source_claim_hash,
            "source_manifest_hash": str(claim["source_manifest_hash"]),
            "source_batch_hash": str(claim["source_batch_hash"]),
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
            "activation_artifact_persistence_allowed": (
                ACTIVATION_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }
        activation = OracleQualifiedResearchClaimActivation(
            **body,
            activation_hash=stable_hash(body),
        )

        if persist:
            payload = dict(activation.to_dict())
            _atomic_write(self._activation_directory / "current.json", payload)
            _atomic_write(
                self._activation_directory
                / "activations"
                / f"{activation.activation_id}-{activation.activation_hash}.json",
                payload,
            )
            _atomic_write(
                self._activation_directory
                / "workers"
                / worker_id
                / f"{activation.activation_id}.json",
                payload,
            )
        return activation


def format_activation(
    activation: OracleQualifiedResearchClaimActivation,
) -> str:
    lines = [
        "=" * 150,
        "ORACLE QUALIFIED RESEARCH CLAIM ACTIVATION",
        "=" * 150,
        f"Generated at:      {activation.generated_at.isoformat()}",
        f"Activation ID:     {activation.activation_id}",
        f"Activation status: {activation.activation_status}",
        f"Worker ID:         {activation.worker_id}",
        f"Source claim:      {activation.source_claim_id}",
        (
            f"Selected batch:    {activation.selected_batch_number} | "
            f"{activation.selected_batch_id}"
        ),
        f"Activated entries: {activation.activated_entry_count}",
        "-" * 150,
    ]
    for entry in activation.entries:
        lines.append(
            f"{entry.activation_sequence:>4} | "
            f"dispatch={entry.dispatch_sequence:>4} | "
            f"queue={entry.queue_position:>4} | "
            f"tier={entry.tier:<10} | "
            f"{entry.dimension}:{entry.key} | "
            f"{entry.activation_status}"
        )
    lines.extend(
        [
            "-" * 150,
            f"Activation hash: {activation.activation_hash}",
            (
                "CLAIM ACTIVATION ONLY — NO RESEARCH EXECUTION, SIGNALS, "
                "ALERTS, RECOMMENDATIONS, QSERIES HANDOFFS, ORDERS, "
                "FUNDS MOVEMENT, PORTFOLIO MUTATION, OR SOURCE MUTATION"
            ),
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="OIA-022 qualified research claim activation gate"
    )
    parser.add_argument(
        "--claim-directory",
        default=str(DEFAULT_CLAIM_DIRECTORY),
    )
    parser.add_argument(
        "--activation-directory",
        default=str(DEFAULT_ACTIVATION_DIRECTORY),
    )
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args(argv)
    activation = OracleQualifiedResearchClaimActivationGate(
        claim_directory=args.claim_directory,
        activation_directory=args.activation_directory,
    ).activate(persist=not args.no_persist)
    print(format_activation(activation))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
