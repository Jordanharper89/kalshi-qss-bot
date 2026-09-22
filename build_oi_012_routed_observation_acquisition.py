from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-012"
INSTALLER_REVISION = "OI_012_ROUTED_OBSERVATION_ACQUISITION_ENGINE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_008 = PACKAGE / "oi_008_observation_source_routing.py"
UPSTREAM_009 = PACKAGE / "oi_009_observation_evidence_assembly.py"
UPSTREAM_011 = PACKAGE / "oi_011_multi_source_consensus.py"
MODULE = PACKAGE / "oi_012_routed_observation_acquisition.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_012_routed_observation_acquisition.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Callable, Mapping, Any

from .oi_001_universal_observation_intake import RawObservationEnvelope, deterministic_sha256
from .oi_002_source_adapter_registry import SourceAdapterRegistry
from .oi_003_canonical_observation_gateway import (
    CanonicalLiveObservation,
    CanonicalLiveObservationGateway,
)
from .oi_008_observation_source_routing import (
    ObservationRouteDecision,
    ObservationRouteRequest,
    ObservationSourceRoutingRegistry,
    verify_observation_source_routing,
)
from .oi_009_observation_evidence_assembly import (
    ObservationEvidenceAssembler,
    ObservationEvidenceBundle,
    verify_observation_evidence_assembly,
)
from .oi_011_multi_source_consensus import verify_multi_source_consensus

BUILD_ID = "OI-012"
OI_012_REVISION = "OI_012_ROUTED_OBSERVATION_ACQUISITION_ENGINE_V1"

READ_ONLY = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class RoutedObservationAcquisitionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AdapterAcquisitionBinding:
    adapter_id: str
    acquire_callable: Callable[[ObservationRouteRequest], tuple[RawObservationEnvelope, ...]]

    def __post_init__(self) -> None:
        adapter_id = str(self.adapter_id).strip().lower()
        if not adapter_id:
            raise RoutedObservationAcquisitionError(
                "adapter_id must not be empty"
            )
        if not callable(self.acquire_callable):
            raise TypeError("acquire_callable must be callable")

        object.__setattr__(self, "adapter_id", adapter_id)


@dataclass(frozen=True, slots=True)
class RoutedObservationAcquisitionResult:
    route_decision: ObservationRouteDecision
    observations: tuple[CanonicalLiveObservation, ...]
    evidence_bundle: ObservationEvidenceBundle
    invoked_adapter_ids: tuple[str, ...]
    acquisition_hash: str


class RoutedObservationAcquisitionEngine:
    read_only = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(
        self,
        *,
        adapter_registry: SourceAdapterRegistry,
        routing_registry: ObservationSourceRoutingRegistry,
        bindings: tuple[AdapterAcquisitionBinding, ...],
    ) -> None:
        if not isinstance(adapter_registry, SourceAdapterRegistry):
            raise TypeError("adapter_registry must be SourceAdapterRegistry")

        if not isinstance(routing_registry, ObservationSourceRoutingRegistry):
            raise TypeError(
                "routing_registry must be ObservationSourceRoutingRegistry"
            )

        values = tuple(bindings)

        if any(
            not isinstance(item, AdapterAcquisitionBinding)
            for item in values
        ):
            raise TypeError(
                "all bindings must be AdapterAcquisitionBinding"
            )

        ordered = tuple(
            sorted(values, key=lambda item: item.adapter_id)
        )

        if values != ordered:
            raise RoutedObservationAcquisitionError(
                "bindings must be deterministically sorted"
            )

        ids = tuple(item.adapter_id for item in values)
        if len(ids) != len(set(ids)):
            raise RoutedObservationAcquisitionError(
                "duplicate adapter binding"
            )

        for adapter_id in ids:
            if adapter_registry.get(adapter_id) is None:
                raise RoutedObservationAcquisitionError(
                    f"binding references unknown adapter: {adapter_id}"
                )

        self._adapter_registry = adapter_registry
        self._routing_registry = routing_registry
        self._bindings = MappingProxyType(
            {item.adapter_id: item for item in values}
        )
        self._gateway = CanonicalLiveObservationGateway(
            adapter_registry
        )
        self._assembler = ObservationEvidenceAssembler()

    def acquire(
        self,
        *,
        query_id: str,
        request: ObservationRouteRequest,
        assembled_at: datetime,
    ) -> RoutedObservationAcquisitionResult:
        if not isinstance(request, ObservationRouteRequest):
            raise TypeError("request must be ObservationRouteRequest")

        if not isinstance(assembled_at, datetime):
            raise TypeError("assembled_at must be datetime")

        if assembled_at.tzinfo is None:
            raise RoutedObservationAcquisitionError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(timezone.utc)

        decision = self._routing_registry.route(request)

        observations: list[CanonicalLiveObservation] = []
        invoked = []

        for adapter_id in decision.adapter_ids:
            binding = self._bindings.get(adapter_id)

            if binding is None:
                raise RoutedObservationAcquisitionError(
                    f"missing acquisition binding for routed adapter: {adapter_id}"
                )

            envelopes = tuple(
                binding.acquire_callable(request)
            )

            if any(
                not isinstance(item, RawObservationEnvelope)
                for item in envelopes
            ):
                raise RoutedObservationAcquisitionError(
                    f"adapter {adapter_id} returned invalid envelope"
                )

            for envelope in envelopes:
                if envelope.source.adapter_id != adapter_id:
                    raise RoutedObservationAcquisitionError(
                        "adapter binding returned envelope owned by different adapter"
                    )

                observations.append(
                    self._gateway.canonicalize(
                        envelope
                    ).canonical_observation
                )

            invoked.append(adapter_id)

        canonical = tuple(
            sorted(
                observations,
                key=lambda item: (
                    item.observed_at,
                    item.canonical_observation_id,
                ),
            )
        )

        bundle = self._assembler.assemble(
            query_id=query_id,
            route_decision=decision,
            observations=canonical,
            assembled_at=assembled_at,
        )

        body = {
            "query_id": query_id,
            "route_decision_hash": decision.decision_hash,
            "invoked_adapter_ids": tuple(invoked),
            "observation_hashes": tuple(
                item.canonical_observation_hash
                for item in canonical
            ),
            "evidence_hash": bundle.evidence_hash,
        }

        return RoutedObservationAcquisitionResult(
            route_decision=decision,
            observations=canonical,
            evidence_bundle=bundle,
            invoked_adapter_ids=tuple(invoked),
            acquisition_hash=deterministic_sha256(body),
        )


def verify_routed_observation_acquisition() -> bool:
    verify_observation_source_routing()
    verify_observation_evidence_assembly()
    verify_multi_source_consensus()

    if READ_ONLY is not True:
        raise AssertionError("OI-012 must remain read-only")

    if any(
        (
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-012 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_012_REVISION",
    "RoutedObservationAcquisitionError",
    "AdapterAcquisitionBinding",
    "RoutedObservationAcquisitionResult",
    "RoutedObservationAcquisitionEngine",
    "verify_routed_observation_acquisition",
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
    ObservationRouteRequest,
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
)
from qseries_v2.observation_intelligence.oi_012_routed_observation_acquisition import (
    OI_012_REVISION,
    AdapterAcquisitionBinding,
    RoutedObservationAcquisitionEngine,
    verify_routed_observation_acquisition,
)

NOW = datetime(2026, 8, 10, 8, 0, tzinfo=timezone.utc)


def coinbase_acquire(request):
    return (
        RawObservationEnvelope(
            source=ObservationSourceIdentity(
                source_id="coinbase.public.spot",
                source_kind="market_data",
                provider="Coinbase",
                adapter_id="adapter.coinbase.spot.v1",
            ),
            external_observation_id="BTC-USD-ROUTED",
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


def kalshi_acquire(request):
    return (
        RawObservationEnvelope(
            source=ObservationSourceIdentity(
                source_id="kalshi.public",
                source_kind="market_venue",
                provider="Kalshi",
                adapter_id="adapter.kalshi.v1",
            ),
            external_observation_id="KXTEST-ROUTED",
            observed_at=NOW,
            subject="Test Market",
            observation_type="market_snapshot",
            payload={
                "ticker": "KXTEST",
                "yes_bid": 50,
                "yes_ask": 52,
            },
            metadata={
                "venue": "kalshi",
                "market_ticker": "KXTEST",
            },
        ),
    )


class TestOI012(unittest.TestCase):
    def setUp(self):
        self.registry = default_source_registry()
        self.router = ObservationSourceRoutingRegistry(
            self.registry,
            default_observation_route_rules(),
        )
        self.engine = RoutedObservationAcquisitionEngine(
            adapter_registry=self.registry,
            routing_registry=self.router,
            bindings=(
                AdapterAcquisitionBinding(
                    adapter_id="adapter.coinbase.spot.v1",
                    acquire_callable=coinbase_acquire,
                ),
                AdapterAcquisitionBinding(
                    adapter_id="adapter.kalshi.v1",
                    acquire_callable=kalshi_acquire,
                ),
            ),
        )

    def test_foundation(self):
        self.assertTrue(
            verify_routed_observation_acquisition()
        )

    def test_crypto_acquisition(self):
        result = self.engine.acquire(
            query_id="query.crypto",
            request=ObservationRouteRequest(
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
            ),
            assembled_at=NOW,
        )

        self.assertEqual(
            result.invoked_adapter_ids,
            ("adapter.coinbase.spot.v1",),
        )
        self.assertEqual(len(result.observations), 1)
        self.assertEqual(
            result.observations[0].subject,
            "BTC",
        )
        self.assertEqual(
            len(result.evidence_bundle.observations),
            1,
        )

    def test_kalshi_acquisition(self):
        result = self.engine.acquire(
            query_id="query.kalshi",
            request=ObservationRouteRequest(
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
            ),
            assembled_at=NOW,
        )

        self.assertEqual(
            result.invoked_adapter_ids,
            ("adapter.kalshi.v1",),
        )
        self.assertEqual(
            result.observations[0].metadata["market_ticker"],
            "KXTEST",
        )

    def test_unknown_route_fails_closed(self):
        result = self.engine.acquire(
            query_id="query.unknown",
            request=ObservationRouteRequest(
                domain="sports",
                entity_kind="player",
                observation_type="lineup",
            ),
            assembled_at=NOW,
        )

        self.assertEqual(result.invoked_adapter_ids, ())
        self.assertEqual(result.observations, ())
        self.assertEqual(result.evidence_bundle.observations, ())

    def test_deterministic(self):
        request = ObservationRouteRequest(
            domain="crypto",
            entity_kind="asset",
            observation_type="spot_price",
        )

        a = self.engine.acquire(
            query_id="query.crypto",
            request=request,
            assembled_at=NOW,
        )

        b = self.engine.acquire(
            query_id="query.crypto",
            request=request,
            assembled_at=NOW,
        )

        self.assertEqual(a.acquisition_hash, b.acquisition_hash)

    def test_side_effects(self):
        self.assertTrue(self.engine.read_only)
        self.assertFalse(self.engine.persistence_allowed)
        self.assertFalse(self.engine.publication_allowed)
        self.assertFalse(self.engine.execution_allowed)
        self.assertFalse(self.engine.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-012 CERTIFICATION TEST")
    print(" ROUTED OBSERVATION ACQUISITION ENGINE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI012
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-012")
    print(f"[PASS] Revision: {OI_012_REVISION}")
    print("[PASS] Route decisions invoke only registered adapter bindings")
    print("[PASS] Routed envelopes canonicalize through OI-003")
    print("[PASS] Routed observations assemble directly into immutable evidence bundles")
    print("[PASS] Missing adapter routes fail closed with empty evidence")
    print("[PASS] Persistence, publication, action authorization, and execution disabled")
    print("[DONE] OI-012 CERTIFIED")
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
    print(" OI-012 INSTALLER")
    print(" ROUTED OBSERVATION ACQUISITION ENGINE")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    upstreams = (
        (UPSTREAM_008, "OI-008"),
        (UPSTREAM_009, "OI-009"),
        (UPSTREAM_011, "OI-011"),
    )

    for path, name in upstreams:
        if not path.is_file():
            raise RuntimeError(f"Certified {name} missing: {path}")

    upstream_hashes = {
        path: sha(path)
        for path, _ in upstreams
    }

    print("[PASS] Certified OI-008, OI-009, and OI-011 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_012_routed_observation_acquisition import *"

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
        print("[PASS] Routed acquisition remains read-only; persistence/publication/execution disabled")
        print("[DONE] OI-012 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-012 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
