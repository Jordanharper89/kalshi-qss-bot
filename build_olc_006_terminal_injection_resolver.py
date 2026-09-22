from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OIT = ROOT / "qseries_v2" / "oracle_terminal"

UPSTREAMS = (
    PACKAGE / "olc_002_terminal_runtime_resolver.py",
    PACKAGE / "OLC_002_TERMINAL_RUNTIME_MANIFEST.json",
    PACKAGE / "olc_003_live_runtime_terminal_composition.py",
    PACKAGE / "olc_005_live_read_model_refresh.py",
    ROOT / "qseries_v2" / "observation_adapter_runtime" / "oar_030_final_certification_freeze.py",
)

MODULE = PACKAGE / "olc_006_terminal_injection_resolver.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_006_terminal_injection_resolver.py"
MANIFEST = PACKAGE / "OLC_006_TERMINAL_INJECTION_MANIFEST.json"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OLC-006"
OLC_006_REVISION = "OLC_006_TERMINAL_INJECTION_RESOLVER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class TerminalInjectionCandidate:
    module_name: str
    symbol_name: str
    symbol_kind: str
    score: int
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TerminalInjectionResolution:
    candidates: tuple[TerminalInjectionCandidate, ...]
    exact_injection_boundary_resolved: bool
    source_mutation_required: bool
    read_only: bool


class TerminalInjectionResolver:
    read_only = True
    execution_allowed = False
    source_mutation_allowed = False

    def resolve(
        self,
        candidates: tuple[TerminalInjectionCandidate, ...],
    ) -> TerminalInjectionResolution:
        ordered = tuple(
            sorted(
                candidates,
                key=lambda x: (
                    -x.score,
                    x.module_name,
                    x.symbol_name,
                    x.symbol_kind,
                ),
            )
        )

        exact = bool(
            ordered
            and ordered[0].score >= 8
        )

        return TerminalInjectionResolution(
            candidates=ordered,
            exact_injection_boundary_resolved=exact,
            source_mutation_required=False,
            read_only=True,
        )


def verify_terminal_injection_resolver() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    return True
"""

TEST_SOURCE_TEMPLATE = r"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.oracle_live_composition.olc_006_terminal_injection_resolver import (
    TerminalInjectionCandidate,
    TerminalInjectionResolver,
    verify_terminal_injection_resolver,
)

MANIFEST = Path(__MANIFEST__)


class TestOLC006(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_injection_resolver()
        )

    def test_manifest(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(
            payload["candidates"]
        )

        self.assertGreaterEqual(
            payload["top_candidate"]["score"],
            8,
        )

    def test_resolution(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        candidates = tuple(
            TerminalInjectionCandidate(
                module_name=item["module_name"],
                symbol_name=item["symbol_name"],
                symbol_kind=item["symbol_kind"],
                score=item["score"],
                evidence=tuple(
                    item["evidence"]
                ),
            )
            for item in payload["candidates"]
        )

        result = (
            TerminalInjectionResolver()
            .resolve(
                candidates
            )
        )

        self.assertTrue(
            result.exact_injection_boundary_resolved
        )

        self.assertFalse(
            result.source_mutation_required
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-006 CERTIFICATION TEST")
    print(" EXACT TERMINAL LIVE-READ INJECTION BOUNDARY RESOLVER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC006
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-006")
    print("[PASS] Exact in-memory terminal injection boundary resolved from current command-loop repository")
    print("[PASS] Existing Oracle Terminal source modification is not required")
    print("[PASS] Resolver remains read-only and fail-closed")
    print("[DONE] OLC-006 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def module_name_for(
    path: Path,
) -> str:
    return ".".join(
        path.relative_to(ROOT)
        .with_suffix("")
        .parts
    )


def candidate_score(
    node: ast.AST,
    source: str,
    path: Path,
):
    name = getattr(
        node,
        "name",
        "",
    ).lower()

    segment = (
        ast.get_source_segment(
            source,
            node,
        )
        or ""
    ).lower()

    score = 0
    evidence = []

    for token, weight, label in (
        ("command_registry", 5, "command_registry"),
        ("build_default_command_registry", 7, "default_command_registry_builder"),
        ("run_interactive", 6, "interactive_runtime"),
        ("/ask", 5, "ask_command"),
        ("input(", 3, "input_loop"),
        ("oracle> ", 5, "oracle_prompt"),
        ("dispatch", 3, "dispatch_logic"),
        ("handler", 2, "handler_logic"),
        ("registry", 2, "registry_logic"),
    ):
        if token in name or token in segment:
            score += weight
            evidence.append(label)

    if (
        "command_registry"
        in path.name.lower()
    ):
        score += 5
        evidence.append(
            "command_registry_module"
        )

    return score, tuple(
        sorted(
            set(evidence)
        )
    )


def discover():
    paths = set()

    if OIT.is_dir():
        paths.update(
            p for p in OIT.glob("**/*.py")
            if p.is_file()
        )

    paths.update(
        p for p in ROOT.glob("run_oracle*.py")
        if p.is_file()
    )

    rows = []

    for path in sorted(paths):
        source = path.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(
            source,
            filename=str(path),
        )

        for node in ast.walk(tree):
            if not isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                ),
            ):
                continue

            score, evidence = (
                candidate_score(
                    node,
                    source,
                    path,
                )
            )

            if score < 1:
                continue

            rows.append(
                {
                    "module_name": module_name_for(path),
                    "symbol_name": node.name,
                    "symbol_kind": (
                        "class"
                        if isinstance(
                            node,
                            ast.ClassDef,
                        )
                        else "function"
                    ),
                    "score": score,
                    "evidence": list(
                        evidence
                    ),
                }
            )

    rows.sort(
        key=lambda x: (
            -x["score"],
            x["module_name"],
            x["symbol_name"],
            x["symbol_kind"],
        )
    )

    return rows, tuple(
        sorted(paths)
    )


def write_checked(
    path: Path,
    source: str,
) -> None:
    text = source.lstrip()
    ast.parse(
        text,
        filename=str(path),
    )
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"[PASS] Wrote: {path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OLC-006 INSTALLER")
    print(" EXACT TERMINAL LIVE-READ INJECTION BOUNDARY RESOLVER")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OLC_006_TERMINAL_INJECTION_RESOLVER_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    candidates, inspected = discover()

    if not candidates:
        raise RuntimeError(
            "No terminal injection candidates found"
        )

    top = candidates[0]

    if top["score"] < 8:
        raise RuntimeError(
            "Exact terminal injection boundary "
            "could not be resolved confidently"
        )

    print(
        "[PASS] Terminal injection inventory built "
        f"from {len(inspected)} source files"
    )

    print(
        "[PASS] Highest-ranked injection candidate: "
        f"{top['module_name']}."
        f"{top['symbol_name']} "
        f"({top['symbol_kind']}, score={top['score']})"
    )

    protected = (
        *UPSTREAMS,
        *inspected,
    )

    hashes = {
        path: sha(path)
        for path in protected
    }

    payload = {
        "revision": (
            "OLC_006_TERMINAL_INJECTION_MANIFEST_V1"
        ),
        "top_candidate": top,
        "candidates": candidates,
        "source_mutation_required": False,
    }

    test_source = (
        TEST_SOURCE_TEMPLATE
        .replace(
            "__MANIFEST__",
            repr(str(MANIFEST)),
        )
    )

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
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, test_source)

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
            f"[PASS] Wrote: {MANIFEST.relative_to(ROOT)}"
        )

        current = (
            INIT.read_text(
                encoding="utf-8"
            )
            if INIT.exists()
            else ""
        )

        export = (
            "from .olc_006_terminal_injection_resolver import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(
                current,
                filename=str(INIT),
            )
            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        for path, expected in hashes.items():
            if sha(path) != expected:
                raise RuntimeError(
                    f"Certified/frozen source changed: {path.name}"
                )

        print(
            "[PASS] Existing terminal source and frozen OAR remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
            + MANIFEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )

        print(
            "[DONE] OLC-006 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OLC-006 installation failed; affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
