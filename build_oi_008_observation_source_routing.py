from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-008"
INSTALLER_REVISION = "OI_008_OBSERVATION_SOURCE_ROUTING_REGISTRY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_002 = PACKAGE / "oi_002_source_adapter_registry.py"
UPSTREAM_007 = PACKAGE / "oi_007_observation_history.py"
MODULE = PACKAGE / "oi_008_observation_source_routing.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_008_observation_source_routing.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_002_source_adapter_registry import (
    SourceAdapterDescriptor,
    SourceAdapterRegistry,
    verify_source_adapter_registry,
)
from .oi_007_observation_history import verify_observation_history

BUILD_ID = "OI-008"
OI_008_REVISION = "OI_008_OBSERVATION_SOURCE_ROUTING_REGISTRY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class ObservationSourceRoutingError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ObservationRouteRule:
    route_id: str
    domains: tuple[str, ...]
    entity_kinds: tuple[str, ...]
    observation_types: tuple[str, ...]
    adapter_ids: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    priority: int

    def __post_init__(self) -> None:
        route_id = str(self.route_id).strip().lower()
        if not route_id:
            raise ObservationSourceRoutingError("route_id must not be empty")
        object.__setattr__(self, "route_id", route_id)

        for field in (
            "domains",
            "entity_kinds",
            "observation_types",
            "adapter_ids",
            "required_capabilities",
        ):
            raw = tuple(getattr(self, field))
            normalized = tuple(
                sorted(
                    {
                        " ".join(str(item).strip().lower().split())
                        for item in raw
                        if str(item).strip()
                    }
                )
            )
            object.__setattr__(self, field, normalized)

        if not self.adapter_ids:
            raise ObservationSourceRoutingError(
                "route rule must target at least one adapter"
            )

        if not isinstance(self.priority, int) or self.priority < 0:
            raise ObservationSourceRoutingError(
                "priority must be a non-negative integer"
            )

    @property
    def rule_hash(self) -> str:
        return deterministic_sha256(
            {
                "route_id": self.route_id,
                "domains": self.domains,
                "entity_kinds": self.entity_kinds,
                "observation_types": self.observation_types,
                "adapter_ids": self.adapter_ids,
                "required_capabilities": self.required_capabilities,
                "priority": self.priority,
            }
        )


@dataclass(frozen=True, slots=True)
class ObservationRouteRequest:
    domain: str
    entity_kind: str
    observation_type: str

    def __post_init__(self) -> None:
        for field in ("domain", "entity_kind", "observation_type"):
            value = " ".join(
                str(getattr(self, field)).strip().lower().split()
            )
            if not value:
                raise ObservationSourceRoutingError(
                    f"{field} must not be empty"
                )
            object.__setattr__(self, field, value)


@dataclass(frozen=True, slots=True)
class ObservationRouteDecision:
    request: ObservationRouteRequest
    adapter_ids: tuple[str, ...]
    matched_rule_ids: tuple[str, ...]
    decision_hash: str


class ObservationSourceRoutingRegistry:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(
        self,
        adapter_registry: SourceAdapterRegistry,
        rules: tuple[ObservationRouteRule, ...],
    ) -> None:
        if not isinstance(adapter_registry, SourceAdapterRegistry):
            raise TypeError("adapter_registry must be SourceAdapterRegistry")

        values = tuple(rules)
        if any(not isinstance(rule, ObservationRouteRule) for rule in values):
            raise TypeError("all rules must be ObservationRouteRule")

        ordered = tuple(
            sorted(
                values,
                key=lambda rule: (
                    rule.priority,
                    rule.route_id,
                ),
            )
        )

        if values != ordered:
            raise ObservationSourceRoutingError(
                "rules must be deterministically sorted"
            )

        route_ids = tuple(rule.route_id for rule in values)
        if len(route_ids) != len(set(route_ids)):
            raise ObservationSourceRoutingError("duplicate route_id")

        for rule in values:
            for adapter_id in rule.adapter_ids:
                descriptor = adapter_registry.get(adapter_id)
                if descriptor is None:
                    raise ObservationSourceRoutingError(
                        f"route references unknown adapter: {adapter_id}"
                    )

                for capability in rule.required_capabilities:
                    if capability not in descriptor.capabilities:
                        raise ObservationSourceRoutingError(
                            f"adapter {adapter_id} missing required capability {capability}"
                        )

        self._registry = adapter_registry
        self._rules = values
        self._by_id = MappingProxyType(
            {rule.route_id: rule for rule in values}
        )

    @property
    def rules(self) -> tuple[ObservationRouteRule, ...]:
        return self._rules

    @property
    def routing_hash(self) -> str:
        return deterministic_sha256(
            {
                "adapter_registry_hash": self._registry.registry_hash,
                "rule_hashes": tuple(rule.rule_hash for rule in self._rules),
            }
        )

    @staticmethod
    def _matches(
        requested: str,
        accepted: tuple[str, ...],
    ) -> bool:
        return not accepted or "*" in accepted or requested in accepted

    def route(
        self,
        request: ObservationRouteRequest,
    ) -> ObservationRouteDecision:
        if not isinstance(request, ObservationRouteRequest):
            raise TypeError("request must be ObservationRouteRequest")

        matches = tuple(
            rule
            for rule in self._rules
            if (
                self._matches(request.domain, rule.domains)
                and self._matches(request.entity_kind, rule.entity_kinds)
                and self._matches(
                    request.observation_type,
                    rule.observation_types,
                )
            )
        )

        adapter_ids = tuple(
            sorted(
                {
                    adapter_id
                    for rule in matches
                    for adapter_id in rule.adapter_ids
                    if (
                        self._registry.get(adapter_id) is not None
                        and self._registry.get(adapter_id).enabled_for_intake
                    )
                }
            )
        )

        matched_rule_ids = tuple(rule.route_id for rule in matches)

        body = {
            "request": {
                "domain": request.domain,
                "entity_kind": request.entity_kind,
                "observation_type": request.observation_type,
            },
            "adapter_ids": adapter_ids,
            "matched_rule_ids": matched_rule_ids,
        }

        return ObservationRouteDecision(
            request=request,
            adapter_ids=adapter_ids,
            matched_rule_ids=matched_rule_ids,
            decision_hash=deterministic_sha256(body),
        )


def default_observation_route_rules() -> tuple[ObservationRouteRule, ...]:
    return (
        ObservationRouteRule(
            route_id="route.crypto.spot",
            domains=("crypto",),
            entity_kinds=("asset",),
            observation_types=("spot_price",),
            adapter_ids=("adapter.coinbase.spot.v1",),
            required_capabilities=("spot price",),
            priority=10,
        ),
        ObservationRouteRule(
            route_id="route.kalshi.market",
            domains=("*",),
            entity_kinds=("market",),
            observation_types=("market_snapshot",),
            adapter_ids=("adapter.kalshi.v1",),
            required_capabilities=("market snapshot",),
            priority=20,
        ),
    )


def verify_observation_source_routing() -> bool:
    verify_source_adapter_registry()
    verify_observation_history()

    if READ_ONLY is not True:
        raise AssertionError("OI-008 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-008 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_008_REVISION",
    "ObservationSourceRoutingError",
    "ObservationRouteRule",
    "ObservationRouteRequest",
    "ObservationRouteDecision",
    "ObservationSourceRoutingRegistry",
    "default_observation_route_rules",
    "verify_observation_source_routing",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_008_observation_source_routing import (
    OI_008_REVISION,
    ObservationRouteRequest,
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
    verify_observation_source_routing,
)


class TestOI008(unittest.TestCase):
    def setUp(self):
        self.router = ObservationSourceRoutingRegistry(
            default_source_registry(),
            default_observation_route_rules(),
        )

    def test_foundation(self):
        self.assertTrue(verify_observation_source_routing())

    def test_crypto_route(self):
        decision = self.router.route(
            ObservationRouteRequest(
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
            )
        )
        self.assertEqual(
            decision.adapter_ids,
            ("adapter.coinbase.spot.v1",),
        )

    def test_kalshi_universal_route(self):
        decision = self.router.route(
            ObservationRouteRequest(
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
            )
        )
        self.assertEqual(
            decision.adapter_ids,
            ("adapter.kalshi.v1",),
        )

    def test_unknown_route(self):
        decision = self.router.route(
            ObservationRouteRequest(
                domain="sports",
                entity_kind="player",
                observation_type="lineup",
            )
        )
        self.assertEqual(decision.adapter_ids, ())

    def test_deterministic(self):
        request = ObservationRouteRequest(
            domain="crypto",
            entity_kind="asset",
            observation_type="spot_price",
        )
        self.assertEqual(
            self.router.route(request).decision_hash,
            self.router.route(request).decision_hash,
        )

    def test_side_effects(self):
        self.assertTrue(self.router.read_only)
        self.assertFalse(self.router.network_allowed)
        self.assertFalse(self.router.persistence_allowed)
        self.assertFalse(self.router.publication_allowed)
        self.assertFalse(self.router.execution_allowed)
        self.assertFalse(self.router.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-008 CERTIFICATION TEST")
    print(" OBSERVATION SOURCE ROUTING REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI008
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-008")
    print(f"[PASS] Revision: {OI_008_REVISION}")
    print("[PASS] Domain/entity/type routing to registered adapters certified")
    print("[PASS] Universal Kalshi market route certified")
    print("[PASS] Missing routes fail closed without guessing")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-008 CERTIFIED")
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
    print(" OI-008 INSTALLER")
    print(" OBSERVATION SOURCE ROUTING REGISTRY")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for path, name in (
        (UPSTREAM_002, "OI-002"),
        (UPSTREAM_007, "OI-007"),
    ):
        if not path.is_file():
            raise RuntimeError(f"Certified {name} missing: {path}")

    upstream_hashes = {
        path: sha(path)
        for path in (UPSTREAM_002, UPSTREAM_007)
    }

    print("[PASS] Certified OI-002 and OI-007 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_008_observation_source_routing import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

        for path, expected in upstream_hashes.items():
            if sha(path) != expected:
                raise RuntimeError(f"Certified upstream changed: {path.name}")

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified upstream remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[PASS] Router remains structural, deterministic, read-only, and non-predictive")
        print("[DONE] OI-008 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-008 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
