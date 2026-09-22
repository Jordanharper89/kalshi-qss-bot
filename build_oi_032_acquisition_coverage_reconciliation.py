from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-032"
INSTALLER_REVISION = "OI_032_ACQUISITION_COVERAGE_RECONCILIATION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_016_evidence_sufficiency_gate.py", "OI-016"),
    (PACKAGE / "oi_029_observation_acquisition_plan.py", "OI-029"),
    (PACKAGE / "oi_031_oracle_observation_request_dispatcher.py", "OI-031"),
)

MODULE = PACKAGE / "oi_032_acquisition_coverage_reconciliation.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_032_acquisition_coverage_reconciliation.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_029_observation_acquisition_plan import ObservationAcquisitionPlan
from .oi_031_oracle_observation_request_dispatcher import (
    OracleObservationDispatchResult,
)

BUILD_ID = "OI-032"
OI_032_REVISION = "OI_032_ACQUISITION_COVERAGE_RECONCILIATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False

STATUS_COMPLETE = "complete"
STATUS_PARTIAL = "partial"
STATUS_EMPTY = "empty"


class AcquisitionCoverageReconciliationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AcquisitionCoverageItem:
    need_id: str
    planned_covered: bool
    dispatched_covered: bool
    observation_count: int
    acquisition_present: bool
    satisfied: bool
    reason_code: str
    item_hash: str


@dataclass(frozen=True, slots=True)
class AcquisitionCoverageReconciliation:
    plan_hash: str
    dispatch_hash: str
    items: tuple[AcquisitionCoverageItem, ...]
    satisfied_count: int
    unsatisfied_count: int
    observation_count: int
    status: str
    reconciliation_hash: str
    read_only: bool


class AcquisitionCoverageReconciler:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def reconcile(
        self,
        *,
        plan: ObservationAcquisitionPlan,
        dispatch: OracleObservationDispatchResult,
    ) -> AcquisitionCoverageReconciliation:
        if not isinstance(plan, ObservationAcquisitionPlan):
            raise TypeError(
                "plan must be ObservationAcquisitionPlan"
            )

        if not isinstance(
            dispatch,
            OracleObservationDispatchResult,
        ):
            raise TypeError(
                "dispatch must be OracleObservationDispatchResult"
            )

        if dispatch.plan_hash != plan.plan_hash:
            raise AcquisitionCoverageReconciliationError(
                "dispatch and plan hash mismatch"
            )

        dispatch_by_need = {
            item.need_id: item
            for item in dispatch.items
        }

        if len(dispatch_by_need) != len(dispatch.items):
            raise AcquisitionCoverageReconciliationError(
                "duplicate dispatch need_id"
            )

        items = []

        for plan_item in plan.items:
            dispatched = dispatch_by_need.get(
                plan_item.need_id
            )

            if dispatched is None:
                raise AcquisitionCoverageReconciliationError(
                    f"dispatch missing planned need: {plan_item.need_id}"
                )

            acquisition_present = (
                dispatched.acquisition_hash is not None
            )

            if not plan_item.covered:
                satisfied = False
                reason = "adapter_capability_missing"
            elif dispatched.observation_count < 1:
                satisfied = False
                reason = "no_observation_returned"
            elif not acquisition_present:
                satisfied = False
                reason = "acquisition_record_missing"
            else:
                satisfied = True
                reason = "satisfied"

            body = {
                "need_id": plan_item.need_id,
                "planned_covered": plan_item.covered,
                "dispatched_covered": dispatched.covered,
                "observation_count": dispatched.observation_count,
                "acquisition_present": acquisition_present,
                "satisfied": satisfied,
                "reason_code": reason,
            }

            items.append(
                AcquisitionCoverageItem(
                    need_id=plan_item.need_id,
                    planned_covered=plan_item.covered,
                    dispatched_covered=dispatched.covered,
                    observation_count=dispatched.observation_count,
                    acquisition_present=acquisition_present,
                    satisfied=satisfied,
                    reason_code=reason,
                    item_hash=deterministic_sha256(body),
                )
            )

        satisfied_count = sum(
            1
            for item in items
            if item.satisfied
        )

        unsatisfied_count = len(items) - satisfied_count

        observation_count = sum(
            item.observation_count
            for item in items
        )

        if not items or satisfied_count == 0:
            status = STATUS_EMPTY
        elif unsatisfied_count == 0:
            status = STATUS_COMPLETE
        else:
            status = STATUS_PARTIAL

        body = {
            "plan_hash": plan.plan_hash,
            "dispatch_hash": dispatch.dispatch_hash,
            "item_hashes": tuple(
                item.item_hash
                for item in items
            ),
            "satisfied_count": satisfied_count,
            "unsatisfied_count": unsatisfied_count,
            "observation_count": observation_count,
            "status": status,
            "read_only": True,
        }

        return AcquisitionCoverageReconciliation(
            plan_hash=plan.plan_hash,
            dispatch_hash=dispatch.dispatch_hash,
            items=tuple(items),
            satisfied_count=satisfied_count,
            unsatisfied_count=unsatisfied_count,
            observation_count=observation_count,
            status=status,
            reconciliation_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_acquisition_coverage_reconciliation() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-032 must remain read-only"
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
        )
    ):
        raise AssertionError(
            "OI-032 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_032_REVISION",
    "STATUS_COMPLETE",
    "STATUS_PARTIAL",
    "STATUS_EMPTY",
    "AcquisitionCoverageReconciliationError",
    "AcquisitionCoverageItem",
    "AcquisitionCoverageReconciliation",
    "AcquisitionCoverageReconciler",
    "verify_acquisition_coverage_reconciliation",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_029_observation_acquisition_plan import (
    ObservationAcquisitionPlan,
    ObservationAcquisitionPlanItem,
)
from qseries_v2.observation_intelligence.oi_031_oracle_observation_request_dispatcher import (
    DispatchedObservationNeed,
    OracleObservationDispatchResult,
)
from qseries_v2.observation_intelligence.oi_032_acquisition_coverage_reconciliation import (
    OI_032_REVISION,
    STATUS_PARTIAL,
    AcquisitionCoverageReconciler,
    verify_acquisition_coverage_reconciliation,
)

NOW = datetime(2026, 8, 10, 21, 0, tzinfo=timezone.utc)


def plan():
    return ObservationAcquisitionPlan(
        plan_id="plan.astros",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        items=(
            ObservationAcquisitionPlanItem(
                ordinal=1,
                need_id="need.market",
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
                subject_hint="Astros strikeouts",
                adapter_ids=("adapter.kalshi.v1",),
                covered=True,
                item_hash="a" * 64,
            ),
            ObservationAcquisitionPlanItem(
                ordinal=2,
                need_id="need.lineup",
                domain="sports",
                entity_kind="team",
                observation_type="lineup",
                subject_hint="Astros strikeouts",
                adapter_ids=(),
                covered=False,
                item_hash="b" * 64,
            ),
        ),
        covered_count=1,
        missing_count=1,
        complete_coverage=False,
        plan_hash="c" * 64,
        read_only=True,
    )


def dispatch():
    return OracleObservationDispatchResult(
        request_id="request.astros",
        request_package_hash="d" * 64,
        plan_hash="c" * 64,
        dispatched_at=NOW,
        items=(
            DispatchedObservationNeed(
                ordinal=1,
                need_id="need.market",
                covered=True,
                adapter_ids=("adapter.kalshi.v1",),
                acquisition_hash="e" * 64,
                observation_count=1,
                evidence_hash="f" * 64,
                dispatch_item_hash="1" * 64,
            ),
            DispatchedObservationNeed(
                ordinal=2,
                need_id="need.lineup",
                covered=False,
                adapter_ids=(),
                acquisition_hash=None,
                observation_count=0,
                evidence_hash=None,
                dispatch_item_hash="2" * 64,
            ),
        ),
        covered_need_count=1,
        missing_need_count=1,
        acquired_observation_count=1,
        dispatch_hash="3" * 64,
        read_only=True,
    )


class TestOI032(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_acquisition_coverage_reconciliation()
        )

    def test_partial(self):
        result = AcquisitionCoverageReconciler().reconcile(
            plan=plan(),
            dispatch=dispatch(),
        )

        self.assertEqual(result.status, STATUS_PARTIAL)
        self.assertEqual(result.satisfied_count, 1)
        self.assertEqual(result.unsatisfied_count, 1)

    def test_missing_reason(self):
        result = AcquisitionCoverageReconciler().reconcile(
            plan=plan(),
            dispatch=dispatch(),
        )

        self.assertEqual(
            result.items[1].reason_code,
            "adapter_capability_missing",
        )

    def test_satisfied_reason(self):
        result = AcquisitionCoverageReconciler().reconcile(
            plan=plan(),
            dispatch=dispatch(),
        )

        self.assertTrue(result.items[0].satisfied)
        self.assertEqual(
            result.items[0].reason_code,
            "satisfied",
        )

    def test_deterministic(self):
        reconciler = AcquisitionCoverageReconciler()

        a = reconciler.reconcile(
            plan=plan(),
            dispatch=dispatch(),
        )

        b = reconciler.reconcile(
            plan=plan(),
            dispatch=dispatch(),
        )

        self.assertEqual(
            a.reconciliation_hash,
            b.reconciliation_hash,
        )

    def test_side_effects(self):
        item = AcquisitionCoverageReconciler()

        self.assertTrue(item.read_only)
        self.assertFalse(item.network_allowed)
        self.assertFalse(item.persistence_allowed)
        self.assertFalse(item.publication_allowed)
        self.assertFalse(item.execution_allowed)
        self.assertFalse(item.qseries_execution_allowed)
        self.assertFalse(item.prediction_allowed)
        self.assertFalse(item.edge_score_allowed)
        self.assertFalse(item.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-032 CERTIFICATION TEST")
    print(" ACQUISITION COVERAGE RECONCILIATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI032
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-032")
    print(f"[PASS] Revision: {OI_032_REVISION}")
    print("[PASS] Planned observation coverage reconciled against actual acquisition results")
    print("[PASS] Missing adapter capability and empty acquisition remain explicitly distinguishable")
    print("[PASS] Complete, partial, and empty acquisition states certified")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-032 CERTIFIED")
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
    print(" OI-032 INSTALLER")
    print(" ACQUISITION COVERAGE RECONCILIATION")
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
        "[PASS] Certified OI-016, OI-029, "
        "and OI-031 verified read-only"
    )

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export = (
            "from .oi_032_acquisition_coverage_reconciliation import *"
        )

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
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[PASS] Coverage reconciliation remains deterministic, "
            "read-only, and fail-closed"
        )
        print("[DONE] OI-032 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-032 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
