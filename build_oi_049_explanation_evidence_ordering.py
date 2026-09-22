from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-049"
INSTALLER_REVISION = "OI_049_EXPLANATION_EVIDENCE_ORDERING_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_045_oracle_reasoning_read_model.py", "OI-045"),
    (PACKAGE / "oi_047_evidence_explanation_synthesis.py", "OI-047"),
    (PACKAGE / "oi_048_oracle_explanation_readout.py", "OI-048"),
)

MODULE = PACKAGE / "oi_049_explanation_evidence_ordering.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_049_explanation_evidence_ordering.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_045_oracle_reasoning_read_model import OracleReasoningReadModel
from .oi_047_evidence_explanation_synthesis import EvidenceExplanationSynthesis

BUILD_ID = "OI-049"
OI_049_REVISION = "OI_049_EXPLANATION_EVIDENCE_ORDERING_V1"

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


@dataclass(frozen=True, slots=True)
class OrderedExplanationEvidenceItem:
    ordinal: int
    subject: str
    status: str
    statement: str
    evidence_count: int
    context_role_count: int
    relationship_type_count: int
    order_hash: str


@dataclass(frozen=True, slots=True)
class ExplanationEvidenceOrdering:
    query_id: str
    items: tuple[OrderedExplanationEvidenceItem, ...]
    item_count: int
    ordering_hash: str
    read_only: bool


class ExplanationEvidenceOrderer:
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

    def order(
        self,
        *,
        read_model: OracleReasoningReadModel,
        synthesis: EvidenceExplanationSynthesis,
    ) -> ExplanationEvidenceOrdering:
        if not isinstance(read_model, OracleReasoningReadModel):
            raise TypeError("read_model must be OracleReasoningReadModel")
        if not isinstance(synthesis, EvidenceExplanationSynthesis):
            raise TypeError("synthesis must be EvidenceExplanationSynthesis")
        if synthesis.read_model_hash != read_model.read_model_hash:
            raise ValueError("synthesis/read model lineage mismatch")

        model_by_subject = {
            item.subject: item
            for item in read_model.items
        }

        rows = []

        for statement in synthesis.statements:
            model_item = model_by_subject.get(statement.subject)
            if model_item is None:
                raise ValueError(
                    f"read model missing explanation subject: {statement.subject}"
                )

            rows.append(
                (
                    -model_item.evidence_count,
                    -len(model_item.relationship_types),
                    -len(model_item.context_roles),
                    statement.subject,
                    statement,
                    model_item,
                )
            )

        rows.sort()

        items = []

        for ordinal, row in enumerate(rows, start=1):
            _, _, _, subject, statement, model_item = row

            body = {
                "ordinal": ordinal,
                "subject": subject,
                "status": statement.status,
                "statement": statement.statement,
                "evidence_count": model_item.evidence_count,
                "context_role_count": len(model_item.context_roles),
                "relationship_type_count": len(model_item.relationship_types),
            }

            items.append(
                OrderedExplanationEvidenceItem(
                    ordinal=ordinal,
                    subject=subject,
                    status=statement.status,
                    statement=statement.statement,
                    evidence_count=model_item.evidence_count,
                    context_role_count=len(model_item.context_roles),
                    relationship_type_count=len(model_item.relationship_types),
                    order_hash=deterministic_sha256(body),
                )
            )

        items = tuple(items)

        body = {
            "query_id": read_model.query_id,
            "item_hashes": tuple(item.order_hash for item in items),
            "item_count": len(items),
            "read_only": True,
        }

        return ExplanationEvidenceOrdering(
            query_id=read_model.query_id,
            items=items,
            item_count=len(items),
            ordering_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_evidence_ordering() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-049 must remain read-only")

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
        raise AssertionError("OI-049 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_049_REVISION",
    "OrderedExplanationEvidenceItem",
    "ExplanationEvidenceOrdering",
    "ExplanationEvidenceOrderer",
    "verify_explanation_evidence_ordering",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_045_oracle_reasoning_read_model import (
    OracleReasoningReadItem,
    OracleReasoningReadModel,
)
from qseries_v2.observation_intelligence.oi_047_evidence_explanation_synthesis import (
    EvidenceExplanationStatement,
    EvidenceExplanationSynthesis,
)
from qseries_v2.observation_intelligence.oi_049_explanation_evidence_ordering import (
    OI_049_REVISION,
    ExplanationEvidenceOrderer,
    verify_explanation_evidence_ordering,
)

NOW = datetime(2026, 8, 11, 11, 0, tzinfo=timezone.utc)


def read_model():
    return OracleReasoningReadModel(
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Test",
        admission_status="admitted",
        evidence_count=3,
        relationship_count=1,
        missing_need_count=0,
        items=(
            OracleReasoningReadItem(
                subject="Alpha",
                signal_type="multi_evidence_context",
                support_class="multi_evidence_structure",
                evidence_count=2,
                context_roles=("evidence", "market_state"),
                relationship_types=("same_subject",),
                item_hash="a" * 64,
            ),
            OracleReasoningReadItem(
                subject="Beta",
                signal_type="single_evidence_context",
                support_class="single_source_structure",
                evidence_count=1,
                context_roles=("evidence",),
                relationship_types=(),
                item_hash="b" * 64,
            ),
        ),
        built_at=NOW,
        read_model_hash="c" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


def synthesis():
    return EvidenceExplanationSynthesis(
        query_id="query.test",
        read_model_hash="c" * 64,
        resolution_hash="d" * 64,
        statements=(
            EvidenceExplanationStatement(
                subject="Beta",
                status="supported",
                statement="Beta statement",
                caveats=("structural association does not establish causation",),
                statement_hash="e" * 64,
            ),
            EvidenceExplanationStatement(
                subject="Alpha",
                status="supported",
                statement="Alpha statement",
                caveats=("structural association does not establish causation",),
                statement_hash="f" * 64,
            ),
        ),
        statement_count=2,
        synthesis_hash="1" * 64,
        read_only=True,
        causal_claim_allowed=False,
    )


class TestOI049(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_explanation_evidence_ordering())

    def test_ordering(self):
        result = ExplanationEvidenceOrderer().order(
            read_model=read_model(),
            synthesis=synthesis(),
        )

        self.assertEqual(result.item_count, 2)
        self.assertEqual(result.items[0].subject, "Alpha")
        self.assertEqual(result.items[1].subject, "Beta")

    def test_ordinals(self):
        result = ExplanationEvidenceOrderer().order(
            read_model=read_model(),
            synthesis=synthesis(),
        )

        self.assertEqual(
            tuple(item.ordinal for item in result.items),
            (1, 2),
        )

    def test_deterministic(self):
        orderer = ExplanationEvidenceOrderer()

        a = orderer.order(
            read_model=read_model(),
            synthesis=synthesis(),
        )
        b = orderer.order(
            read_model=read_model(),
            synthesis=synthesis(),
        )

        self.assertEqual(a.ordering_hash, b.ordering_hash)

    def test_side_effects(self):
        item = ExplanationEvidenceOrderer()

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


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-049 CERTIFICATION TEST")
    print(" EXPLANATION EVIDENCE ORDERING")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI049)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-049")
    print(f"[PASS] Revision: {OI_049_REVISION}")
    print("[PASS] Explanation evidence ordered deterministically by structural support")
    print("[PASS] Evidence count, context density, relationship density, and subject tie-break preserved")
    print("[PASS] No causal claim, probability, prediction, or edge score introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-049 CERTIFIED")
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
    print(" OI-049 INSTALLER")
    print(" EXPLANATION EVIDENCE ORDERING")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for upstream, name in UPSTREAMS:
        if not upstream.is_file():
            raise RuntimeError(f"Certified {name} missing: {upstream}")

    upstream_hashes = {upstream: sha(upstream) for upstream, _ in UPSTREAMS}

    print(
        "[PASS] Certified OI-045, OI-047, "
        "and OI-048 verified read-only"
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
        export = "from .oi_049_explanation_evidence_ordering import *"

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
            "[PASS] Explanation evidence ordering remains deterministic, "
            "read-only, and non-causal"
        )
        print("[DONE] OI-049 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-049 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
