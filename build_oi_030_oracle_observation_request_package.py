from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-030"
INSTALLER_REVISION = "OI_030_ORACLE_OBSERVATION_REQUEST_PACKAGE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_025_oracle_explanation_query_engine.py", "OI-025"),
    (PACKAGE / "oi_026_evidence_explanation_formatter.py", "OI-026"),
    (PACKAGE / "oi_029_observation_acquisition_plan.py", "OI-029"),
)

MODULE = PACKAGE / "oi_030_oracle_observation_request_package.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_030_oracle_observation_request_package.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_025_oracle_explanation_query_engine import OracleExplanationQuery
from .oi_029_observation_acquisition_plan import ObservationAcquisitionPlan

BUILD_ID = "OI-030"
OI_030_REVISION = "OI_030_ORACLE_OBSERVATION_REQUEST_PACKAGE_V1"

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


class OracleObservationRequestPackageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleObservationRequestPackage:
    request_id: str
    query_id: str
    query_kind: str
    subject_hint: str
    profile_id: str
    acquisition_plan_hash: str
    requested_adapter_ids: tuple[str, ...]
    missing_need_ids: tuple[str, ...]
    complete_adapter_coverage: bool
    assembled_at: datetime
    package_hash: str
    read_only: bool
    predictive: bool
    terminal_mutation_allowed: bool


class OracleObservationRequestPackageBuilder:
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
        request_id: str,
        query: OracleExplanationQuery,
        acquisition_plan: ObservationAcquisitionPlan,
        assembled_at: datetime,
    ) -> OracleObservationRequestPackage:
        request_id_value = str(request_id).strip()

        if not request_id_value:
            raise OracleObservationRequestPackageError(
                "request_id must not be empty"
            )

        if not isinstance(query, OracleExplanationQuery):
            raise TypeError(
                "query must be OracleExplanationQuery"
            )

        if not isinstance(
            acquisition_plan,
            ObservationAcquisitionPlan,
        ):
            raise TypeError(
                "acquisition_plan must be ObservationAcquisitionPlan"
            )

        if query.profile_id != acquisition_plan.profile_id:
            raise OracleObservationRequestPackageError(
                "query profile and acquisition plan profile mismatch"
            )

        if query.subject_hint != acquisition_plan.subject_hint:
            raise OracleObservationRequestPackageError(
                "query subject and acquisition plan subject mismatch"
            )

        if not isinstance(assembled_at, datetime):
            raise TypeError(
                "assembled_at must be datetime"
            )

        if assembled_at.tzinfo is None:
            raise OracleObservationRequestPackageError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(
            timezone.utc
        )

        requested_adapter_ids = tuple(
            sorted(
                {
                    adapter_id
                    for item in acquisition_plan.items
                    for adapter_id in item.adapter_ids
                }
            )
        )

        missing_need_ids = tuple(
            item.need_id
            for item in acquisition_plan.items
            if not item.covered
        )

        body = {
            "request_id": request_id_value,
            "query_id": query.query_id,
            "query_kind": query.query_kind,
            "subject_hint": query.subject_hint,
            "profile_id": query.profile_id,
            "acquisition_plan_hash": acquisition_plan.plan_hash,
            "requested_adapter_ids": requested_adapter_ids,
            "missing_need_ids": missing_need_ids,
            "complete_adapter_coverage": (
                acquisition_plan.complete_coverage
            ),
            "assembled_at": assembled_at,
            "read_only": True,
            "predictive": False,
            "terminal_mutation_allowed": False,
        }

        return OracleObservationRequestPackage(
            request_id=request_id_value,
            query_id=query.query_id,
            query_kind=query.query_kind,
            subject_hint=query.subject_hint,
            profile_id=query.profile_id,
            acquisition_plan_hash=(
                acquisition_plan.plan_hash
            ),
            requested_adapter_ids=(
                requested_adapter_ids
            ),
            missing_need_ids=missing_need_ids,
            complete_adapter_coverage=(
                acquisition_plan.complete_coverage
            ),
            assembled_at=assembled_at,
            package_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            terminal_mutation_allowed=False,
        )


def verify_oracle_observation_request_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-030 must remain read-only"
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
            "OI-030 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_030_REVISION",
    "OracleObservationRequestPackageError",
    "OracleObservationRequestPackage",
    "OracleObservationRequestPackageBuilder",
    "verify_oracle_observation_request_package",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_025_oracle_explanation_query_engine import (
    OracleExplanationQueryEngine,
    default_explanation_profile_map,
)
from qseries_v2.observation_intelligence.oi_029_observation_acquisition_plan import (
    ObservationAcquisitionPlan,
    ObservationAcquisitionPlanItem,
)
from qseries_v2.observation_intelligence.oi_030_oracle_observation_request_package import (
    OI_030_REVISION,
    OracleObservationRequestPackageBuilder,
    verify_oracle_observation_request_package,
)

NOW = datetime(
    2026,
    8,
    10,
    19,
    0,
    tzinfo=timezone.utc,
)


def query():
    return OracleExplanationQueryEngine(
        default_explanation_profile_map()
    ).resolve(
        query_id="query.astros",
        text="Explain why the Astros strikeout edge moved",
        subject_hint="Astros strikeouts",
        domain="sports",
    )


def plan():
    return ObservationAcquisitionPlan(
        plan_id="plan.astros",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        items=(
            ObservationAcquisitionPlanItem(
                ordinal=1,
                need_id="profile.market_explanation.need.1",
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
                need_id="profile.market_explanation.need.2",
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


class TestOI030(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_observation_request_package()
        )

    def test_build(self):
        package = (
            OracleObservationRequestPackageBuilder()
            .build(
                request_id="request.astros",
                query=query(),
                acquisition_plan=plan(),
                assembled_at=NOW,
            )
        )

        self.assertEqual(
            package.requested_adapter_ids,
            ("adapter.kalshi.v1",),
        )

        self.assertEqual(
            package.missing_need_ids,
            ("profile.market_explanation.need.2",),
        )

        self.assertFalse(
            package.complete_adapter_coverage
        )

    def test_query_preserved(self):
        package = (
            OracleObservationRequestPackageBuilder()
            .build(
                request_id="request.astros",
                query=query(),
                acquisition_plan=plan(),
                assembled_at=NOW,
            )
        )

        self.assertEqual(
            package.query_kind,
            "explanation",
        )

        self.assertEqual(
            package.subject_hint,
            "Astros strikeouts",
        )

    def test_deterministic(self):
        builder = OracleObservationRequestPackageBuilder()

        a = builder.build(
            request_id="request.astros",
            query=query(),
            acquisition_plan=plan(),
            assembled_at=NOW,
        )

        b = builder.build(
            request_id="request.astros",
            query=query(),
            acquisition_plan=plan(),
            assembled_at=NOW,
        )

        self.assertEqual(
            a.package_hash,
            b.package_hash,
        )

    def test_side_effects(self):
        builder = OracleObservationRequestPackageBuilder()

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
    print(" OI-030 CERTIFICATION TEST")
    print(" ORACLE OBSERVATION REQUEST PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI030
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-030")
    print(f"[PASS] Revision: {OI_030_REVISION}")
    print("[PASS] Explanation query and acquisition plan packaged into deterministic Oracle observation request")
    print("[PASS] Requested adapters and missing observation capabilities remain explicit")
    print("[PASS] Request package is terminal-safe, read-only, and non-mutating")
    print("[PASS] Prediction, probability, scoring, publication, and execution disabled")
    print("[DONE] OI-030 CERTIFIED")
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
    print(" OI-030 INSTALLER")
    print(" ORACLE OBSERVATION REQUEST PACKAGE")
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
        "[PASS] Certified OI-025, OI-026, "
        "and OI-029 verified read-only"
    )

    affected = (MODULE, TEST, INIT)

    backups = {
        item: (
            item.read_bytes()
            if item.exists()
            else None
        )
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
            "from .oi_030_oracle_observation_request_package import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"

            current += export + "\n"

            ast.parse(
                current,
                filename=str(INIT),
            )

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
                    f"Certified upstream changed: "
                    f"{upstream.name}"
                )

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified upstream remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[PASS] Observation request packaging remains "
            "deterministic, read-only, and terminal-safe"
        )

        print(
            "[DONE] OI-030 INSTALLATION COMPLETE"
        )

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
            "[ROLLBACK] OI-030 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
