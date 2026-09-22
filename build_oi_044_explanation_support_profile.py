from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-044"
INSTALLER_REVISION = "OI_044_EXPLANATION_SUPPORT_PROFILE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_019_evidence_contradiction_registry.py", "OI-019"),
    (PACKAGE / "oi_023_evidence_confidence_composition.py", "OI-023"),
    (PACKAGE / "oi_043_structural_reasoning_synthesis.py", "OI-043"),
)

MODULE = PACKAGE / "oi_044_explanation_support_profile.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_044_explanation_support_profile.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_043_structural_reasoning_synthesis import (
    StructuralReasoningSynthesis,
)

BUILD_ID = "OI-044"
OI_044_REVISION = "OI_044_EXPLANATION_SUPPORT_PROFILE_V1"

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

SUPPORT_SINGLE = "single_source_structure"
SUPPORT_MULTI = "multi_evidence_structure"
SUPPORT_MIXED = "mixed_structure"


class ExplanationSupportProfileError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExplanationSupportItem:
    subject: str
    support_class: str
    evidence_count: int
    context_role_count: int
    relationship_type_count: int
    support_hash: str


@dataclass(frozen=True, slots=True)
class ExplanationSupportProfile:
    synthesis_hash: str
    items: tuple[ExplanationSupportItem, ...]
    item_count: int
    profile_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool


class ExplanationSupportProfiler:
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

    def build(
        self,
        synthesis: StructuralReasoningSynthesis,
    ) -> ExplanationSupportProfile:
        if not isinstance(
            synthesis,
            StructuralReasoningSynthesis,
        ):
            raise TypeError(
                "synthesis must be StructuralReasoningSynthesis"
            )

        items = []

        for signal in synthesis.signals:
            evidence_count = len(
                signal.evidence_observation_ids
            )
            role_count = len(
                signal.context_roles
            )
            relationship_count = len(
                signal.relationship_types
            )

            if (
                evidence_count > 1
                and relationship_count > 0
            ):
                support_class = SUPPORT_MULTI
            elif evidence_count == 1:
                support_class = SUPPORT_SINGLE
            else:
                support_class = SUPPORT_MIXED

            body = {
                "subject": signal.subject,
                "support_class": support_class,
                "evidence_count": evidence_count,
                "context_role_count": role_count,
                "relationship_type_count": relationship_count,
            }

            items.append(
                ExplanationSupportItem(
                    subject=signal.subject,
                    support_class=support_class,
                    evidence_count=evidence_count,
                    context_role_count=role_count,
                    relationship_type_count=relationship_count,
                    support_hash=deterministic_sha256(body),
                )
            )

        items = tuple(
            sorted(
                items,
                key=lambda item: item.subject,
            )
        )

        body = {
            "synthesis_hash": synthesis.synthesis_hash,
            "support_hashes": tuple(
                item.support_hash
                for item in items
            ),
            "item_count": len(items),
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
        }

        return ExplanationSupportProfile(
            synthesis_hash=synthesis.synthesis_hash,
            items=items,
            item_count=len(items),
            profile_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
        )


def verify_explanation_support_profile() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-044 must remain read-only")

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
        )
    ):
        raise AssertionError("OI-044 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_044_REVISION",
    "SUPPORT_SINGLE",
    "SUPPORT_MULTI",
    "SUPPORT_MIXED",
    "ExplanationSupportProfileError",
    "ExplanationSupportItem",
    "ExplanationSupportProfile",
    "ExplanationSupportProfiler",
    "verify_explanation_support_profile",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_043_structural_reasoning_synthesis import (
    StructuralReasoningSignal,
    StructuralReasoningSynthesis,
)
from qseries_v2.observation_intelligence.oi_044_explanation_support_profile import (
    OI_044_REVISION,
    SUPPORT_MULTI,
    SUPPORT_SINGLE,
    ExplanationSupportProfiler,
    verify_explanation_support_profile,
)


def synthesis():
    return StructuralReasoningSynthesis(
        assembly_hash="a" * 64,
        signals=(
            StructuralReasoningSignal(
                signal_type="multi_evidence_context",
                subject="Astros strikeouts",
                evidence_observation_ids=("obs.1", "obs.2"),
                context_roles=("evidence", "market_state", "sports_context"),
                relationship_types=("same_subject",),
                signal_hash="b" * 64,
            ),
            StructuralReasoningSignal(
                signal_type="single_evidence_context",
                subject="Bitcoin",
                evidence_observation_ids=("obs.3",),
                context_roles=("evidence", "market_state"),
                relationship_types=(),
                signal_hash="c" * 64,
            ),
        ),
        signal_count=2,
        synthesis_hash="d" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


class TestOI044(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_support_profile()
        )

    def test_profile(self):
        profile = ExplanationSupportProfiler().build(
            synthesis()
        )

        self.assertEqual(profile.item_count, 2)

    def test_multi_support(self):
        profile = ExplanationSupportProfiler().build(
            synthesis()
        )

        astros = tuple(
            item
            for item in profile.items
            if item.subject == "Astros strikeouts"
        )[0]

        self.assertEqual(
            astros.support_class,
            SUPPORT_MULTI,
        )

    def test_single_support(self):
        profile = ExplanationSupportProfiler().build(
            synthesis()
        )

        btc = tuple(
            item
            for item in profile.items
            if item.subject == "Bitcoin"
        )[0]

        self.assertEqual(
            btc.support_class,
            SUPPORT_SINGLE,
        )

    def test_deterministic(self):
        profiler = ExplanationSupportProfiler()

        a = profiler.build(synthesis())
        b = profiler.build(synthesis())

        self.assertEqual(
            a.profile_hash,
            b.profile_hash,
        )

    def test_side_effects(self):
        profiler = ExplanationSupportProfiler()

        self.assertTrue(profiler.read_only)
        self.assertFalse(profiler.network_allowed)
        self.assertFalse(profiler.persistence_allowed)
        self.assertFalse(profiler.publication_allowed)
        self.assertFalse(profiler.execution_allowed)
        self.assertFalse(profiler.qseries_execution_allowed)
        self.assertFalse(profiler.prediction_allowed)
        self.assertFalse(profiler.edge_score_allowed)
        self.assertFalse(profiler.probability_allowed)
        self.assertFalse(profiler.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-044 CERTIFICATION TEST")
    print(" EXPLANATION SUPPORT PROFILE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI044
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-044")
    print(f"[PASS] Revision: {OI_044_REVISION}")
    print("[PASS] Structural explanation support classified without probability or edge scoring")
    print("[PASS] Single-evidence and multi-evidence support states certified")
    print("[PASS] Support classification is descriptive only and does not establish causation")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-044 CERTIFIED")
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
    print(" OI-044 INSTALLER")
    print(" EXPLANATION SUPPORT PROFILE")
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
        "[PASS] Certified OI-019, OI-023, "
        "and OI-043 verified read-only"
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
        export = "from .oi_044_explanation_support_profile import *"

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

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print(
            "[PASS] Explanation support profiling remains deterministic, "
            "read-only, descriptive, and non-causal"
        )
        print("[DONE] OI-044 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-044 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
