from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_terminal_decision_brief_consumption_contract import (
    OracleTerminalBriefConsumptionContract,
    OracleTerminalBriefConsumptionInvariantError,
    OracleTerminalBriefSection,
    build_terminal_brief_consumption_contract,
    verify_terminal_brief_consumption_contract,
)

SCHEMA_VERSION = "OIT-024"
ENGINE_ID = "OIT-024"
POLICY_ID = "oracle.terminal-decision-brief-presentation-view-model.v1"


class OracleTerminalPresentationInvariantError(
    OracleTerminalBriefConsumptionInvariantError
):
    pass


@dataclass(frozen=True)
class OracleTerminalPresentationPanel:
    panel_index: int
    panel_type: str
    panel_label: str
    severity: str
    content_lines: tuple[str, ...]
    source_section_hash: str
    operator_attention_required: bool
    display_order: int
    read_only: bool
    panel_hash: str


@dataclass(frozen=True)
class OracleTerminalPresentationViewModel:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    consumption_contract_hash: str
    terminal_heading: str
    terminal_subheading: str
    status_label: str
    direction_label: str
    panels: tuple[OracleTerminalPresentationPanel, ...]
    panel_count: int
    critical_panel_count: int
    warning_panel_count: int
    informational_panel_count: int
    operator_attention_count: int
    rendering_ready: bool
    keyboard_navigation_ready: bool
    expandable_evidence_ready: bool
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    action_authorization_allowed: bool
    failure_reason: str | None
    view_model_hash: str


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


def _severity(section: OracleTerminalBriefSection) -> str:
    if section.attention_required or section.section_type == "blockers":
        return "critical"
    if section.section_type in {"next_steps", "decision_item"}:
        return "warning"
    return "informational"


def _label(section: OracleTerminalBriefSection) -> str:
    mapping = {
        "executive_summary": "Executive Summary",
        "attention": "Operator Attention",
        "decision_item": "Decision Item",
        "next_steps": "Next Steps",
        "blockers": "Unresolved Blockers",
    }
    return mapping[section.section_type]


def _panel(
    section: OracleTerminalBriefSection,
    index: int,
) -> OracleTerminalPresentationPanel:
    severity = _severity(section)
    priority_map = {
        "critical": 1,
        "warning": 2,
        "informational": 3,
    }
    body = {
        "panel_index": index,
        "panel_type": section.section_type,
        "panel_label": _label(section),
        "severity": severity,
        "content_lines": tuple(section.content_lines),
        "source_section_hash": section.section_hash,
        "operator_attention_required": section.attention_required,
        "display_order": priority_map[severity],
        "read_only": True,
    }
    return OracleTerminalPresentationPanel(
        **body,
        panel_hash=_stable_hash(body),
    )


def verify_terminal_presentation_panel(
    panel: OracleTerminalPresentationPanel,
) -> bool:
    body = asdict(panel)
    supplied = body.pop("panel_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalPresentationInvariantError(
            "terminal presentation panel hash mismatch"
        )
    if panel.severity not in {
        "critical",
        "warning",
        "informational",
    }:
        raise OracleTerminalPresentationInvariantError(
            "unsupported panel severity"
        )
    if not panel.panel_label or not panel.content_lines:
        raise OracleTerminalPresentationInvariantError(
            "panel presentation content missing"
        )
    if not panel.source_section_hash:
        raise OracleTerminalPresentationInvariantError(
            "panel source-section lineage missing"
        )
    if not panel.read_only:
        raise OracleTerminalPresentationInvariantError(
            "terminal presentation panel is not read-only"
        )
    if panel.display_order < 1:
        raise OracleTerminalPresentationInvariantError(
            "panel display order invalid"
        )
    return True


def build_terminal_presentation_view_model(
    repository_root: str | Path,
    query: str,
    *,
    consumption_contract: OracleTerminalBriefConsumptionContract | None = None,
) -> OracleTerminalPresentationViewModel:
    root = Path(repository_root).resolve()
    source = consumption_contract
    if source is None:
        source = build_terminal_brief_consumption_contract(root, query)
    verify_terminal_brief_consumption_contract(source)

    generated = tuple(
        _panel(section, index)
        for index, section in enumerate(source.sections, start=1)
    )
    panels = tuple(
        sorted(
            generated,
            key=lambda panel: (
                panel.display_order,
                panel.panel_index,
                panel.panel_hash,
            ),
        )
    )
    for panel in panels:
        verify_terminal_presentation_panel(panel)

    critical = sum(panel.severity == "critical" for panel in panels)
    warning = sum(panel.severity == "warning" for panel in panels)
    informational = sum(
        panel.severity == "informational" for panel in panels
    )
    attention = sum(
        panel.operator_attention_required for panel in panels
    )
    rendering_ready = bool(
        source.consumption_ready
        and panels
        and all(panel.source_section_hash for panel in panels)
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "consumption_contract_hash": source.contract_hash,
        "terminal_heading": source.terminal_title,
        "terminal_subheading": source.terminal_summary,
        "status_label": source.primary_state.upper(),
        "direction_label": source.primary_direction.upper(),
        "panels": panels,
        "panel_count": len(panels),
        "critical_panel_count": critical,
        "warning_panel_count": warning,
        "informational_panel_count": informational,
        "operator_attention_count": attention,
        "rendering_ready": rendering_ready,
        "keyboard_navigation_ready": rendering_ready,
        "expandable_evidence_ready": rendering_ready,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    view_model = OracleTerminalPresentationViewModel(
        **body,
        view_model_hash=_stable_hash(body),
    )
    verify_terminal_presentation_view_model(view_model)
    return view_model


def verify_terminal_presentation_view_model(
    view_model: OracleTerminalPresentationViewModel,
) -> bool:
    body = asdict(view_model)
    supplied = body.pop("view_model_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalPresentationInvariantError(
            "terminal presentation view-model hash mismatch"
        )
    if view_model.schema_version != SCHEMA_VERSION:
        raise OracleTerminalPresentationInvariantError("schema mismatch")
    if view_model.policy_id != POLICY_ID:
        raise OracleTerminalPresentationInvariantError("policy mismatch")
    if not view_model.read_only:
        raise OracleTerminalPresentationInvariantError(
            "terminal presentation view-model is not read-only"
        )
    if (
        view_model.analytics_execution_performed
        or view_model.database_access_performed
        or view_model.publication_allowed
        or view_model.qseries_execution_allowed
        or view_model.action_authorization_allowed
    ):
        raise OracleTerminalPresentationInvariantError(
            "forbidden capability enabled"
        )
    if view_model.panel_count != len(view_model.panels):
        raise OracleTerminalPresentationInvariantError(
            "terminal presentation panel count mismatch"
        )
    counts = {
        "critical": view_model.critical_panel_count,
        "warning": view_model.warning_panel_count,
        "informational": view_model.informational_panel_count,
    }
    for severity, expected in counts.items():
        actual = sum(
            panel.severity == severity for panel in view_model.panels
        )
        if actual != expected:
            raise OracleTerminalPresentationInvariantError(
                f"{severity} panel count mismatch"
            )
    if sum(counts.values()) != view_model.panel_count:
        raise OracleTerminalPresentationInvariantError(
            "classified panel count mismatch"
        )
    if view_model.operator_attention_count != sum(
        panel.operator_attention_required for panel in view_model.panels
    ):
        raise OracleTerminalPresentationInvariantError(
            "operator attention panel count mismatch"
        )
    for panel in view_model.panels:
        verify_terminal_presentation_panel(panel)
    expected = tuple(
        sorted(
            view_model.panels,
            key=lambda panel: (
                panel.display_order,
                panel.panel_index,
                panel.panel_hash,
            ),
        )
    )
    if view_model.panels != expected:
        raise OracleTerminalPresentationInvariantError(
            "terminal presentation panel ordering mismatch"
        )
    if (
        view_model.rendering_ready
        and (
            not view_model.keyboard_navigation_ready
            or not view_model.expandable_evidence_ready
        )
    ):
        raise OracleTerminalPresentationInvariantError(
            "rendering-ready view model missing interaction readiness"
        )
    return True
