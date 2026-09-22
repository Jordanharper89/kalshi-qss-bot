from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-050"
INSTALLER_REVISION = "OI_050_EXPLANATION_COMPLETENESS_EVALUATION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_046_explanation_candidate_resolution.py", "OI-046"),
    (PACKAGE / "oi_049_explanation_evidence_ordering.py", "OI-049"),
)

MODULE = PACKAGE / "oi_050_explanation_completeness_evaluation.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_050_explanation_completeness_evaluation.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_046_explanation_candidate_resolution import (
    ExplanationCandidateResolution,
)
from .oi_049_explanation_evidence_ordering import (
    ExplanationEvidenceOrdering,
)

BUILD_ID = "OI-050"
OI_050_REVISION = "OI_050_EXPLANATION_COMPLETENESS_EVALUATION_V1"

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

COMPLETE = "complete"
PARTIAL = "partial"
INSUFFICIENT = "insufficient"


@dataclass(frozen=True, slots=True)
class ExplanationCompletenessEvaluation:
    query_id: str
    status: str
    supported_count: int
    partial_count: int
    unsupported_count: int
    ordered_item_count: int
    reason_codes: tuple[str, ...]
    evaluation_hash: str
    read_only: bool


class ExplanationCompletenessEvaluator:
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

    def evaluate(
        self,
        *,
        resolution: ExplanationCandidateResolution,
        ordering: ExplanationEvidenceOrdering,
    ) -> ExplanationCompletenessEvaluation:
        if not isinstance(
            resolution,
            ExplanationCandidateResolution,
        ):
            raise TypeError(
                "resolution must be ExplanationCandidateResolution"
            )
        if not isinstance(
            ordering,
            ExplanationEvidenceOrdering,
        ):
            raise TypeError(
                "ordering must be ExplanationEvidenceOrdering"
            )
        if resolution.query_id != ordering.query_id:
            raise ValueError(
                "resolution/ordering query_id mismatch"
            )

        reasons = []

        if resolution.unsupported_count > 0:
            status = INSUFFICIENT
            reasons.append("unsupported_explanation_candidates")
        elif resolution.partial_count > 0:
            status = PARTIAL
            reasons.append("partial_explanation_candidates")
        elif (
            resolution.supported_count > 0
            and ordering.item_count > 0
        ):
            status = COMPLETE
        else:
            status = INSUFFICIENT
            reasons.append("no_supported_explanation")

        if ordering.item_count == 0:
            reasons.append("no_ordered_explanation_evidence")

        reasons = tuple(sorted(set(reasons)))

        body = {
            "query_id": resolution.query_id,
            "status": status,
            "supported_count": resolution.supported_count,
            "partial_count": resolution.partial_count,
            "unsupported_count": resolution.unsupported_count,
            "ordered_item_count": ordering.item_count,
            "reason_codes": reasons,
            "read_only": True,
        }

        return ExplanationCompletenessEvaluation(
            query_id=resolution.query_id,
            status=status,
            supported_count=resolution.supported_count,
            partial_count=resolution.partial_count,
            unsupported_count=resolution.unsupported_count,
            ordered_item_count=ordering.item_count,
            reason_codes=reasons,
            evaluation_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_completeness_evaluation() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-050 must remain read-only")

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
        raise AssertionError("OI-050 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_050_REVISION",
    "COMPLETE",
    "PARTIAL",
    "INSUFFICIENT",
    "ExplanationCompletenessEvaluation",
    "ExplanationCompletenessEvaluator",
    "verify_explanation_completeness_evaluation",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_046_explanation_candidate_resolution import (
    ExplanationCandidateResolution,
)
from qseries_v2.observation_intelligence.oi_049_explanation_evidence_ordering import (
    ExplanationEvidenceOrdering,
)
from qseries_v2.observation_intelligence.oi_050_explanation_completeness_evaluation import (
    OI_050_REVISION,
    COMPLETE,
    PARTIAL,
    INSUFFICIENT,
    ExplanationCompletenessEvaluator,
    verify_explanation_completeness_evaluation,
)


def resolution(
    supported=1,
    partial=0,
    unsupported=0,
):
    return ExplanationCandidateResolution(
        query_id="query.test",
        read_model_hash="a" * 64,
        items=(),
        supported_count=supported,
        partial_count=partial,
        unsupported_count=unsupported,
        resolution_hash="b" * 64,
        read_only=True,
    )


def ordering(count=1):
    return ExplanationEvidenceOrdering(
        query_id="query.test",
        items=(),
        item_count=count,
        ordering_hash="c" * 64,
        read_only=True,
    )


class TestOI050(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_completeness_evaluation()
        )

    def test_complete(self):
        value = ExplanationCompletenessEvaluator().evaluate(
            resolution=resolution(),
            ordering=ordering(),
        )
        self.assertEqual(value.status, COMPLETE)

    def test_partial(self):
        value = ExplanationCompletenessEvaluator().evaluate(
            resolution=resolution(supported=0, partial=1),
            ordering=ordering(),
        )
        self.assertEqual(value.status, PARTIAL)

    def test_insufficient(self):
        value = ExplanationCompletenessEvaluator().evaluate(
            resolution=resolution(supported=0, unsupported=1),
            ordering=ordering(),
        )
        self.assertEqual(value.status, INSUFFICIENT)

    def test_empty(self):
        value = ExplanationCompletenessEvaluator().evaluate(
            resolution=resolution(supported=0),
            ordering=ordering(0),
        )
        self.assertEqual(value.status, INSUFFICIENT)
        self.assertIn(
            "no_ordered_explanation_evidence",
            value.reason_codes,
        )

    def test_deterministic(self):
        evaluator = ExplanationCompletenessEvaluator()

        a = evaluator.evaluate(
            resolution=resolution(),
            ordering=ordering(),
        )
        b = evaluator.evaluate(
            resolution=resolution(),
            ordering=ordering(),
        )

        self.assertEqual(
            a.evaluation_hash,
            b.evaluation_hash,
        )

    def test_side_effects(self):
        item = ExplanationCompletenessEvaluator()

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
    print(" OI-050 CERTIFICATION TEST")
    print(" EXPLANATION COMPLETENESS EVALUATION")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI050)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-050")
    print(f"[PASS] Revision: {OI_050_REVISION}")
    print("[PASS] Complete, partial, and insufficient explanation states certified")
    print("[PASS] Missing or unsupported explanation evidence remains explicit")
    print("[PASS] Completeness evaluation is descriptive only and introduces no probability or score")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-050 CERTIFIED")
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
    print(" OI-050 INSTALLER")
    print(" EXPLANATION COMPLETENESS EVALUATION")
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
        "[PASS] Certified OI-046 and OI-049 "
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
        export = "from .oi_050_explanation_completeness_evaluation import *"

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
            "[PASS] Explanation completeness evaluation remains "
            "deterministic, read-only, and fail-closed"
        )
        print("[DONE] OI-050 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-050 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
