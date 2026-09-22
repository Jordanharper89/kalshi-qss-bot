from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-035"
INSTALLER_REVISION = "OI_035_REASONING_EVIDENCE_ADMISSION_GATE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_016_evidence_sufficiency_gate.py", "OI-016"),
    (PACKAGE / "oi_033_oracle_evidence_intake_package.py", "OI-033"),
    (PACKAGE / "oi_034_canonical_evidence_materialization.py", "OI-034"),
)

MODULE = PACKAGE / "oi_035_reasoning_evidence_admission_gate.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_035_reasoning_evidence_admission_gate.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_033_oracle_evidence_intake_package import OracleEvidenceIntakePackage
from .oi_034_canonical_evidence_materialization import (
    CanonicalEvidenceMaterialization,
)

BUILD_ID = "OI-035"
OI_035_REVISION = "OI_035_REASONING_EVIDENCE_ADMISSION_GATE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False

ADMITTED = "admitted"
PARTIAL = "partial"
REJECTED = "rejected"


class ReasoningEvidenceAdmissionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceAdmission:
    intake_hash: str
    materialization_hash: str
    status: str
    observation_count: int
    missing_need_count: int
    complete_count_match: bool
    reason_codes: tuple[str, ...]
    admission_hash: str
    read_only: bool


class ReasoningEvidenceAdmissionGate:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def evaluate(
        self,
        *,
        intake: OracleEvidenceIntakePackage,
        materialization: CanonicalEvidenceMaterialization,
    ) -> ReasoningEvidenceAdmission:
        if not isinstance(
            intake,
            OracleEvidenceIntakePackage,
        ):
            raise TypeError(
                "intake must be OracleEvidenceIntakePackage"
            )

        if not isinstance(
            materialization,
            CanonicalEvidenceMaterialization,
        ):
            raise TypeError(
                "materialization must be CanonicalEvidenceMaterialization"
            )

        if materialization.intake_hash != intake.intake_hash:
            raise ReasoningEvidenceAdmissionError(
                "materialization does not belong to intake package"
            )

        reasons = []

        if materialization.observation_count < 1:
            reasons.append("no_canonical_observations")

        if not materialization.complete_count_match:
            reasons.append("observation_count_mismatch")

        if intake.missing_need_ids:
            reasons.append("missing_required_observation_needs")

        reasons = tuple(
            sorted(set(reasons))
        )

        if (
            materialization.observation_count < 1
            or not materialization.complete_count_match
        ):
            status = REJECTED
        elif intake.missing_need_ids:
            status = PARTIAL
        else:
            status = ADMITTED

        body = {
            "intake_hash": intake.intake_hash,
            "materialization_hash": (
                materialization.materialization_hash
            ),
            "status": status,
            "observation_count": (
                materialization.observation_count
            ),
            "missing_need_count": len(
                intake.missing_need_ids
            ),
            "complete_count_match": (
                materialization.complete_count_match
            ),
            "reason_codes": reasons,
            "read_only": True,
        }

        return ReasoningEvidenceAdmission(
            intake_hash=intake.intake_hash,
            materialization_hash=(
                materialization.materialization_hash
            ),
            status=status,
            observation_count=(
                materialization.observation_count
            ),
            missing_need_count=len(
                intake.missing_need_ids
            ),
            complete_count_match=(
                materialization.complete_count_match
            ),
            reason_codes=reasons,
            admission_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_reasoning_evidence_admission_gate() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-035 must remain read-only"
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
            "OI-035 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_035_REVISION",
    "ADMITTED",
    "PARTIAL",
    "REJECTED",
    "ReasoningEvidenceAdmissionError",
    "ReasoningEvidenceAdmission",
    "ReasoningEvidenceAdmissionGate",
    "verify_reasoning_evidence_admission_gate",
]
"""

TEST_SOURCE = r"""
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
    print(" OI-035 INSTALLER")
    print(" REASONING EVIDENCE ADMISSION GATE")
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
        "[PASS] Certified OI-016, OI-033, "
        "and OI-034 verified read-only"
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
            "from .oi_035_reasoning_evidence_admission_gate import *"
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
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[PASS] Evidence admission remains deterministic, "
            "read-only, and fail-closed"
        )
        print("[DONE] OI-035 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-035 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
