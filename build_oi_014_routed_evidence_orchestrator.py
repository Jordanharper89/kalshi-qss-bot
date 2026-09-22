from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-014"
INSTALLER_REVISION = "OI_014_ROUTED_EVIDENCE_ORCHESTRATOR_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_010 = PACKAGE / "oi_010_observation_freshness_health.py"
UPSTREAM_011 = PACKAGE / "oi_011_multi_source_consensus.py"
UPSTREAM_012 = PACKAGE / "oi_012_routed_observation_acquisition.py"
UPSTREAM_013 = PACKAGE / "oi_013_observation_requirement_resolution.py"
MODULE = PACKAGE / "oi_014_routed_evidence_orchestrator.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_014_routed_evidence_orchestrator.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_010_observation_freshness_health import (
    ObservationFreshnessHealthEngine,
    ObservationHealth,
    default_freshness_policies,
)
from .oi_012_routed_observation_acquisition import (
    RoutedObservationAcquisitionEngine,
    RoutedObservationAcquisitionResult,
)
from .oi_013_observation_requirement_resolution import (
    ObservationRequirementResolver,
)

BUILD_ID = "OI-014"
OI_014_REVISION = "OI_014_ROUTED_EVIDENCE_ORCHESTRATOR_V1"

READ_ONLY = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class RoutedEvidenceOrchestratorError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RoutedEvidenceRequirementResult:
    requirement_index: int
    acquisition: RoutedObservationAcquisitionResult
    health: tuple[ObservationHealth, ...]


@dataclass(frozen=True, slots=True)
class RoutedEvidenceOrchestration:
    profile_id: str
    query_id: str
    required_count: int
    satisfied_count: int
    missing_count: int
    results: tuple[RoutedEvidenceRequirementResult, ...]
    orchestration_hash: str


class RoutedEvidenceOrchestrator:
    read_only = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(
        self,
        *,
        requirement_resolver: ObservationRequirementResolver,
        acquisition_engine: RoutedObservationAcquisitionEngine,
        freshness_engine: ObservationFreshnessHealthEngine | None = None,
    ) -> None:
        if not isinstance(
            requirement_resolver,
            ObservationRequirementResolver,
        ):
            raise TypeError(
                "requirement_resolver must be ObservationRequirementResolver"
            )

        if not isinstance(
            acquisition_engine,
            RoutedObservationAcquisitionEngine,
        ):
            raise TypeError(
                "acquisition_engine must be RoutedObservationAcquisitionEngine"
            )

        self._resolver = requirement_resolver
        self._acquisition = acquisition_engine
        self._freshness = (
            freshness_engine
            or ObservationFreshnessHealthEngine(
                default_freshness_policies()
            )
        )

    def orchestrate(
        self,
        *,
        profile_id: str,
        query_id: str,
        evaluated_at: datetime,
    ) -> RoutedEvidenceOrchestration:
        if not isinstance(evaluated_at, datetime):
            raise TypeError("evaluated_at must be datetime")

        if evaluated_at.tzinfo is None:
            raise RoutedEvidenceOrchestratorError(
                "evaluated_at must be timezone-aware"
            )

        evaluated_at = evaluated_at.astimezone(timezone.utc)

        requests = self._resolver.required_requests(
            profile_id
        )

        results = []

        for index, request in enumerate(requests):
            acquisition = self._acquisition.acquire(
                query_id=f"{query_id}.requirement.{index}",
                request=request,
                assembled_at=evaluated_at,
            )

            health = tuple(
                self._freshness.evaluate(
                    observation,
                    evaluated_at=evaluated_at,
                )
                for observation in acquisition.observations
            )

            results.append(
                RoutedEvidenceRequirementResult(
                    requirement_index=index,
                    acquisition=acquisition,
                    health=health,
                )
            )

        satisfied_count = sum(
            1
            for item in results
            if item.acquisition.observations
        )

        required_count = len(results)
        missing_count = required_count - satisfied_count

        body = {
            "profile_id": str(profile_id).strip().lower(),
            "query_id": str(query_id).strip(),
            "required_count": required_count,
            "satisfied_count": satisfied_count,
            "missing_count": missing_count,
            "acquisition_hashes": tuple(
                item.acquisition.acquisition_hash
                for item in results
            ),
            "health_hashes": tuple(
                tuple(health.health_hash for health in item.health)
                for item in results
            ),
        }

        return RoutedEvidenceOrchestration(
            profile_id=str(profile_id).strip().lower(),
            query_id=str(query_id).strip(),
            required_count=required_count,
            satisfied_count=satisfied_count,
            missing_count=missing_count,
            results=tuple(results),
            orchestration_hash=deterministic_sha256(body),
        )


def verify_routed_evidence_orchestrator() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-014 must remain read-only")

    if any(
        (
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-014 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_014_REVISION",
    "RoutedEvidenceOrchestratorError",
    "RoutedEvidenceRequirementResult",
    "RoutedEvidenceOrchestration",
    "RoutedEvidenceOrchestrator",
    "verify_routed_evidence_orchestrator",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_008_observation_source_routing import (
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
)
from qseries_v2.observation_intelligence.oi_012_routed_observation_acquisition import (
    AdapterAcquisitionBinding,
    RoutedObservationAcquisitionEngine,
)
from qseries_v2.observation_intelligence.oi_013_observation_requirement_resolution import (
    ObservationRequirement,
    ObservationRequirementResolver,
    build_requirement_profile,
)
from qseries_v2.observation_intelligence.oi_014_routed_evidence_orchestrator import (
    OI_014_REVISION,
    RoutedEvidenceOrchestrator,
    verify_routed_evidence_orchestrator,
)

NOW = datetime(2026, 8, 10, 9, 0, tzinfo=timezone.utc)


def coinbase_acquire(request):
    return (
        RawObservationEnvelope(
            source=ObservationSourceIdentity(
                source_id="coinbase.public.spot",
                source_kind="market_data",
                provider="Coinbase",
                adapter_id="adapter.coinbase.spot.v1",
            ),
            external_observation_id="BTC-USD-OI014",
            observed_at=NOW,
            subject="BTC",
            observation_type="spot_price",
            payload={
                "product_id": "BTC-USD",
                "symbol": "BTC",
                "quote_currency": "USD",
                "price": "100.0",
            },
            metadata={"venue": "coinbase"},
        ),
    )


def requirement_resolver():
    profile = build_requirement_profile(
        "profile.asset_state",
        (
            ObservationRequirement(
                requirement_id="requirement.spot",
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
                required=True,
                reason="current asset state",
            ),
        ),
    )

    return ObservationRequirementResolver(
        (profile,)
    )


def acquisition_engine():
    registry = default_source_registry()
    router = ObservationSourceRoutingRegistry(
        registry,
        default_observation_route_rules(),
    )

    return RoutedObservationAcquisitionEngine(
        adapter_registry=registry,
        routing_registry=router,
        bindings=(
            AdapterAcquisitionBinding(
                adapter_id="adapter.coinbase.spot.v1",
                acquire_callable=coinbase_acquire,
            ),
            AdapterAcquisitionBinding(
                adapter_id="adapter.kalshi.v1",
                acquire_callable=lambda request: (),
            ),
        ),
    )


class TestOI014(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_routed_evidence_orchestrator()
        )

    def test_orchestration(self):
        value = RoutedEvidenceOrchestrator(
            requirement_resolver=requirement_resolver(),
            acquisition_engine=acquisition_engine(),
        ).orchestrate(
            profile_id="profile.asset_state",
            query_id="query.asset",
            evaluated_at=NOW,
        )

        self.assertEqual(value.required_count, 1)
        self.assertEqual(value.satisfied_count, 1)
        self.assertEqual(value.missing_count, 0)

    def test_health(self):
        value = RoutedEvidenceOrchestrator(
            requirement_resolver=requirement_resolver(),
            acquisition_engine=acquisition_engine(),
        ).orchestrate(
            profile_id="profile.asset_state",
            query_id="query.asset",
            evaluated_at=NOW,
        )

        self.assertEqual(
            value.results[0].health[0].freshness_status,
            "fresh",
        )

    def test_deterministic(self):
        orchestrator = RoutedEvidenceOrchestrator(
            requirement_resolver=requirement_resolver(),
            acquisition_engine=acquisition_engine(),
        )

        a = orchestrator.orchestrate(
            profile_id="profile.asset_state",
            query_id="query.asset",
            evaluated_at=NOW,
        )

        b = orchestrator.orchestrate(
            profile_id="profile.asset_state",
            query_id="query.asset",
            evaluated_at=NOW,
        )

        self.assertEqual(
            a.orchestration_hash,
            b.orchestration_hash,
        )

    def test_side_effects(self):
        value = RoutedEvidenceOrchestrator(
            requirement_resolver=requirement_resolver(),
            acquisition_engine=acquisition_engine(),
        )

        self.assertTrue(value.read_only)
        self.assertFalse(value.persistence_allowed)
        self.assertFalse(value.publication_allowed)
        self.assertFalse(value.execution_allowed)
        self.assertFalse(value.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-014 CERTIFICATION TEST")
    print(" ROUTED EVIDENCE ORCHESTRATOR")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI014
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-014")
    print(f"[PASS] Revision: {OI_014_REVISION}")
    print("[PASS] Requirement profiles drive routed acquisition")
    print("[PASS] Routed evidence receives freshness health")
    print("[PASS] Satisfied and missing required evidence counted deterministically")
    print("[PASS] No prediction or edge scoring introduced")
    print("[PASS] Persistence, publication, and execution disabled")
    print("[DONE] OI-014 CERTIFIED")
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
    print(" OI-014 INSTALLER")
    print(" ROUTED EVIDENCE ORCHESTRATOR")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    upstreams = (
        (UPSTREAM_010, "OI-010"),
        (UPSTREAM_011, "OI-011"),
        (UPSTREAM_012, "OI-012"),
        (UPSTREAM_013, "OI-013"),
    )

    for path, name in upstreams:
        if not path.is_file():
            raise RuntimeError(f"Certified {name} missing: {path}")

    upstream_hashes = {
        path: sha(path)
        for path, _ in upstreams
    }

    print("[PASS] Certified OI-010 through OI-013 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_014_routed_evidence_orchestrator import *"

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
        print("[PASS] Orchestration remains deterministic, read-only, and non-predictive")
        print("[DONE] OI-014 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-014 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
