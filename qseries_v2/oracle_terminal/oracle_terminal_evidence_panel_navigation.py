from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "OIT-032"
ENGINE_ID = "OIT-032"
POLICY_ID = "oracle.evidence-panel-navigation.v1"


class OracleTerminalPanelNavigationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleTerminalPanelDefinition:
    panel_name: str
    panel_index: int
    aliases: tuple[str, ...]
    source_frame_types: tuple[str, ...]
    summary: str
    read_only: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    definition_hash: str


@dataclass(frozen=True)
class OracleTerminalPanelRegistry:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    panels: tuple[OracleTerminalPanelDefinition, ...]
    panel_count: int
    aliases_unique: bool
    registry_ready: bool
    read_only: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    registry_hash: str


@dataclass(frozen=True)
class OracleTerminalPanelSelection:
    requested_panel: str
    matched: bool
    panel_name: str | None
    panel_index: int | None
    source_frame_types: tuple[str, ...]
    selection_hash: str


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


def _panel(
    panel_name: str,
    panel_index: int,
    aliases: Sequence[str],
    source_frame_types: Sequence[str],
    summary: str,
) -> OracleTerminalPanelDefinition:
    body = {
        "panel_name": panel_name.strip().lower(),
        "panel_index": int(panel_index),
        "aliases": tuple(sorted({str(item).strip().lower() for item in aliases if str(item).strip()})),
        "source_frame_types": tuple(str(item).strip().lower() for item in source_frame_types if str(item).strip()),
        "summary": summary.strip(),
        "read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }
    definition = OracleTerminalPanelDefinition(
        **body,
        definition_hash=_stable_hash(body),
    )
    verify_panel_definition(definition)
    return definition


def build_default_panel_registry() -> OracleTerminalPanelRegistry:
    panels = (
        _panel("overview", 0, ("summary",), ("banner", "summary", "informational"), "Primary intelligence overview."),
        _panel("evidence", 1, ("sources", "source"), ("evidence", "source", "citation"), "Evidence and source inspection."),
        _panel("debate", 2, ("bull-bear", "bullbear"), ("debate", "bull", "bear", "neutral"), "Bull, bear, and neutral analysis."),
        _panel("timeline", 3, ("history", "temporal"), ("timeline", "temporal", "event"), "Temporal intelligence reconstruction."),
        _panel("cross-market", 4, ("crossmarket", "relationships"), ("cross-market", "relationship", "market-link"), "Cross-market relationship analysis."),
        _panel("uncertainty", 5, ("contradictions", "risk"), ("uncertainty", "contradiction", "risk"), "Uncertainty and contradiction inspection."),
    )

    tokens: list[str] = []
    for panel in panels:
        tokens.append(panel.panel_name)
        tokens.extend(panel.aliases)

    aliases_unique = len(tokens) == len(set(tokens))
    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "panels": panels,
        "panel_count": len(panels),
        "aliases_unique": aliases_unique,
        "registry_ready": bool(panels and aliases_unique),
        "read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }
    registry = OracleTerminalPanelRegistry(
        **body,
        registry_hash=_stable_hash(body),
    )
    verify_panel_registry(registry)
    return registry


def verify_panel_definition(definition: OracleTerminalPanelDefinition) -> bool:
    body = asdict(definition)
    supplied = body.pop("definition_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalPanelNavigationInvariantError("panel definition hash mismatch")
    if not definition.panel_name:
        raise OracleTerminalPanelNavigationInvariantError("panel name missing")
    if definition.panel_index < 0:
        raise OracleTerminalPanelNavigationInvariantError("panel index invalid")
    if not definition.source_frame_types:
        raise OracleTerminalPanelNavigationInvariantError("panel frame types missing")
    if not definition.read_only:
        raise OracleTerminalPanelNavigationInvariantError("panel is not read-only")
    if (
        definition.publication_allowed
        or definition.action_authorization_allowed
        or definition.qseries_execution_allowed
    ):
        raise OracleTerminalPanelNavigationInvariantError("forbidden panel capability enabled")
    return True


def verify_panel_registry(registry: OracleTerminalPanelRegistry) -> bool:
    body = asdict(registry)
    supplied = body.pop("registry_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalPanelNavigationInvariantError("panel registry hash mismatch")
    if registry.schema_version != SCHEMA_VERSION:
        raise OracleTerminalPanelNavigationInvariantError("schema mismatch")
    if registry.policy_id != POLICY_ID:
        raise OracleTerminalPanelNavigationInvariantError("policy mismatch")
    if registry.panel_count != len(registry.panels):
        raise OracleTerminalPanelNavigationInvariantError("panel count mismatch")
    for panel in registry.panels:
        verify_panel_definition(panel)
    if not registry.aliases_unique:
        raise OracleTerminalPanelNavigationInvariantError("panel aliases overlap")
    if registry.registry_ready != bool(registry.panels and registry.aliases_unique):
        raise OracleTerminalPanelNavigationInvariantError("panel registry readiness mismatch")
    if not registry.read_only:
        raise OracleTerminalPanelNavigationInvariantError("panel registry is not read-only")
    if (
        registry.publication_allowed
        or registry.action_authorization_allowed
        or registry.qseries_execution_allowed
    ):
        raise OracleTerminalPanelNavigationInvariantError("forbidden registry capability enabled")
    return True


def resolve_panel(
    requested_panel: str,
    *,
    registry: OracleTerminalPanelRegistry | None = None,
) -> OracleTerminalPanelSelection:
    active = registry or build_default_panel_registry()
    verify_panel_registry(active)
    requested = " ".join(str(requested_panel).strip().lower().split())
    match = None
    for panel in active.panels:
        if requested == panel.panel_name or requested in panel.aliases:
            match = panel
            break

    body = {
        "requested_panel": requested,
        "matched": match is not None,
        "panel_name": match.panel_name if match else None,
        "panel_index": match.panel_index if match else None,
        "source_frame_types": match.source_frame_types if match else (),
    }
    selection = OracleTerminalPanelSelection(
        **body,
        selection_hash=_stable_hash(body),
    )
    verify_panel_selection(selection)
    return selection


def verify_panel_selection(selection: OracleTerminalPanelSelection) -> bool:
    body = asdict(selection)
    supplied = body.pop("selection_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalPanelNavigationInvariantError("panel selection hash mismatch")
    if selection.matched and (
        selection.panel_name is None
        or selection.panel_index is None
        or not selection.source_frame_types
    ):
        raise OracleTerminalPanelNavigationInvariantError("matched panel selection incomplete")
    if not selection.matched and (
        selection.panel_name is not None
        or selection.panel_index is not None
        or selection.source_frame_types
    ):
        raise OracleTerminalPanelNavigationInvariantError("unmatched panel selection contains data")
    return True
