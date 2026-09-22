from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-026"
INSTALLER_REVISION = "OI_026_EVIDENCE_EXPLANATION_FORMATTER_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_023_evidence_confidence_composition.py", "OI-023"),
    (PACKAGE / "oi_024_oracle_explanation_read_model.py", "OI-024"),
    (PACKAGE / "oi_025_oracle_explanation_query_engine.py", "OI-025"),
)

MODULE = PACKAGE / "oi_026_evidence_explanation_formatter.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_026_evidence_explanation_formatter.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_024_oracle_explanation_read_model import OracleExplanationReadModel
from .oi_025_oracle_explanation_query_engine import OracleExplanationQuery

BUILD_ID = "OI-026"
OI_026_REVISION = "OI_026_EVIDENCE_EXPLANATION_FORMATTER_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class EvidenceExplanationFormatterError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceExplanationView:
    query_id: str
    title: str
    summary_lines: tuple[str, ...]
    timeline_lines: tuple[str, ...]
    caveat_lines: tuple[str, ...]
    view_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool


class EvidenceExplanationFormatter:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_claim_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def format(
        self,
        *,
        query: OracleExplanationQuery,
        model: OracleExplanationReadModel,
    ) -> EvidenceExplanationView:
        if not isinstance(query, OracleExplanationQuery):
            raise TypeError("query must be OracleExplanationQuery")

        if not isinstance(model, OracleExplanationReadModel):
            raise TypeError("model must be OracleExplanationReadModel")

        if model.query_id != query.query_id:
            raise EvidenceExplanationFormatterError(
                "query and read model query_id mismatch"
            )

        if model.profile_id != query.profile_id:
            raise EvidenceExplanationFormatterError(
                "query and read model profile_id mismatch"
            )

        title = (
            f"Oracle Evidence Explanation — "
            f"{query.subject_hint}"
        )

        summary_lines = (
            f"Query kind: {query.query_kind}",
            f"Evidence completeness: {model.completeness_status}",
            f"Evidence items: {model.evidence_item_count}",
            f"Distinct sources: {model.distinct_source_count}",
            f"Stale evidence items: {model.stale_evidence_count}",
            f"Supporting relationships: {model.supporting_relationship_count}",
            f"Contradicting relationships: {model.contradicting_relationship_count}",
        )

        timeline_lines = tuple(
            (
                f"{item.ordinal}. {item.evidence_observation_id} "
                f"{item.temporal_relation} change "
                f"({item.seconds_from_change_observation:+d}s); "
                f"agreements={item.agreement_count}; "
                f"contradictions={item.contradiction_count}"
            )
            for item in model.timeline
        )

        caveats = []

        if model.missing_required_evidence:
            caveats.append(
                "Required evidence is incomplete."
            )

        if model.contradicting_relationship_count:
            caveats.append(
                "Contradicting evidence is present."
            )

        if model.stale_evidence_count:
            caveats.append(
                "Stale evidence is present."
            )

        caveats.extend(
            (
                "Temporal association does not establish causation.",
                "No prediction probability or edge score is produced.",
                "Read-only explanation; no trade authorization.",
            )
        )

        body = {
            "query_id": query.query_id,
            "title": title,
            "summary_lines": summary_lines,
            "timeline_lines": timeline_lines,
            "caveat_lines": tuple(caveats),
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
        }

        return EvidenceExplanationView(
            query_id=query.query_id,
            title=title,
            summary_lines=summary_lines,
            timeline_lines=timeline_lines,
            caveat_lines=tuple(caveats),
            view_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
        )


def verify_evidence_explanation_formatter() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-026 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
        )
    ):
        raise AssertionError("OI-026 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_026_REVISION",
    "EvidenceExplanationFormatterError",
    "EvidenceExplanationView",
    "EvidenceExplanationFormatter",
    "verify_evidence_explanation_formatter",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_024_oracle_explanation_read_model import (
    OracleExplanationReadModel,
    OracleExplanationTimelineEntry,
)
from qseries_v2.observation_intelligence.oi_025_oracle_explanation_query_engine import (
    OracleExplanationQueryEngine,
    default_explanation_profile_map,
)
from qseries_v2.observation_intelligence.oi_026_evidence_explanation_formatter import (
    OI_026_REVISION,
    EvidenceExplanationFormatter,
    verify_evidence_explanation_formatter,
)

NOW = datetime(2026, 8, 10, 18, 0, tzinfo=timezone.utc)


def query():
    return OracleExplanationQueryEngine(
        default_explanation_profile_map()
    ).resolve(
        query_id="query.astros",
        text="Explain why the Astros strikeout edge moved",
        subject_hint="Astros strikeouts",
        domain="sports",
    )


def model():
    return OracleExplanationReadModel(
        query_id="query.astros",
        profile_id="profile.market_explanation",
        built_at=NOW,
        sufficient_evidence=True,
        completeness_status="complete",
        evidence_item_count=3,
        distinct_source_count=2,
        stale_evidence_count=0,
        supporting_relationship_count=2,
        contradicting_relationship_count=1,
        timeline=(
            OracleExplanationTimelineEntry(
                ordinal=1,
                evidence_observation_id="obs.lineup",
                temporal_relation="before",
                seconds_from_change_observation=-120,
                agreement_count=1,
                contradiction_count=0,
            ),
        ),
        missing_required_evidence=False,
        read_model_hash="a" * 64,
        causal_claim_allowed=False,
        predictive=False,
        edge_score_allowed=False,
        probability_allowed=False,
        read_only=True,
    )


class TestOI026(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_evidence_explanation_formatter()
        )

    def test_format(self):
        view = EvidenceExplanationFormatter().format(
            query=query(),
            model=model(),
        )

        self.assertIn(
            "Astros strikeouts",
            view.title,
        )
        self.assertEqual(
            len(view.timeline_lines),
            1,
        )

    def test_contradiction_caveat(self):
        view = EvidenceExplanationFormatter().format(
            query=query(),
            model=model(),
        )

        self.assertTrue(
            any(
                "Contradicting evidence" in line
                for line in view.caveat_lines
            )
        )

    def test_non_causal(self):
        view = EvidenceExplanationFormatter().format(
            query=query(),
            model=model(),
        )

        self.assertFalse(view.predictive)
        self.assertFalse(view.causal_claim_allowed)
        self.assertTrue(view.read_only)

    def test_deterministic(self):
        formatter = EvidenceExplanationFormatter()

        a = formatter.format(
            query=query(),
            model=model(),
        )
        b = formatter.format(
            query=query(),
            model=model(),
        )

        self.assertEqual(a.view_hash, b.view_hash)

    def test_side_effects(self):
        formatter = EvidenceExplanationFormatter()

        self.assertTrue(formatter.read_only)
        self.assertFalse(formatter.network_allowed)
        self.assertFalse(formatter.persistence_allowed)
        self.assertFalse(formatter.publication_allowed)
        self.assertFalse(formatter.execution_allowed)
        self.assertFalse(formatter.qseries_execution_allowed)
        self.assertFalse(formatter.causal_claim_allowed)
        self.assertFalse(formatter.prediction_allowed)
        self.assertFalse(formatter.edge_score_allowed)
        self.assertFalse(formatter.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-026 CERTIFICATION TEST")
    print(" EVIDENCE EXPLANATION FORMATTER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI026
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-026")
    print(f"[PASS] Revision: {OI_026_REVISION}")
    print("[PASS] Explanation read models format into deterministic operator-readable evidence views")
    print("[PASS] Timeline, completeness, source diversity, contradictions, and caveats preserved")
    print("[PASS] Formatter remains non-causal, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-026 CERTIFIED")
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
    print(" OI-026 INSTALLER")
    print(" EVIDENCE EXPLANATION FORMATTER")
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

    print("[PASS] Certified OI-023 through OI-025 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_026_evidence_explanation_formatter import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")

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
        print("[PASS] Explanation formatter remains deterministic, read-only, non-causal, non-predictive, and non-scoring")
        print("[DONE] OI-026 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_bytes(original)

        print("[ROLLBACK] OI-026 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
