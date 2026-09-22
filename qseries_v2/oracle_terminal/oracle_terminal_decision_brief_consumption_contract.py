from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_operator_decision_brief_assembly import (
    OracleOperatorDecisionBrief,
    OracleOperatorDecisionBriefInvariantError,
    OracleOperatorDecisionBriefItem,
    build_operator_decision_brief,
    verify_operator_decision_brief,
)

SCHEMA_VERSION = "OIT-023"
ENGINE_ID = "OIT-023"
POLICY_ID = "oracle.terminal-decision-brief-consumption-contract.v1"


class OracleTerminalBriefConsumptionInvariantError(
    OracleOperatorDecisionBriefInvariantError
):
    pass


@dataclass(frozen=True)
class OracleTerminalBriefSection:
    section_index: int
    section_type: str
    title: str
    content_lines: tuple[str, ...]
    source_item_hashes: tuple[str, ...]
    attention_required: bool
    display_priority: int
    section_hash: str


@dataclass(frozen=True)
class OracleTerminalBriefConsumptionContract:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    operator_brief_hash: str
    terminal_title: str
    terminal_summary: str
    sections: tuple[OracleTerminalBriefSection, ...]
    section_count: int
    attention_section_count: int
    source_item_count: int
    primary_state: str
    primary_direction: str
    consumption_ready: bool
    rendering_allowed: bool
    interactive_query_allowed: bool
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    action_authorization_allowed: bool
    failure_reason: str | None
    contract_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _section(
    index: int,
    section_type: str,
    title: str,
    lines: tuple[str, ...],
    hashes: tuple[str, ...],
    attention: bool,
    priority: int,
) -> OracleTerminalBriefSection:
    body = {
        "section_index": index,
        "section_type": section_type,
        "title": title,
        "content_lines": lines,
        "source_item_hashes": hashes,
        "attention_required": attention,
        "display_priority": priority,
    }
    return OracleTerminalBriefSection(
        **body,
        section_hash=_stable_hash(body),
    )


def _item_lines(item: OracleOperatorDecisionBriefItem) -> tuple[str, ...]:
    return (
        item.headline,
        item.explanation,
        *(f"EVIDENCE: {line}" for line in item.evidence_points),
        *(f"CONFIRM: {line}" for line in item.confirmation_actions),
        *(f"BLOCKER: {line}" for line in item.blocking_conditions),
    )


def verify_terminal_brief_section(
    section: OracleTerminalBriefSection,
) -> bool:
    body = asdict(section)
    supplied = body.pop("section_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalBriefConsumptionInvariantError(
            "terminal section hash mismatch"
        )
    if section.section_type not in {
        "executive_summary",
        "attention",
        "decision_item",
        "next_steps",
        "blockers",
    }:
        raise OracleTerminalBriefConsumptionInvariantError(
            "unsupported terminal section type"
        )
    if not section.title or not section.content_lines:
        raise OracleTerminalBriefConsumptionInvariantError(
            "terminal section content missing"
        )
    if section.display_priority < 1:
        raise OracleTerminalBriefConsumptionInvariantError(
            "terminal section priority invalid"
        )
    return True


def build_terminal_brief_consumption_contract(
    repository_root: str | Path,
    query: str,
    *,
    operator_brief: OracleOperatorDecisionBrief | None = None,
) -> OracleTerminalBriefConsumptionContract:
    root = Path(repository_root).resolve()
    source = operator_brief
    if source is None:
        source = build_operator_decision_brief(root, query)
    verify_operator_decision_brief(source)

    sections: list[OracleTerminalBriefSection] = []
    sections.append(
        _section(
            1,
            "executive_summary",
            source.brief_title,
            (source.executive_summary,),
            tuple(item.item_hash for item in source.brief_items),
            source.operator_attention_count > 0,
            1,
        )
    )

    next_index = 2
    for item in source.brief_items:
        section_type = (
            "attention"
            if item.operator_attention_required
            else "decision_item"
        )
        sections.append(
            _section(
                next_index,
                section_type,
                item.headline,
                _item_lines(item),
                (item.item_hash,),
                item.operator_attention_required,
                2 if item.operator_attention_required else 3,
            )
        )
        next_index += 1

    if source.operator_next_steps:
        sections.append(
            _section(
                next_index,
                "next_steps",
                "Operator Next Steps",
                tuple(source.operator_next_steps),
                tuple(item.item_hash for item in source.brief_items),
                False,
                4,
            )
        )
        next_index += 1

    if source.unresolved_blockers:
        sections.append(
            _section(
                next_index,
                "blockers",
                "Unresolved Blockers",
                tuple(source.unresolved_blockers),
                tuple(item.item_hash for item in source.brief_items),
                True,
                2,
            )
        )

    ordered = tuple(
        sorted(
            sections,
            key=lambda section: (
                section.display_priority,
                section.section_index,
                section.section_hash,
            ),
        )
    )
    for section in ordered:
        verify_terminal_brief_section(section)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "operator_brief_hash": source.brief_hash,
        "terminal_title": source.brief_title,
        "terminal_summary": source.executive_summary,
        "sections": ordered,
        "section_count": len(ordered),
        "attention_section_count": sum(
            section.attention_required for section in ordered
        ),
        "source_item_count": source.item_count,
        "primary_state": source.primary_state,
        "primary_direction": source.primary_direction,
        "consumption_ready": bool(
            ordered
            and (
                source.terminal_consumption_ready
                or (
                    source.item_count == 0
                    and source.primary_state == "abstain"
                    and source.primary_direction == "neutral"
                    and ordered[0].section_type == "executive_summary"
                    and bool(source.executive_summary)
                )
            )
        ),
        "rendering_allowed": True,
        "interactive_query_allowed": True,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    contract = OracleTerminalBriefConsumptionContract(
        **body,
        contract_hash=_stable_hash(body),
    )
    verify_terminal_brief_consumption_contract(contract)
    return contract


def verify_terminal_brief_consumption_contract(
    contract: OracleTerminalBriefConsumptionContract,
) -> bool:
    body = asdict(contract)
    supplied = body.pop("contract_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalBriefConsumptionInvariantError(
            "terminal consumption contract hash mismatch"
        )
    if contract.schema_version != SCHEMA_VERSION:
        raise OracleTerminalBriefConsumptionInvariantError(
            "schema mismatch"
        )
    if contract.policy_id != POLICY_ID:
        raise OracleTerminalBriefConsumptionInvariantError(
            "policy mismatch"
        )
    if not contract.read_only:
        raise OracleTerminalBriefConsumptionInvariantError(
            "terminal consumption contract is not read-only"
        )
    if (
        contract.analytics_execution_performed
        or contract.database_access_performed
        or contract.publication_allowed
        or contract.qseries_execution_allowed
        or contract.action_authorization_allowed
    ):
        raise OracleTerminalBriefConsumptionInvariantError(
            "forbidden capability enabled"
        )
    if not contract.rendering_allowed:
        raise OracleTerminalBriefConsumptionInvariantError(
            "terminal rendering must remain available"
        )
    if not contract.interactive_query_allowed:
        raise OracleTerminalBriefConsumptionInvariantError(
            "interactive read-only query must remain available"
        )
    if contract.section_count != len(contract.sections):
        raise OracleTerminalBriefConsumptionInvariantError(
            "terminal section count mismatch"
        )
    if contract.attention_section_count != sum(
        section.attention_required for section in contract.sections
    ):
        raise OracleTerminalBriefConsumptionInvariantError(
            "attention section count mismatch"
        )
    if contract.primary_state not in {"ready", "observe", "abstain"}:
        raise OracleTerminalBriefConsumptionInvariantError(
            "invalid primary state"
        )
    if contract.primary_direction not in {"bull", "bear", "neutral"}:
        raise OracleTerminalBriefConsumptionInvariantError(
            "invalid primary direction"
        )
    for section in contract.sections:
        verify_terminal_brief_section(section)
    expected = tuple(
        sorted(
            contract.sections,
            key=lambda section: (
                section.display_priority,
                section.section_index,
                section.section_hash,
            ),
        )
    )
    if contract.sections != expected:
        raise OracleTerminalBriefConsumptionInvariantError(
            "terminal section ordering mismatch"
        )
    if contract.consumption_ready and not contract.sections:
        raise OracleTerminalBriefConsumptionInvariantError(
            "empty contract marked consumption-ready"
        )

    bounded_zero_item_abstention = bool(
        contract.source_item_count == 0
        and contract.primary_state == "abstain"
        and contract.primary_direction == "neutral"
        and contract.sections
        and contract.sections[0].section_type == "executive_summary"
        and bool(contract.terminal_summary)
    )

    if (
        contract.consumption_ready
        and contract.source_item_count == 0
        and not bounded_zero_item_abstention
    ):
        raise OracleTerminalBriefConsumptionInvariantError(
            "unsupported zero-item contract marked consumption-ready"
        )

    if bounded_zero_item_abstention and not contract.consumption_ready:
        raise OracleTerminalBriefConsumptionInvariantError(
            "bounded abstention contract must remain displayable"
        )
    return True
