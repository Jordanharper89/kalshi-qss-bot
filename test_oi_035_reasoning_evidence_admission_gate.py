from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_033_oracle_evidence_intake_package import (
    OracleEvidenceIntakeItem,
    OracleEvidenceIntakePackage,
)
from qseries_v2.observation_intelligence.oi_034_canonical_evidence_materialization import (
    CanonicalEvidenceMaterialization,
    MaterializedEvidenceItem,
)
from qseries_v2.observation_intelligence.oi_035_reasoning_evidence_admission_gate import (
    OI_035_REVISION,
    ADMITTED,
    PARTIAL,
    REJECTED,
    ReasoningEvidenceAdmissionGate,
    verify_reasoning_evidence_admission_gate,
)

NOW = datetime(2026, 8, 11, 0, 0, tzinfo=timezone.utc)


def intake(missing=()):
    return OracleEvidenceIntakePackage(
        intake_id="intake.test",
        request_id="request.test",
        query_id="query.test",
        query_kind="explanation",
        subject_hint="Test market",
        profile_id="profile.market_explanation",
        acquisition_status="complete" if not missing else "partial",
        evidence_items=(
            OracleEvidenceIntakeItem(
                need_id="need.market",
                adapter_ids=("adapter.kalshi.v1",),
                evidence_hash="a" * 64,
                observation_count=1,
                satisfied=True,
                reason_code="satisfied",
                item_hash="b" * 64,
            ),
        ),
        total_observation_count=1,
        missing_need_ids=tuple(missing),
        complete_evidence_intake=not bool(missing),
        assembled_at=NOW,
        intake_hash="c" * 64,
        read_only=True,
        predictive=False,
        terminal_mutation_allowed=False,
    )


def materialization(
    *,
    count=1,
    match=True,
):
    items = (
        (
            MaterializedEvidenceItem(
                canonical_observation_id="obs.1",
                canonical_observation_hash="d" * 64,
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Test market",
                observation_type="market_snapshot",
                observed_at=NOW,
                materialization_hash="e" * 64,
            ),
        )
        if count
        else ()
    )

    return CanonicalEvidenceMaterialization(
        intake_id="intake.test",
        intake_hash="c" * 64,
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Test market",
        items=items,
        observation_count=count,
        complete_count_match=match,
        materialization_hash="f" * 64,
        read_only=True,
    )


class TestOI035(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_admission_gate()
        )

    def test_admitted(self):
        result = ReasoningEvidenceAdmissionGate().evaluate(
            intake=intake(),
            materialization=materialization(),
        )

        self.assertEqual(result.status, ADMITTED)

    def test_partial(self):
        result = ReasoningEvidenceAdmissionGate().evaluate(
            intake=intake(("need.lineup",)),
            materialization=materialization(),
        )

        self.assertEqual(result.status, PARTIAL)
        self.assertIn(
            "missing_required_observation_needs",
            result.reason_codes,
        )

    def test_rejected_empty(self):
        result = ReasoningEvidenceAdmissionGate().evaluate(
            intake=intake(),
            materialization=materialization(
                count=0,
                match=False,
            ),
        )

        self.assertEqual(result.status, REJECTED)

    def test_deterministic(self):
        gate = ReasoningEvidenceAdmissionGate()

        a = gate.evaluate(
            intake=intake(),
            materialization=materialization(),
        )
        b = gate.evaluate(
            intake=intake(),
            materialization=materialization(),
        )

        self.assertEqual(
            a.admission_hash,
            b.admission_hash,
        )

    def test_side_effects(self):
        gate = ReasoningEvidenceAdmissionGate()

        self.assertTrue(gate.read_only)
        self.assertFalse(gate.network_allowed)
        self.assertFalse(gate.persistence_allowed)
        self.assertFalse(gate.publication_allowed)
        self.assertFalse(gate.execution_allowed)
        self.assertFalse(gate.qseries_execution_allowed)
        self.assertFalse(gate.prediction_allowed)
        self.assertFalse(gate.edge_score_allowed)
        self.assertFalse(gate.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-035 CERTIFICATION TEST")
    print(" REASONING EVIDENCE ADMISSION GATE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI035
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-035")
    print(f"[PASS] Revision: {OI_035_REVISION}")
    print("[PASS] Admitted, partial, and rejected evidence states certified")
    print("[PASS] Missing needs and observation-count mismatches remain explicit")
    print("[PASS] Evidence admission fails closed before reasoning")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-035 CERTIFIED")
