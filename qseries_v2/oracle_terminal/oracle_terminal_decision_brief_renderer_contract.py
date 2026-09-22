from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_terminal_decision_brief_presentation_view_model import (
    OracleTerminalPresentationInvariantError,
    OracleTerminalPresentationPanel,
    OracleTerminalPresentationViewModel,
    build_terminal_presentation_view_model,
    verify_terminal_presentation_view_model,
)

SCHEMA_VERSION = "OIT-025"
ENGINE_ID = "OIT-025"
POLICY_ID = "oracle.terminal-decision-brief-renderer-contract.v1"


class OracleTerminalRendererInvariantError(
    OracleTerminalPresentationInvariantError
):
    pass


@dataclass(frozen=True)
class OracleTerminalRenderedBlock:
    block_index: int
    block_type: str
    severity: str
    heading: str
    rendered_lines: tuple[str, ...]
    source_panel_hash: str
    operator_attention_required: bool
    read_only: bool
    block_hash: str


@dataclass(frozen=True)
class OracleTerminalRendererContract:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    presentation_view_model_hash: str
    banner_lines: tuple[str, ...]
    rendered_blocks: tuple[OracleTerminalRenderedBlock, ...]
    block_count: int
    critical_block_count: int
    warning_block_count: int
    informational_block_count: int
    operator_attention_count: int
    renderer_ready: bool
    terminal_output_lines: tuple[str, ...]
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


def _render_panel(
    panel: OracleTerminalPresentationPanel,
    index: int,
) -> OracleTerminalRenderedBlock:
    marker = {
        "critical": "[!]",
        "warning": "[~]",
        "informational": "[i]",
    }[panel.severity]
    lines = (
        f"{marker} {panel.panel_label}",
        *(f"  {line}" for line in panel.content_lines),
    )
    body = {
        "block_index": index,
        "block_type": panel.panel_type,
        "severity": panel.severity,
        "heading": panel.panel_label,
        "rendered_lines": lines,
        "source_panel_hash": panel.panel_hash,
        "operator_attention_required": panel.operator_attention_required,
        "read_only": True,
    }
    return OracleTerminalRenderedBlock(
        **body,
        block_hash=_stable_hash(body),
    )


def verify_terminal_rendered_block(
    block: OracleTerminalRenderedBlock,
) -> bool:
    body = asdict(block)
    supplied = body.pop("block_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRendererInvariantError(
            "terminal rendered block hash mismatch"
        )
    if block.severity not in {"critical", "warning", "informational"}:
        raise OracleTerminalRendererInvariantError(
            "unsupported rendered block severity"
        )
    if not block.heading or not block.rendered_lines:
        raise OracleTerminalRendererInvariantError(
            "rendered block content missing"
        )
    if not block.source_panel_hash:
        raise OracleTerminalRendererInvariantError(
            "rendered block panel lineage missing"
        )
    if not block.read_only:
        raise OracleTerminalRendererInvariantError(
            "rendered block is not read-only"
        )
    return True


def _flatten_output(
    banner: tuple[str, ...],
    blocks: tuple[OracleTerminalRenderedBlock, ...],
) -> tuple[str, ...]:
    lines: list[str] = list(banner)
    for block in blocks:
        lines.append("")
        lines.extend(block.rendered_lines)
    return tuple(lines)


def build_terminal_renderer_contract(
    repository_root: str | Path,
    query: str,
    *,
    presentation_view_model: OracleTerminalPresentationViewModel | None = None,
) -> OracleTerminalRendererContract:
    root = Path(repository_root).resolve()
    source = presentation_view_model
    if source is None:
        source = build_terminal_presentation_view_model(root, query)
    verify_terminal_presentation_view_model(source)

    blocks = tuple(
        _render_panel(panel, index)
        for index, panel in enumerate(source.panels, start=1)
    )
    for block in blocks:
        verify_terminal_rendered_block(block)

    banner = (
        "=" * 64,
        source.terminal_heading,
        f"STATUS: {source.status_label} | DIRECTION: {source.direction_label}",
        source.terminal_subheading,
        "=" * 64,
    )
    output_lines = _flatten_output(banner, blocks)
    renderer_ready = bool(
        source.rendering_ready
        and blocks
        and output_lines
        and all(block.source_panel_hash for block in blocks)
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "presentation_view_model_hash": source.view_model_hash,
        "banner_lines": banner,
        "rendered_blocks": blocks,
        "block_count": len(blocks),
        "critical_block_count": sum(
            block.severity == "critical" for block in blocks
        ),
        "warning_block_count": sum(
            block.severity == "warning" for block in blocks
        ),
        "informational_block_count": sum(
            block.severity == "informational" for block in blocks
        ),
        "operator_attention_count": sum(
            block.operator_attention_required for block in blocks
        ),
        "renderer_ready": renderer_ready,
        "terminal_output_lines": output_lines,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    contract = OracleTerminalRendererContract(
        **body,
        contract_hash=_stable_hash(body),
    )
    verify_terminal_renderer_contract(contract)
    return contract


def verify_terminal_renderer_contract(
    contract: OracleTerminalRendererContract,
) -> bool:
    body = asdict(contract)
    supplied = body.pop("contract_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRendererInvariantError(
            "terminal renderer contract hash mismatch"
        )
    if contract.schema_version != SCHEMA_VERSION:
        raise OracleTerminalRendererInvariantError("schema mismatch")
    if contract.policy_id != POLICY_ID:
        raise OracleTerminalRendererInvariantError("policy mismatch")
    if not contract.read_only:
        raise OracleTerminalRendererInvariantError(
            "terminal renderer contract is not read-only"
        )
    if (
        contract.analytics_execution_performed
        or contract.database_access_performed
        or contract.publication_allowed
        or contract.qseries_execution_allowed
        or contract.action_authorization_allowed
    ):
        raise OracleTerminalRendererInvariantError(
            "forbidden capability enabled"
        )
    if contract.block_count != len(contract.rendered_blocks):
        raise OracleTerminalRendererInvariantError(
            "rendered block count mismatch"
        )
    counts = {
        "critical": contract.critical_block_count,
        "warning": contract.warning_block_count,
        "informational": contract.informational_block_count,
    }
    for severity, expected in counts.items():
        actual = sum(
            block.severity == severity
            for block in contract.rendered_blocks
        )
        if actual != expected:
            raise OracleTerminalRendererInvariantError(
                f"{severity} rendered block count mismatch"
            )
    if sum(counts.values()) != contract.block_count:
        raise OracleTerminalRendererInvariantError(
            "classified rendered block count mismatch"
        )
    if contract.operator_attention_count != sum(
        block.operator_attention_required
        for block in contract.rendered_blocks
    ):
        raise OracleTerminalRendererInvariantError(
            "operator attention rendered block count mismatch"
        )
    for block in contract.rendered_blocks:
        verify_terminal_rendered_block(block)
    expected_output = _flatten_output(
        contract.banner_lines,
        contract.rendered_blocks,
    )
    if contract.terminal_output_lines != expected_output:
        raise OracleTerminalRendererInvariantError(
            "terminal output flattening mismatch"
        )
    if contract.renderer_ready and not contract.terminal_output_lines:
        raise OracleTerminalRendererInvariantError(
            "renderer-ready contract missing output"
        )
    return True
