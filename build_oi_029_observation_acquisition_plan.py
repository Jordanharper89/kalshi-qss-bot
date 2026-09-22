from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-029"
INSTALLER_REVISION = "OI_029_OBSERVATION_ACQUISITION_PLAN_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_013_observation_requirement_resolution.py", "OI-013"),
    (PACKAGE / "oi_027_generic_observation_router_interface.py", "OI-027"),
    (PACKAGE / "oi_028_adapter_capability_coverage.py", "OI-028"),
)

MODULE = PACKAGE / "oi_029_observation_acquisition_plan.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_029_observation_acquisition_plan.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_013_observation_requirement_resolution import (
    ObservationRequirementResolver,
)
from .oi_027_generic_observation_router_interface import (
    GenericObservationNeed,
)
from .oi_028_adapter_capability_coverage import (
    AdapterCapabilityCoverageRegistry,
)

BUILD_ID = "OI-029"
OI_029_REVISION = "OI_029_OBSERVATION_ACQUISITION_PLAN_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class ObservationAcquisitionPlanError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ObservationAcquisitionPlanItem:
    ordinal: int
    need_id: str
    domain: str
    entity_kind: str
    observation_type: str
    subject_hint: str
    adapter_ids: tuple[str, ...]
    covered: bool
    item_hash: str


@dataclass(frozen=True, slots=True)
class ObservationAcquisitionPlan:
    plan_id: str
    profile_id: str
    subject_hint: str
    items: tuple[ObservationAcquisitionPlanItem, ...]
    covered_count: int
    missing_count: int
    complete_coverage: bool
    plan_hash: str
    read_only: bool


class ObservationAcquisitionPlanBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def __init__(
        self,
        *,
        resolver: ObservationRequirementResolver,
        coverage_registry: AdapterCapabilityCoverageRegistry,
    ) -> None:
        if not isinstance(
            resolver,
            ObservationRequirementResolver,
        ):
            raise TypeError(
                "resolver must be ObservationRequirementResolver"
            )

        if not isinstance(
            coverage_registry,
            AdapterCapabilityCoverageRegistry,
        ):
            raise TypeError(
                "coverage_registry must be AdapterCapabilityCoverageRegistry"
            )

        self._resolver = resolver
        self._coverage = coverage_registry

    def build(
        self,
        *,
        plan_id: str,
        profile_id: str,
        subject_hint: str,
    ) -> ObservationAcquisitionPlan:
        plan_id_value = str(plan_id).strip()
        profile_id_value = " ".join(
            str(profile_id).strip().lower().split()
        )
        subject_value = " ".join(
            str(subject_hint).strip().split()
        )

        if not plan_id_value:
            raise ObservationAcquisitionPlanError(
                "plan_id must not be empty"
            )

        if not profile_id_value:
            raise ObservationAcquisitionPlanError(
                "profile_id must not be empty"
            )

        if not subject_value:
            raise ObservationAcquisitionPlanError(
                "subject_hint must not be empty"
            )

        requests = self._resolver.required_requests(
            profile_id_value
        )

        items = []

        for ordinal, request in enumerate(
            requests,
            start=1,
        ):
            need = GenericObservationNeed(
                need_id=(
                    f"{profile_id_value}.need.{ordinal}"
                ),
                domain=request.domain,
                entity_kind=request.entity_kind,
                observation_type=request.observation_type,
                subject_hint=subject_value,
            )

            coverage = self._coverage.evaluate_need(
                need
            )

            body = {
                "ordinal": ordinal,
                "need_id": need.need_id,
                "domain": need.domain,
                "entity_kind": need.entity_kind,
                "observation_type": need.observation_type,
                "subject_hint": need.subject_hint,
                "adapter_ids": coverage.adapter_ids,
                "covered": coverage.covered,
            }

            items.append(
                ObservationAcquisitionPlanItem(
                    ordinal=ordinal,
                    need_id=need.need_id,
                    domain=need.domain,
                    entity_kind=need.entity_kind,
                    observation_type=need.observation_type,
                    subject_hint=need.subject_hint,
                    adapter_ids=coverage.adapter_ids,
                    covered=coverage.covered,
                    item_hash=deterministic_sha256(body),
                )
            )

        covered_count = sum(
            1
            for item in items
            if item.covered
        )

        missing_count = len(items) - covered_count
        complete_coverage = missing_count == 0

        body = {
            "plan_id": plan_id_value,
            "profile_id": profile_id_value,
            "subject_hint": subject_value,
            "item_hashes": tuple(
                item.item_hash
                for item in items
            ),
            "covered_count": covered_count,
            "missing_count": missing_count,
            "complete_coverage": complete_coverage,
            "read_only": True,
        }

        return ObservationAcquisitionPlan(
            plan_id=plan_id_value,
            profile_id=profile_id_value,
            subject_hint=subject_value,
            items=tuple(items),
            covered_count=covered_count,
            missing_count=missing_count,
            complete_coverage=complete_coverage,
            plan_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_observation_acquisition_plan() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-029 must remain read-only"
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
            "OI-029 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_029_REVISION",
    "ObservationAcquisitionPlanError",
    "ObservationAcquisitionPlanItem",
    "ObservationAcquisitionPlan",
    "ObservationAcquisitionPlanBuilder",
    "verify_observation_acquisition_plan",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_008_observation_source_routing import (
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
)
from qseries_v2.observation_intelligence.oi_013_observation_requirement_resolution import (
    ObservationRequirement,
    ObservationRequirementResolver,
    build_requirement_profile,
)
from qseries_v2.observation_intelligence.oi_027_generic_observation_router_interface import (
    GenericObservationRouterInterface,
)
from qseries_v2.observation_intelligence.oi_028_adapter_capability_coverage import (
    AdapterCapabilityCoverageRegistry,
)
from qseries_v2.observation_intelligence.oi_029_observation_acquisition_plan import (
    OI_029_REVISION,
    ObservationAcquisitionPlanBuilder,
    verify_observation_acquisition_plan,
)


def builder():
    profile = build_requirement_profile(
        "profile.market_explanation",
        (
            ObservationRequirement(
                requirement_id="requirement.market",
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
                required=True,
                reason="current market state",
            ),
            ObservationRequirement(
                requirement_id="requirement.lineup",
                domain="sports",
                entity_kind="team",
                observation_type="lineup",
                required=True,
                reason="team lineup context",
            ),
        ),
    )

    resolver = ObservationRequirementResolver(
        (profile,)
    )

    registry = default_source_registry()

    router = GenericObservationRouterInterface(
        ObservationSourceRoutingRegistry(
            registry,
            default_observation_route_rules(),
        )
    )

    coverage = AdapterCapabilityCoverageRegistry(
        adapter_registry=registry,
        router=router,
    )

    return ObservationAcquisitionPlanBuilder(
        resolver=resolver,
        coverage_registry=coverage,
    )


class TestOI029(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_observation_acquisition_plan()
        )

    def test_plan(self):
        plan = builder().build(
            plan_id="plan.astros",
            profile_id="profile.market_explanation",
            subject_hint="Astros strikeouts",
        )

        self.assertEqual(len(plan.items), 2)
        self.assertEqual(plan.covered_count, 1)
        self.assertEqual(plan.missing_count, 1)
        self.assertFalse(plan.complete_coverage)

    def test_covered_adapter_preserved(self):
        plan = builder().build(
            plan_id="plan.astros",
            profile_id="profile.market_explanation",
            subject_hint="Astros strikeouts",
        )

        market_item = tuple(
            item
            for item in plan.items
            if item.observation_type == "market_snapshot"
        )[0]

        self.assertEqual(
            market_item.adapter_ids,
            ("adapter.kalshi.v1",),
        )

    def test_missing_adapter_explicit(self):
        plan = builder().build(
            plan_id="plan.astros",
            profile_id="profile.market_explanation",
            subject_hint="Astros strikeouts",
        )

        lineup_item = tuple(
            item
            for item in plan.items
            if item.observation_type == "lineup"
        )[0]

        self.assertFalse(lineup_item.covered)
        self.assertEqual(lineup_item.adapter_ids, ())

    def test_deterministic(self):
        a = builder().build(
            plan_id="plan.astros",
            profile_id="profile.market_explanation",
            subject_hint="Astros strikeouts",
        )

        b = builder().build(
            plan_id="plan.astros",
            profile_id="profile.market_explanation",
            subject_hint="Astros strikeouts",
        )

        self.assertEqual(a.plan_hash, b.plan_hash)

    def test_side_effects(self):
        item = builder()

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
    print(" OI-029 CERTIFICATION TEST")
    print(" OBSERVATION ACQUISITION PLAN")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI029
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-029")
    print(f"[PASS] Revision: {OI_029_REVISION}")
    print("[PASS] Requirement profiles convert into deterministic adapter acquisition plans")
    print("[PASS] Covered and missing observation needs remain explicit")
    print("[PASS] Missing adapter capability never silently downgrades a requirement")
    print("[PASS] Prediction, probability, scoring, publication, and execution disabled")
    print("[DONE] OI-029 CERTIFIED")
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
    print(" OI-029 INSTALLER")
    print(" OBSERVATION ACQUISITION PLAN")
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
        "[PASS] Certified OI-013, OI-027, "
        "and OI-028 verified read-only"
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
            "from .oi_029_observation_acquisition_plan import *"
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
            "[PASS] Acquisition planning remains "
            "deterministic, read-only, and fail-closed"
        )

        print(
            "[DONE] OI-029 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OI-029 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
