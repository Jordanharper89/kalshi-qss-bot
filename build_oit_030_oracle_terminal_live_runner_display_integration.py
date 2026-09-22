from __future__ import annotations

import ast
import hashlib
import shutil
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
            / "oracle_terminal_live_runner_display_integration_certification.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_030 = PACKAGE / "oracle_terminal_live_runner_display_integration_certification.py"
OIT_030_TEST = ROOT / "test_oit_030_oracle_terminal_live_runner_display_integration.py"
REGISTRY = PACKAGE / "oracle_terminal_interactive_command_registry.py"
TEST = ROOT / "test_oit_031_oracle_terminal_interactive_command_registry.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
BACKUP = ROOT / "run_oracle_open_intelligence_terminal_PRE_OIT_031.py"

REGISTRY_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nSCHEMA_VERSION = "OIT-031"\nENGINE_ID = "OIT-031"\nPOLICY_ID = "oracle.interactive-command-registry.v1"\n\n\nclass OracleTerminalCommandRegistryInvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalCommandDefinition:\n    command: str\n    aliases: tuple[str, ...]\n    handler_name: str\n    summary: str\n    accepts_argument: bool\n    exits_terminal: bool\n    clears_terminal: bool\n    read_only: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    definition_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalCommandResolution:\n    raw_input: str\n    normalized_input: str\n    matched: bool\n    command: str | None\n    handler_name: str | None\n    argument: str\n    exits_terminal: bool\n    clears_terminal: bool\n    read_only: bool\n    resolution_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalCommandRegistryReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    commands: tuple[OracleTerminalCommandDefinition, ...]\n    command_count: int\n    aliases_unique: bool\n    registry_ready: bool\n    read_only: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _definition(\n    command: str,\n    aliases: tuple[str, ...],\n    handler_name: str,\n    summary: str,\n    *,\n    accepts_argument: bool = False,\n    exits_terminal: bool = False,\n    clears_terminal: bool = False,\n) -> OracleTerminalCommandDefinition:\n    canonical_command = command.strip().lower()\n    canonical_aliases = tuple(\n        sorted({alias.strip().lower() for alias in aliases if alias.strip()})\n    )\n    body = {\n        "command": canonical_command,\n        "aliases": canonical_aliases,\n        "handler_name": handler_name,\n        "summary": summary,\n        "accepts_argument": accepts_argument,\n        "exits_terminal": exits_terminal,\n        "clears_terminal": clears_terminal,\n        "read_only": True,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n    }\n    definition = OracleTerminalCommandDefinition(\n        **body,\n        definition_hash=_stable_hash(body),\n    )\n    verify_command_definition(definition)\n    return definition\n\n\ndef build_default_command_registry() -> OracleTerminalCommandRegistryReport:\n    commands = (\n        _definition(\n            "/help",\n            ("help", "?"),\n            "handle_help",\n            "Show available terminal commands.",\n        ),\n        _definition(\n            "/status",\n            ("status",),\n            "handle_status",\n            "Show certified read-only terminal status.",\n        ),\n        _definition(\n            "/ask",\n            ("ask",),\n            "handle_ask",\n            "Submit a natural-language intelligence question.",\n            accepts_argument=True,\n        ),\n        _definition(\n            "/session",\n            ("session",),\n            "handle_session",\n            "Show the current local read-only session state.",\n        ),\n        _definition(\n            "/clear",\n            ("clear",),\n            "handle_clear",\n            "Clear the visible terminal screen.",\n            clears_terminal=True,\n        ),\n        _definition(\n            "/quit",\n            ("/exit", "quit", "exit"),\n            "handle_quit",\n            "Close the Oracle terminal.",\n            exits_terminal=True,\n        ),\n    )\n\n    tokens: list[str] = []\n    for item in commands:\n        tokens.append(item.command)\n        tokens.extend(item.aliases)\n    aliases_unique = len(tokens) == len(set(tokens))\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "commands": commands,\n        "command_count": len(commands),\n        "aliases_unique": aliases_unique,\n        "registry_ready": bool(commands and aliases_unique),\n        "read_only": True,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n    }\n    report = OracleTerminalCommandRegistryReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_command_registry_report(report)\n    return report\n\n\ndef verify_command_definition(\n    definition: OracleTerminalCommandDefinition,\n) -> bool:\n    body = asdict(definition)\n    supplied = body.pop("definition_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalCommandRegistryInvariantError(\n            "command definition hash mismatch"\n        )\n    if not definition.command.startswith("/"):\n        raise OracleTerminalCommandRegistryInvariantError(\n            "canonical command must start with slash"\n        )\n    if not definition.handler_name.startswith("handle_"):\n        raise OracleTerminalCommandRegistryInvariantError(\n            "command handler identity invalid"\n        )\n    if not definition.read_only:\n        raise OracleTerminalCommandRegistryInvariantError(\n            "command definition is not read-only"\n        )\n    if (\n        definition.publication_allowed\n        or definition.action_authorization_allowed\n        or definition.qseries_execution_allowed\n    ):\n        raise OracleTerminalCommandRegistryInvariantError(\n            "forbidden command capability enabled"\n        )\n    return True\n\n\ndef verify_command_registry_report(\n    report: OracleTerminalCommandRegistryReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalCommandRegistryInvariantError(\n            "command registry report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalCommandRegistryInvariantError("schema mismatch")\n    if report.policy_id != POLICY_ID:\n        raise OracleTerminalCommandRegistryInvariantError("policy mismatch")\n    if report.command_count != len(report.commands):\n        raise OracleTerminalCommandRegistryInvariantError(\n            "command count mismatch"\n        )\n    for definition in report.commands:\n        verify_command_definition(definition)\n    if not report.aliases_unique:\n        raise OracleTerminalCommandRegistryInvariantError(\n            "command aliases overlap"\n        )\n    if report.registry_ready != bool(report.commands and report.aliases_unique):\n        raise OracleTerminalCommandRegistryInvariantError(\n            "registry readiness mismatch"\n        )\n    if not report.read_only:\n        raise OracleTerminalCommandRegistryInvariantError(\n            "command registry is not read-only"\n        )\n    if (\n        report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleTerminalCommandRegistryInvariantError(\n            "forbidden registry capability enabled"\n        )\n    return True\n\n\ndef resolve_terminal_command(\n    raw_input: str,\n    *,\n    registry: OracleTerminalCommandRegistryReport | None = None,\n) -> OracleTerminalCommandResolution:\n    active_registry = registry or build_default_command_registry()\n    verify_command_registry_report(active_registry)\n\n    normalized = " ".join(str(raw_input).strip().split())\n    token = normalized\n    argument = ""\n    if " " in normalized:\n        token, argument = normalized.split(" ", 1)\n    lowered = token.lower()\n\n    matched_definition = None\n    for definition in active_registry.commands:\n        if lowered == definition.command or lowered in definition.aliases:\n            matched_definition = definition\n            break\n\n    body = {\n        "raw_input": str(raw_input),\n        "normalized_input": normalized,\n        "matched": matched_definition is not None,\n        "command": (\n            matched_definition.command if matched_definition is not None else None\n        ),\n        "handler_name": (\n            matched_definition.handler_name\n            if matched_definition is not None\n            else None\n        ),\n        "argument": argument if matched_definition is not None else normalized,\n        "exits_terminal": bool(\n            matched_definition and matched_definition.exits_terminal\n        ),\n        "clears_terminal": bool(\n            matched_definition and matched_definition.clears_terminal\n        ),\n        "read_only": True,\n    }\n    resolution = OracleTerminalCommandResolution(\n        **body,\n        resolution_hash=_stable_hash(body),\n    )\n    verify_command_resolution(resolution)\n    return resolution\n\n\ndef verify_command_resolution(\n    resolution: OracleTerminalCommandResolution,\n) -> bool:\n    body = asdict(resolution)\n    supplied = body.pop("resolution_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalCommandRegistryInvariantError(\n            "command resolution hash mismatch"\n        )\n    if not resolution.read_only:\n        raise OracleTerminalCommandRegistryInvariantError(\n            "command resolution is not read-only"\n        )\n    if resolution.matched and (\n        not resolution.command or not resolution.handler_name\n    ):\n        raise OracleTerminalCommandRegistryInvariantError(\n            "matched command resolution incomplete"\n        )\n    if not resolution.matched and (\n        resolution.command is not None\n        or resolution.handler_name is not None\n        or resolution.exits_terminal\n        or resolution.clears_terminal\n    ):\n        raise OracleTerminalCommandRegistryInvariantError(\n            "unmatched input resolved to command behavior"\n        )\n    return True\n'
RUNNER_SOURCE = '\nfrom __future__ import annotations\n\nimport argparse\nimport os\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Callable, Iterable, Sequence\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (\n    OracleTerminalDisplayFrame,\n    OracleTerminalDisplaySessionGateReport,\n    build_terminal_display_session_gate_report,\n    verify_terminal_display_session_gate_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_interactive_command_registry import (\n    OracleTerminalCommandRegistryReport,\n    build_default_command_registry,\n    resolve_terminal_command,\n    verify_command_registry_report,\n)\n\nRUNNER_VERSION = "OIT-031"\nPROMPT = "oracle> "\n\n\nclass OracleTerminalRunnerError(RuntimeError):\n    pass\n\n\n@dataclass\nclass LocalTerminalSession:\n    query_count: int = 0\n    last_query: str = ""\n    last_session_id: str = ""\n\n\ndef repository_root() -> Path:\n    return Path(__file__).resolve().parent\n\n\ndef normalize_query(value: str) -> str:\n    query = " ".join(str(value).strip().split())\n    if not query:\n        raise OracleTerminalRunnerError("query cannot be empty")\n    return query\n\n\ndef render_frame_lines(frame: OracleTerminalDisplayFrame) -> tuple[str, ...]:\n    if not frame.read_only or not frame.display_only:\n        raise OracleTerminalRunnerError(\n            "refusing to render a non-read-only display frame"\n        )\n    if not frame.frame_lines:\n        raise OracleTerminalRunnerError(\n            "refusing to render an empty display frame"\n        )\n    return tuple(frame.frame_lines)\n\n\ndef flatten_display_session(\n    report: OracleTerminalDisplaySessionGateReport,\n) -> tuple[str, ...]:\n    verify_terminal_display_session_gate_report(report)\n    if not report.display_session_ready:\n        raise OracleTerminalRunnerError(\n            report.failure_reason or "display session is not ready"\n        )\n    if not report.read_only:\n        raise OracleTerminalRunnerError(\n            "display-session report is not read-only"\n        )\n    if (\n        report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleTerminalRunnerError(\n            "forbidden capability exposed by display session"\n        )\n\n    lines: list[str] = []\n    for index, frame in enumerate(report.display_session.frames):\n        if index:\n            lines.append("")\n        lines.extend(render_frame_lines(frame))\n    return tuple(lines)\n\n\ndef print_lines(\n    lines: Iterable[str],\n    *,\n    write: Callable[[str], None] = print,\n) -> None:\n    for line in lines:\n        write(str(line))\n\n\ndef execute_query(\n    query: str,\n    *,\n    root: Path | None = None,\n    builder: Callable[..., OracleTerminalDisplaySessionGateReport] = (\n        build_terminal_display_session_gate_report\n    ),\n) -> OracleTerminalDisplaySessionGateReport:\n    canonical_query = normalize_query(query)\n    active_root = (root or repository_root()).resolve()\n    report = builder(active_root, canonical_query)\n    verify_terminal_display_session_gate_report(report)\n    if report.query != canonical_query:\n        raise OracleTerminalRunnerError(\n            "display-session query lineage mismatch"\n        )\n    return report\n\n\ndef display_query(\n    query: str,\n    *,\n    session: LocalTerminalSession | None = None,\n    root: Path | None = None,\n    builder: Callable[..., OracleTerminalDisplaySessionGateReport] = (\n        build_terminal_display_session_gate_report\n    ),\n    write: Callable[[str], None] = print,\n) -> OracleTerminalDisplaySessionGateReport:\n    report = execute_query(query, root=root, builder=builder)\n    print_lines(flatten_display_session(report), write=write)\n    if session is not None:\n        session.query_count += 1\n        session.last_query = report.query\n        session.last_session_id = report.display_session.session_id\n    return report\n\n\ndef help_lines(\n    registry: OracleTerminalCommandRegistryReport,\n) -> tuple[str, ...]:\n    verify_command_registry_report(registry)\n    lines = [\n        "Oracle Open Intelligence Terminal",\n        f"Runner certification: {RUNNER_VERSION}",\n        "",\n        "Enter a natural-language intelligence question.",\n        "",\n        "Commands:",\n    ]\n    for definition in registry.commands:\n        suffix = " <question>" if definition.accepts_argument else ""\n        lines.append(\n            f"  {definition.command}{suffix:<12} {definition.summary}"\n        )\n    return tuple(lines)\n\n\ndef status_lines() -> tuple[str, ...]:\n    return (\n        "Oracle Terminal Status",\n        f"  runner: {RUNNER_VERSION}",\n        "  mode: interactive read-only",\n        "  command registry: OIT-031 certified",\n        "  display boundary: OIT-027 certified session",\n        "  publication: disabled",\n        "  action authorization: disabled",\n        "  Q Series execution: disabled",\n    )\n\n\ndef session_lines(session: LocalTerminalSession) -> tuple[str, ...]:\n    return (\n        "Oracle Terminal Session",\n        f"  queries: {session.query_count}",\n        f"  last query: {session.last_query or \'(none)\'}",\n        f"  last display session: {session.last_session_id or \'(none)\'}",\n        "  persistence: local process only",\n        "  mode: read-only",\n    )\n\n\ndef clear_terminal() -> None:\n    os.system("cls" if os.name == "nt" else "clear")\n\n\ndef dispatch_command(\n    raw_input: str,\n    *,\n    registry: OracleTerminalCommandRegistryReport,\n    session: LocalTerminalSession,\n    root: Path | None = None,\n    builder: Callable[..., OracleTerminalDisplaySessionGateReport] = (\n        build_terminal_display_session_gate_report\n    ),\n    write: Callable[[str], None] = print,\n    clear: Callable[[], None] = clear_terminal,\n) -> bool:\n    resolution = resolve_terminal_command(raw_input, registry=registry)\n\n    if not resolution.matched:\n        display_query(\n            resolution.argument,\n            session=session,\n            root=root,\n            builder=builder,\n            write=write,\n        )\n        return True\n\n    if resolution.handler_name == "handle_help":\n        print_lines(help_lines(registry), write=write)\n        return True\n    if resolution.handler_name == "handle_status":\n        print_lines(status_lines(), write=write)\n        return True\n    if resolution.handler_name == "handle_session":\n        print_lines(session_lines(session), write=write)\n        return True\n    if resolution.handler_name == "handle_clear":\n        clear()\n        return True\n    if resolution.handler_name == "handle_quit":\n        write("Oracle Terminal closed.")\n        return False\n    if resolution.handler_name == "handle_ask":\n        if not resolution.argument:\n            write("[ERROR] OracleTerminalRunnerError: /ask requires a question")\n            return True\n        display_query(\n            resolution.argument,\n            session=session,\n            root=root,\n            builder=builder,\n            write=write,\n        )\n        return True\n\n    raise OracleTerminalRunnerError(\n        f"unsupported command handler: {resolution.handler_name}"\n    )\n\n\ndef run_interactive(\n    *,\n    root: Path | None = None,\n    builder: Callable[..., OracleTerminalDisplaySessionGateReport] = (\n        build_terminal_display_session_gate_report\n    ),\n    read: Callable[[str], str] = input,\n    write: Callable[[str], None] = print,\n    clear: Callable[[], None] = clear_terminal,\n) -> int:\n    registry = build_default_command_registry()\n    verify_command_registry_report(registry)\n    session = LocalTerminalSession()\n    print_lines(help_lines(registry), write=write)\n\n    while True:\n        try:\n            raw = read(PROMPT)\n        except (EOFError, KeyboardInterrupt):\n            write("")\n            write("Oracle Terminal closed.")\n            return 0\n\n        if not raw.strip():\n            continue\n\n        try:\n            keep_running = dispatch_command(\n                raw,\n                registry=registry,\n                session=session,\n                root=root,\n                builder=builder,\n                write=write,\n                clear=clear,\n            )\n        except Exception as exc:\n            write(f"[ERROR] {type(exc).__name__}: {exc}")\n            continue\n\n        if not keep_running:\n            return 0\n\n\ndef build_argument_parser() -> argparse.ArgumentParser:\n    parser = argparse.ArgumentParser(\n        description="Oracle Open Intelligence Terminal",\n    )\n    parser.add_argument(\n        "query",\n        nargs="*",\n        help="optional one-shot natural-language query",\n    )\n    parser.add_argument(\n        "--status",\n        action="store_true",\n        help="show read-only terminal status and exit",\n    )\n    return parser\n\n\ndef main(argv: Sequence[str] | None = None) -> int:\n    parser = build_argument_parser()\n    arguments = parser.parse_args(argv)\n\n    if arguments.status:\n        print_lines(status_lines())\n        return 0\n\n    if arguments.query:\n        try:\n            display_query(" ".join(arguments.query))\n            return 0\n        except Exception as exc:\n            print(f"[ERROR] {type(exc).__name__}: {exc}")\n            return 1\n\n    return run_interactive()\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (\n    ENGINE_ID as OIT_027_ENGINE_ID,\n    POLICY_ID as OIT_027_POLICY_ID,\n    SCHEMA_VERSION as OIT_027_SCHEMA_VERSION,\n    OracleTerminalDisplayFrame,\n    OracleTerminalDisplaySession,\n    OracleTerminalDisplaySessionGateReport,\n    _stable_hash as oit_027_hash,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_interactive_command_registry import (\n    OracleTerminalCommandRegistryInvariantError,\n    build_default_command_registry,\n    resolve_terminal_command,\n    verify_command_registry_report,\n)\n\n\ndef load_runner(root: Path):\n    path = root / "run_oracle_open_intelligence_terminal.py"\n    spec = importlib.util.spec_from_file_location("oit_031_runner_test", path)\n    if spec is None or spec.loader is None:\n        raise AssertionError("unable to load runner")\n    module = importlib.util.module_from_spec(spec)\n    spec.loader.exec_module(module)\n    return module\n\n\ndef display_report(root: Path, query: str):\n    frame_body = {\n        "frame_index": 1,\n        "frame_type": "informational",\n        "frame_lines": ("[i] Query", f"  {query}"),\n        "source_activation_hash": "activation-hash",\n        "display_only": True,\n        "read_only": True,\n    }\n    frame = OracleTerminalDisplayFrame(\n        **frame_body,\n        frame_hash=oit_027_hash(frame_body),\n    )\n    session_body = {\n        "session_id": "session-031",\n        "query": query,\n        "source_activation_report_hash": "activation-report-hash",\n        "source_output_activation_hash": "activation-hash",\n        "frames": (frame,),\n        "frame_count": 1,\n        "output_line_count": 2,\n        "session_open": True,\n        "display_ready": True,\n        "interactive_read_only": True,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n    }\n    session = OracleTerminalDisplaySession(\n        **session_body,\n        session_hash=oit_027_hash(session_body),\n    )\n    report_body = {\n        "schema_version": OIT_027_SCHEMA_VERSION,\n        "engine_id": OIT_027_ENGINE_ID,\n        "policy_id": OIT_027_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": query,\n        "activation_report_hash": "activation-report-hash",\n        "display_session": session,\n        "session_open": True,\n        "display_ready": True,\n        "output_preserved_exactly": True,\n        "display_session_ready": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    return OracleTerminalDisplaySessionGateReport(\n        **report_body,\n        report_hash=oit_027_hash(report_body),\n    )\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-031 TEST")\n    print(" INTERACTIVE COMMAND REGISTRY")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    module = load_runner(root)\n    registry = build_default_command_registry()\n\n    assert registry.registry_ready\n    assert registry.command_count == 6\n    assert verify_command_registry_report(registry)\n\n    assert resolve_terminal_command("/help", registry=registry).handler_name == "handle_help"\n    assert resolve_terminal_command("status", registry=registry).handler_name == "handle_status"\n    ask = resolve_terminal_command("/ask What changed?", registry=registry)\n    assert ask.handler_name == "handle_ask"\n    assert ask.argument == "What changed?"\n    plain = resolve_terminal_command("What is strongest?", registry=registry)\n    assert not plain.matched\n    assert plain.argument == "What is strongest?"\n\n    captured = []\n    cleared = []\n    session = module.LocalTerminalSession()\n\n    def builder(repository_root, query):\n        return display_report(Path(repository_root), query)\n\n    assert module.dispatch_command(\n        "/status",\n        registry=registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: cleared.append(True),\n    )\n    assert module.dispatch_command(\n        "/ask What changed?",\n        registry=registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: cleared.append(True),\n    )\n    assert session.query_count == 1\n    assert session.last_query == "What changed?"\n    assert session.last_session_id == "session-031"\n\n    assert module.dispatch_command(\n        "/session",\n        registry=registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: cleared.append(True),\n    )\n    assert module.dispatch_command(\n        "/clear",\n        registry=registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: cleared.append(True),\n    )\n    assert cleared == [True]\n    assert not module.dispatch_command(\n        "/quit",\n        registry=registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: cleared.append(True),\n    )\n\n    tampered = replace(registry, aliases_unique=False)\n    try:\n        verify_command_registry_report(tampered)\n    except OracleTerminalCommandRegistryInvariantError:\n        pass\n    else:\n        raise AssertionError("tampered command registry accepted")\n\n    print("[PASS] OIT-031 command registry materialized")\n    print("[PASS] Command aliases unique and deterministic")\n    print("[PASS] /help command resolved")\n    print("[PASS] /status command resolved")\n    print("[PASS] /ask command accepted natural-language argument")\n    print("[PASS] Plain natural-language input routed as query")\n    print("[PASS] /session local read-only state activated")\n    print("[PASS] /clear command activated")\n    print("[PASS] /quit command activated")\n    print("[PASS] Live OIT-030 runner upgraded to registry dispatch")\n    print("[PASS] Tampered command registry rejected")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-031 INTERACTIVE COMMAND REGISTRY PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_030, OIT_030_TEST):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-031 INSTALLER")
    print(" INTERACTIVE COMMAND REGISTRY")
    print("=" * 48)
    try:
        require_contract(
            OIT_030,
            (
                'SCHEMA_VERSION = "OIT-030"',
                'POLICY_ID = "oracle.live-runner-display-integration-certification.v1"',
                "OracleTerminalLiveRunnerIntegrationCertification",
                "certify_live_runner_integration",
                "verify_live_runner_integration_certification",
                "runner_integration_ready",
            ),
            "Certified OIT-030 production",
        )
        require_contract(
            OIT_030_TEST,
            (
                "OIT-030 TEST",
                "LIVE RUNNER DISPLAY INTEGRATION",
                "OIT-030 LIVE RUNNER DISPLAY INTEGRATION PASS",
            ),
            "Certified OIT-030 standalone test",
        )
        require_contract(
            RUNNER,
            (
                'RUNNER_VERSION = "OIT-030"',
                "build_terminal_display_session_gate_report",
                "run_interactive",
                "display_query",
                '"/help"',
                '"/status"',
                '"/quit"',
            ),
            "Live OIT-030 terminal runner",
        )

        protected = protected_sources()
        print("[OK] Certified OIT-030 production contract verified")
        print("[OK] Certified OIT-030 standalone test verified")
        print("[OK] Live OIT-030 terminal runner verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_030_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-030 certification failed with exit code {upstream.returncode}"
            )

        if not BACKUP.exists():
            shutil.copy2(RUNNER, BACKUP)
            print(f"[OK] PRE-OIT-031 RUNNER BACKUP: {BACKUP.resolve()}")
        else:
            print(f"[OK] PRE-OIT-031 RUNNER BACKUP PRESENT: {BACKUP.resolve()}")

        write_complete(REGISTRY, REGISTRY_SOURCE)
        write_complete(RUNNER, RUNNER_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_terminal_interactive_command_registry import *"
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
                f"OIT-031 test failed with exit code {completed.returncode}"
            )

        status = subprocess.run(
            [sys.executable, str(RUNNER), "--status"],
            cwd=ROOT,
            check=False,
        )
        if status.returncode:
            raise RuntimeError(
                f"OIT-031 runner status check failed: {status.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-030 production and test unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-031 command registry installed")
        print("[PASS] OIT-031 standalone test installed")
        print("[PASS] Live runner upgraded to deterministic registry dispatch")
        print("[PASS] /help, /status, /ask, /session, /clear, and /quit activated")
        print("[PASS] Plain natural-language questions remain supported")
        print("[PASS] Local session state remains process-only and read-only")
        print("[PASS] Previous runner preserved in PRE-OIT-031 backup")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-031 INTERACTIVE COMMAND REGISTRY INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
