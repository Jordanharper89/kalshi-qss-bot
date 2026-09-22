from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-065"
INSTALLER_REVISION = "OI_065_FOLLOWUP_EVIDENCE_ROUTE_PLANNING_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_027_generic_observation_router_interface.py", "OI-027"),
    (PACKAGE / "oi_028_adapter_capability_coverage.py", "OI-028"),
    (PACKAGE / "oi_064_followup_evidence_requirement_projection.py", "OI-064"),
)

MODULE = PACKAGE / "oi_065_followup_evidence_route_planning.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_065_followup_evidence_route_planning.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_064_followup_evidence_requirement_projection import (
    FollowUpEvidenceRequirementProjection,
    NEED_CURRENT_EVIDENCE,
    NEED_ADDITIONAL_EVIDENCE,
    NEED_CONTRADICTORY_EVIDENCE,
    NEED_TEMPORAL_EVIDENCE,
    NEED_SUBJECT_DISCOVERY,
)

BUILD_ID = "OI-065"
OI_065_REVISION = "OI_065_FOLLOWUP_EVIDENCE_ROUTE_PLANNING_V1"

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


@dataclass(frozen=True, slots=True)
class FollowUpEvidenceRoute:
    route_id: str
    requirement_id: str
    subject_hint: str | None
    observation_need: str
    capability_group: str
    required: bool
    route_hash: str


@dataclass(frozen=True, slots=True)
class FollowUpEvidenceRoutePlan:
    session_id: str
    subject_hint: str | None
    routes: tuple[FollowUpEvidenceRoute, ...]
    missing_route_count: int
    route_plan_hash: str
    read_only: bool


class FollowUpEvidenceRoutePlanner:
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

    _CAPABILITY_MAP = {
        NEED_CURRENT_EVIDENCE: (
            "subject_observation",
            "general_observation",
        ),
        NEED_ADDITIONAL_EVIDENCE: (
            "independent_support_observation",
            "general_observation",
        ),
        NEED_CONTRADICTORY_EVIDENCE: (
            "contradiction_observation",
            "general_observation",
        ),
        NEED_TEMPORAL_EVIDENCE: (
            "temporal_observation",
            "historical_observation",
        ),
        NEED_SUBJECT_DISCOVERY: (
            "subject_discovery",
            "discovery_observation",
        ),
    }

    def plan(
        self,
        projection: FollowUpEvidenceRequirementProjection,
    ) -> FollowUpEvidenceRoutePlan:
        if not isinstance(
            projection,
            FollowUpEvidenceRequirementProjection,
        ):
            raise TypeError(
                "projection must be "
                "FollowUpEvidenceRequirementProjection"
            )

        routes = []
        missing = 0

        for requirement in projection.requirements:
            mapped = self._CAPABILITY_MAP.get(
                requirement.need_type
            )

            if mapped is None:
                missing += 1
                continue

            observation_need, capability_group = mapped

            body = {
                "requirement_id": (
                    requirement.requirement_id
                ),
                "subject_hint": (
                    requirement.subject_hint
                ),
                "observation_need": observation_need,
                "capability_group": capability_group,
                "required": requirement.required,
            }

            route_hash = deterministic_sha256(body)

            routes.append(
                FollowUpEvidenceRoute(
                    route_id=(
                        f"route.{route_hash[:24]}"
                    ),
                    requirement_id=(
                        requirement.requirement_id
                    ),
                    subject_hint=(
                        requirement.subject_hint
                    ),
                    observation_need=observation_need,
                    capability_group=capability_group,
                    required=requirement.required,
                    route_hash=route_hash,
                )
            )

        routes = tuple(routes)

        body = {
            "session_id": projection.session_id,
            "subject_hint": projection.subject_hint,
            "route_hashes": tuple(
                item.route_hash
                for item in routes
            ),
            "missing_route_count": missing,
            "read_only": True,
        }

        return FollowUpEvidenceRoutePlan(
            session_id=projection.session_id,
            subject_hint=projection.subject_hint,
            routes=routes,
            missing_route_count=missing,
            route_plan_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_followup_evidence_route_planning() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-065 must remain read-only"
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
            "OI-065 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_065_REVISION",
    "FollowUpEvidenceRoute",
    "FollowUpEvidenceRoutePlan",
    "FollowUpEvidenceRoutePlanner",
    "verify_followup_evidence_route_planning",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_064_followup_evidence_requirement_projection import (
    FollowUpEvidenceRequirement,
    FollowUpEvidenceRequirementProjection,
)
from qseries_v2.observation_intelligence.oi_065_followup_evidence_route_planning import (
    OI_065_REVISION,
    FollowUpEvidenceRoutePlanner,
    verify_followup_evidence_route_planning,
)


def projection():
    requirement = FollowUpEvidenceRequirement(
        requirement_id="req.1",
        subject_hint="Astros strikeouts",
        need_type="contradictory_evidence",
        required=True,
        reason="inspect_conflicting_evidence",
        requirement_hash="a" * 64,
    )

    return FollowUpEvidenceRequirementProjection(
        session_id="session.1",
        intent="contradiction",
        subject_hint="Astros strikeouts",
        requirements=(requirement,),
        projection_status="projected",
        projection_hash="b" * 64,
        read_only=True,
    )


class TestOI065(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_followup_evidence_route_planning()
        )

    def test_plan(self):
        plan = FollowUpEvidenceRoutePlanner().plan(
            projection()
        )

        self.assertEqual(
            len(plan.routes),
            1,
        )

        self.assertEqual(
            plan.routes[0].observation_need,
            "contradiction_observation",
        )

    def test_subject_preserved(self):
        plan = FollowUpEvidenceRoutePlanner().plan(
            projection()
        )

        self.assertEqual(
            plan.routes[0].subject_hint,
            "Astros strikeouts",
        )

    def test_no_missing_route(self):
        plan = FollowUpEvidenceRoutePlanner().plan(
            projection()
        )

        self.assertEqual(
            plan.missing_route_count,
            0,
        )

    def test_deterministic(self):
        planner = FollowUpEvidenceRoutePlanner()

        a = planner.plan(projection())
        b = planner.plan(projection())

        self.assertEqual(
            a.route_plan_hash,
            b.route_plan_hash,
        )

    def test_side_effects(self):
        planner = FollowUpEvidenceRoutePlanner()

        self.assertTrue(planner.read_only)
        self.assertFalse(planner.network_allowed)
        self.assertFalse(planner.persistence_allowed)
        self.assertFalse(planner.publication_allowed)
        self.assertFalse(planner.execution_allowed)
        self.assertFalse(planner.qseries_execution_allowed)
        self.assertFalse(planner.prediction_allowed)
        self.assertFalse(planner.edge_score_allowed)
        self.assertFalse(planner.probability_allowed)
        self.assertFalse(planner.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-065 CERTIFICATION TEST")
    print(" FOLLOW-UP EVIDENCE ROUTE PLANNING")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI065
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-065")
    print(f"[PASS] Revision: {OI_065_REVISION}")
    print("[PASS] Follow-up evidence requirements converted into generic observation routes")
    print("[PASS] Contradiction, temporal, additional-support, current-support, and subject-discovery capabilities remain domain-agnostic")
    print("[PASS] No adapter is invented when a capability cannot be routed")
    print("[DONE] OI-065 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checked(path: Path, source: str) -> None:
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"[PASS] Wrote: {path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OI-065 INSTALLER")
    print(" FOLLOW-UP EVIDENCE ROUTE PLANNING")
    print("=" * 72)
    print(
        f"[BOOT] Revision: {INSTALLER_REVISION}"
    )
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
        "[PASS] Certified OI-027, OI-028, "
        "and OI-064 verified read-only"
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
            "from .oi_065_followup_evidence_route_planning import *"
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

        print(
            "[PASS] In-memory compilation verified"
        )
        print(
            "[PASS] Certified upstream remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[PASS] Follow-up route planning remains "
            "deterministic, read-only, domain-agnostic, "
            "and fail-closed"
        )

        print(
            "[DONE] OI-065 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OI-065 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
