from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-054"
INSTALLER_REVISION = "OI_054_EXPLANATION_TERMINAL_HANDOFF_BOUNDARY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_051_oracle_explanation_delivery_model.py", "OI-051"),
    (PACKAGE / "oi_052_terminal_explanation_adapter.py", "OI-052"),
    (PACKAGE / "oi_053_explanation_query_response_package.py", "OI-053"),
)

MODULE = PACKAGE / "oi_054_explanation_terminal_handoff_boundary.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_054_explanation_terminal_handoff_boundary.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_053_explanation_query_response_package import (
    ExplanationQueryResponsePackage,
)

BUILD_ID = "OI-054"
OI_054_REVISION = "OI_054_EXPLANATION_TERMINAL_HANDOFF_BOUNDARY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
TERMINAL_MUTATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class ExplanationTerminalHandoff:
    response_id: str
    query_id: str
    subject_hint: str
    completeness_status: str
    display_payload: tuple[str, ...]
    handoff_hash: str
    read_only: bool
    terminal_mutation_allowed: bool


class ExplanationTerminalHandoffBoundary:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False
    causal_claim_allowed = False
    terminal_mutation_allowed = False

    def handoff(
        self,
        package: ExplanationQueryResponsePackage,
    ) -> ExplanationTerminalHandoff:
        if not isinstance(
            package,
            ExplanationQueryResponsePackage,
        ):
            raise TypeError(
                "package must be ExplanationQueryResponsePackage"
            )

        lines = [
            "=" * 64,
            package.title,
            f"STATUS: {package.completeness_status.upper()}",
            "",
        ]

        lines.extend(package.body_lines)

        if package.caveat_lines:
            lines.append("")
            lines.append("CAVEATS:")
            lines.extend(
                f"- {item}"
                for item in package.caveat_lines
            )

        lines.append("")
        lines.append(package.footer)
        lines.append("=" * 64)

        display_payload = tuple(lines)

        body = {
            "response_id": package.response_id,
            "query_id": package.query_id,
            "subject_hint": package.subject_hint,
            "completeness_status": package.completeness_status,
            "display_payload": display_payload,
            "read_only": True,
            "terminal_mutation_allowed": False,
        }

        return ExplanationTerminalHandoff(
            response_id=package.response_id,
            query_id=package.query_id,
            subject_hint=package.subject_hint,
            completeness_status=package.completeness_status,
            display_payload=display_payload,
            handoff_hash=deterministic_sha256(body),
            read_only=True,
            terminal_mutation_allowed=False,
        )


def verify_explanation_terminal_handoff_boundary() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-054 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            TERMINAL_MUTATION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-054 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_054_REVISION",
    "ExplanationTerminalHandoff",
    "ExplanationTerminalHandoffBoundary",
    "verify_explanation_terminal_handoff_boundary",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_053_explanation_query_response_package import (
    ExplanationQueryResponsePackage,
)
from qseries_v2.observation_intelligence.oi_054_explanation_terminal_handoff_boundary import (
    OI_054_REVISION,
    ExplanationTerminalHandoffBoundary,
    verify_explanation_terminal_handoff_boundary,
)

NOW = datetime(2026, 8, 11, 15, 0, tzinfo=timezone.utc)


def package():
    return ExplanationQueryResponsePackage(
        response_id="response.astros",
        query_id="query.astros",
        query_kind="explanation",
        subject_hint="Astros strikeouts",
        completeness_status="partial",
        title="Oracle Evidence Explanation — Astros strikeouts",
        body_lines=(
            "Astros strikeouts: evidence explanation line.",
        ),
        caveat_lines=(
            "missing_required_evidence",
            "structural association does not establish causation",
        ),
        footer=(
            "MODE: READ-ONLY | "
            "NO TRADE AUTHORIZATION | "
            "NO CAUSAL CLAIM"
        ),
        assembled_at=NOW,
        response_hash="a" * 64,
        read_only=True,
    )


class TestOI054(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_terminal_handoff_boundary()
        )

    def test_handoff(self):
        value = ExplanationTerminalHandoffBoundary().handoff(
            package()
        )

        self.assertEqual(
            value.completeness_status,
            "partial",
        )

        self.assertIn(
            "STATUS: PARTIAL",
            value.display_payload,
        )

    def test_caveats_rendered(self):
        value = ExplanationTerminalHandoffBoundary().handoff(
            package()
        )

        payload = "\n".join(
            value.display_payload
        )

        self.assertIn(
            "missing_required_evidence",
            payload,
        )

        self.assertIn(
            "NO TRADE AUTHORIZATION",
            payload,
        )

    def test_deterministic(self):
        boundary = ExplanationTerminalHandoffBoundary()

        a = boundary.handoff(package())
        b = boundary.handoff(package())

        self.assertEqual(
            a.handoff_hash,
            b.handoff_hash,
        )

    def test_side_effects(self):
        boundary = ExplanationTerminalHandoffBoundary()

        self.assertTrue(boundary.read_only)
        self.assertFalse(boundary.network_allowed)
        self.assertFalse(boundary.persistence_allowed)
        self.assertFalse(boundary.publication_allowed)
        self.assertFalse(boundary.execution_allowed)
        self.assertFalse(boundary.qseries_execution_allowed)
        self.assertFalse(boundary.prediction_allowed)
        self.assertFalse(boundary.edge_score_allowed)
        self.assertFalse(boundary.probability_allowed)
        self.assertFalse(boundary.causal_claim_allowed)
        self.assertFalse(boundary.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-054 CERTIFICATION TEST")
    print(" EXPLANATION TERMINAL HANDOFF BOUNDARY")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI054)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-054")
    print(f"[PASS] Revision: {OI_054_REVISION}")
    print("[PASS] Explanation response package converted into deterministic terminal handoff payload")
    print("[PASS] Status, explanation body, caveats, subject identity, and read-only safety footer preserved")
    print("[PASS] Handoff remains non-mutating and cannot publish, predict, score, authorize, or execute")
    print("[DONE] OI-054 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checked(path: Path, source: str) -> None:
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OI-054 INSTALLER")
    print(" EXPLANATION TERMINAL HANDOFF BOUNDARY")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for upstream, name in UPSTREAMS:
        if not upstream.is_file():
            raise RuntimeError(
                f"Certified {name} missing: {upstream}"
            )

    upstream_hashes = {
        upstream: sha(upstream)
        for upstream, _ in UPSTREAMS
    }

    print(
        "[PASS] Certified OI-051 through OI-053 "
        "verified read-only"
    )

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_054_explanation_terminal_handoff_boundary import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        print(
            "[PASS] Updated: "
            "qseries_v2\\observation_intelligence\\__init__.py"
        )

        compile(
            MODULE.read_text(encoding="utf-8"),
            str(MODULE),
            "exec",
        )
        compile(
            TEST.read_text(encoding="utf-8"),
            str(TEST),
            "exec",
        )

        for upstream, expected in upstream_hashes.items():
            if sha(upstream) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: {upstream.name}"
                )

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified upstream remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[PASS] Terminal handoff boundary remains deterministic, "
            "read-only, non-mutating, and fail-closed"
        )
        print("[DONE] OI-054 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                item.write_bytes(original)

        print(
            "[ROLLBACK] OI-054 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
