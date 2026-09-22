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
            / "oracle_terminal_renderer_invocation_output_activation_gate.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_026 = PACKAGE / "oracle_terminal_renderer_invocation_output_activation_gate.py"
OIT_026_TEST = ROOT / "test_oit_026_oracle_terminal_renderer_invocation_output_activation_gate.py"
PRODUCTION = PACKAGE / "oracle_terminal_activated_output_display_session_gate.py"
TEST = ROOT / "test_oit_027_oracle_terminal_activated_output_display_session_gate.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_terminal_renderer_invocation_output_activation_gate import (\n    OracleTerminalRendererActivationGateReport,\n    OracleTerminalRendererActivationInvariantError,\n    build_terminal_renderer_activation_gate_report,\n    verify_terminal_renderer_activation_gate_report,\n)\n\nSCHEMA_VERSION = "OIT-027"\nENGINE_ID = "OIT-027"\nPOLICY_ID = "oracle.terminal-activated-output-display-session-gate.v1"\n\n\nclass OracleTerminalDisplaySessionInvariantError(\n    OracleTerminalRendererActivationInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalDisplayFrame:\n    frame_index: int\n    frame_type: str\n    frame_lines: tuple[str, ...]\n    source_activation_hash: str\n    display_only: bool\n    read_only: bool\n    frame_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalDisplaySession:\n    session_id: str\n    query: str\n    source_activation_report_hash: str\n    source_output_activation_hash: str\n    frames: tuple[OracleTerminalDisplayFrame, ...]\n    frame_count: int\n    output_line_count: int\n    session_open: bool\n    display_ready: bool\n    interactive_read_only: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    session_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalDisplaySessionGateReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    query: str\n    activation_report_hash: str\n    display_session: OracleTerminalDisplaySession\n    session_open: bool\n    display_ready: bool\n    output_preserved_exactly: bool\n    display_session_ready: bool\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _frame_type(lines: tuple[str, ...]) -> str:\n    if not lines:\n        return "empty"\n    first = lines[0]\n    if first.startswith("="):\n        return "banner"\n    if first.startswith("[!]"):\n        return "critical"\n    if first.startswith("[~]"):\n        return "warning"\n    if first.startswith("[i]"):\n        return "informational"\n    return "content"\n\n\ndef _split_frames(\n    output_lines: tuple[str, ...],\n    activation_hash: str,\n) -> tuple[OracleTerminalDisplayFrame, ...]:\n    groups: list[tuple[str, ...]] = []\n    current: list[str] = []\n    for line in output_lines:\n        if line == "":\n            if current:\n                groups.append(tuple(current))\n                current = []\n            continue\n        current.append(line)\n    if current:\n        groups.append(tuple(current))\n\n    frames = []\n    for index, lines in enumerate(groups, start=1):\n        body = {\n            "frame_index": index,\n            "frame_type": _frame_type(lines),\n            "frame_lines": lines,\n            "source_activation_hash": activation_hash,\n            "display_only": True,\n            "read_only": True,\n        }\n        frames.append(\n            OracleTerminalDisplayFrame(\n                **body,\n                frame_hash=_stable_hash(body),\n            )\n        )\n    return tuple(frames)\n\n\ndef verify_terminal_display_frame(\n    frame: OracleTerminalDisplayFrame,\n) -> bool:\n    body = asdict(frame)\n    supplied = body.pop("frame_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "terminal display frame hash mismatch"\n        )\n    if frame.frame_type not in {\n        "banner",\n        "critical",\n        "warning",\n        "informational",\n        "content",\n    }:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "unsupported terminal display frame type"\n        )\n    if not frame.frame_lines:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "terminal display frame is empty"\n        )\n    if not frame.source_activation_hash:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "terminal display frame activation lineage missing"\n        )\n    if not frame.display_only or not frame.read_only:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "terminal display frame is not read-only display-only"\n        )\n    return True\n\n\ndef _flatten_frames(\n    frames: tuple[OracleTerminalDisplayFrame, ...],\n) -> tuple[str, ...]:\n    lines: list[str] = []\n    for index, frame in enumerate(frames):\n        if index:\n            lines.append("")\n        lines.extend(frame.frame_lines)\n    return tuple(lines)\n\n\ndef _build_display_session(\n    query: str,\n    activation_report: OracleTerminalRendererActivationGateReport,\n) -> OracleTerminalDisplaySession:\n    activation = activation_report.activation\n    frames = _split_frames(\n        tuple(activation.terminal_output_lines),\n        activation.activation_hash,\n    )\n    for frame in frames:\n        verify_terminal_display_frame(frame)\n\n    session_id = _stable_hash(\n        {\n            "query": query,\n            "activation_report_hash": activation_report.report_hash,\n            "activation_hash": activation.activation_hash,\n            "frames": frames,\n        }\n    )[:24]\n\n    body = {\n        "session_id": session_id,\n        "query": str(query),\n        "source_activation_report_hash": activation_report.report_hash,\n        "source_output_activation_hash": activation.activation_hash,\n        "frames": frames,\n        "frame_count": len(frames),\n        "output_line_count": len(activation.terminal_output_lines),\n        "session_open": bool(\n            activation_report.renderer_activation_ready and frames\n        ),\n        "display_ready": bool(\n            activation.display_ready and activation.output_activated\n        ),\n        "interactive_read_only": True,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n    }\n    session = OracleTerminalDisplaySession(\n        **body,\n        session_hash=_stable_hash(body),\n    )\n    verify_terminal_display_session(session)\n    return session\n\n\ndef verify_terminal_display_session(\n    session: OracleTerminalDisplaySession,\n) -> bool:\n    body = asdict(session)\n    supplied = body.pop("session_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "terminal display session hash mismatch"\n        )\n    if not session.read_only or not session.interactive_read_only:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "terminal display session is not read-only"\n        )\n    if (\n        session.publication_allowed\n        or session.action_authorization_allowed\n        or session.qseries_execution_allowed\n    ):\n        raise OracleTerminalDisplaySessionInvariantError(\n            "forbidden display session capability enabled"\n        )\n    if session.frame_count != len(session.frames):\n        raise OracleTerminalDisplaySessionInvariantError(\n            "terminal display frame count mismatch"\n        )\n    for frame in session.frames:\n        verify_terminal_display_frame(frame)\n        if frame.source_activation_hash != session.source_output_activation_hash:\n            raise OracleTerminalDisplaySessionInvariantError(\n                "terminal display frame lineage mismatch"\n            )\n    if session.session_open and not session.frames:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "empty terminal display session opened"\n        )\n    if session.session_open and not session.display_ready:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "terminal display session opened without display readiness"\n        )\n    return True\n\n\ndef build_terminal_display_session_gate_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    activation_report: OracleTerminalRendererActivationGateReport | None = None,\n) -> OracleTerminalDisplaySessionGateReport:\n    root = Path(repository_root).resolve()\n    source = activation_report\n    if source is None:\n        source = build_terminal_renderer_activation_gate_report(root, query)\n    verify_terminal_renderer_activation_gate_report(source)\n\n    session = _build_display_session(query, source)\n    source_output = tuple(source.activation.terminal_output_lines)\n    reconstructed = _flatten_frames(session.frames)\n    preserved = reconstructed == source_output\n    ready = bool(\n        source.renderer_activation_ready\n        and session.session_open\n        and session.display_ready\n        and preserved\n    )\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "query": str(query),\n        "activation_report_hash": source.report_hash,\n        "display_session": session,\n        "session_open": session.session_open,\n        "display_ready": session.display_ready,\n        "output_preserved_exactly": preserved,\n        "display_session_ready": ready,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleTerminalDisplaySessionGateReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_terminal_display_session_gate_report(report)\n    return report\n\n\ndef verify_terminal_display_session_gate_report(\n    report: OracleTerminalDisplaySessionGateReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "terminal display session gate report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "policy mismatch"\n        )\n    if not report.read_only:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "terminal display session gate report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleTerminalDisplaySessionInvariantError(\n            "forbidden capability enabled"\n        )\n    verify_terminal_display_session(report.display_session)\n    if report.activation_report_hash != (\n        report.display_session.source_activation_report_hash\n    ):\n        raise OracleTerminalDisplaySessionInvariantError(\n            "display session activation-report lineage mismatch"\n        )\n    if report.session_open != report.display_session.session_open:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "display session open state mismatch"\n        )\n    if report.display_ready != report.display_session.display_ready:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "display session readiness state mismatch"\n        )\n    expected_ready = bool(\n        report.session_open\n        and report.display_ready\n        and report.output_preserved_exactly\n    )\n    if report.display_session_ready != expected_ready:\n        raise OracleTerminalDisplaySessionInvariantError(\n            "display session gate readiness mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_renderer_invocation_output_activation_gate import (\n    ENGINE_ID as OIT_026_ENGINE_ID,\n    POLICY_ID as OIT_026_POLICY_ID,\n    SCHEMA_VERSION as OIT_026_SCHEMA_VERSION,\n    OracleTerminalRendererActivationGateReport,\n    OracleTerminalRendererInvocation,\n    OracleTerminalRendererOutputActivation,\n    _stable_hash as oit_026_hash,\n    verify_terminal_renderer_activation_gate_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (\n    OracleTerminalDisplaySessionInvariantError,\n    build_terminal_display_session_gate_report,\n    verify_terminal_display_session_gate_report,\n)\n\n\ndef make_activation_report(root: Path):\n    output = (\n        "=" * 64,\n        "Oracle Operator Decision Brief",\n        "STATUS: OBSERVE | DIRECTION: BULL",\n        "Synthetic activated output.",\n        "=" * 64,\n        "",\n        "[!] Operator Attention",\n        "  review contested evidence",\n        "",\n        "[~] Next Steps",\n        "  confirm persistence",\n    )\n    invocation_body = {\n        "invocation_id": "invocation-001",\n        "query": "Open the display session.",\n        "source_renderer_contract_hash": "renderer-contract-hash",\n        "requested_operation": "render_terminal_output",\n        "output_mode": "display_only",\n        "invocation_authorized": True,\n        "display_only": True,\n        "read_only": True,\n    }\n    invocation = OracleTerminalRendererInvocation(\n        **invocation_body,\n        invocation_hash=oit_026_hash(invocation_body),\n    )\n    activation_body = {\n        "activation_id": "activation-001",\n        "invocation_hash": invocation.invocation_hash,\n        "source_renderer_contract_hash": "renderer-contract-hash",\n        "terminal_output_lines": output,\n        "output_line_count": len(output),\n        "display_ready": True,\n        "output_activated": True,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n    }\n    activation = OracleTerminalRendererOutputActivation(\n        **activation_body,\n        activation_hash=oit_026_hash(activation_body),\n    )\n    report_body = {\n        "schema_version": OIT_026_SCHEMA_VERSION,\n        "engine_id": OIT_026_ENGINE_ID,\n        "policy_id": OIT_026_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Open the display session.",\n        "renderer_contract_hash": "renderer-contract-hash",\n        "invocation": invocation,\n        "activation": activation,\n        "invocation_authorized": True,\n        "output_activated": True,\n        "display_ready": True,\n        "renderer_activation_ready": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleTerminalRendererActivationGateReport(\n        **report_body,\n        report_hash=oit_026_hash(report_body),\n    )\n    verify_terminal_renderer_activation_gate_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-027 TEST")\n    print(" TERMINAL ACTIVATED OUTPUT DISPLAY SESSION GATE")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_activation_report(root)\n        report = build_terminal_display_session_gate_report(\n            root,\n            source.query,\n            activation_report=source,\n        )\n\n        assert report.activation_report_hash == source.report_hash\n        assert report.session_open\n        assert report.display_ready\n        assert report.output_preserved_exactly\n        assert report.display_session_ready\n        assert report.display_session.frame_count == 3\n        assert report.display_session.output_line_count == len(\n            source.activation.terminal_output_lines\n        )\n        assert report.display_session.frames[0].frame_type == "banner"\n        assert report.display_session.frames[1].frame_type == "critical"\n        assert report.display_session.frames[2].frame_type == "warning"\n\n        replay = build_terminal_display_session_gate_report(\n            root,\n            source.query,\n            activation_report=source,\n        )\n        assert replay == report\n        assert verify_terminal_display_session_gate_report(report)\n\n        tampered = replace(\n            report,\n            output_preserved_exactly=False,\n        )\n        try:\n            verify_terminal_display_session_gate_report(tampered)\n        except OracleTerminalDisplaySessionInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered display session report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Certified OIT-026 activation report consumed")\n    print("[PASS] Read-only display session materialized")\n    print("[PASS] Banner frame materialized")\n    print("[PASS] Critical frame materialized")\n    print("[PASS] Warning frame materialized")\n    print("[PASS] Activated output preserved exactly")\n    print("[PASS] Interactive read-only session enabled")\n    print("[PASS] Display-session readiness certified")\n    print("[PASS] Complete OIT-026 lineage retained")\n    print("[PASS] Display-session report deterministic across replay")\n    print("[PASS] Tampered display-session report rejected")\n    print("[PASS] No analytics execution or database access performed")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-027 TERMINAL ACTIVATED OUTPUT DISPLAY SESSION GATE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_026, OIT_026_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-027 INSTALLER")
    print(" TERMINAL ACTIVATED OUTPUT DISPLAY SESSION GATE")
    print("=" * 48)
    try:
        require_contract(
            OIT_026,
            (
                'SCHEMA_VERSION = "OIT-026"',
                'POLICY_ID = "oracle.terminal-renderer-invocation-output-activation-gate.v1"',
                "OracleTerminalRendererActivationGateReport",
                "OracleTerminalRendererInvocation",
                "OracleTerminalRendererOutputActivation",
                "build_terminal_renderer_activation_gate_report",
                "verify_terminal_renderer_activation_gate_report",
                "renderer_activation_ready",
                "terminal_output_lines",
                "display_ready",
                "publication_allowed",
                "action_authorization_allowed",
                "qseries_execution_allowed",
            ),
            "Certified OIT-026 production",
        )
        require_contract(
            OIT_026_TEST,
            (
                "OIT-026 TEST",
                "TERMINAL RENDERER INVOCATION OUTPUT ACTIVATION GATE",
                "OIT-026 TERMINAL RENDERER INVOCATION OUTPUT ACTIVATION GATE PASS",
            ),
            "Certified OIT-026 standalone test",
        )

        protected = protected_sources()
        print("[OK] Certified OIT-026 production contract verified")
        print("[OK] Certified OIT-026 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_026_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-026 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_activated_output_display_session_gate import *"
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
                f"OIT-027 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-026 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-027 production module installed")
        print("[PASS] OIT-027 standalone test installed")
        print("[PASS] Activated-output display session certified")
        print("[PASS] Exact terminal output preservation certified")
        print("[PASS] Interactive read-only display boundary prepared")
        print("[PASS] Publication and action authorization remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-027 TERMINAL ACTIVATED OUTPUT DISPLAY SESSION GATE INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
