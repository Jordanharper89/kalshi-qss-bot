from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        required = (
            candidate / "qseries_v2" / "oracle_terminal"
            / "oracle_terminal_decision_brief_presentation_view_model.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_024 = PACKAGE / "oracle_terminal_decision_brief_presentation_view_model.py"
OIT_024_TEST = ROOT / "test_oit_024_oracle_terminal_decision_brief_presentation_view_model.py"
PRODUCTION = PACKAGE / "oracle_terminal_decision_brief_renderer_contract.py"
TEST = ROOT / "test_oit_025_oracle_terminal_decision_brief_renderer_contract.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_terminal_decision_brief_presentation_view_model import (\n    OracleTerminalPresentationInvariantError,\n    OracleTerminalPresentationPanel,\n    OracleTerminalPresentationViewModel,\n    build_terminal_presentation_view_model,\n    verify_terminal_presentation_view_model,\n)\n\nSCHEMA_VERSION = "OIT-025"\nENGINE_ID = "OIT-025"\nPOLICY_ID = "oracle.terminal-decision-brief-renderer-contract.v1"\n\n\nclass OracleTerminalRendererInvariantError(\n    OracleTerminalPresentationInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRenderedBlock:\n    block_index: int\n    block_type: str\n    severity: str\n    heading: str\n    rendered_lines: tuple[str, ...]\n    source_panel_hash: str\n    operator_attention_required: bool\n    read_only: bool\n    block_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRendererContract:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    presentation_view_model_hash: str\n    banner_lines: tuple[str, ...]\n    rendered_blocks: tuple[OracleTerminalRenderedBlock, ...]\n    block_count: int\n    critical_block_count: int\n    warning_block_count: int\n    informational_block_count: int\n    operator_attention_count: int\n    renderer_ready: bool\n    terminal_output_lines: tuple[str, ...]\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    qseries_execution_allowed: bool\n    action_authorization_allowed: bool\n    failure_reason: str | None\n    contract_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _render_panel(\n    panel: OracleTerminalPresentationPanel,\n    index: int,\n) -> OracleTerminalRenderedBlock:\n    marker = {\n        "critical": "[!]",\n        "warning": "[~]",\n        "informational": "[i]",\n    }[panel.severity]\n    lines = (\n        f"{marker} {panel.panel_label}",\n        *(f"  {line}" for line in panel.content_lines),\n    )\n    body = {\n        "block_index": index,\n        "block_type": panel.panel_type,\n        "severity": panel.severity,\n        "heading": panel.panel_label,\n        "rendered_lines": lines,\n        "source_panel_hash": panel.panel_hash,\n        "operator_attention_required": panel.operator_attention_required,\n        "read_only": True,\n    }\n    return OracleTerminalRenderedBlock(\n        **body,\n        block_hash=_stable_hash(body),\n    )\n\n\ndef verify_terminal_rendered_block(\n    block: OracleTerminalRenderedBlock,\n) -> bool:\n    body = asdict(block)\n    supplied = body.pop("block_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRendererInvariantError(\n            "terminal rendered block hash mismatch"\n        )\n    if block.severity not in {"critical", "warning", "informational"}:\n        raise OracleTerminalRendererInvariantError(\n            "unsupported rendered block severity"\n        )\n    if not block.heading or not block.rendered_lines:\n        raise OracleTerminalRendererInvariantError(\n            "rendered block content missing"\n        )\n    if not block.source_panel_hash:\n        raise OracleTerminalRendererInvariantError(\n            "rendered block panel lineage missing"\n        )\n    if not block.read_only:\n        raise OracleTerminalRendererInvariantError(\n            "rendered block is not read-only"\n        )\n    return True\n\n\ndef _flatten_output(\n    banner: tuple[str, ...],\n    blocks: tuple[OracleTerminalRenderedBlock, ...],\n) -> tuple[str, ...]:\n    lines: list[str] = list(banner)\n    for block in blocks:\n        lines.append("")\n        lines.extend(block.rendered_lines)\n    return tuple(lines)\n\n\ndef build_terminal_renderer_contract(\n    repository_root: str | Path,\n    query: str,\n    *,\n    presentation_view_model: OracleTerminalPresentationViewModel | None = None,\n) -> OracleTerminalRendererContract:\n    root = Path(repository_root).resolve()\n    source = presentation_view_model\n    if source is None:\n        source = build_terminal_presentation_view_model(root, query)\n    verify_terminal_presentation_view_model(source)\n\n    blocks = tuple(\n        _render_panel(panel, index)\n        for index, panel in enumerate(source.panels, start=1)\n    )\n    for block in blocks:\n        verify_terminal_rendered_block(block)\n\n    banner = (\n        "=" * 64,\n        source.terminal_heading,\n        f"STATUS: {source.status_label} | DIRECTION: {source.direction_label}",\n        source.terminal_subheading,\n        "=" * 64,\n    )\n    output_lines = _flatten_output(banner, blocks)\n    renderer_ready = bool(\n        source.rendering_ready\n        and blocks\n        and output_lines\n        and all(block.source_panel_hash for block in blocks)\n    )\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "presentation_view_model_hash": source.view_model_hash,\n        "banner_lines": banner,\n        "rendered_blocks": blocks,\n        "block_count": len(blocks),\n        "critical_block_count": sum(\n            block.severity == "critical" for block in blocks\n        ),\n        "warning_block_count": sum(\n            block.severity == "warning" for block in blocks\n        ),\n        "informational_block_count": sum(\n            block.severity == "informational" for block in blocks\n        ),\n        "operator_attention_count": sum(\n            block.operator_attention_required for block in blocks\n        ),\n        "renderer_ready": renderer_ready,\n        "terminal_output_lines": output_lines,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    contract = OracleTerminalRendererContract(\n        **body,\n        contract_hash=_stable_hash(body),\n    )\n    verify_terminal_renderer_contract(contract)\n    return contract\n\n\ndef verify_terminal_renderer_contract(\n    contract: OracleTerminalRendererContract,\n) -> bool:\n    body = asdict(contract)\n    supplied = body.pop("contract_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRendererInvariantError(\n            "terminal renderer contract hash mismatch"\n        )\n    if contract.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalRendererInvariantError("schema mismatch")\n    if contract.policy_id != POLICY_ID:\n        raise OracleTerminalRendererInvariantError("policy mismatch")\n    if not contract.read_only:\n        raise OracleTerminalRendererInvariantError(\n            "terminal renderer contract is not read-only"\n        )\n    if (\n        contract.analytics_execution_performed\n        or contract.database_access_performed\n        or contract.publication_allowed\n        or contract.qseries_execution_allowed\n        or contract.action_authorization_allowed\n    ):\n        raise OracleTerminalRendererInvariantError(\n            "forbidden capability enabled"\n        )\n    if contract.block_count != len(contract.rendered_blocks):\n        raise OracleTerminalRendererInvariantError(\n            "rendered block count mismatch"\n        )\n    counts = {\n        "critical": contract.critical_block_count,\n        "warning": contract.warning_block_count,\n        "informational": contract.informational_block_count,\n    }\n    for severity, expected in counts.items():\n        actual = sum(\n            block.severity == severity\n            for block in contract.rendered_blocks\n        )\n        if actual != expected:\n            raise OracleTerminalRendererInvariantError(\n                f"{severity} rendered block count mismatch"\n            )\n    if sum(counts.values()) != contract.block_count:\n        raise OracleTerminalRendererInvariantError(\n            "classified rendered block count mismatch"\n        )\n    if contract.operator_attention_count != sum(\n        block.operator_attention_required\n        for block in contract.rendered_blocks\n    ):\n        raise OracleTerminalRendererInvariantError(\n            "operator attention rendered block count mismatch"\n        )\n    for block in contract.rendered_blocks:\n        verify_terminal_rendered_block(block)\n    expected_output = _flatten_output(\n        contract.banner_lines,\n        contract.rendered_blocks,\n    )\n    if contract.terminal_output_lines != expected_output:\n        raise OracleTerminalRendererInvariantError(\n            "terminal output flattening mismatch"\n        )\n    if contract.renderer_ready and not contract.terminal_output_lines:\n        raise OracleTerminalRendererInvariantError(\n            "renderer-ready contract missing output"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_decision_brief_presentation_view_model import (\n    ENGINE_ID as OIT_024_ENGINE_ID,\n    POLICY_ID as OIT_024_POLICY_ID,\n    SCHEMA_VERSION as OIT_024_SCHEMA_VERSION,\n    OracleTerminalPresentationPanel,\n    OracleTerminalPresentationViewModel,\n    _stable_hash as oit_024_hash,\n    verify_terminal_presentation_view_model,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_decision_brief_renderer_contract import (\n    OracleTerminalRendererInvariantError,\n    build_terminal_renderer_contract,\n    verify_terminal_renderer_contract,\n)\n\n\ndef panel(index: int, severity: str, attention: bool):\n    body = {\n        "panel_index": index,\n        "panel_type": "attention" if attention else "decision_item",\n        "panel_label": f"{severity.title()} Panel",\n        "severity": severity,\n        "content_lines": (f"{severity} content",),\n        "source_section_hash": f"section-{index}",\n        "operator_attention_required": attention,\n        "display_order": 1 if severity == "critical" else 2 if severity == "warning" else 3,\n        "read_only": True,\n    }\n    return OracleTerminalPresentationPanel(\n        **body,\n        panel_hash=oit_024_hash(body),\n    )\n\n\ndef make_view_model(root: Path):\n    panels = (\n        panel(1, "critical", True),\n        panel(2, "warning", False),\n        panel(3, "informational", False),\n    )\n    body = {\n        "schema_version": OIT_024_SCHEMA_VERSION,\n        "engine_id": OIT_024_ENGINE_ID,\n        "policy_id": OIT_024_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Render the terminal decision brief.",\n        "consumption_contract_hash": "consumption-contract-hash",\n        "terminal_heading": "Oracle Operator Decision Brief",\n        "terminal_subheading": "Synthetic presentation model.",\n        "status_label": "ABSTAIN",\n        "direction_label": "BULL",\n        "panels": panels,\n        "panel_count": 3,\n        "critical_panel_count": 1,\n        "warning_panel_count": 1,\n        "informational_panel_count": 1,\n        "operator_attention_count": 1,\n        "rendering_ready": True,\n        "keyboard_navigation_ready": True,\n        "expandable_evidence_ready": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    view_model = OracleTerminalPresentationViewModel(\n        **body,\n        view_model_hash=oit_024_hash(body),\n    )\n    verify_terminal_presentation_view_model(view_model)\n    return view_model\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-025 TEST")\n    print(" TERMINAL DECISION BRIEF RENDERER CONTRACT")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_view_model(root)\n        contract = build_terminal_renderer_contract(\n            root,\n            source.query,\n            presentation_view_model=source,\n        )\n\n        assert contract.presentation_view_model_hash == source.view_model_hash\n        assert contract.block_count == 3\n        assert contract.critical_block_count == 1\n        assert contract.warning_block_count == 1\n        assert contract.informational_block_count == 1\n        assert contract.operator_attention_count == 1\n        assert contract.renderer_ready\n        assert contract.banner_lines\n        assert contract.terminal_output_lines\n        assert "STATUS: ABSTAIN | DIRECTION: BULL" in contract.banner_lines\n\n        assert contract.rendered_blocks[0].rendered_lines[0].startswith("[!]")\n        assert contract.rendered_blocks[1].rendered_lines[0].startswith("[~]")\n        assert contract.rendered_blocks[2].rendered_lines[0].startswith("[i]")\n\n        for block in contract.rendered_blocks:\n            assert block.heading\n            assert block.rendered_lines\n            assert block.source_panel_hash\n            assert block.read_only\n\n        replay = build_terminal_renderer_contract(\n            root,\n            source.query,\n            presentation_view_model=source,\n        )\n        assert replay == contract\n        assert verify_terminal_renderer_contract(contract)\n\n        tampered = replace(\n            contract,\n            terminal_output_lines=contract.terminal_output_lines + ("tampered",),\n        )\n        try:\n            verify_terminal_renderer_contract(tampered)\n        except OracleTerminalRendererInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered renderer contract accepted")\n\n        assert contract.read_only\n        assert not contract.analytics_execution_performed\n        assert not contract.database_access_performed\n        assert not contract.publication_allowed\n        assert not contract.qseries_execution_allowed\n        assert not contract.action_authorization_allowed\n\n    print("[PASS] Certified OIT-024 presentation view model consumed")\n    print("[PASS] Terminal banner materialized")\n    print("[PASS] Critical rendering marker materialized")\n    print("[PASS] Warning rendering marker materialized")\n    print("[PASS] Informational rendering marker materialized")\n    print("[PASS] Terminal output flattened deterministically")\n    print("[PASS] Operator-attention rendering preserved")\n    print("[PASS] Renderer readiness certified")\n    print("[PASS] Complete OIT-024 lineage retained")\n    print("[PASS] Renderer contract deterministic across replay")\n    print("[PASS] Tampered renderer contract rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-025 TERMINAL DECISION BRIEF RENDERER CONTRACT PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def require_contract(path: Path, tokens: tuple[str, ...], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")


def protected_sources() -> dict[Path, str]:
    protected = {}
    roots = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )
    for base in roots:
        if base.exists():
            for path in base.rglob("*.py"):
                if path.is_file():
                    protected[path] = sha256(path)
    for path in (OIT_024, OIT_024_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-025 INSTALLER")
    print(" TERMINAL DECISION BRIEF RENDERER CONTRACT")
    print("=" * 48)
    try:
        require_contract(
            OIT_024,
            (
                'SCHEMA_VERSION = "OIT-024"',
                'POLICY_ID = "oracle.terminal-decision-brief-presentation-view-model.v1"',
                "OracleTerminalPresentationViewModel",
                "OracleTerminalPresentationPanel",
                "build_terminal_presentation_view_model",
                "verify_terminal_presentation_view_model",
                "rendering_ready",
                "keyboard_navigation_ready",
                "expandable_evidence_ready",
                "action_authorization_allowed",
            ),
            "Certified OIT-024 production",
        )
        require_contract(
            OIT_024_TEST,
            (
                "OIT-024 TEST",
                "TERMINAL DECISION BRIEF PRESENTATION VIEW MODEL",
                "OIT-024 TERMINAL DECISION BRIEF PRESENTATION VIEW MODEL PASS",
            ),
            "Certified OIT-024 standalone test",
        )

        protected = protected_sources()
        print("[OK] Certified OIT-024 production contract verified")
        print("[OK] Certified OIT-024 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_024_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-024 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_decision_brief_renderer_contract import *"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            INIT.write_text(
                current + export + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")
        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-025 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-024 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-025 production module installed")
        print("[PASS] OIT-025 standalone test installed")
        print("[PASS] Terminal renderer contract certified")
        print("[PASS] Deterministic terminal output materialized")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-025 TERMINAL DECISION BRIEF RENDERER CONTRACT INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
