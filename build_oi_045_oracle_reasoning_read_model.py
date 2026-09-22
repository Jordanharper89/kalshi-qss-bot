from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-045"
INSTALLER_REVISION = "OI_045_ORACLE_REASONING_READ_MODEL_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_042_oracle_reasoning_assembly.py", "OI-042"),
    (PACKAGE / "oi_043_structural_reasoning_synthesis.py", "OI-043"),
    (PACKAGE / "oi_044_explanation_support_profile.py", "OI-044"),
)

MODULE = PACKAGE / "oi_045_oracle_reasoning_read_model.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_045_oracle_reasoning_read_model.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_042_oracle_reasoning_assembly import OracleReasoningAssembly
from .oi_043_structural_reasoning_synthesis import (
    StructuralReasoningSynthesis,
)
from .oi_044_explanation_support_profile import ExplanationSupportProfile

BUILD_ID = "OI-045"
OI_045_REVISION = "OI_045_ORACLE_REASONING_READ_MODEL_V1"

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


class OracleReasoningReadModelError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleReasoningReadItem:
    subject: str
    signal_type: str
    support_class: str
    evidence_count: int
    context_roles: tuple[str, ...]
    relationship_types: tuple[str, ...]
    item_hash: str


@dataclass(frozen=True, slots=True)
class OracleReasoningReadModel:
    query_id: str
    profile_id: str
    subject_hint: str
    admission_status: str
    evidence_count: int
    relationship_count: int
    missing_need_count: int
    items: tuple[OracleReasoningReadItem, ...]
    built_at: datetime
    read_model_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool


class OracleReasoningReadModelBuilder:
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
        *,
        assembly: OracleReasoningAssembly,
        synthesis: StructuralReasoningSynthesis,
        support_profile: ExplanationSupportProfile,
        built_at: datetime,
    ) -> OracleReasoningReadModel:
        if not isinstance(assembly, OracleReasoningAssembly):
            raise TypeError("assembly must be OracleReasoningAssembly")
        if not isinstance(
            synthesis,
            StructuralReasoningSynthesis,
        ):
            raise TypeError(
                "synthesis must be StructuralReasoningSynthesis"
            )
        if not isinstance(
            support_profile,
            ExplanationSupportProfile,
        ):
            raise TypeError(
                "support_profile must be ExplanationSupportProfile"
            )

        if synthesis.assembly_hash != assembly.assembly_hash:
            raise OracleReasoningReadModelError(
                "synthesis does not belong to assembly"
            )

        if support_profile.synthesis_hash != synthesis.synthesis_hash:
            raise OracleReasoningReadModelError(
                "support profile does not belong to synthesis"
            )

        if not isinstance(built_at, datetime):
            raise TypeError("built_at must be datetime")

        if built_at.tzinfo is None:
            raise OracleReasoningReadModelError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(timezone.utc)

        support_by_subject = {
            item.subject: item
            for item in support_profile.items
        }

        items = []

        for signal in synthesis.signals:
            support = support_by_subject.get(
                signal.subject
            )

            if support is None:
                raise OracleReasoningReadModelError(
                    f"support profile missing subject: {signal.subject}"
                )

            body = {
                "subject": signal.subject,
                "signal_type": signal.signal_type,
                "support_class": support.support_class,
                "evidence_count": len(
                    signal.evidence_observation_ids
                ),
                "context_roles": signal.context_roles,
                "relationship_types": signal.relationship_types,
            }

            items.append(
                OracleReasoningReadItem(
                    subject=signal.subject,
                    signal_type=signal.signal_type,
                    support_class=support.support_class,
                    evidence_count=len(
                        signal.evidence_observation_ids
                    ),
                    context_roles=signal.context_roles,
                    relationship_types=signal.relationship_types,
                    item_hash=deterministic_sha256(body),
                )
            )

        items = tuple(
            sorted(
                items,
                key=lambda item: item.subject,
            )
        )

        body = {
            "query_id": assembly.query_id,
            "profile_id": assembly.profile_id,
            "subject_hint": assembly.subject_hint,
            "admission_status": assembly.admission_status,
            "evidence_count": assembly.evidence_count,
            "relationship_count": assembly.relationship_count,
            "missing_need_count": assembly.missing_need_count,
            "item_hashes": tuple(
                item.item_hash
                for item in items
            ),
            "built_at": built_at,
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
        }

        return OracleReasoningReadModel(
            query_id=assembly.query_id,
            profile_id=assembly.profile_id,
            subject_hint=assembly.subject_hint,
            admission_status=assembly.admission_status,
            evidence_count=assembly.evidence_count,
            relationship_count=assembly.relationship_count,
            missing_need_count=assembly.missing_need_count,
            items=items,
            built_at=built_at,
            read_model_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
        )


def verify_oracle_reasoning_read_model() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-045 must remain read-only")

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
        raise AssertionError("OI-045 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_045_REVISION",
    "OracleReasoningReadModelError",
    "OracleReasoningReadItem",
    "OracleReasoningReadModel",
    "OracleReasoningReadModelBuilder",
    "verify_oracle_reasoning_read_model",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_042_oracle_reasoning_assembly import (
    OracleReasoningAssembly,
)
from qseries_v2.observation_intelligence.oi_043_structural_reasoning_synthesis import (
    StructuralReasoningSignal,
    StructuralReasoningSynthesis,
)
from qseries_v2.observation_intelligence.oi_044_explanation_support_profile import (
    ExplanationSupportItem,
    ExplanationSupportProfile,
)
from qseries_v2.observation_intelligence.oi_045_oracle_reasoning_read_model import (
    OI_045_REVISION,
    OracleReasoningReadModelBuilder,
    verify_oracle_reasoning_read_model,
)

NOW = datetime(2026, 8, 11, 7, 0, tzinfo=timezone.utc)


def assembly():
    return OracleReasoningAssembly(
        assembly_id="assembly.test",
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status="partial",
        evidence_package_hash="a" * 64,
        context_registry_hash="b" * 64,
        relationship_registry_hash="c" * 64,
        evidence_count=2,
        context_count=2,
        relationship_count=1,
        missing_need_count=1,
        assembled_at=NOW,
        assembly_hash="d" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


def synthesis():
    return StructuralReasoningSynthesis(
        assembly_hash="d" * 64,
        signals=(
            StructuralReasoningSignal(
                signal_type="multi_evidence_context",
                subject="Astros strikeouts",
                evidence_observation_ids=("obs.1", "obs.2"),
                context_roles=(
                    "evidence",
                    "market_state",
                    "sports_context",
                ),
                relationship_types=(
                    "same_subject",
                ),
                signal_hash="e" * 64,
            ),
        ),
        signal_count=1,
        synthesis_hash="f" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


def support_profile():
    return ExplanationSupportProfile(
        synthesis_hash="f" * 64,
        items=(
            ExplanationSupportItem(
                subject="Astros strikeouts",
                support_class="multi_evidence_structure",
                evidence_count=2,
                context_role_count=3,
                relationship_type_count=1,
                support_hash="1" * 64,
            ),
        ),
        item_count=1,
        profile_hash="2" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


class TestOI045(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_reasoning_read_model()
        )

    def test_build(self):
        model = OracleReasoningReadModelBuilder().build(
            assembly=assembly(),
            synthesis=synthesis(),
            support_profile=support_profile(),
            built_at=NOW,
        )

        self.assertEqual(model.evidence_count, 2)
        self.assertEqual(model.relationship_count, 1)
        self.assertEqual(model.missing_need_count, 1)
        self.assertEqual(len(model.items), 1)

    def test_support_preserved(self):
        model = OracleReasoningReadModelBuilder().build(
            assembly=assembly(),
            synthesis=synthesis(),
            support_profile=support_profile(),
            built_at=NOW,
        )

        self.assertEqual(
            model.items[0].support_class,
            "multi_evidence_structure",
        )

    def test_partial_preserved(self):
        model = OracleReasoningReadModelBuilder().build(
            assembly=assembly(),
            synthesis=synthesis(),
            support_profile=support_profile(),
            built_at=NOW,
        )

        self.assertEqual(
            model.admission_status,
            "partial",
        )
        self.assertEqual(
            model.missing_need_count,
            1,
        )

    def test_deterministic(self):
        builder = OracleReasoningReadModelBuilder()

        a = builder.build(
            assembly=assembly(),
            synthesis=synthesis(),
            support_profile=support_profile(),
            built_at=NOW,
        )
        b = builder.build(
            assembly=assembly(),
            synthesis=synthesis(),
            support_profile=support_profile(),
            built_at=NOW,
        )

        self.assertEqual(
            a.read_model_hash,
            b.read_model_hash,
        )

    def test_side_effects(self):
        builder = OracleReasoningReadModelBuilder()

        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.prediction_allowed)
        self.assertFalse(builder.edge_score_allowed)
        self.assertFalse(builder.probability_allowed)
        self.assertFalse(builder.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-045 CERTIFICATION TEST")
    print(" ORACLE REASONING READ MODEL")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI045
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-045")
    print(f"[PASS] Revision: {OI_045_REVISION}")
    print("[PASS] Structural reasoning and explanation-support state exposed through deterministic Oracle read model")
    print("[PASS] Evidence count, relationships, admission status, and missing evidence preserved")
    print("[PASS] Read model remains non-causal, non-predictive, non-scoring, and read-only")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-045 CERTIFIED")
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
    print(" OI-045 INSTALLER")
    print(" ORACLE REASONING READ MODEL")
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
        "[PASS] Certified OI-042 through OI-044 "
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
        export = "from .oi_045_oracle_reasoning_read_model import *"

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
            "[PASS] Oracle reasoning read model remains deterministic, "
            "read-only, non-causal, and non-predictive"
        )
        print("[DONE] OI-045 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-045 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
