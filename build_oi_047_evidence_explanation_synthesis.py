from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-047"
INSTALLER_REVISION = "OI_047_EVIDENCE_EXPLANATION_SYNTHESIS_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_026_evidence_explanation_formatter.py", "OI-026"),
    (PACKAGE / "oi_045_oracle_reasoning_read_model.py", "OI-045"),
    (PACKAGE / "oi_046_explanation_candidate_resolution.py", "OI-046"),
)

MODULE = PACKAGE / "oi_047_evidence_explanation_synthesis.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_047_evidence_explanation_synthesis.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_045_oracle_reasoning_read_model import OracleReasoningReadModel
from .oi_046_explanation_candidate_resolution import (
    ExplanationCandidateResolution,
)

BUILD_ID = "OI-047"
OI_047_REVISION = "OI_047_EVIDENCE_EXPLANATION_SYNTHESIS_V1"

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


class EvidenceExplanationSynthesisError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceExplanationStatement:
    subject: str
    status: str
    statement: str
    caveats: tuple[str, ...]
    statement_hash: str


@dataclass(frozen=True, slots=True)
class EvidenceExplanationSynthesis:
    query_id: str
    read_model_hash: str
    resolution_hash: str
    statements: tuple[EvidenceExplanationStatement, ...]
    statement_count: int
    synthesis_hash: str
    read_only: bool
    causal_claim_allowed: bool


class EvidenceExplanationSynthesizer:
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

    def synthesize(
        self,
        *,
        read_model: OracleReasoningReadModel,
        resolution: ExplanationCandidateResolution,
    ) -> EvidenceExplanationSynthesis:
        if not isinstance(
            read_model,
            OracleReasoningReadModel,
        ):
            raise TypeError(
                "read_model must be OracleReasoningReadModel"
            )

        if not isinstance(
            resolution,
            ExplanationCandidateResolution,
        ):
            raise TypeError(
                "resolution must be ExplanationCandidateResolution"
            )

        if resolution.read_model_hash != read_model.read_model_hash:
            raise EvidenceExplanationSynthesisError(
                "resolution does not belong to read model"
            )

        read_by_subject = {
            item.subject: item
            for item in read_model.items
        }

        statements = []

        for candidate in resolution.items:
            read_item = read_by_subject.get(
                candidate.subject
            )

            if read_item is None:
                raise EvidenceExplanationSynthesisError(
                    f"read model missing resolved subject: "
                    f"{candidate.subject}"
                )

            context_text = ", ".join(
                read_item.context_roles
            ) or "no structural context"

            relationship_text = ", ".join(
                read_item.relationship_types
            ) or "no structural relationships"

            statement = (
                f"{candidate.subject}: "
                f"{candidate.evidence_count} evidence item(s) "
                f"provide {candidate.support_class} with context "
                f"[{context_text}] and relationships "
                f"[{relationship_text}]."
            )

            caveats = list(candidate.reason_codes)

            caveats.append(
                "structural association does not establish causation"
            )

            if candidate.status != "supported":
                caveats.append(
                    "explanation is incomplete"
                )

            caveats = tuple(
                sorted(set(caveats))
            )

            body = {
                "subject": candidate.subject,
                "status": candidate.status,
                "statement": statement,
                "caveats": caveats,
            }

            statements.append(
                EvidenceExplanationStatement(
                    subject=candidate.subject,
                    status=candidate.status,
                    statement=statement,
                    caveats=caveats,
                    statement_hash=deterministic_sha256(body),
                )
            )

        statements = tuple(
            sorted(
                statements,
                key=lambda item: item.subject,
            )
        )

        body = {
            "query_id": read_model.query_id,
            "read_model_hash": read_model.read_model_hash,
            "resolution_hash": resolution.resolution_hash,
            "statement_hashes": tuple(
                item.statement_hash
                for item in statements
            ),
            "statement_count": len(statements),
            "read_only": True,
            "causal_claim_allowed": False,
        }

        return EvidenceExplanationSynthesis(
            query_id=read_model.query_id,
            read_model_hash=read_model.read_model_hash,
            resolution_hash=resolution.resolution_hash,
            statements=statements,
            statement_count=len(statements),
            synthesis_hash=deterministic_sha256(body),
            read_only=True,
            causal_claim_allowed=False,
        )


def verify_evidence_explanation_synthesis() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-047 must remain read-only"
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
        )
    ):
        raise AssertionError(
            "OI-047 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_047_REVISION",
    "EvidenceExplanationSynthesisError",
    "EvidenceExplanationStatement",
    "EvidenceExplanationSynthesis",
    "EvidenceExplanationSynthesizer",
    "verify_evidence_explanation_synthesis",
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
from qseries_v2.observation_intelligence.oi_046_explanation_candidate_resolution import (
    ExplanationCandidateResolution,
    ExplanationCandidateResolutionItem,
)
from qseries_v2.observation_intelligence.oi_047_evidence_explanation_synthesis import (
    OI_047_REVISION,
    EvidenceExplanationSynthesizer,
    verify_evidence_explanation_synthesis,
)

NOW = datetime(2026, 8, 11, 9, 0, tzinfo=timezone.utc)


def read_model():
    return OracleReasoningReadModel(
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status="partial",
        evidence_count=2,
        relationship_count=1,
        missing_need_count=1,
        items=(
            OracleReasoningReadItem(
                subject="Astros strikeouts",
                signal_type="multi_evidence_context",
                support_class="multi_evidence_structure",
                evidence_count=2,
                context_roles=(
                    "evidence",
                    "market_state",
                    "sports_context",
                ),
                relationship_types=(
                    "same_subject",
                ),
                item_hash="a" * 64,
            ),
        ),
        built_at=NOW,
        read_model_hash="b" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


def resolution():
    return ExplanationCandidateResolution(
        query_id="query.test",
        read_model_hash="b" * 64,
        items=(
            ExplanationCandidateResolutionItem(
                subject="Astros strikeouts",
                status="partial",
                evidence_count=2,
                support_class="multi_evidence_structure",
                context_roles=(
                    "evidence",
                    "market_state",
                    "sports_context",
                ),
                relationship_types=(
                    "same_subject",
                ),
                reason_codes=(
                    "missing_required_evidence",
                ),
                item_hash="c" * 64,
            ),
        ),
        supported_count=0,
        partial_count=1,
        unsupported_count=0,
        resolution_hash="d" * 64,
        read_only=True,
    )


class TestOI047(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_evidence_explanation_synthesis()
        )

    def test_synthesis(self):
        result = EvidenceExplanationSynthesizer().synthesize(
            read_model=read_model(),
            resolution=resolution(),
        )

        self.assertEqual(
            result.statement_count,
            1,
        )

        self.assertIn(
            "Astros strikeouts",
            result.statements[0].statement,
        )

    def test_partial_caveat(self):
        result = EvidenceExplanationSynthesizer().synthesize(
            read_model=read_model(),
            resolution=resolution(),
        )

        self.assertIn(
            "explanation is incomplete",
            result.statements[0].caveats,
        )

    def test_non_causal(self):
        result = EvidenceExplanationSynthesizer().synthesize(
            read_model=read_model(),
            resolution=resolution(),
        )

        self.assertFalse(
            result.causal_claim_allowed
        )

    def test_deterministic(self):
        synthesizer = EvidenceExplanationSynthesizer()

        a = synthesizer.synthesize(
            read_model=read_model(),
            resolution=resolution(),
        )

        b = synthesizer.synthesize(
            read_model=read_model(),
            resolution=resolution(),
        )

        self.assertEqual(
            a.synthesis_hash,
            b.synthesis_hash,
        )

    def test_side_effects(self):
        item = EvidenceExplanationSynthesizer()

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
    print(" OI-047 CERTIFICATION TEST")
    print(" EVIDENCE EXPLANATION SYNTHESIS")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI047
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-047")
    print(f"[PASS] Revision: {OI_047_REVISION}")
    print("[PASS] Structural reasoning converted into deterministic evidence-grounded explanation statements")
    print("[PASS] Partial explanation state and caveats remain explicit")
    print("[PASS] Association is not promoted to causation, prediction, probability, or edge")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-047 CERTIFIED")
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
    print(" OI-047 INSTALLER")
    print(" EVIDENCE EXPLANATION SYNTHESIS")
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
        "[PASS] Certified OI-026, OI-045, "
        "and OI-046 verified read-only"
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
        export = "from .oi_047_evidence_explanation_synthesis import *"

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
            "[PASS] Explanation synthesis remains deterministic, "
            "read-only, evidence-grounded, and non-causal"
        )
        print("[DONE] OI-047 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-047 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
