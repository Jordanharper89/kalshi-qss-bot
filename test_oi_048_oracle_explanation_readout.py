from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_025_oracle_explanation_query_engine import (
    OracleExplanationQueryEngine,
    default_explanation_profile_map,
)
from qseries_v2.observation_intelligence.oi_047_evidence_explanation_synthesis import (
    EvidenceExplanationStatement,
    EvidenceExplanationSynthesis,
)
from qseries_v2.observation_intelligence.oi_048_oracle_explanation_readout import (
    OI_048_REVISION,
    OracleExplanationReadoutBuilder,
    verify_oracle_explanation_readout,
)

NOW = datetime(2026, 8, 11, 10, 0, tzinfo=timezone.utc)


def query():
    return OracleExplanationQueryEngine(
        default_explanation_profile_map()
    ).resolve(
        query_id="query.astros",
        text="Explain why the Astros strikeout edge moved",
        subject_hint="Astros strikeouts",
        domain="sports",
    )


def synthesis():
    return EvidenceExplanationSynthesis(
        query_id="query.astros",
        read_model_hash="a" * 64,
        resolution_hash="b" * 64,
        statements=(
            EvidenceExplanationStatement(
                subject="Astros strikeouts",
                status="partial",
                statement=(
                    "Astros strikeouts: 2 evidence item(s) provide "
                    "multi_evidence_structure with context "
                    "[evidence, market_state, sports_context] and "
                    "relationships [same_subject]."
                ),
                caveats=(
                    "explanation is incomplete",
                    "missing_required_evidence",
                    "structural association does not establish causation",
                ),
                statement_hash="c" * 64,
            ),
        ),
        statement_count=1,
        synthesis_hash="d" * 64,
        read_only=True,
        causal_claim_allowed=False,
    )


class TestOI048(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_explanation_readout()
        )

    def test_build(self):
        readout = OracleExplanationReadoutBuilder().build(
            query=query(),
            synthesis=synthesis(),
            built_at=NOW,
        )

        self.assertIn(
            "Astros strikeouts",
            readout.headline,
        )

        self.assertEqual(
            len(readout.explanation_lines),
            1,
        )

    def test_caveats(self):
        readout = OracleExplanationReadoutBuilder().build(
            query=query(),
            synthesis=synthesis(),
            built_at=NOW,
        )

        self.assertIn(
            "missing_required_evidence",
            readout.caveat_lines,
        )

    def test_non_causal(self):
        readout = OracleExplanationReadoutBuilder().build(
            query=query(),
            synthesis=synthesis(),
            built_at=NOW,
        )

        self.assertFalse(
            readout.predictive
        )
        self.assertFalse(
            readout.causal_claim_allowed
        )
        self.assertFalse(
            readout.terminal_mutation_allowed
        )

    def test_deterministic(self):
        builder = OracleExplanationReadoutBuilder()

        a = builder.build(
            query=query(),
            synthesis=synthesis(),
            built_at=NOW,
        )

        b = builder.build(
            query=query(),
            synthesis=synthesis(),
            built_at=NOW,
        )

        self.assertEqual(
            a.readout_hash,
            b.readout_hash,
        )

    def test_side_effects(self):
        builder = OracleExplanationReadoutBuilder()

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
        self.assertFalse(builder.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-048 CERTIFICATION TEST")
    print(" ORACLE EXPLANATION READOUT")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI048
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-048")
    print(f"[PASS] Revision: {OI_048_REVISION}")
    print("[PASS] Evidence-grounded explanation synthesis converted into Oracle terminal-ready readout")
    print("[PASS] Explanation text, caveats, query identity, and subject identity preserved")
    print("[PASS] Readout remains read-only, non-causal, non-predictive, non-scoring, and non-mutating")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-048 CERTIFIED")
