from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-009"
INSTALLER_REVISION = "OI_009_OBSERVATION_EVIDENCE_ASSEMBLY_FOUNDATION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_007 = PACKAGE / "oi_007_observation_history.py"
UPSTREAM_008 = PACKAGE / "oi_008_observation_source_routing.py"
MODULE = PACKAGE / "oi_009_observation_evidence_assembly.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_009_observation_evidence_assembly.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_007_observation_history import UniversalObservationHistory, verify_observation_history
from .oi_008_observation_source_routing import (
    ObservationRouteDecision,
    verify_observation_source_routing,
)

BUILD_ID = "OI-009"
OI_009_REVISION = "OI_009_OBSERVATION_EVIDENCE_ASSEMBLY_FOUNDATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class ObservationEvidenceAssemblyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceObservationRef:
    canonical_observation_id: str
    canonical_observation_hash: str
    source_id: str
    provider: str
    adapter_id: str
    observed_at: datetime
    subject: str
    observation_type: str
    facts: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "facts",
            MappingProxyType(dict(self.facts)),
        )


@dataclass(frozen=True, slots=True)
class ObservationEvidenceBundle:
    query_id: str
    assembled_at: datetime
    route_decision_hash: str
    adapter_ids: tuple[str, ...]
    observations: tuple[EvidenceObservationRef, ...]
    evidence_hash: str
    read_only: bool
    predictive: bool


class ObservationEvidenceAssembler:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def assemble(
        self,
        *,
        query_id: str,
        route_decision: ObservationRouteDecision,
        observations: tuple[CanonicalLiveObservation, ...],
        assembled_at: datetime,
    ) -> ObservationEvidenceBundle:
        if not isinstance(route_decision, ObservationRouteDecision):
            raise TypeError(
                "route_decision must be ObservationRouteDecision"
            )

        query_id = str(query_id).strip()
        if not query_id:
            raise ObservationEvidenceAssemblyError(
                "query_id must not be empty"
            )

        if not isinstance(assembled_at, datetime):
            raise TypeError("assembled_at must be datetime")

        if assembled_at.tzinfo is None:
            raise ObservationEvidenceAssemblyError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(timezone.utc)

        values = tuple(observations)

        if any(
            not isinstance(item, CanonicalLiveObservation)
            for item in values
        ):
            raise TypeError(
                "all observations must be CanonicalLiveObservation"
            )

        ordered = tuple(
            sorted(
                values,
                key=lambda item: (
                    item.observed_at,
                    item.canonical_observation_id,
                ),
            )
        )

        if values != ordered:
            raise ObservationEvidenceAssemblyError(
                "observations must be deterministically sorted"
            )

        allowed_adapters = set(route_decision.adapter_ids)

        if any(
            item.adapter_id not in allowed_adapters
            for item in values
        ):
            raise ObservationEvidenceAssemblyError(
                "observation adapter not authorized by route decision"
            )

        refs = tuple(
            EvidenceObservationRef(
                canonical_observation_id=item.canonical_observation_id,
                canonical_observation_hash=item.canonical_observation_hash,
                source_id=item.source_id,
                provider=item.provider,
                adapter_id=item.adapter_id,
                observed_at=item.observed_at,
                subject=item.subject,
                observation_type=item.observation_type,
                facts=dict(item.facts),
            )
            for item in values
        )

        body = {
            "query_id": query_id,
            "assembled_at": assembled_at,
            "route_decision_hash": route_decision.decision_hash,
            "adapter_ids": route_decision.adapter_ids,
            "observation_hashes": tuple(
                ref.canonical_observation_hash
                for ref in refs
            ),
            "read_only": True,
            "predictive": False,
        }

        return ObservationEvidenceBundle(
            query_id=query_id,
            assembled_at=assembled_at,
            route_decision_hash=route_decision.decision_hash,
            adapter_ids=route_decision.adapter_ids,
            observations=refs,
            evidence_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
        )


def verify_observation_evidence_assembly() -> bool:
    verify_observation_history()
    verify_observation_source_routing()

    if READ_ONLY is not True:
        raise AssertionError("OI-009 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-009 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_009_REVISION",
    "ObservationEvidenceAssemblyError",
    "EvidenceObservationRef",
    "ObservationEvidenceBundle",
    "ObservationEvidenceAssembler",
    "verify_observation_evidence_assembly",
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
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_008_observation_source_routing import (
    ObservationRouteRequest,
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
)
from qseries_v2.observation_intelligence.oi_009_observation_evidence_assembly import (
    OI_009_REVISION,
    ObservationEvidenceAssembler,
    verify_observation_evidence_assembly,
)


NOW = datetime(2026, 8, 10, 5, 0, tzinfo=timezone.utc)


def btc_observation():
    source = ObservationSourceIdentity(
        source_id="coinbase.public.spot",
        source_kind="market_data",
        provider="Coinbase",
        adapter_id="adapter.coinbase.spot.v1",
    )

    envelope = RawObservationEnvelope(
        source=source,
        external_observation_id="BTC-USD-EVIDENCE",
        observed_at=NOW,
        subject="BTC",
        observation_type="spot_price",
        payload={
            "product_id": "BTC-USD",
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": "100.00",
        },
        metadata={"venue": "coinbase"},
    )

    return CanonicalLiveObservationGateway(
        default_source_registry()
    ).canonicalize(envelope).canonical_observation


class TestOI009(unittest.TestCase):
    def setUp(self):
        router = ObservationSourceRoutingRegistry(
            default_source_registry(),
            default_observation_route_rules(),
        )

        self.decision = router.route(
            ObservationRouteRequest(
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
            )
        )

        self.observation = btc_observation()

    def test_foundation(self):
        self.assertTrue(
            verify_observation_evidence_assembly()
        )

    def test_assembly(self):
        bundle = ObservationEvidenceAssembler().assemble(
            query_id="query.btc.price",
            route_decision=self.decision,
            observations=(self.observation,),
            assembled_at=NOW,
        )

        self.assertEqual(len(bundle.observations), 1)
        self.assertEqual(
            bundle.observations[0].adapter_id,
            "adapter.coinbase.spot.v1",
        )

    def test_hash_deterministic(self):
        assembler = ObservationEvidenceAssembler()

        a = assembler.assemble(
            query_id="query.btc.price",
            route_decision=self.decision,
            observations=(self.observation,),
            assembled_at=NOW,
        )

        b = assembler.assemble(
            query_id="query.btc.price",
            route_decision=self.decision,
            observations=(self.observation,),
            assembled_at=NOW,
        )

        self.assertEqual(a.evidence_hash, b.evidence_hash)

    def test_predictive_false(self):
        bundle = ObservationEvidenceAssembler().assemble(
            query_id="query.btc.price",
            route_decision=self.decision,
            observations=(self.observation,),
            assembled_at=NOW,
        )

        self.assertFalse(bundle.predictive)
        self.assertTrue(bundle.read_only)

    def test_wrong_adapter_rejected(self):
        router = ObservationSourceRoutingRegistry(
            default_source_registry(),
            default_observation_route_rules(),
        )

        decision = router.route(
            ObservationRouteRequest(
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
            )
        )

        with self.assertRaises(ValueError):
            ObservationEvidenceAssembler().assemble(
                query_id="bad",
                route_decision=decision,
                observations=(self.observation,),
                assembled_at=NOW,
            )

    def test_side_effects(self):
        assembler = ObservationEvidenceAssembler()
        self.assertTrue(assembler.read_only)
        self.assertFalse(assembler.network_allowed)
        self.assertFalse(assembler.persistence_allowed)
        self.assertFalse(assembler.publication_allowed)
        self.assertFalse(assembler.execution_allowed)
        self.assertFalse(assembler.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-009 CERTIFICATION TEST")
    print(" OBSERVATION EVIDENCE ASSEMBLY FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI009
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-009")
    print(f"[PASS] Revision: {OI_009_REVISION}")
    print("[PASS] Routed canonical observations assemble into immutable evidence bundles")
    print("[PASS] Source, provider, adapter, time, facts, and lineage preserved")
    print("[PASS] Unauthorized adapter evidence rejected")
    print("[PASS] Evidence assembly remains non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-009 CERTIFIED")
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
    print(" OI-009 INSTALLER")
    print(" OBSERVATION EVIDENCE ASSEMBLY FOUNDATION")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for path, name in (
        (UPSTREAM_007, "OI-007"),
        (UPSTREAM_008, "OI-008"),
    ):
        if not path.is_file():
            raise RuntimeError(f"Certified {name} missing: {path}")

    upstream_hashes = {
        path: sha(path)
        for path in (UPSTREAM_007, UPSTREAM_008)
    }

    print("[PASS] Certified OI-007 and OI-008 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_009_observation_evidence_assembly import *"

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
        print("[PASS] Evidence foundation remains deterministic, read-only, and non-predictive")
        print("[DONE] OI-009 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-009 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
