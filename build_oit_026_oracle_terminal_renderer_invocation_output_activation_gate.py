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
            / "oracle_terminal_decision_brief_renderer_contract.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_025 = PACKAGE / "oracle_terminal_decision_brief_renderer_contract.py"
OIT_025_TEST = ROOT / "test_oit_025_oracle_terminal_decision_brief_renderer_contract.py"
PRODUCTION = PACKAGE / "oracle_terminal_renderer_invocation_output_activation_gate.py"
TEST = ROOT / "test_oit_026_oracle_terminal_renderer_invocation_output_activation_gate.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_terminal_decision_brief_renderer_contract import (\n    OracleTerminalRendererContract,\n    OracleTerminalRendererInvariantError,\n    build_terminal_renderer_contract,\n    verify_terminal_renderer_contract,\n)\n\nSCHEMA_VERSION = "OIT-026"\nENGINE_ID = "OIT-026"\nPOLICY_ID = "oracle.terminal-renderer-invocation-output-activation-gate.v1"\n\n\nclass OracleTerminalRendererActivationInvariantError(\n    OracleTerminalRendererInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRendererInvocation:\n    invocation_id: str\n    query: str\n    source_renderer_contract_hash: str\n    requested_operation: str\n    output_mode: str\n    invocation_authorized: bool\n    display_only: bool\n    read_only: bool\n    invocation_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRendererOutputActivation:\n    activation_id: str\n    invocation_hash: str\n    source_renderer_contract_hash: str\n    terminal_output_lines: tuple[str, ...]\n    output_line_count: int\n    display_ready: bool\n    output_activated: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    activation_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRendererActivationGateReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    renderer_contract_hash: str\n    invocation: OracleTerminalRendererInvocation\n    activation: OracleTerminalRendererOutputActivation\n    invocation_authorized: bool\n    output_activated: bool\n    display_ready: bool\n    renderer_activation_ready: bool\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _build_invocation(\n    query: str,\n    renderer_contract: OracleTerminalRendererContract,\n) -> OracleTerminalRendererInvocation:\n    invocation_id = _stable_hash(\n        {\n            "query": query,\n            "renderer_contract_hash": renderer_contract.contract_hash,\n            "operation": "render_terminal_output",\n            "output_mode": "display_only",\n        }\n    )[:24]\n    body = {\n        "invocation_id": invocation_id,\n        "query": str(query),\n        "source_renderer_contract_hash": renderer_contract.contract_hash,\n        "requested_operation": "render_terminal_output",\n        "output_mode": "display_only",\n        "invocation_authorized": bool(\n            renderer_contract.renderer_ready\n            and renderer_contract.terminal_output_lines\n        ),\n        "display_only": True,\n        "read_only": True,\n    }\n    return OracleTerminalRendererInvocation(\n        **body,\n        invocation_hash=_stable_hash(body),\n    )\n\n\ndef verify_terminal_renderer_invocation(\n    invocation: OracleTerminalRendererInvocation,\n) -> bool:\n    body = asdict(invocation)\n    supplied = body.pop("invocation_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRendererActivationInvariantError(\n            "terminal renderer invocation hash mismatch"\n        )\n    if invocation.requested_operation != "render_terminal_output":\n        raise OracleTerminalRendererActivationInvariantError(\n            "unsupported renderer invocation operation"\n        )\n    if invocation.output_mode != "display_only":\n        raise OracleTerminalRendererActivationInvariantError(\n            "renderer invocation output mode is not display-only"\n        )\n    if not invocation.display_only or not invocation.read_only:\n        raise OracleTerminalRendererActivationInvariantError(\n            "renderer invocation is not read-only display-only"\n        )\n    if not invocation.source_renderer_contract_hash:\n        raise OracleTerminalRendererActivationInvariantError(\n            "renderer invocation lineage missing"\n        )\n    return True\n\n\ndef _build_activation(\n    invocation: OracleTerminalRendererInvocation,\n    renderer_contract: OracleTerminalRendererContract,\n) -> OracleTerminalRendererOutputActivation:\n    output = tuple(renderer_contract.terminal_output_lines)\n    activation_id = _stable_hash(\n        {\n            "invocation_hash": invocation.invocation_hash,\n            "renderer_contract_hash": renderer_contract.contract_hash,\n            "output": output,\n        }\n    )[:24]\n    activated = bool(\n        invocation.invocation_authorized\n        and renderer_contract.renderer_ready\n        and output\n    )\n    body = {\n        "activation_id": activation_id,\n        "invocation_hash": invocation.invocation_hash,\n        "source_renderer_contract_hash": renderer_contract.contract_hash,\n        "terminal_output_lines": output,\n        "output_line_count": len(output),\n        "display_ready": activated,\n        "output_activated": activated,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n    }\n    return OracleTerminalRendererOutputActivation(\n        **body,\n        activation_hash=_stable_hash(body),\n    )\n\n\ndef verify_terminal_renderer_output_activation(\n    activation: OracleTerminalRendererOutputActivation,\n) -> bool:\n    body = asdict(activation)\n    supplied = body.pop("activation_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRendererActivationInvariantError(\n            "terminal renderer activation hash mismatch"\n        )\n    if not activation.read_only:\n        raise OracleTerminalRendererActivationInvariantError(\n            "terminal renderer activation is not read-only"\n        )\n    if (\n        activation.publication_allowed\n        or activation.action_authorization_allowed\n        or activation.qseries_execution_allowed\n    ):\n        raise OracleTerminalRendererActivationInvariantError(\n            "forbidden activation capability enabled"\n        )\n    if activation.output_line_count != len(activation.terminal_output_lines):\n        raise OracleTerminalRendererActivationInvariantError(\n            "terminal activation output-line count mismatch"\n        )\n    if activation.output_activated != activation.display_ready:\n        raise OracleTerminalRendererActivationInvariantError(\n            "terminal activation display state mismatch"\n        )\n    if activation.output_activated and not activation.terminal_output_lines:\n        raise OracleTerminalRendererActivationInvariantError(\n            "empty output activated"\n        )\n    return True\n\n\ndef build_terminal_renderer_activation_gate_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    renderer_contract: OracleTerminalRendererContract | None = None,\n) -> OracleTerminalRendererActivationGateReport:\n    root = Path(repository_root).resolve()\n    source = renderer_contract\n    if source is None:\n        source = build_terminal_renderer_contract(root, query)\n    verify_terminal_renderer_contract(source)\n\n    invocation = _build_invocation(query, source)\n    verify_terminal_renderer_invocation(invocation)\n\n    activation = _build_activation(invocation, source)\n    verify_terminal_renderer_output_activation(activation)\n\n    ready = bool(\n        invocation.invocation_authorized\n        and activation.output_activated\n        and activation.display_ready\n    )\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "renderer_contract_hash": source.contract_hash,\n        "invocation": invocation,\n        "activation": activation,\n        "invocation_authorized": invocation.invocation_authorized,\n        "output_activated": activation.output_activated,\n        "display_ready": activation.display_ready,\n        "renderer_activation_ready": ready,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleTerminalRendererActivationGateReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_terminal_renderer_activation_gate_report(report)\n    return report\n\n\ndef verify_terminal_renderer_activation_gate_report(\n    report: OracleTerminalRendererActivationGateReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRendererActivationInvariantError(\n            "terminal renderer activation report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalRendererActivationInvariantError(\n            "schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleTerminalRendererActivationInvariantError(\n            "policy mismatch"\n        )\n    if not report.read_only:\n        raise OracleTerminalRendererActivationInvariantError(\n            "terminal renderer activation report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleTerminalRendererActivationInvariantError(\n            "forbidden capability enabled"\n        )\n    verify_terminal_renderer_invocation(report.invocation)\n    verify_terminal_renderer_output_activation(report.activation)\n    if report.renderer_contract_hash != (\n        report.invocation.source_renderer_contract_hash\n    ):\n        raise OracleTerminalRendererActivationInvariantError(\n            "renderer invocation lineage mismatch"\n        )\n    if report.renderer_contract_hash != (\n        report.activation.source_renderer_contract_hash\n    ):\n        raise OracleTerminalRendererActivationInvariantError(\n            "renderer activation lineage mismatch"\n        )\n    if report.activation.invocation_hash != report.invocation.invocation_hash:\n        raise OracleTerminalRendererActivationInvariantError(\n            "activation invocation lineage mismatch"\n        )\n    if report.invocation_authorized != report.invocation.invocation_authorized:\n        raise OracleTerminalRendererActivationInvariantError(\n            "invocation authorization state mismatch"\n        )\n    if report.output_activated != report.activation.output_activated:\n        raise OracleTerminalRendererActivationInvariantError(\n            "output activation state mismatch"\n        )\n    if report.display_ready != report.activation.display_ready:\n        raise OracleTerminalRendererActivationInvariantError(\n            "display readiness state mismatch"\n        )\n    expected_ready = bool(\n        report.invocation_authorized\n        and report.output_activated\n        and report.display_ready\n    )\n    if report.renderer_activation_ready != expected_ready:\n        raise OracleTerminalRendererActivationInvariantError(\n            "renderer activation readiness mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_decision_brief_renderer_contract import (\n    ENGINE_ID as OIT_025_ENGINE_ID,\n    POLICY_ID as OIT_025_POLICY_ID,\n    SCHEMA_VERSION as OIT_025_SCHEMA_VERSION,\n    OracleTerminalRenderedBlock,\n    OracleTerminalRendererContract,\n    _stable_hash as oit_025_hash,\n    verify_terminal_renderer_contract,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_renderer_invocation_output_activation_gate import (\n    OracleTerminalRendererActivationInvariantError,\n    build_terminal_renderer_activation_gate_report,\n    verify_terminal_renderer_activation_gate_report,\n)\n\n\ndef rendered_block(index: int):\n    body = {\n        "block_index": index,\n        "block_type": "decision_item",\n        "severity": "warning",\n        "heading": "Decision Item",\n        "rendered_lines": ("[~] Decision Item", "  evidence"),\n        "source_panel_hash": f"panel-{index}",\n        "operator_attention_required": False,\n        "read_only": True,\n    }\n    return OracleTerminalRenderedBlock(\n        **body,\n        block_hash=oit_025_hash(body),\n    )\n\n\ndef make_contract(root: Path):\n    blocks = (rendered_block(1),)\n    banner = (\n        "=" * 64,\n        "Oracle Operator Decision Brief",\n        "STATUS: OBSERVE | DIRECTION: BULL",\n        "Synthetic renderer contract.",\n        "=" * 64,\n    )\n    output = banner + ("",) + blocks[0].rendered_lines\n    body = {\n        "schema_version": OIT_025_SCHEMA_VERSION,\n        "engine_id": OIT_025_ENGINE_ID,\n        "policy_id": OIT_025_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Activate renderer output.",\n        "presentation_view_model_hash": "presentation-view-model-hash",\n        "banner_lines": banner,\n        "rendered_blocks": blocks,\n        "block_count": 1,\n        "critical_block_count": 0,\n        "warning_block_count": 1,\n        "informational_block_count": 0,\n        "operator_attention_count": 0,\n        "renderer_ready": True,\n        "terminal_output_lines": output,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "qseries_execution_allowed": False,\n        "action_authorization_allowed": False,\n        "failure_reason": None,\n    }\n    contract = OracleTerminalRendererContract(\n        **body,\n        contract_hash=oit_025_hash(body),\n    )\n    verify_terminal_renderer_contract(contract)\n    return contract\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-026 TEST")\n    print(" TERMINAL RENDERER INVOCATION OUTPUT ACTIVATION GATE")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_contract(root)\n        report = build_terminal_renderer_activation_gate_report(\n            root,\n            source.query,\n            renderer_contract=source,\n        )\n\n        assert report.renderer_contract_hash == source.contract_hash\n        assert report.invocation.invocation_authorized\n        assert report.invocation.display_only\n        assert report.invocation.read_only\n        assert report.activation.output_activated\n        assert report.activation.display_ready\n        assert report.activation.terminal_output_lines == source.terminal_output_lines\n        assert report.activation.output_line_count == len(source.terminal_output_lines)\n        assert report.renderer_activation_ready\n\n        replay = build_terminal_renderer_activation_gate_report(\n            root,\n            source.query,\n            renderer_contract=source,\n        )\n        assert replay == report\n        assert verify_terminal_renderer_activation_gate_report(report)\n\n        tampered = replace(\n            report,\n            display_ready=False,\n        )\n        try:\n            verify_terminal_renderer_activation_gate_report(tampered)\n        except OracleTerminalRendererActivationInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered activation report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Certified OIT-025 renderer contract consumed")\n    print("[PASS] Renderer invocation materialized")\n    print("[PASS] Display-only invocation authorized")\n    print("[PASS] Terminal output activation materialized")\n    print("[PASS] Activated output matched certified renderer output")\n    print("[PASS] Output line count certified")\n    print("[PASS] Renderer activation readiness certified")\n    print("[PASS] Complete OIT-025 lineage retained")\n    print("[PASS] Activation report deterministic across replay")\n    print("[PASS] Tampered activation report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-026 TERMINAL RENDERER INVOCATION OUTPUT ACTIVATION GATE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_025, OIT_025_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-026 INSTALLER")
    print(" TERMINAL RENDERER INVOCATION OUTPUT ACTIVATION GATE")
    print("=" * 48)
    try:
        require_contract(
            OIT_025,
            (
                'SCHEMA_VERSION = "OIT-025"',
                'POLICY_ID = "oracle.terminal-decision-brief-renderer-contract.v1"',
                "OracleTerminalRendererContract",
                "OracleTerminalRenderedBlock",
                "build_terminal_renderer_contract",
                "verify_terminal_renderer_contract",
                "renderer_ready",
                "terminal_output_lines",
                "publication_allowed",
                "action_authorization_allowed",
                "qseries_execution_allowed",
            ),
            "Certified OIT-025 production",
        )
        require_contract(
            OIT_025_TEST,
            (
                "OIT-025 TEST",
                "TERMINAL DECISION BRIEF RENDERER CONTRACT",
                "OIT-025 TERMINAL DECISION BRIEF RENDERER CONTRACT PASS",
            ),
            "Certified OIT-025 standalone test",
        )

        protected = protected_sources()
        print("[OK] Certified OIT-025 production contract verified")
        print("[OK] Certified OIT-025 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_025_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-025 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_renderer_invocation_output_activation_gate import *"
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
                f"OIT-026 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-025 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-026 production module installed")
        print("[PASS] OIT-026 standalone test installed")
        print("[PASS] Renderer invocation and output activation certified")
        print("[PASS] Display-only terminal activation boundary prepared")
        print("[PASS] Publication and action authorization remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-026 TERMINAL RENDERER INVOCATION OUTPUT ACTIVATION GATE INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
