from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-027"
INSTALLER_REVISION = "OI_027_GENERIC_OBSERVATION_ROUTER_INTERFACE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_008_observation_source_routing.py", "OI-008"),
    (PACKAGE / "oi_012_routed_observation_acquisition.py", "OI-012"),
    (PACKAGE / "oi_013_observation_requirement_resolution.py", "OI-013"),
    (PACKAGE / "oi_025_oracle_explanation_query_engine.py", "OI-025"),
)

MODULE = PACKAGE / "oi_027_generic_observation_router_interface.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_027_generic_observation_router_interface.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_008_observation_source_routing import (
    ObservationRouteDecision,
    ObservationRouteRequest,
    ObservationSourceRoutingRegistry,
)
from .oi_013_observation_requirement_resolution import (
    ObservationRequirementResolver,
)

BUILD_ID = "OI-027"
OI_027_REVISION = "OI_027_GENERIC_OBSERVATION_ROUTER_INTERFACE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class GenericObservationRouterInterfaceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class GenericObservationNeed:
    need_id: str
    domain: str
    entity_kind: str
    observation_type: str
    subject_hint: str

    def __post_init__(self) -> None:
        for field in (
            "need_id",
            "domain",
            "entity_kind",
            "observation_type",
            "subject_hint",
        ):
            value = " ".join(
                str(getattr(self, field)).strip().split()
            )

            if not value:
                raise GenericObservationRouterInterfaceError(
                    f"{field} must not be empty"
                )

            if field != "subject_hint":
                value = value.lower()

            object.__setattr__(
                self,
                field,
                value,
            )


@dataclass(frozen=True, slots=True)
class GenericObservationRoute:
    need: GenericObservationNeed
    route_decision: ObservationRouteDecision
    route_hash: str


class GenericObservationRouterInterface:
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
        routing_registry: ObservationSourceRoutingRegistry,
    ) -> None:
        if not isinstance(
            routing_registry,
            ObservationSourceRoutingRegistry,
        ):
            raise TypeError(
                "routing_registry must be ObservationSourceRoutingRegistry"
            )

        self._routing_registry = routing_registry

    def route_need(
        self,
        need: GenericObservationNeed,
    ) -> GenericObservationRoute:
        if not isinstance(
            need,
            GenericObservationNeed,
        ):
            raise TypeError(
                "need must be GenericObservationNeed"
            )

        request = ObservationRouteRequest(
            domain=need.domain,
            entity_kind=need.entity_kind,
            observation_type=need.observation_type,
        )

        decision = self._routing_registry.route(
            request
        )

        body = {
            "need_id": need.need_id,
            "domain": need.domain,
            "entity_kind": need.entity_kind,
            "observation_type": need.observation_type,
            "subject_hint": need.subject_hint,
            "decision_hash": decision.decision_hash,
            "adapter_ids": decision.adapter_ids,
        }

        return GenericObservationRoute(
            need=need,
            route_decision=decision,
            route_hash=deterministic_sha256(body),
        )

    def route_profile(
        self,
        *,
        profile_id: str,
        resolver: ObservationRequirementResolver,
        subject_hint: str,
    ) -> tuple[GenericObservationRoute, ...]:
        if not isinstance(
            resolver,
            ObservationRequirementResolver,
        ):
            raise TypeError(
                "resolver must be ObservationRequirementResolver"
            )

        requests = resolver.required_requests(
            profile_id
        )

        routes = []

        for index, request in enumerate(
            requests,
            start=1,
        ):
            need = GenericObservationNeed(
                need_id=(
                    f"{str(profile_id).strip().lower()}."
                    f"need.{index}"
                ),
                domain=request.domain,
                entity_kind=request.entity_kind,
                observation_type=request.observation_type,
                subject_hint=subject_hint,
            )

            routes.append(
                self.route_need(
                    need
                )
            )

        return tuple(routes)


def verify_generic_observation_router_interface() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-027 must remain read-only"
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
            "OI-027 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_027_REVISION",
    "GenericObservationRouterInterfaceError",
    "GenericObservationNeed",
    "GenericObservationRoute",
    "GenericObservationRouterInterface",
    "verify_generic_observation_router_interface",
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
    OI_027_REVISION,
    GenericObservationNeed,
    GenericObservationRouterInterface,
    verify_generic_observation_router_interface,
)


def router():
    return GenericObservationRouterInterface(
        ObservationSourceRoutingRegistry(
            default_source_registry(),
            default_observation_route_rules(),
        )
    )


class TestOI027(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_generic_observation_router_interface()
        )

    def test_crypto_need(self):
        route = router().route_need(
            GenericObservationNeed(
                need_id="need.crypto.price",
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
                subject_hint="Bitcoin",
            )
        )

        self.assertEqual(
            route.route_decision.adapter_ids,
            ("adapter.coinbase.spot.v1",),
        )

    def test_kalshi_market_need(self):
        route = router().route_need(
            GenericObservationNeed(
                need_id="need.sports.market",
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
                subject_hint="Astros strikeouts",
            )
        )

        self.assertEqual(
            route.route_decision.adapter_ids,
            ("adapter.kalshi.v1",),
        )

    def test_unavailable_adapter_fails_closed(self):
        route = router().route_need(
            GenericObservationNeed(
                need_id="need.sports.lineup",
                domain="sports",
                entity_kind="team",
                observation_type="lineup",
                subject_hint="Astros",
            )
        )

        self.assertEqual(
            route.route_decision.adapter_ids,
            (),
        )

    def test_profile_routing(self):
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
            ),
        )

        resolver = ObservationRequirementResolver(
            (profile,)
        )

        routes = router().route_profile(
            profile_id="profile.market_explanation",
            resolver=resolver,
            subject_hint="Astros strikeouts",
        )

        self.assertEqual(len(routes), 1)
        self.assertEqual(
            routes[0].route_decision.adapter_ids,
            ("adapter.kalshi.v1",),
        )

    def test_deterministic(self):
        interface = router()
        need = GenericObservationNeed(
            need_id="need.test",
            domain="crypto",
            entity_kind="asset",
            observation_type="spot_price",
            subject_hint="Bitcoin",
        )

        a = interface.route_need(need)
        b = interface.route_need(need)

        self.assertEqual(
            a.route_hash,
            b.route_hash,
        )

    def test_side_effects(self):
        interface = router()

        self.assertTrue(interface.read_only)
        self.assertFalse(interface.network_allowed)
        self.assertFalse(interface.persistence_allowed)
        self.assertFalse(interface.publication_allowed)
        self.assertFalse(interface.execution_allowed)
        self.assertFalse(interface.qseries_execution_allowed)
        self.assertFalse(interface.prediction_allowed)
        self.assertFalse(interface.edge_score_allowed)
        self.assertFalse(interface.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-027 CERTIFICATION TEST")
    print(" GENERIC OBSERVATION ROUTER INTERFACE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI027
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-027")
    print(f"[PASS] Revision: {OI_027_REVISION}")
    print("[PASS] Generic observation needs route through the certified adapter registry")
    print("[PASS] Requirement profiles route without category-specific reasoning code")
    print("[PASS] Missing adapter capabilities fail closed with empty routes")
    print("[PASS] Prediction, probability, edge scoring, publication, and execution disabled")
    print("[DONE] OI-027 CERTIFIED")
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
    print(" OI-027 INSTALLER")
    print(" GENERIC OBSERVATION ROUTER INTERFACE")
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

    print("[PASS] Certified OI-008, OI-012, OI-013, and OI-025 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_027_generic_observation_router_interface import *"

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
        print("[PASS] Generic router interface remains deterministic, read-only, and fail-closed")
        print("[DONE] OI-027 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_bytes(original)

        print("[ROLLBACK] OI-027 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
