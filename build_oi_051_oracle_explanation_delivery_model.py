from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-051"
INSTALLER_REVISION = "OI_051_ORACLE_EXPLANATION_DELIVERY_MODEL_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_048_oracle_explanation_readout.py", "OI-048"),
    (PACKAGE / "oi_049_explanation_evidence_ordering.py", "OI-049"),
    (PACKAGE / "oi_050_explanation_completeness_evaluation.py", "OI-050"),
)

MODULE = PACKAGE / "oi_051_oracle_explanation_delivery_model.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_051_oracle_explanation_delivery_model.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_048_oracle_explanation_readout import OracleExplanationReadout
from .oi_049_explanation_evidence_ordering import ExplanationEvidenceOrdering
from .oi_050_explanation_completeness_evaluation import (
    ExplanationCompletenessEvaluation,
)

BUILD_ID = "OI-051"
OI_051_REVISION = "OI_051_ORACLE_EXPLANATION_DELIVERY_MODEL_V1"

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
class OracleExplanationDeliveryModel:
    query_id: str
    subject_hint: str
    completeness_status: str
    headline: str
    ordered_explanations: tuple[str, ...]
    caveats: tuple[str, ...]
    delivered_at: datetime
    delivery_hash: str
    read_only: bool
    terminal_mutation_allowed: bool


class OracleExplanationDeliveryModelBuilder:
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

    def build(
        self,
        *,
        readout: OracleExplanationReadout,
        ordering: ExplanationEvidenceOrdering,
        completeness: ExplanationCompletenessEvaluation,
        delivered_at: datetime,
    ) -> OracleExplanationDeliveryModel:
        if not isinstance(readout, OracleExplanationReadout):
            raise TypeError("readout must be OracleExplanationReadout")
        if not isinstance(ordering, ExplanationEvidenceOrdering):
            raise TypeError(
                "ordering must be ExplanationEvidenceOrdering"
            )
        if not isinstance(
            completeness,
            ExplanationCompletenessEvaluation,
        ):
            raise TypeError(
                "completeness must be ExplanationCompletenessEvaluation"
            )

        if not (
            readout.query_id
            == ordering.query_id
            == completeness.query_id
        ):
            raise ValueError(
                "readout/ordering/completeness query_id mismatch"
            )

        if not isinstance(delivered_at, datetime):
            raise TypeError("delivered_at must be datetime")

        if delivered_at.tzinfo is None:
            raise ValueError(
                "delivered_at must be timezone-aware"
            )

        delivered_at = delivered_at.astimezone(timezone.utc)

        ordered_explanations = tuple(
            item.statement
            for item in ordering.items
        )

        caveats = tuple(
            sorted(
                set(readout.caveat_lines)
                | set(completeness.reason_codes)
            )
        )

        body = {
            "query_id": readout.query_id,
            "subject_hint": readout.subject_hint,
            "completeness_status": completeness.status,
            "headline": readout.headline,
            "ordered_explanations": ordered_explanations,
            "caveats": caveats,
            "delivered_at": delivered_at,
            "read_only": True,
            "terminal_mutation_allowed": False,
        }

        return OracleExplanationDeliveryModel(
            query_id=readout.query_id,
            subject_hint=readout.subject_hint,
            completeness_status=completeness.status,
            headline=readout.headline,
            ordered_explanations=ordered_explanations,
            caveats=caveats,
            delivered_at=delivered_at,
            delivery_hash=deterministic_sha256(body),
            read_only=True,
            terminal_mutation_allowed=False,
        )


def verify_oracle_explanation_delivery_model() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-051 must remain read-only")

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
        raise AssertionError("OI-051 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_051_REVISION",
    "OracleExplanationDeliveryModel",
    "OracleExplanationDeliveryModelBuilder",
    "verify_oracle_explanation_delivery_model",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_048_oracle_explanation_readout import (
    OracleExplanationReadout,
)
from qseries_v2.observation_intelligence.oi_049_explanation_evidence_ordering import (
    OrderedExplanationEvidenceItem,
    ExplanationEvidenceOrdering,
)
from qseries_v2.observation_intelligence.oi_050_explanation_completeness_evaluation import (
    ExplanationCompletenessEvaluation,
)
from qseries_v2.observation_intelligence.oi_051_oracle_explanation_delivery_model import (
    OI_051_REVISION,
    OracleExplanationDeliveryModelBuilder,
    verify_oracle_explanation_delivery_model,
)

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)


def readout():
    return OracleExplanationReadout(
        query_id="query.test",
        query_kind="explanation",
        subject_hint="Astros strikeouts",
        headline="Oracle Evidence Explanation — Astros strikeouts",
        explanation_lines=("Fallback statement",),
        caveat_lines=(
            "structural association does not establish causation",
        ),
        built_at=NOW,
        readout_hash="a" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
        terminal_mutation_allowed=False,
    )


def ordering():
    return ExplanationEvidenceOrdering(
        query_id="query.test",
        items=(
            OrderedExplanationEvidenceItem(
                ordinal=1,
                subject="Astros strikeouts",
                status="partial",
                statement="Ordered explanation statement",
                evidence_count=2,
                context_role_count=3,
                relationship_type_count=1,
                order_hash="b" * 64,
            ),
        ),
        item_count=1,
        ordering_hash="c" * 64,
        read_only=True,
    )


def completeness():
    return ExplanationCompletenessEvaluation(
        query_id="query.test",
        status="partial",
        supported_count=0,
        partial_count=1,
        unsupported_count=0,
        ordered_item_count=1,
        reason_codes=("partial_explanation_candidates",),
        evaluation_hash="d" * 64,
        read_only=True,
    )


class TestOI051(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_explanation_delivery_model()
        )

    def test_build(self):
        model = OracleExplanationDeliveryModelBuilder().build(
            readout=readout(),
            ordering=ordering(),
            completeness=completeness(),
            delivered_at=NOW,
        )

        self.assertEqual(
            model.completeness_status,
            "partial",
        )
        self.assertEqual(
            model.ordered_explanations,
            ("Ordered explanation statement",),
        )

    def test_caveats_merged(self):
        model = OracleExplanationDeliveryModelBuilder().build(
            readout=readout(),
            ordering=ordering(),
            completeness=completeness(),
            delivered_at=NOW,
        )

        self.assertIn(
            "partial_explanation_candidates",
            model.caveats,
        )
        self.assertIn(
            "structural association does not establish causation",
            model.caveats,
        )

    def test_deterministic(self):
        builder = OracleExplanationDeliveryModelBuilder()

        a = builder.build(
            readout=readout(),
            ordering=ordering(),
            completeness=completeness(),
            delivered_at=NOW,
        )
        b = builder.build(
            readout=readout(),
            ordering=ordering(),
            completeness=completeness(),
            delivered_at=NOW,
        )

        self.assertEqual(
            a.delivery_hash,
            b.delivery_hash,
        )

    def test_side_effects(self):
        item = OracleExplanationDeliveryModelBuilder()

        self.assertTrue(item.read_only)
        self.assertFalse(item.network_allowed)
        self.assertFalse(item.persistence_allowed)
        self.assertFalse(item.publication_allowed)
        self.assertFalse(item.execution_allowed)
        self.assertFalse(item.qseries_execution_allowed)
        self.assertFalse(item.prediction_allowed)
        self.assertFalse(item.edge_score_allowed)
        self.assertFalse(item.probability_allowed)
        self.assertFalse(item.causal_claim_allowed)
        self.assertFalse(item.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-051 CERTIFICATION TEST")
    print(" ORACLE EXPLANATION DELIVERY MODEL")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI051)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-051")
    print(f"[PASS] Revision: {OI_051_REVISION}")
    print("[PASS] Ordered explanation readout and completeness state merged into deterministic delivery model")
    print("[PASS] Explanation ordering, completeness status, caveats, and subject identity preserved")
    print("[PASS] Delivery remains read-only, terminal-safe, non-causal, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-051 CERTIFIED")
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
    print(" OI-051 INSTALLER")
    print(" ORACLE EXPLANATION DELIVERY MODEL")
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
        "[PASS] Certified OI-048 through OI-050 "
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
        export = "from .oi_051_oracle_explanation_delivery_model import *"

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
            "[PASS] Oracle explanation delivery remains deterministic, "
            "read-only, terminal-safe, and non-causal"
        )
        print("[DONE] OI-051 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-051 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
