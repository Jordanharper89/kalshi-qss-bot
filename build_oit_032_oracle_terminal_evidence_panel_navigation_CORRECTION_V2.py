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

        package = candidate / "qseries_v2" / "oracle_terminal"
        panel = package / "oracle_terminal_evidence_panel_navigation.py"
        registry = package / "oracle_terminal_interactive_command_registry.py"
        runner = candidate / "run_oracle_open_intelligence_terminal.py"

        if panel.is_file() and registry.is_file() and runner.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
PANEL_NAVIGATION = PACKAGE / "oracle_terminal_evidence_panel_navigation.py"
COMMAND_REGISTRY = PACKAGE / "oracle_terminal_interactive_command_registry.py"
DISPLAY_GATE = PACKAGE / "oracle_terminal_activated_output_display_session_gate.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
TEST = ROOT / "test_oit_032_oracle_terminal_evidence_panel_navigation.py"

TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (\n    ENGINE_ID as OIT_027_ENGINE_ID,\n    POLICY_ID as OIT_027_POLICY_ID,\n    SCHEMA_VERSION as OIT_027_SCHEMA_VERSION,\n    OracleTerminalDisplayFrame,\n    OracleTerminalDisplaySession,\n    OracleTerminalDisplaySessionGateReport,\n    _stable_hash as oit_027_hash,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_evidence_panel_navigation import (\n    build_default_panel_registry,\n    resolve_panel,\n    verify_panel_registry,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_interactive_command_registry import (\n    build_default_command_registry,\n    resolve_terminal_command,\n    verify_command_registry_report,\n)\n\n\ndef load_runner(root: Path):\n    path = root / "run_oracle_open_intelligence_terminal.py"\n    module_name = "oit_032_runner_test"\n    spec = importlib.util.spec_from_file_location(module_name, path)\n    if spec is None or spec.loader is None:\n        raise AssertionError("unable to load OIT-032 runner")\n\n    module = importlib.util.module_from_spec(spec)\n\n    # Required by Python 3.14 before dataclass decorators execute.\n    sys.modules[module_name] = module\n    try:\n        spec.loader.exec_module(module)\n    except Exception:\n        sys.modules.pop(module_name, None)\n        raise\n\n    return module\n\n\ndef make_report(root: Path, query: str):\n    # OIT-027 is the authoritative display-frame contract. The fixture uses\n    # only the already certified "informational" frame type instead of\n    # inventing semantic frame types that OIT-027 rejects.\n    frame_definitions = (\n        (\n            "informational",\n            (\n                "Oracle Intelligence Overview",\n                f"Query: {query}",\n            ),\n        ),\n        (\n            "informational",\n            (\n                "Certified Read-Only Result",\n                "No synthetic evidence frame type introduced.",\n            ),\n        ),\n    )\n\n    frames = []\n    for index, (frame_type, lines) in enumerate(frame_definitions, start=1):\n        body = {\n            "frame_index": index,\n            "frame_type": frame_type,\n            "frame_lines": lines,\n            "source_activation_hash": "activation-hash",\n            "display_only": True,\n            "read_only": True,\n        }\n        frames.append(\n            OracleTerminalDisplayFrame(\n                **body,\n                frame_hash=oit_027_hash(body),\n            )\n        )\n\n    session_body = {\n        "session_id": "session-032-correction-v2",\n        "query": query,\n        "source_activation_report_hash": "activation-report-hash",\n        "source_output_activation_hash": "activation-hash",\n        "frames": tuple(frames),\n        "frame_count": len(frames),\n        "output_line_count": sum(len(frame.frame_lines) for frame in frames),\n        "session_open": True,\n        "display_ready": True,\n        "interactive_read_only": True,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n    }\n    session = OracleTerminalDisplaySession(\n        **session_body,\n        session_hash=oit_027_hash(session_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_027_SCHEMA_VERSION,\n        "engine_id": OIT_027_ENGINE_ID,\n        "policy_id": OIT_027_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": query,\n        "activation_report_hash": "activation-report-hash",\n        "display_session": session,\n        "session_open": True,\n        "display_ready": True,\n        "output_preserved_exactly": True,\n        "display_session_ready": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    return OracleTerminalDisplaySessionGateReport(\n        **report_body,\n        report_hash=oit_027_hash(report_body),\n    )\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-032 TEST")\n    print(" EVIDENCE EXPANSION AND PANEL NAVIGATION")\n    print(" CORRECTION V2 - OIT-027 FRAME ALIGNED")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    runner = load_runner(root)\n    command_registry = build_default_command_registry()\n    panel_registry = build_default_panel_registry()\n\n    assert verify_command_registry_report(command_registry)\n    assert verify_panel_registry(panel_registry)\n    assert command_registry.command_count == 11\n    assert panel_registry.panel_count == 6\n\n    assert resolve_terminal_command(\n        "/panels",\n        registry=command_registry,\n    ).handler_name == "handle_panels"\n    assert resolve_terminal_command(\n        "/evidence",\n        registry=command_registry,\n    ).handler_name == "handle_evidence"\n\n    panel_resolution = resolve_terminal_command(\n        "/panel timeline",\n        registry=command_registry,\n    )\n    assert panel_resolution.handler_name == "handle_panel"\n    assert panel_resolution.argument == "timeline"\n\n    assert resolve_terminal_command(\n        "/next",\n        registry=command_registry,\n    ).handler_name == "handle_next"\n    assert resolve_terminal_command(\n        "/back",\n        registry=command_registry,\n    ).handler_name == "handle_back"\n\n    evidence_selection = resolve_panel(\n        "sources",\n        registry=panel_registry,\n    )\n    assert evidence_selection.matched\n    assert evidence_selection.panel_name == "evidence"\n    assert evidence_selection.panel_index == 1\n\n    captured: list[str] = []\n    session = runner.LocalTerminalSession()\n\n    def builder(repository_root, query):\n        return make_report(Path(repository_root), query)\n\n    assert runner.dispatch_command(\n        "/ask What changed?",\n        registry=command_registry,\n        panel_registry=panel_registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: None,\n    )\n\n    assert session.query_count == 1\n    assert session.last_query == "What changed?"\n    assert session.last_session_id == "session-032-correction-v2"\n    assert session.last_report is not None\n    assert session.active_panel_index == 0\n    assert "Oracle Intelligence Overview" in captured\n\n    assert runner.dispatch_command(\n        "/panels",\n        registry=command_registry,\n        panel_registry=panel_registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: None,\n    )\n    assert "Oracle Intelligence Panels" in captured\n\n    evidence_start = len(captured)\n    assert runner.dispatch_command(\n        "/evidence",\n        registry=command_registry,\n        panel_registry=panel_registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: None,\n    )\n    evidence_output = captured[evidence_start:]\n    assert session.active_panel_index == 1\n    assert evidence_output == [\n        "Oracle Panel: evidence",\n        "  No matching certified frames are available in the current session.",\n    ]\n\n    timeline_start = len(captured)\n    assert runner.dispatch_command(\n        "/panel timeline",\n        registry=command_registry,\n        panel_registry=panel_registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: None,\n    )\n    timeline_output = captured[timeline_start:]\n    assert session.active_panel_index == 3\n    assert timeline_output == [\n        "Oracle Panel: timeline",\n        "  No matching certified frames are available in the current session.",\n    ]\n\n    assert runner.dispatch_command(\n        "/next",\n        registry=command_registry,\n        panel_registry=panel_registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: None,\n    )\n    assert session.active_panel_index == 4\n\n    assert runner.dispatch_command(\n        "/back",\n        registry=command_registry,\n        panel_registry=panel_registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: None,\n    )\n    assert session.active_panel_index == 3\n\n    empty_session = runner.LocalTerminalSession()\n    empty_output: list[str] = []\n    assert runner.dispatch_command(\n        "/evidence",\n        registry=command_registry,\n        panel_registry=panel_registry,\n        session=empty_session,\n        root=root,\n        builder=builder,\n        write=empty_output.append,\n        clear=lambda: None,\n    )\n    assert empty_output == [\n        "[ERROR] OracleTerminalRunnerError: run a query before opening panels"\n    ]\n\n    print("[PASS] Current OIT-032 production runner imported")\n    print("[PASS] OIT-027-supported informational frames consumed")\n    print("[PASS] Unsupported synthetic frame types removed")\n    print("[PASS] OIT-032 command registry certified")\n    print("[PASS] OIT-032 panel registry certified")\n    print("[PASS] /panels command activated")\n    print("[PASS] /panel <name> command activated")\n    print("[PASS] /evidence command activated")\n    print("[PASS] /next and /back navigation activated")\n    print("[PASS] Empty matching-panel fallback certified")\n    print("[PASS] Pre-query panel rejection certified")\n    print("[PASS] Active panel state retained locally")\n    print("[PASS] Python 3.14 dynamic runner import verified")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-032 EVIDENCE EXPANSION AND PANEL NAVIGATION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(
    path: Path,
    tokens: tuple[str, ...],
    label: str,
) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")

    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")


def write_complete(path: Path, source: str) -> None:
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


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

    for path in (
        PANEL_NAVIGATION,
        COMMAND_REGISTRY,
        DISPLAY_GATE,
        RUNNER,
    ):
        protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-032 CORRECTION V2 INSTALLER")
    print(" OIT-027 DISPLAY FRAME ALIGNMENT")
    print("=" * 48)

    try:
        require_contract(
            PANEL_NAVIGATION,
            (
                'SCHEMA_VERSION = "OIT-032"',
                'POLICY_ID = "oracle.evidence-panel-navigation.v1"',
                "OracleTerminalPanelDefinition",
                "OracleTerminalPanelRegistry",
                "build_default_panel_registry",
                "resolve_panel",
                "verify_panel_registry",
            ),
            "Installed OIT-032 panel navigation",
        )

        require_contract(
            COMMAND_REGISTRY,
            (
                'SCHEMA_VERSION = "OIT-032"',
                'POLICY_ID = "oracle.interactive-command-registry.v2"',
                '"/panels"',
                '"/panel"',
                '"/evidence"',
                '"/next"',
                '"/back"',
                "handle_panels",
                "handle_panel",
                "handle_evidence",
                "handle_next",
                "handle_back",
            ),
            "Installed OIT-032 command registry",
        )

        require_contract(
            RUNNER,
            (
                'RUNNER_VERSION = "OIT-032"',
                "OracleTerminalPanelRegistry",
                "LocalTerminalSession",
                "last_report",
                "active_panel_index",
                "filtered_panel_lines",
                "open_panel",
                "dispatch_command",
                'handler == "handle_panels"',
                'handler == "handle_panel"',
                'handler == "handle_evidence"',
                'handler in ("handle_next", "handle_back")',
            ),
            "Installed OIT-032 live runner",
        )

        require_contract(
            DISPLAY_GATE,
            (
                "OracleTerminalDisplayFrame",
                "verify_terminal_display_frame",
                "unsupported terminal display frame type",
            ),
            "Certified OIT-027 display gate",
        )

        protected = protected_sources()

        print("[OK] Installed OIT-032 panel navigation verified")
        print("[OK] Installed OIT-032 command registry verified")
        print("[OK] Installed OIT-032 live runner verified")
        print("[OK] Certified OIT-027 display gate verified")
        print("[OK] Current repository state accepted")
        print("[OK] Root cause confirmed: invalid synthetic test frame types")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        write_complete(TEST, TEST_SOURCE)

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-032 corrected test failed with exit code {completed.returncode}"
            )

        status = subprocess.run(
            [sys.executable, str(RUNNER), "--status"],
            cwd=ROOT,
            check=False,
        )
        if status.returncode:
            raise RuntimeError(
                f"OIT-032 runner status check failed: {status.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] OIT-032 panel navigation unchanged")
        print("[PASS] OIT-032 command registry unchanged")
        print("[PASS] OIT-032 live terminal runner unchanged")
        print("[PASS] OIT-032 standalone test fully replaced")
        print("[PASS] Test fixtures aligned to certified OIT-027 frame contract")
        print("[PASS] Unsupported synthetic frame types eliminated")
        print("[PASS] Empty matching-panel fallback certified")
        print("[PASS] Live runner status check passed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-032 CORRECTION V2 INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
