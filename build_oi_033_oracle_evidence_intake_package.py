from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-033"
INSTALLER_REVISION = "OI_033_ORACLE_EVIDENCE_INTAKE_PACKAGE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_030_oracle_observation_request_package.py", "OI-030"),
    (PACKAGE / "oi_031_oracle_observation_request_dispatcher.py", "OI-031"),
    (PACKAGE / "oi_032_acquisition_coverage_reconciliation.py", "OI-032"),
)

MODULE = PACKAGE / "oi_033_oracle_evidence_intake_package.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_033_oracle_evidence_intake_package.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_030_oracle_observation_request_package import (
    OracleObservationRequestPackage,
)
from .oi_031_oracle_observation_request_dispatcher import (
    OracleObservationDispatchResult,
)
from .oi_032_acquisition_coverage_reconciliation import (
    AcquisitionCoverageReconciliation,
)

BUILD_ID = "OI-033"
OI_033_REVISION = "OI_033_ORACLE_EVIDENCE_INTAKE_PACKAGE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False
TERMINAL_MUTATION_ALLOWED = False


class OracleEvidenceIntakePackageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleEvidenceIntakeItem:
    need_id: str
    adapter_ids: tuple[str, ...]
    evidence_hash: str | None
    observation_count: int
    satisfied: bool
    reason_code: str
    item_hash: str


@dataclass(frozen=True, slots=True)
class OracleEvidenceIntakePackage:
    intake_id: str
    request_id: str
    query_id: str
    query_kind: str
    subject_hint: str
    profile_id: str
    acquisition_status: str
    evidence_items: tuple[OracleEvidenceIntakeItem, ...]
    total_observation_count: int
    missing_need_ids: tuple[str, ...]
    complete_evidence_intake: bool
    assembled_at: datetime
    intake_hash: str
    read_only: bool
    predictive: bool
    terminal_mutation_allowed: bool


class OracleEvidenceIntakePackageBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False
    terminal_mutation_allowed = False

    def build(
        self,
        *,
        intake_id: str,
        request_package: OracleObservationRequestPackage,
        dispatch: OracleObservationDispatchResult,
        reconciliation: AcquisitionCoverageReconciliation,
        assembled_at: datetime,
    ) -> OracleEvidenceIntakePackage:
        intake_id_value = str(intake_id).strip()

        if not intake_id_value:
            raise OracleEvidenceIntakePackageError(
                "intake_id must not be empty"
            )

        if not isinstance(
            request_package,
            OracleObservationRequestPackage,
        ):
            raise TypeError(
                "request_package must be OracleObservationRequestPackage"
            )

        if not isinstance(
            dispatch,
            OracleObservationDispatchResult,
        ):
            raise TypeError(
                "dispatch must be OracleObservationDispatchResult"
            )

        if not isinstance(
            reconciliation,
            AcquisitionCoverageReconciliation,
        ):
            raise TypeError(
                "reconciliation must be AcquisitionCoverageReconciliation"
            )

        if (
            dispatch.request_package_hash
            != request_package.package_hash
        ):
            raise OracleEvidenceIntakePackageError(
                "dispatch does not belong to request package"
            )

        if (
            reconciliation.dispatch_hash
            != dispatch.dispatch_hash
        ):
            raise OracleEvidenceIntakePackageError(
                "reconciliation does not belong to dispatch"
            )

        if not isinstance(assembled_at, datetime):
            raise TypeError(
                "assembled_at must be datetime"
            )

        if assembled_at.tzinfo is None:
            raise OracleEvidenceIntakePackageError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(
            timezone.utc
        )

        dispatch_by_need = {
            item.need_id: item
            for item in dispatch.items
        }

        items = []

        for reconciled in reconciliation.items:
            dispatched = dispatch_by_need.get(
                reconciled.need_id
            )

            if dispatched is None:
                raise OracleEvidenceIntakePackageError(
                    f"dispatch missing reconciled need: "
                    f"{reconciled.need_id}"
                )

            body = {
                "need_id": reconciled.need_id,
                "adapter_ids": dispatched.adapter_ids,
                "evidence_hash": dispatched.evidence_hash,
                "observation_count": reconciled.observation_count,
                "satisfied": reconciled.satisfied,
                "reason_code": reconciled.reason_code,
            }

            items.append(
                OracleEvidenceIntakeItem(
                    need_id=reconciled.need_id,
                    adapter_ids=dispatched.adapter_ids,
                    evidence_hash=dispatched.evidence_hash,
                    observation_count=reconciled.observation_count,
                    satisfied=reconciled.satisfied,
                    reason_code=reconciled.reason_code,
                    item_hash=deterministic_sha256(body),
                )
            )

        missing_need_ids = tuple(
            item.need_id
            for item in items
            if not item.satisfied
        )

        complete = (
            reconciliation.unsatisfied_count == 0
            and bool(items)
        )

        body = {
            "intake_id": intake_id_value,
            "request_id": request_package.request_id,
            "query_id": request_package.query_id,
            "query_kind": request_package.query_kind,
            "subject_hint": request_package.subject_hint,
            "profile_id": request_package.profile_id,
            "acquisition_status": reconciliation.status,
            "evidence_item_hashes": tuple(
                item.item_hash
                for item in items
            ),
            "total_observation_count": (
                reconciliation.observation_count
            ),
            "missing_need_ids": missing_need_ids,
            "complete_evidence_intake": complete,
            "assembled_at": assembled_at,
            "read_only": True,
            "predictive": False,
            "terminal_mutation_allowed": False,
        }

        return OracleEvidenceIntakePackage(
            intake_id=intake_id_value,
            request_id=request_package.request_id,
            query_id=request_package.query_id,
            query_kind=request_package.query_kind,
            subject_hint=request_package.subject_hint,
            profile_id=request_package.profile_id,
            acquisition_status=reconciliation.status,
            evidence_items=tuple(items),
            total_observation_count=(
                reconciliation.observation_count
            ),
            missing_need_ids=missing_need_ids,
            complete_evidence_intake=complete,
            assembled_at=assembled_at,
            intake_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            terminal_mutation_allowed=False,
        )


def verify_oracle_evidence_intake_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-033 must remain read-only"
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
            TERMINAL_MUTATION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-033 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_033_REVISION",
    "OracleEvidenceIntakePackageError",
    "OracleEvidenceIntakeItem",
    "OracleEvidenceIntakePackage",
    "OracleEvidenceIntakePackageBuilder",
    "verify_oracle_evidence_intake_package",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_030_oracle_observation_request_package import (
    OracleObservationRequestPackage,
)
from qseries_v2.observation_intelligence.oi_031_oracle_observation_request_dispatcher import (
    DispatchedObservationNeed,
    OracleObservationDispatchResult,
)
from qseries_v2.observation_intelligence.oi_032_acquisition_coverage_reconciliation import (
    AcquisitionCoverageItem,
    AcquisitionCoverageReconciliation,
)
from qseries_v2.observation_intelligence.oi_033_oracle_evidence_intake_package import (
    OI_033_REVISION,
    OracleEvidenceIntakePackageBuilder,
    verify_oracle_evidence_intake_package,
)

NOW = datetime(2026, 8, 10, 22, 0, tzinfo=timezone.utc)


def request_package():
    return OracleObservationRequestPackage(
        request_id="request.astros",
        query_id="query.astros",
        query_kind="explanation",
        subject_hint="Astros strikeouts",
        profile_id="profile.market_explanation",
        acquisition_plan_hash="a" * 64,
        requested_adapter_ids=("adapter.kalshi.v1",),
        missing_need_ids=("need.lineup",),
        complete_adapter_coverage=False,
        assembled_at=NOW,
        package_hash="b" * 64,
        read_only=True,
        predictive=False,
        terminal_mutation_allowed=False,
    )


def dispatch():
    return OracleObservationDispatchResult(
        request_id="request.astros",
        request_package_hash="b" * 64,
        plan_hash="a" * 64,
        dispatched_at=NOW,
        items=(
            DispatchedObservationNeed(
                ordinal=1,
                need_id="need.market",
                covered=True,
                adapter_ids=("adapter.kalshi.v1",),
                acquisition_hash="c" * 64,
                observation_count=1,
                evidence_hash="d" * 64,
                dispatch_item_hash="e" * 64,
            ),
            DispatchedObservationNeed(
                ordinal=2,
                need_id="need.lineup",
                covered=False,
                adapter_ids=(),
                acquisition_hash=None,
                observation_count=0,
                evidence_hash=None,
                dispatch_item_hash="f" * 64,
            ),
        ),
        covered_need_count=1,
        missing_need_count=1,
        acquired_observation_count=1,
        dispatch_hash="1" * 64,
        read_only=True,
    )


def reconciliation():
    return AcquisitionCoverageReconciliation(
        plan_hash="a" * 64,
        dispatch_hash="1" * 64,
        items=(
            AcquisitionCoverageItem(
                need_id="need.market",
                planned_covered=True,
                dispatched_covered=True,
                observation_count=1,
                acquisition_present=True,
                satisfied=True,
                reason_code="satisfied",
                item_hash="2" * 64,
            ),
            AcquisitionCoverageItem(
                need_id="need.lineup",
                planned_covered=False,
                dispatched_covered=False,
                observation_count=0,
                acquisition_present=False,
                satisfied=False,
                reason_code="adapter_capability_missing",
                item_hash="3" * 64,
            ),
        ),
        satisfied_count=1,
        unsatisfied_count=1,
        observation_count=1,
        status="partial",
        reconciliation_hash="4" * 64,
        read_only=True,
    )


class TestOI033(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_evidence_intake_package()
        )

    def test_build(self):
        package = OracleEvidenceIntakePackageBuilder().build(
            intake_id="intake.astros",
            request_package=request_package(),
            dispatch=dispatch(),
            reconciliation=reconciliation(),
            assembled_at=NOW,
        )

        self.assertEqual(
            package.acquisition_status,
            "partial",
        )
        self.assertEqual(
            package.total_observation_count,
            1,
        )
        self.assertFalse(
            package.complete_evidence_intake
        )

    def test_missing_need_preserved(self):
        package = OracleEvidenceIntakePackageBuilder().build(
            intake_id="intake.astros",
            request_package=request_package(),
            dispatch=dispatch(),
            reconciliation=reconciliation(),
            assembled_at=NOW,
        )

        self.assertEqual(
            package.missing_need_ids,
            ("need.lineup",),
        )

    def test_evidence_hash_preserved(self):
        package = OracleEvidenceIntakePackageBuilder().build(
            intake_id="intake.astros",
            request_package=request_package(),
            dispatch=dispatch(),
            reconciliation=reconciliation(),
            assembled_at=NOW,
        )

        self.assertEqual(
            package.evidence_items[0].evidence_hash,
            "d" * 64,
        )

    def test_deterministic(self):
        builder = OracleEvidenceIntakePackageBuilder()

        a = builder.build(
            intake_id="intake.astros",
            request_package=request_package(),
            dispatch=dispatch(),
            reconciliation=reconciliation(),
            assembled_at=NOW,
        )

        b = builder.build(
            intake_id="intake.astros",
            request_package=request_package(),
            dispatch=dispatch(),
            reconciliation=reconciliation(),
            assembled_at=NOW,
        )

        self.assertEqual(
            a.intake_hash,
            b.intake_hash,
        )

    def test_side_effects(self):
        builder = OracleEvidenceIntakePackageBuilder()

        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.prediction_allowed)
        self.assertFalse(builder.edge_score_allowed)
        self.assertFalse(builder.probability_allowed)
        self.assertFalse(builder.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-033 CERTIFICATION TEST")
    print(" ORACLE EVIDENCE INTAKE PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI033
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-033")
    print(f"[PASS] Revision: {OI_033_REVISION}")
    print("[PASS] Actual acquired evidence reconciled into deterministic Oracle intake package")
    print("[PASS] Evidence hashes, adapter identities, observation counts, and missing needs preserved")
    print("[PASS] Partial evidence intake remains explicit instead of being promoted to complete")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-033 CERTIFIED")
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
    print(" OI-033 INSTALLER")
    print(" ORACLE EVIDENCE INTAKE PACKAGE")
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
        "[PASS] Certified OI-030 through OI-032 "
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

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export = (
            "from .oi_033_oracle_evidence_intake_package import *"
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
            "[PASS] Evidence intake remains deterministic, "
            "read-only, terminal-safe, and fail-closed"
        )
        print("[DONE] OI-033 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-033 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
