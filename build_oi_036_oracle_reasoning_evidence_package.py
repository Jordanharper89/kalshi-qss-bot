from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-036"
INSTALLER_REVISION = "OI_036_ORACLE_REASONING_EVIDENCE_PACKAGE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_015_reasoning_input_builder.py", "OI-015"),
    (PACKAGE / "oi_034_canonical_evidence_materialization.py", "OI-034"),
    (PACKAGE / "oi_035_reasoning_evidence_admission_gate.py", "OI-035"),
)

MODULE = PACKAGE / "oi_036_oracle_reasoning_evidence_package.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_036_oracle_reasoning_evidence_package.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_034_canonical_evidence_materialization import (
    CanonicalEvidenceMaterialization,
)
from .oi_035_reasoning_evidence_admission_gate import (
    ReasoningEvidenceAdmission,
    REJECTED,
)

BUILD_ID = "OI-036"
OI_036_REVISION = "OI_036_ORACLE_REASONING_EVIDENCE_PACKAGE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class OracleReasoningEvidencePackageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleReasoningEvidenceItem:
    canonical_observation_id: str
    canonical_observation_hash: str
    adapter_id: str
    provider: str
    subject: str
    observation_type: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class OracleReasoningEvidencePackage:
    package_id: str
    query_id: str
    profile_id: str
    subject_hint: str
    admission_status: str
    admission_hash: str
    materialization_hash: str
    evidence_items: tuple[OracleReasoningEvidenceItem, ...]
    missing_need_count: int
    built_at: datetime
    package_hash: str
    read_only: bool
    predictive: bool


class OracleReasoningEvidencePackageBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def build(
        self,
        *,
        package_id: str,
        materialization: CanonicalEvidenceMaterialization,
        admission: ReasoningEvidenceAdmission,
        built_at: datetime,
    ) -> OracleReasoningEvidencePackage:
        package_id_value = str(package_id).strip()

        if not package_id_value:
            raise OracleReasoningEvidencePackageError(
                "package_id must not be empty"
            )

        if not isinstance(
            materialization,
            CanonicalEvidenceMaterialization,
        ):
            raise TypeError(
                "materialization must be CanonicalEvidenceMaterialization"
            )

        if not isinstance(
            admission,
            ReasoningEvidenceAdmission,
        ):
            raise TypeError(
                "admission must be ReasoningEvidenceAdmission"
            )

        if (
            admission.materialization_hash
            != materialization.materialization_hash
        ):
            raise OracleReasoningEvidencePackageError(
                "admission does not belong to materialization"
            )

        if admission.status == REJECTED:
            raise OracleReasoningEvidencePackageError(
                "rejected evidence cannot enter reasoning package"
            )

        if not isinstance(built_at, datetime):
            raise TypeError(
                "built_at must be datetime"
            )

        if built_at.tzinfo is None:
            raise OracleReasoningEvidencePackageError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(
            timezone.utc
        )

        items = tuple(
            OracleReasoningEvidenceItem(
                canonical_observation_id=(
                    item.canonical_observation_id
                ),
                canonical_observation_hash=(
                    item.canonical_observation_hash
                ),
                adapter_id=item.adapter_id,
                provider=item.provider,
                subject=item.subject,
                observation_type=item.observation_type,
                observed_at=item.observed_at,
            )
            for item in materialization.items
        )

        body = {
            "package_id": package_id_value,
            "query_id": materialization.query_id,
            "profile_id": materialization.profile_id,
            "subject_hint": materialization.subject_hint,
            "admission_status": admission.status,
            "admission_hash": admission.admission_hash,
            "materialization_hash": (
                materialization.materialization_hash
            ),
            "evidence": tuple(
                (
                    item.canonical_observation_id,
                    item.canonical_observation_hash,
                    item.adapter_id,
                    item.provider,
                    item.subject,
                    item.observation_type,
                    item.observed_at,
                )
                for item in items
            ),
            "missing_need_count": admission.missing_need_count,
            "built_at": built_at,
            "read_only": True,
            "predictive": False,
        }

        return OracleReasoningEvidencePackage(
            package_id=package_id_value,
            query_id=materialization.query_id,
            profile_id=materialization.profile_id,
            subject_hint=materialization.subject_hint,
            admission_status=admission.status,
            admission_hash=admission.admission_hash,
            materialization_hash=(
                materialization.materialization_hash
            ),
            evidence_items=items,
            missing_need_count=admission.missing_need_count,
            built_at=built_at,
            package_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
        )


def verify_oracle_reasoning_evidence_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-036 must remain read-only"
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
            "OI-036 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_036_REVISION",
    "OracleReasoningEvidencePackageError",
    "OracleReasoningEvidenceItem",
    "OracleReasoningEvidencePackage",
    "OracleReasoningEvidencePackageBuilder",
    "verify_oracle_reasoning_evidence_package",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_034_canonical_evidence_materialization import (
    CanonicalEvidenceMaterialization,
    MaterializedEvidenceItem,
)
from qseries_v2.observation_intelligence.oi_035_reasoning_evidence_admission_gate import (
    ReasoningEvidenceAdmission,
)
from qseries_v2.observation_intelligence.oi_036_oracle_reasoning_evidence_package import (
    OI_036_REVISION,
    OracleReasoningEvidencePackageBuilder,
    verify_oracle_reasoning_evidence_package,
)

NOW = datetime(2026, 8, 11, 1, 0, tzinfo=timezone.utc)


def materialization():
    return CanonicalEvidenceMaterialization(
        intake_id="intake.test",
        intake_hash="a" * 64,
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Test market",
        items=(
            MaterializedEvidenceItem(
                canonical_observation_id="obs.1",
                canonical_observation_hash="b" * 64,
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Test market",
                observation_type="market_snapshot",
                observed_at=NOW,
                materialization_hash="c" * 64,
            ),
        ),
        observation_count=1,
        complete_count_match=True,
        materialization_hash="d" * 64,
        read_only=True,
    )


def admission(status="admitted"):
    return ReasoningEvidenceAdmission(
        intake_hash="a" * 64,
        materialization_hash="d" * 64,
        status=status,
        observation_count=1,
        missing_need_count=0 if status == "admitted" else 1,
        complete_count_match=True,
        reason_codes=() if status == "admitted" else (
            "missing_required_observation_needs",
        ),
        admission_hash="e" * 64,
        read_only=True,
    )


class TestOI036(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_reasoning_evidence_package()
        )

    def test_build(self):
        package = (
            OracleReasoningEvidencePackageBuilder()
            .build(
                package_id="reasoning.test",
                materialization=materialization(),
                admission=admission(),
                built_at=NOW,
            )
        )

        self.assertEqual(
            len(package.evidence_items),
            1,
        )
        self.assertEqual(
            package.admission_status,
            "admitted",
        )

    def test_partial_allowed(self):
        package = (
            OracleReasoningEvidencePackageBuilder()
            .build(
                package_id="reasoning.test",
                materialization=materialization(),
                admission=admission("partial"),
                built_at=NOW,
            )
        )

        self.assertEqual(
            package.missing_need_count,
            1,
        )

    def test_rejected_blocked(self):
        rejected = ReasoningEvidenceAdmission(
            intake_hash="a" * 64,
            materialization_hash="d" * 64,
            status="rejected",
            observation_count=0,
            missing_need_count=1,
            complete_count_match=False,
            reason_codes=("no_canonical_observations",),
            admission_hash="f" * 64,
            read_only=True,
        )

        with self.assertRaises(ValueError):
            OracleReasoningEvidencePackageBuilder().build(
                package_id="reasoning.test",
                materialization=materialization(),
                admission=rejected,
                built_at=NOW,
            )

    def test_deterministic(self):
        builder = OracleReasoningEvidencePackageBuilder()

        a = builder.build(
            package_id="reasoning.test",
            materialization=materialization(),
            admission=admission(),
            built_at=NOW,
        )

        b = builder.build(
            package_id="reasoning.test",
            materialization=materialization(),
            admission=admission(),
            built_at=NOW,
        )

        self.assertEqual(
            a.package_hash,
            b.package_hash,
        )

    def test_side_effects(self):
        builder = OracleReasoningEvidencePackageBuilder()

        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.prediction_allowed)
        self.assertFalse(builder.edge_score_allowed)
        self.assertFalse(builder.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-036 CERTIFICATION TEST")
    print(" ORACLE REASONING EVIDENCE PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI036
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-036")
    print(f"[PASS] Revision: {OI_036_REVISION}")
    print("[PASS] Admitted canonical evidence packaged for Oracle reasoning consumption")
    print("[PASS] Partial evidence remains marked partial; rejected evidence is blocked")
    print("[PASS] Observation lineage and admission lineage preserved")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-036 CERTIFIED")
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
    print(" OI-036 INSTALLER")
    print(" ORACLE REASONING EVIDENCE PACKAGE")
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
        "[PASS] Certified OI-015, OI-034, "
        "and OI-035 verified read-only"
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
            "from .oi_036_oracle_reasoning_evidence_package import *"
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
            "[PASS] Reasoning evidence packaging remains deterministic, "
            "read-only, and fail-closed"
        )
        print("[DONE] OI-036 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-036 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
