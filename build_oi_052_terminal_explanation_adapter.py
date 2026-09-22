from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-052"
INSTALLER_REVISION = "OI_052_TERMINAL_EXPLANATION_ADAPTER_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_048_oracle_explanation_readout.py", "OI-048"),
    (PACKAGE / "oi_051_oracle_explanation_delivery_model.py", "OI-051"),
)

MODULE = PACKAGE / "oi_052_terminal_explanation_adapter.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_052_terminal_explanation_adapter.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_051_oracle_explanation_delivery_model import (
    OracleExplanationDeliveryModel,
)

BUILD_ID = "OI-052"
OI_052_REVISION = "OI_052_TERMINAL_EXPLANATION_ADAPTER_V1"

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
class TerminalExplanationView:
    query_id: str
    subject_hint: str
    completeness_status: str
    title: str
    body_lines: tuple[str, ...]
    caveat_lines: tuple[str, ...]
    footer: str
    view_hash: str
    read_only: bool


class TerminalExplanationAdapter:
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

    def adapt(
        self,
        delivery: OracleExplanationDeliveryModel,
    ) -> TerminalExplanationView:
        if not isinstance(
            delivery,
            OracleExplanationDeliveryModel,
        ):
            raise TypeError(
                "delivery must be OracleExplanationDeliveryModel"
            )

        body_lines = tuple(delivery.ordered_explanations)

        caveat_lines = tuple(delivery.caveats)

        footer = (
            "MODE: READ-ONLY | "
            "NO TRADE AUTHORIZATION | "
            "NO CAUSAL CLAIM"
        )

        body = {
            "query_id": delivery.query_id,
            "subject_hint": delivery.subject_hint,
            "completeness_status": delivery.completeness_status,
            "title": delivery.headline,
            "body_lines": body_lines,
            "caveat_lines": caveat_lines,
            "footer": footer,
            "read_only": True,
        }

        return TerminalExplanationView(
            query_id=delivery.query_id,
            subject_hint=delivery.subject_hint,
            completeness_status=delivery.completeness_status,
            title=delivery.headline,
            body_lines=body_lines,
            caveat_lines=caveat_lines,
            footer=footer,
            view_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_terminal_explanation_adapter() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-052 must remain read-only")

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
        raise AssertionError("OI-052 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_052_REVISION",
    "TerminalExplanationView",
    "TerminalExplanationAdapter",
    "verify_terminal_explanation_adapter",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_051_oracle_explanation_delivery_model import (
    OracleExplanationDeliveryModel,
)
from qseries_v2.observation_intelligence.oi_052_terminal_explanation_adapter import (
    OI_052_REVISION,
    TerminalExplanationAdapter,
    verify_terminal_explanation_adapter,
)

NOW = datetime(2026, 8, 11, 13, 0, tzinfo=timezone.utc)


def delivery():
    return OracleExplanationDeliveryModel(
        query_id="query.astros",
        subject_hint="Astros strikeouts",
        completeness_status="partial",
        headline="Oracle Evidence Explanation — Astros strikeouts",
        ordered_explanations=(
            "Astros strikeouts: two evidence items provide structural support.",
        ),
        caveats=(
            "partial_explanation_candidates",
            "structural association does not establish causation",
        ),
        delivered_at=NOW,
        delivery_hash="a" * 64,
        read_only=True,
        terminal_mutation_allowed=False,
    )


class TestOI052(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_explanation_adapter()
        )

    def test_adapt(self):
        view = TerminalExplanationAdapter().adapt(
            delivery()
        )

        self.assertEqual(
            view.completeness_status,
            "partial",
        )
        self.assertEqual(
            len(view.body_lines),
            1,
        )

    def test_footer(self):
        view = TerminalExplanationAdapter().adapt(
            delivery()
        )

        self.assertIn(
            "READ-ONLY",
            view.footer,
        )
        self.assertIn(
            "NO TRADE AUTHORIZATION",
            view.footer,
        )

    def test_deterministic(self):
        adapter = TerminalExplanationAdapter()

        a = adapter.adapt(delivery())
        b = adapter.adapt(delivery())

        self.assertEqual(
            a.view_hash,
            b.view_hash,
        )

    def test_side_effects(self):
        adapter = TerminalExplanationAdapter()

        self.assertTrue(adapter.read_only)
        self.assertFalse(adapter.network_allowed)
        self.assertFalse(adapter.persistence_allowed)
        self.assertFalse(adapter.publication_allowed)
        self.assertFalse(adapter.execution_allowed)
        self.assertFalse(adapter.qseries_execution_allowed)
        self.assertFalse(adapter.prediction_allowed)
        self.assertFalse(adapter.edge_score_allowed)
        self.assertFalse(adapter.probability_allowed)
        self.assertFalse(adapter.causal_claim_allowed)
        self.assertFalse(adapter.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-052 CERTIFICATION TEST")
    print(" TERMINAL EXPLANATION ADAPTER")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI052)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-052")
    print(f"[PASS] Revision: {OI_052_REVISION}")
    print("[PASS] Oracle explanation delivery converted into deterministic terminal-safe view")
    print("[PASS] Completeness, explanation lines, caveats, subject, and read-only footer preserved")
    print("[PASS] Terminal mutation, prediction, probability, scoring, causation, and execution remain disabled")
    print("[DONE] OI-052 CERTIFIED")
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
    print(" OI-052 INSTALLER")
    print(" TERMINAL EXPLANATION ADAPTER")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for upstream, name in UPSTREAMS:
        if not upstream.is_file():
            raise RuntimeError(f"Certified {name} missing: {upstream}")

    upstream_hashes = {
        upstream: sha(upstream)
        for upstream, _ in UPSTREAMS
    }

    print(
        "[PASS] Certified OI-048 and OI-051 "
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
        export = "from .oi_052_terminal_explanation_adapter import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print(
            "[PASS] Updated: "
            "qseries_v2\\observation_intelligence\\__init__.py"
        )

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

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

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print(
            "[PASS] Terminal explanation adaptation remains deterministic, "
            "read-only, terminal-safe, and non-causal"
        )
        print("[DONE] OI-052 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_bytes(original)

        print(
            "[ROLLBACK] OI-052 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
