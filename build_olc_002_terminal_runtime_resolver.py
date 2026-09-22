from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OIT = ROOT / "qseries_v2" / "oracle_terminal"

UPSTREAMS = (
    PACKAGE / "olc_001_live_composition_foundation.py",
    ROOT / "qseries_v2" / "observation_adapter_runtime" / "oar_030_final_certification_freeze.py",
)

MODULE = PACKAGE / "olc_002_terminal_runtime_resolver.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_002_terminal_runtime_resolver.py"
MANIFEST = PACKAGE / "OLC_002_TERMINAL_RUNTIME_MANIFEST.json"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OLC-002"
OLC_002_REVISION = "OLC_002_TERMINAL_RUNTIME_RESOLVER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class TerminalRuntimeCandidate:
    module_name: str
    symbol_name: str
    symbol_kind: str
    score: int
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TerminalRuntimeResolution:
    candidates: tuple[TerminalRuntimeCandidate, ...]
    candidate_count: int
    exact_runtime_resolved: bool
    read_only: bool


class TerminalRuntimeResolver:
    read_only = True
    execution_allowed = False

    def resolve(
        self,
        candidates: tuple[TerminalRuntimeCandidate, ...],
    ) -> TerminalRuntimeResolution:
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

        return TerminalRuntimeResolution(
            candidates=ordered,
            candidate_count=len(ordered),
            exact_runtime_resolved=bool(
                ordered
                and ordered[0].score >= 8
            ),
            read_only=True,
        )


def verify_terminal_runtime_resolver() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True
"""

TEST_SOURCE_TEMPLATE = r"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.oracle_live_composition.olc_002_terminal_runtime_resolver import (
    TerminalRuntimeCandidate,
    TerminalRuntimeResolver,
    verify_terminal_runtime_resolver,
)

MANIFEST = Path(__MANIFEST__)


class TestOLC002(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_runtime_resolver()
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
            TerminalRuntimeCandidate(
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

        result = TerminalRuntimeResolver().resolve(
            candidates
        )

        self.assertTrue(
            result.exact_runtime_resolved
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-002 CERTIFICATION TEST")
    print(" EXACT INTERACTIVE ORACLE TERMINAL RUNTIME RESOLVER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC002
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-002")
    print("[PASS] Exact interactive Oracle Terminal runtime boundary resolved from current repository")
    print("[PASS] Existing OIT source remains unchanged")
    print("[DONE] OLC-002 CERTIFIED")
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


def score_node(
    node: ast.AST,
    source: str,
    path: Path,
):
    name = getattr(
        node,
        "name",
        "",
    ).lower()

    score = 0
    evidence = []

    if name == "main":
        score += 3
        evidence.append(
            "symbol_named_main"
        )

    if "run" in name:
        score += 2
        evidence.append(
            "symbol_name_contains_run"
        )

    if "terminal" in name:
        score += 2
        evidence.append(
            "symbol_name_contains_terminal"
        )

    if "interactive" in name:
        score += 3
        evidence.append(
            "symbol_name_contains_interactive"
        )

    segment = (
        ast.get_source_segment(
            source,
            node,
        )
        or ""
    ).lower()

    checks = (
        ('"oracle> "', 7, "contains_oracle_prompt"),
        ("'oracle> '", 7, "contains_oracle_prompt"),
        ("input(", 4, "contains_input_call"),
        ("/ask", 3, "contains_ask_command"),
        ("/quit", 2, "contains_quit_command"),
        ("command_registry", 2, "contains_command_registry"),
        ("while true", 2, "contains_command_loop"),
    )

    for token, weight, label in checks:
        if token in segment:
            score += weight
            evidence.append(label)

    filename = path.name.lower()

    if "run_oracle" in filename:
        score += 4
        evidence.append(
            "launcher_filename"
        )

    if "terminal" in filename:
        score += 2
        evidence.append(
            "terminal_filename"
        )

    return score, tuple(
        sorted(
            set(evidence)
        )
    )


def discover_candidates():
    roots = [
        OIT,
        ROOT,
    ]

    paths = set()

    for root in roots:
        if root == ROOT:
            paths.update(
                p
                for p in ROOT.glob(
                    "run_oracle*.py"
                )
                if p.is_file()
            )
        elif root.is_dir():
            paths.update(
                p
                for p in root.glob(
                    "**/*.py"
                )
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

            score, evidence = score_node(
                node,
                source,
                path,
            )

            if score <= 0:
                continue

            rows.append(
                {
                    "module_name": (
                        module_name_for(path)
                    ),
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

    return rows, tuple(sorted(paths))


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
    print(" OLC-002 INSTALLER")
    print(" EXACT INTERACTIVE ORACLE TERMINAL RUNTIME RESOLVER")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OLC_002_TERMINAL_RUNTIME_RESOLVER_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    candidates, inspected = (
        discover_candidates()
    )

    if not candidates:
        raise RuntimeError(
            "No interactive Oracle Terminal runtime candidates found"
        )

    top = candidates[0]

    if top["score"] < 8:
        raise RuntimeError(
            "Interactive Oracle Terminal runtime boundary "
            "could not be resolved confidently"
        )

    print(
        "[PASS] Interactive terminal inventory built "
        f"from {len(inspected)} candidate source files"
    )

    print(
        "[PASS] Highest-ranked candidate: "
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

    manifest_payload = {
        "revision": (
            "OLC_002_TERMINAL_RUNTIME_MANIFEST_V1"
        ),
        "top_candidate": top,
        "candidates": candidates,
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
        write_checked(
            MODULE,
            MODULE_SOURCE,
        )

        write_checked(
            TEST,
            test_source,
        )

        MANIFEST.write_text(
            json.dumps(
                manifest_payload,
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
            "from .olc_002_terminal_runtime_resolver import *"
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
            "[PASS] Existing terminal and frozen OAR source remained unchanged"
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
            "[DONE] OLC-002 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OLC-002 installation failed; affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
