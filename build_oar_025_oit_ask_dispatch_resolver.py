from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
OIT = ROOT / "qseries_v2" / "oracle_terminal"

UPSTREAMS = (
    PKG / "oar_022_terminal_live_intelligence_read_model.py",
    PKG / "oar_023_terminal_live_query_router.py",
    PKG / "oar_024_oit_live_intelligence_bridge.py",
)

MODULE = PKG / "oar_025_oit_ask_dispatch_resolver.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_025_oit_ask_dispatch_resolver.py"
MANIFEST = PKG / "oar_025_oit_ask_dispatch_manifest.json"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OAR-025"
OAR_025_REVISION = "OAR_025_OIT_ASK_DISPATCH_RESOLVER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class OITAskDispatchCandidate:
    module_name: str
    symbol_name: str
    symbol_kind: str
    score: int
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OITAskDispatchResolution:
    candidates: tuple[OITAskDispatchCandidate, ...]
    candidate_count: int
    exact_boundary_resolved: bool
    read_only: bool


class OITAskDispatchResolver:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def resolve(
        self,
        candidates: tuple[OITAskDispatchCandidate, ...],
    ) -> OITAskDispatchResolution:
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
            and ordered[0].score >= 6
        )

        return OITAskDispatchResolution(
            candidates=ordered,
            candidate_count=len(ordered),
            exact_boundary_resolved=exact,
            read_only=True,
        )


def verify_oit_ask_dispatch_resolver() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True
"""

TEST_SOURCE_TEMPLATE = r"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.observation_adapter_runtime.oar_025_oit_ask_dispatch_resolver import (
    OITAskDispatchCandidate,
    OITAskDispatchResolver,
    verify_oit_ask_dispatch_resolver,
)

MANIFEST = Path(__MANIFEST_PATH__)


class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oit_ask_dispatch_resolver()
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

        self.assertTrue(
            payload["top_candidate"][
                "score"
            ] >= 6
        )

    def test_resolve(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        candidates = tuple(
            OITAskDispatchCandidate(
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

        result = OITAskDispatchResolver().resolve(
            candidates
        )

        self.assertTrue(
            result.exact_boundary_resolved
        )

        self.assertEqual(
            result.candidates[0].module_name,
            payload["top_candidate"][
                "module_name"
            ],
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-025 CERTIFICATION TEST")
    print(" EXACT OIT /ASK DISPATCH BOUNDARY RESOLVER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-025")
    print("[PASS] Exact OIT /ask dispatch boundary resolved from the certified terminal repository")
    print("[PASS] Resolver remains read-only and does not modify certified OIT source")
    print("[DONE] OAR-025 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def module_name_for(path: Path) -> str:
    return ".".join(
        path.relative_to(ROOT)
        .with_suffix("")
        .parts
    )


def score_node(
    node: ast.AST,
    source: str,
) -> tuple[int, tuple[str, ...]]:
    score = 0
    evidence = []

    name = getattr(
        node,
        "name",
        "",
    ).lower()

    if "ask" in name:
        score += 4
        evidence.append(
            "symbol_name_contains_ask"
        )

    if "dispatch" in name:
        score += 3
        evidence.append(
            "symbol_name_contains_dispatch"
        )

    if "query" in name:
        score += 2
        evidence.append(
            "symbol_name_contains_query"
        )

    try:
        segment = ast.get_source_segment(
            source,
            node,
        ) or ""
    except Exception:
        segment = ""

    lower = segment.lower()

    for token, weight, label in (
        ("/ask", 6, "contains_literal_/ask"),
        ("handle_query", 3, "contains_handle_query"),
        ("dispatch", 2, "contains_dispatch"),
        ("natural_language", 2, "contains_natural_language"),
        ("oracle>", 1, "contains_terminal_prompt"),
    ):
        if token in lower:
            score += weight
            evidence.append(label)

    return score, tuple(
        sorted(set(evidence))
    )


def discover_candidates():
    if not OIT.is_dir():
        raise RuntimeError(
            f"Certified OIT package missing: {OIT}"
        )

    rows = []

    for path in sorted(
        OIT.glob("**/*.py")
    ):
        if not path.is_file():
            continue

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

    return rows


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
        f"[PASS] Wrote: "
        f"{path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OAR-025 INSTALLER")
    print(" EXACT OIT /ASK DISPATCH BOUNDARY RESOLVER")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_025_OIT_ASK_DISPATCH_RESOLVER_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    oit_files = tuple(
        sorted(
            path
            for path in OIT.glob(
                "**/*.py"
            )
            if path.is_file()
        )
    )

    if not oit_files:
        raise RuntimeError(
            "Certified OIT modules missing"
        )

    candidates = discover_candidates()

    if not candidates:
        raise RuntimeError(
            "No OIT /ask dispatch candidates found"
        )

    top = candidates[0]

    if top["score"] < 6:
        raise RuntimeError(
            "Exact OIT /ask dispatch boundary "
            "could not be resolved confidently"
        )

    print(
        "[PASS] OIT /ask boundary inventory built "
        f"from {len(oit_files)} modules"
    )

    print(
        "[PASS] Highest-ranked candidate: "
        f"{top['module_name']}."
        f"{top['symbol_name']} "
        f"({top['symbol_kind']}, "
        f"score={top['score']})"
    )

    protected = (
        *UPSTREAMS,
        *oit_files,
    )

    hashes = {
        path: sha(path)
        for path in protected
    }

    manifest_payload = {
        "revision": (
            "OAR_025_OIT_ASK_DISPATCH_MANIFEST_V1"
        ),
        "top_candidate": top,
        "candidates": candidates,
    }

    test_source = (
        TEST_SOURCE_TEMPLATE
        .replace(
            "__MANIFEST_PATH__",
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
            "oar_025_oit_ask_dispatch_resolver "
            "import *"
        )

        if export not in current.splitlines():
            if (
                current
                and not current.endswith("\n")
            ):
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
                    "Certified OIT/OAR upstream changed: "
                    f"{path.name}"
                )

        print(
            "[PASS] Certified OIT and OAR upstream "
            "remained unchanged"
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
            "[DONE] OAR-025 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OAR-025 installation failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
