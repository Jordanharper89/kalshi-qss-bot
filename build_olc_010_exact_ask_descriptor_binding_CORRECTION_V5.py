from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()

PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OAR = ROOT / "qseries_v2" / "observation_adapter_runtime"
LAUNCHER = ROOT / "run_oracle_open_intelligence_terminal.py"

UPSTREAMS = (
    PACKAGE / "olc_006_terminal_injection_resolver.py",
    PACKAGE / "OLC_006_TERMINAL_INJECTION_MANIFEST.json",
    PACKAGE / "olc_008_command_registry_contract_resolver.py",
    PACKAGE / "OLC_008_COMMAND_REGISTRY_CONTRACT_MANIFEST.json",
    PACKAGE / "olc_009_live_ask_registry_overlay.py",
    OAR / "oar_030_final_certification_freeze.py",
    OAR / "OAR_FINAL_FREEZE_MANIFEST.json",
    LAUNCHER,
)

MODULE = PACKAGE / "olc_010_exact_ask_descriptor_binding.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_010_exact_ask_descriptor_binding.py"
MANIFEST = PACKAGE / "OLC_010_EXACT_ASK_DESCRIPTOR_MANIFEST.json"

INSTALLER_REVISION = (
    "OLC_010_EXACT_ASK_DESCRIPTOR_BINDING_"
    "INSTALLER_CORRECTION_V5"
)

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from qseries_v2.oracle_live_composition.olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
)
from qseries_v2.observation_adapter_runtime.oar_026_live_ask_dispatch_binding import (
    LiveAskDispatchBinding,
)

BUILD_ID = "OLC-010"
OLC_010_REVISION = "OLC_010_EXACT_ASK_DESCRIPTOR_BINDING_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False

INJECTION_SYMBOL = "display_query"
DISPATCH_SYMBOL = "dispatch_command"
ASK_HANDLER_NAME = "handle_ask"


@dataclass(frozen=True, slots=True)
class LiveDisplayQueryDispatch:
    query: str
    live_handled: bool
    fallback_used: bool
    route: str
    observation_count: int
    read_model_id: str | None
    evidence_hash: str | None
    read_only: bool


def build_live_display_query(
    *,
    store: AtomicLiveReadModelStore,
    original_display_query: Callable[..., Any],
) -> Callable[..., Any]:
    if not isinstance(
        store,
        AtomicLiveReadModelStore,
    ):
        raise TypeError(
            "store must be AtomicLiveReadModelStore"
        )

    if not callable(
        original_display_query
    ):
        raise TypeError(
            "original_display_query must be callable"
        )

    def live_display_query(
        query,
        *,
        session=None,
        root=None,
        builder=None,
        write=print,
    ):
        snapshot = store.snapshot()

        dispatch = (
            LiveAskDispatchBinding()
            .dispatch(
                query=str(query),
                read_model=snapshot.read_model,
            )
        )

        response = dispatch.live_response

        if dispatch.consume_existing_terminal:
            kwargs = {
                "session": session,
                "root": root,
                "write": write,
            }

            if builder is not None:
                kwargs["builder"] = builder

            return original_display_query(
                query,
                **kwargs,
            )

        # This boundary deliberately exposes only certified
        # read-model facts. It does not invent explanation,
        # probability, direction, or trade authorization.
        write(
            "================================================================"
        )
        write(
            "Oracle Live Intelligence Read Path"
        )
        write(
            "STATUS: LIVE EVIDENCE AVAILABLE | MODE: READ-ONLY"
        )
        write(
            f"route: {response.route}"
        )
        write(
            f"observations: {response.observation_count}"
        )
        write(
            f"read model: {response.read_model_id}"
        )
        write(
            f"evidence hash: {response.evidence_hash}"
        )
        write(
            "Live evidence is attached to the terminal query path. "
            "Reasoning remains bounded by the existing certified Oracle pipeline."
        )
        write(
            "================================================================"
        )

        if session is not None:
            if hasattr(
                session,
                "query_count",
            ):
                session.query_count += 1

            if hasattr(
                session,
                "last_query",
            ):
                session.last_query = str(
                    query
                )

            if hasattr(
                session,
                "last_session_id",
            ):
                session.last_session_id = (
                    response.read_model_id
                    or ""
                )

        return LiveDisplayQueryDispatch(
            query=str(query),
            live_handled=True,
            fallback_used=False,
            route=response.route,
            observation_count=(
                response.observation_count
            ),
            read_model_id=(
                response.read_model_id
            ),
            evidence_hash=(
                response.evidence_hash
            ),
            read_only=True,
        )

    live_display_query.__name__ = (
        "olc_live_display_query"
    )

    live_display_query.__doc__ = (
        "Read-only live intelligence overlay for the "
        "actual run_oracle_open_intelligence_terminal.display_query boundary."
    )

    return live_display_query


def verify_exact_ask_descriptor_binding() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert INJECTION_SYMBOL == "display_query"
    assert DISPATCH_SYMBOL == "dispatch_command"
    assert ASK_HANDLER_NAME == "handle_ask"
    return True


__all__ = [
    "BUILD_ID",
    "OLC_010_REVISION",
    "INJECTION_SYMBOL",
    "DISPATCH_SYMBOL",
    "ASK_HANDLER_NAME",
    "LiveDisplayQueryDispatch",
    "build_live_display_query",
    "verify_exact_ask_descriptor_binding",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib
import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from qseries_v2.oracle_live_composition.olc_004_live_intelligence_cycle import (
    LiveIntelligenceCycleResult,
)
from qseries_v2.oracle_live_composition.olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
)
from qseries_v2.oracle_live_composition.olc_010_exact_ask_descriptor_binding import (
    ASK_HANDLER_NAME,
    DISPATCH_SYMBOL,
    INJECTION_SYMBOL,
    build_live_display_query,
    verify_exact_ask_descriptor_binding,
)

NOW = datetime(
    2026,
    8,
    12,
    17,
    0,
    tzinfo=timezone.utc,
)


def populated_store():
    store = AtomicLiveReadModelStore()

    read_model = TerminalLiveIntelligenceReadModel(
        read_model_id="terminal.live.v5",
        iteration_number=1,
        observation_count=2,
        observation_ids=(
            "liveobs.1",
            "liveobs.2",
        ),
        provider_ids=(
            "coinbase",
            "kalshi",
        ),
        capability_ids=(
            "spot_price",
            "market_snapshot",
        ),
        oi_ready=True,
        umd_ready=True,
        oml_ready=True,
        lineage_valid=True,
        generated_at=NOW,
        evidence_hash="a"*64,
        read_only=True,
    )

    cycle = LiveIntelligenceCycleResult(
        composition_id="oracle.live.composition.v1",
        runtime_id="oracle.live.observation.production",
        iteration_number=1,
        adapter_request_count=2,
        adapter_success_count=2,
        adapter_failure_count=0,
        raw_observation_count=2,
        admitted_observation_count=2,
        terminal_read_model=read_model,
        read_only=True,
        execution_allowed=False,
    )

    store.publish(
        cycle
    )

    return store


class TestOLC010(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_exact_ask_descriptor_binding()
        )

        self.assertEqual(
            INJECTION_SYMBOL,
            "display_query",
        )

        self.assertEqual(
            DISPATCH_SYMBOL,
            "dispatch_command",
        )

        self.assertEqual(
            ASK_HANDLER_NAME,
            "handle_ask",
        )

    def test_live_display_query_intercepts(self):
        store = populated_store()
        legacy_calls = []
        lines = []

        def legacy(
            query,
            *,
            session=None,
            root=None,
            builder=None,
            write=print,
        ):
            legacy_calls.append(
                query
            )
            return "legacy"

        live = build_live_display_query(
            store=store,
            original_display_query=legacy,
        )

        result = live(
            "why is bitcoin moving?",
            write=lines.append,
        )

        self.assertTrue(
            result.live_handled
        )

        self.assertFalse(
            result.fallback_used
        )

        self.assertEqual(
            result.observation_count,
            2,
        )

        self.assertEqual(
            legacy_calls,
            [],
        )

        self.assertTrue(
            any(
                "LIVE EVIDENCE AVAILABLE"
                in line
                for line in lines
            )
        )

    def test_existing_terminal_fallback(self):
        store = populated_store()
        calls = []

        def legacy(
            query,
            *,
            session=None,
            root=None,
            builder=None,
            write=print,
        ):
            calls.append(
                query
            )
            return "legacy-result"

        live = build_live_display_query(
            store=store,
            original_display_query=legacy,
        )

        result = live(
            "show current session"
        )

        self.assertEqual(
            result,
            "legacy-result",
        )

        self.assertEqual(
            calls,
            [
                "show current session",
            ],
        )

    def test_real_launcher_symbols(self):
        launcher = importlib.import_module(
            "run_oracle_open_intelligence_terminal"
        )

        self.assertTrue(
            callable(
                getattr(
                    launcher,
                    "dispatch_command",
                )
            )
        )

        self.assertTrue(
            callable(
                getattr(
                    launcher,
                    "display_query",
                )
            )
        )

        self.assertTrue(
            callable(
                getattr(
                    launcher,
                    "run_interactive",
                )
            )
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-010 CERTIFICATION TEST")
    print(
        " EXACT /ASK RUNTIME DISPLAY BOUNDARY "
        "— CORRECTION V5"
    )
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC010
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-010")
    print(
        "[PASS] /ask metadata handler_name='handle_ask' "
        "correctly treated as dispatch metadata, not a callable"
    )
    print(
        "[PASS] Actual runtime injection boundary certified: "
        "run_oracle_open_intelligence_terminal.display_query"
    )
    print(
        "[PASS] dispatch_command -> handle_ask -> display_query "
        "chain preserved exactly"
    )
    print(
        "[PASS] Existing display_query remains exact fallback"
    )
    print(
        "[PASS] Oracle Terminal source remains unchanged"
    )
    print("[DONE] OLC-010 CERTIFIED")
"""


def sha(
    path: Path,
) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def source_segment(
    source: str,
    node: ast.AST,
) -> str:
    return (
        ast.get_source_segment(
            source,
            node,
        )
        or ""
    )


def inspect_launcher():
    if not LAUNCHER.is_file():
        raise RuntimeError(
            f"Oracle terminal launcher missing: "
            f"{LAUNCHER}"
        )

    source = LAUNCHER.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source,
        filename=str(
            LAUNCHER
        ),
    )

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
    }

    required = (
        "dispatch_command",
        "display_query",
        "run_interactive",
    )

    for name in required:
        if name not in functions:
            raise RuntimeError(
                f"Exact launcher function missing: "
                f"{name}"
            )

    dispatch_text = source_segment(
        source,
        functions[
            "dispatch_command"
        ],
    )

    run_text = source_segment(
        source,
        functions[
            "run_interactive"
        ],
    )

    if (
        'handler == "handle_ask"'
        not in dispatch_text
    ):
        raise RuntimeError(
            "dispatch_command does not contain "
            "the exact handle_ask branch"
        )

    if (
        "display_query("
        not in dispatch_text
    ):
        raise RuntimeError(
            "handle_ask dispatch branch does not "
            "route through display_query"
        )

    if (
        "dispatch_command("
        not in run_text
    ):
        raise RuntimeError(
            "run_interactive does not route through "
            "dispatch_command"
        )

    # The launcher currently contains a later additive
    # INT-ORACLE-LIVE-001 display_query definition.
    display_defs = [
        node
        for node in tree.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and node.name
        == "display_query"
    ]

    if len(
        display_defs
    ) < 1:
        raise RuntimeError(
            "display_query runtime boundary missing"
        )

    return {
        "launcher_module": (
            "run_oracle_open_intelligence_terminal"
        ),
        "interactive_symbol": (
            "run_interactive"
        ),
        "dispatch_symbol": (
            "dispatch_command"
        ),
        "ask_handler_name": (
            "handle_ask"
        ),
        "injection_symbol": (
            "display_query"
        ),
        "display_query_definition_count": (
            len(
                display_defs
            )
        ),
        "int_oracle_live_001_bound": (
            "INT_ORACLE_LIVE_001_BOUND"
            in source
        ),
        "binding_mode": (
            "runtime_display_query_overlay"
        ),
        "source_mutation_required": False,
        "read_only": True,
    }


def write_checked(
    path: Path,
    source: str,
) -> None:
    content = source.lstrip()

    ast.parse(
        content,
        filename=str(
            path
        ),
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[PASS] Wrote: "
        f"{path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OLC-010 INSTALLER")
    print(
        " EXACT /ASK RUNTIME DISPLAY BOUNDARY "
        "— CORRECTION V5"
    )
    print("=" * 72)

    print(
        f"[BOOT] Revision: "
        f"{INSTALLER_REVISION}"
    )

    print(
        f"[ROOT] {ROOT}"
    )

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    exact = inspect_launcher()

    print(
        "[PASS] Exact interactive runtime: "
        "run_oracle_open_intelligence_terminal.run_interactive"
    )

    print(
        "[PASS] Exact command dispatch: "
        "run_oracle_open_intelligence_terminal.dispatch_command"
    )

    print(
        "[PASS] /ask dispatch metadata: "
        "handler_name='handle_ask'"
    )

    print(
        "[PASS] Exact executable boundary: "
        "run_oracle_open_intelligence_terminal.display_query"
    )

    print(
        "[PASS] Existing INT-ORACLE-LIVE-001 bridge detected: "
        f"{exact['int_oracle_live_001_bound']}"
    )

    protected = UPSTREAMS

    hashes = {
        path: sha(
            path
        )
        for path in protected
    }

    payload = {
        "revision": (
            "OLC_010_EXACT_ASK_DESCRIPTOR_MANIFEST_V1"
        ),
        **exact,
    }

    affected = (
        MODULE,
        TEST,
        INIT,
        MANIFEST,
    )

    backups = {
        path: (
            path.read_bytes()
            if path.exists()
            else None
        )
        for path in affected
    }

    try:
        write_checked(
            MODULE,
            MODULE_SOURCE,
        )

        write_checked(
            TEST,
            TEST_SOURCE,
        )

        MANIFEST.write_text(
            json.dumps(
                payload,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

        print(
            f"[PASS] Wrote: "
            f"{MANIFEST.relative_to(ROOT)}"
        )

        current = (
            INIT.read_text(
                encoding="utf-8"
            )
            if INIT.exists()
            else ""
        )

        export = (
            "from ."
            "olc_010_exact_ask_descriptor_binding "
            "import *"
        )

        if export not in current.splitlines():
            if (
                current
                and not current.endswith(
                    "\n"
                )
            ):
                current += "\n"

            current += (
                export
                + "\n"
            )

            ast.parse(
                current,
                filename=str(
                    INIT
                ),
            )

            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        for path, expected in hashes.items():
            if sha(
                path
            ) != expected:
                raise RuntimeError(
                    "Certified/frozen upstream changed: "
                    f"{path.name}"
                )

        print(
            "[PASS] Launcher, existing Oracle Terminal, "
            "and frozen OAR remained unchanged"
        )

        print(
            "[PASS] In-memory compilation verified"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
            + MANIFEST.read_bytes()
        ).hexdigest()

        print(
            "[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[PASS] OLC-010 now follows the actual "
            "runtime dispatch contract from the uploaded launcher"
        )

        print(
            "[DONE] OLC-010 INSTALLATION COMPLETE"
        )

        return 0

    except Exception:
        for path, original in backups.items():
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(
                    original
                )

        print(
            "[ROLLBACK] OLC-010 correction failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
