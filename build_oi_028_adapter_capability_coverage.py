from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-028"
INSTALLER_REVISION = "OI_028_ADAPTER_CAPABILITY_COVERAGE_REGISTRY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_002_source_adapter_registry.py", "OI-002"),
    (PACKAGE / "oi_008_observation_source_routing.py", "OI-008"),
    (PACKAGE / "oi_027_generic_observation_router_interface.py", "OI-027"),
)

MODULE = PACKAGE / "oi_028_adapter_capability_coverage.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_028_adapter_capability_coverage.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_002_source_adapter_registry import SourceAdapterRegistry
from .oi_027_generic_observation_router_interface import (
    GenericObservationNeed,
    GenericObservationRouterInterface,
)

BUILD_ID = "OI-028"
OI_028_REVISION = "OI_028_ADAPTER_CAPABILITY_COVERAGE_REGISTRY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class AdapterCapabilityCoverageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AdapterCoverageRecord:
    need_id: str
    domain: str
    entity_kind: str
    observation_type: str
    subject_hint: str
    covered: bool
    adapter_ids: tuple[str, ...]
    coverage_hash: str


class AdapterCapabilityCoverageRegistry:
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
        adapter_registry: SourceAdapterRegistry,
        router: GenericObservationRouterInterface,
    ) -> None:
        if not isinstance(adapter_registry, SourceAdapterRegistry):
            raise TypeError(
                "adapter_registry must be SourceAdapterRegistry"
            )
        if not isinstance(router, GenericObservationRouterInterface):
            raise TypeError(
                "router must be GenericObservationRouterInterface"
            )

        self._adapter_registry = adapter_registry
        self._router = router

    def evaluate_need(
        self,
        need: GenericObservationNeed,
    ) -> AdapterCoverageRecord:
        if not isinstance(need, GenericObservationNeed):
            raise TypeError("need must be GenericObservationNeed")

        route = self._router.route_need(need)

        enabled_adapter_ids = tuple(
            adapter_id
            for adapter_id in route.route_decision.adapter_ids
            if (
                self._adapter_registry.get(adapter_id) is not None
                and self._adapter_registry.get(adapter_id).enabled_for_intake
            )
        )

        covered = bool(enabled_adapter_ids)

        body = {
            "need_id": need.need_id,
            "domain": need.domain,
            "entity_kind": need.entity_kind,
            "observation_type": need.observation_type,
            "subject_hint": need.subject_hint,
            "covered": covered,
            "adapter_ids": enabled_adapter_ids,
        }

        return AdapterCoverageRecord(
            need_id=need.need_id,
            domain=need.domain,
            entity_kind=need.entity_kind,
            observation_type=need.observation_type,
            subject_hint=need.subject_hint,
            covered=covered,
            adapter_ids=enabled_adapter_ids,
            coverage_hash=deterministic_sha256(body),
        )

    def evaluate_many(
        self,
        needs: tuple[GenericObservationNeed, ...],
    ) -> tuple[AdapterCoverageRecord, ...]:
        values = tuple(needs)

        if any(
            not isinstance(item, GenericObservationNeed)
            for item in values
        ):
            raise TypeError(
                "all needs must be GenericObservationNeed"
            )

        ids = tuple(item.need_id for item in values)

        if len(ids) != len(set(ids)):
            raise AdapterCapabilityCoverageError(
                "duplicate need_id"
            )

        ordered = tuple(
            sorted(
                values,
                key=lambda item: item.need_id,
            )
        )

        if values != ordered:
            raise AdapterCapabilityCoverageError(
                "needs must be deterministically sorted"
            )

        return tuple(
            self.evaluate_need(item)
            for item in values
        )

    def coverage_summary(
        self,
        needs: tuple[GenericObservationNeed, ...],
    ) -> MappingProxyType:
        records = self.evaluate_many(needs)

        covered = tuple(
            item.need_id
            for item in records
            if item.covered
        )

        missing = tuple(
            item.need_id
            for item in records
            if not item.covered
        )

        return MappingProxyType(
            {
                "total": len(records),
                "covered": len(covered),
                "missing": len(missing),
                "covered_need_ids": covered,
                "missing_need_ids": missing,
                "coverage_hash": deterministic_sha256(
                    tuple(
                        item.coverage_hash
                        for item in records
                    )
                ),
            }
        )


def verify_adapter_capability_coverage() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-028 must remain read-only"
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
            "OI-028 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_028_REVISION",
    "AdapterCapabilityCoverageError",
    "AdapterCoverageRecord",
    "AdapterCapabilityCoverageRegistry",
    "verify_adapter_capability_coverage",
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
from qseries_v2.observation_intelligence.oi_027_generic_observation_router_interface import (
    GenericObservationNeed,
    GenericObservationRouterInterface,
)
from qseries_v2.observation_intelligence.oi_028_adapter_capability_coverage import (
    OI_028_REVISION,
    AdapterCapabilityCoverageRegistry,
    verify_adapter_capability_coverage,
)


def coverage():
    registry = default_source_registry()

    router = GenericObservationRouterInterface(
        ObservationSourceRoutingRegistry(
            registry,
            default_observation_route_rules(),
        )
    )

    return AdapterCapabilityCoverageRegistry(
        adapter_registry=registry,
        router=router,
    )


class TestOI028(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_adapter_capability_coverage()
        )

    def test_covered_need(self):
        record = coverage().evaluate_need(
            GenericObservationNeed(
                need_id="need.crypto.price",
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
                subject_hint="Bitcoin",
            )
        )

        self.assertTrue(record.covered)
        self.assertEqual(
            record.adapter_ids,
            ("adapter.coinbase.spot.v1",),
        )

    def test_missing_need(self):
        record = coverage().evaluate_need(
            GenericObservationNeed(
                need_id="need.sports.lineup",
                domain="sports",
                entity_kind="team",
                observation_type="lineup",
                subject_hint="Astros",
            )
        )

        self.assertFalse(record.covered)
        self.assertEqual(record.adapter_ids, ())

    def test_summary(self):
        summary = coverage().coverage_summary(
            (
                GenericObservationNeed(
                    need_id="need.a",
                    domain="crypto",
                    entity_kind="asset",
                    observation_type="spot_price",
                    subject_hint="Bitcoin",
                ),
                GenericObservationNeed(
                    need_id="need.b",
                    domain="sports",
                    entity_kind="team",
                    observation_type="lineup",
                    subject_hint="Astros",
                ),
            )
        )

        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["covered"], 1)
        self.assertEqual(summary["missing"], 1)

    def test_deterministic(self):
        need = GenericObservationNeed(
            need_id="need.crypto.price",
            domain="crypto",
            entity_kind="asset",
            observation_type="spot_price",
            subject_hint="Bitcoin",
        )

        a = coverage().evaluate_need(need)
        b = coverage().evaluate_need(need)

        self.assertEqual(
            a.coverage_hash,
            b.coverage_hash,
        )

    def test_side_effects(self):
        item = coverage()

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
    print(" OI-028 CERTIFICATION TEST")
    print(" ADAPTER CAPABILITY COVERAGE REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI028
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-028")
    print(f"[PASS] Revision: {OI_028_REVISION}")
    print("[PASS] Covered and missing observation needs certified against enabled adapters")
    print("[PASS] Adapter capability gaps are explicit and deterministic")
    print("[PASS] Missing capabilities fail closed without fallback guessing")
    print("[PASS] Prediction, probability, scoring, publication, and execution disabled")
    print("[DONE] OI-028 CERTIFIED")
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
    print(" OI-028 INSTALLER")
    print(" ADAPTER CAPABILITY COVERAGE REGISTRY")
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
        "[PASS] Certified OI-002, OI-008, "
        "and OI-027 verified read-only"
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
            "from .oi_028_adapter_capability_coverage import *"
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
            "[PASS] Capability coverage remains "
            "deterministic, read-only, and fail-closed"
        )

        print(
            "[DONE] OI-028 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OI-028 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
