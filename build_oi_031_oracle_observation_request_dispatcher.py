from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-031"
INSTALLER_REVISION = "OI_031_ORACLE_OBSERVATION_REQUEST_DISPATCHER_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_012_routed_observation_acquisition.py", "OI-012"),
    (PACKAGE / "oi_029_observation_acquisition_plan.py", "OI-029"),
    (PACKAGE / "oi_030_oracle_observation_request_package.py", "OI-030"),
)

MODULE = PACKAGE / "oi_031_oracle_observation_request_dispatcher.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_031_oracle_observation_request_dispatcher.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_008_observation_source_routing import ObservationRouteRequest
from .oi_012_routed_observation_acquisition import (
    RoutedObservationAcquisitionEngine,
    RoutedObservationAcquisitionResult,
)
from .oi_029_observation_acquisition_plan import ObservationAcquisitionPlan
from .oi_030_oracle_observation_request_package import (
    OracleObservationRequestPackage,
)

BUILD_ID = "OI-031"
OI_031_REVISION = "OI_031_ORACLE_OBSERVATION_REQUEST_DISPATCHER_V1"

READ_ONLY = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class OracleObservationRequestDispatcherError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DispatchedObservationNeed:
    ordinal: int
    need_id: str
    covered: bool
    adapter_ids: tuple[str, ...]
    acquisition_hash: str | None
    observation_count: int
    evidence_hash: str | None
    dispatch_item_hash: str


@dataclass(frozen=True, slots=True)
class OracleObservationDispatchResult:
    request_id: str
    request_package_hash: str
    plan_hash: str
    dispatched_at: datetime
    items: tuple[DispatchedObservationNeed, ...]
    covered_need_count: int
    missing_need_count: int
    acquired_observation_count: int
    dispatch_hash: str
    read_only: bool


class OracleObservationRequestDispatcher:
    read_only = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def __init__(
        self,
        acquisition_engine: RoutedObservationAcquisitionEngine,
    ) -> None:
        if not isinstance(
            acquisition_engine,
            RoutedObservationAcquisitionEngine,
        ):
            raise TypeError(
                "acquisition_engine must be RoutedObservationAcquisitionEngine"
            )

        self._acquisition_engine = acquisition_engine

    def dispatch(
        self,
        *,
        request_package: OracleObservationRequestPackage,
        acquisition_plan: ObservationAcquisitionPlan,
        dispatched_at: datetime,
    ) -> OracleObservationDispatchResult:
        if not isinstance(
            request_package,
            OracleObservationRequestPackage,
        ):
            raise TypeError(
                "request_package must be OracleObservationRequestPackage"
            )

        if not isinstance(
            acquisition_plan,
            ObservationAcquisitionPlan,
        ):
            raise TypeError(
                "acquisition_plan must be ObservationAcquisitionPlan"
            )

        if (
            request_package.acquisition_plan_hash
            != acquisition_plan.plan_hash
        ):
            raise OracleObservationRequestDispatcherError(
                "request package and acquisition plan hash mismatch"
            )

        if not isinstance(dispatched_at, datetime):
            raise TypeError("dispatched_at must be datetime")

        if dispatched_at.tzinfo is None:
            raise OracleObservationRequestDispatcherError(
                "dispatched_at must be timezone-aware"
            )

        dispatched_at = dispatched_at.astimezone(
            timezone.utc
        )

        items = []

        for plan_item in acquisition_plan.items:
            if not plan_item.covered:
                body = {
                    "ordinal": plan_item.ordinal,
                    "need_id": plan_item.need_id,
                    "covered": False,
                    "adapter_ids": (),
                    "acquisition_hash": None,
                    "observation_count": 0,
                    "evidence_hash": None,
                }

                items.append(
                    DispatchedObservationNeed(
                        ordinal=plan_item.ordinal,
                        need_id=plan_item.need_id,
                        covered=False,
                        adapter_ids=(),
                        acquisition_hash=None,
                        observation_count=0,
                        evidence_hash=None,
                        dispatch_item_hash=deterministic_sha256(body),
                    )
                )
                continue

            acquisition = self._acquisition_engine.acquire(
                query_id=(
                    f"{request_package.query_id}."
                    f"need.{plan_item.ordinal}"
                ),
                request=ObservationRouteRequest(
                    domain=plan_item.domain,
                    entity_kind=plan_item.entity_kind,
                    observation_type=plan_item.observation_type,
                ),
                assembled_at=dispatched_at,
            )

            if tuple(acquisition.invoked_adapter_ids) != tuple(
                plan_item.adapter_ids
            ):
                raise OracleObservationRequestDispatcherError(
                    "acquisition invoked adapters differ from certified plan"
                )

            body = {
                "ordinal": plan_item.ordinal,
                "need_id": plan_item.need_id,
                "covered": True,
                "adapter_ids": acquisition.invoked_adapter_ids,
                "acquisition_hash": acquisition.acquisition_hash,
                "observation_count": len(acquisition.observations),
                "evidence_hash": acquisition.evidence_bundle.evidence_hash,
            }

            items.append(
                DispatchedObservationNeed(
                    ordinal=plan_item.ordinal,
                    need_id=plan_item.need_id,
                    covered=True,
                    adapter_ids=tuple(acquisition.invoked_adapter_ids),
                    acquisition_hash=acquisition.acquisition_hash,
                    observation_count=len(acquisition.observations),
                    evidence_hash=acquisition.evidence_bundle.evidence_hash,
                    dispatch_item_hash=deterministic_sha256(body),
                )
            )

        covered_need_count = sum(
            1
            for item in items
            if item.covered
        )

        missing_need_count = len(items) - covered_need_count

        acquired_observation_count = sum(
            item.observation_count
            for item in items
        )

        body = {
            "request_id": request_package.request_id,
            "request_package_hash": request_package.package_hash,
            "plan_hash": acquisition_plan.plan_hash,
            "dispatched_at": dispatched_at,
            "item_hashes": tuple(
                item.dispatch_item_hash
                for item in items
            ),
            "covered_need_count": covered_need_count,
            "missing_need_count": missing_need_count,
            "acquired_observation_count": acquired_observation_count,
            "read_only": True,
        }

        return OracleObservationDispatchResult(
            request_id=request_package.request_id,
            request_package_hash=request_package.package_hash,
            plan_hash=acquisition_plan.plan_hash,
            dispatched_at=dispatched_at,
            items=tuple(items),
            covered_need_count=covered_need_count,
            missing_need_count=missing_need_count,
            acquired_observation_count=acquired_observation_count,
            dispatch_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_oracle_observation_request_dispatcher() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-031 must remain read-only"
        )

    if any(
        (
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
            "OI-031 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_031_REVISION",
    "OracleObservationRequestDispatcherError",
    "DispatchedObservationNeed",
    "OracleObservationDispatchResult",
    "OracleObservationRequestDispatcher",
    "verify_oracle_observation_request_dispatcher",
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
from qseries_v2.observation_intelligence.oi_029_observation_acquisition_plan import (
    ObservationAcquisitionPlan,
    ObservationAcquisitionPlanItem,
)
from qseries_v2.observation_intelligence.oi_030_oracle_observation_request_package import (
    OracleObservationRequestPackage,
)
from qseries_v2.observation_intelligence.oi_031_oracle_observation_request_dispatcher import (
    OI_031_REVISION,
    OracleObservationRequestDispatcher,
    verify_oracle_observation_request_dispatcher,
)

NOW = datetime(2026, 8, 10, 20, 0, tzinfo=timezone.utc)


def kalshi_acquire(request):
    return (
        RawObservationEnvelope(
            source=ObservationSourceIdentity(
                source_id="kalshi.public",
                source_kind="market_venue",
                provider="Kalshi",
                adapter_id="adapter.kalshi.v1",
            ),
            external_observation_id="KX-ASTROS-OI031",
            observed_at=NOW,
            subject="Astros strikeouts",
            observation_type="market_snapshot",
            payload={
                "ticker": "KXASTROS",
                "yes_bid": 54,
                "yes_ask": 56,
            },
            metadata={
                "venue": "kalshi",
                "market_ticker": "KXASTROS",
            },
        ),
    )


def engine():
    registry = default_source_registry()

    return RoutedObservationAcquisitionEngine(
        adapter_registry=registry,
        routing_registry=ObservationSourceRoutingRegistry(
            registry,
            default_observation_route_rules(),
        ),
        bindings=(
            AdapterAcquisitionBinding(
                adapter_id="adapter.coinbase.spot.v1",
                acquire_callable=lambda request: (),
            ),
            AdapterAcquisitionBinding(
                adapter_id="adapter.kalshi.v1",
                acquire_callable=kalshi_acquire,
            ),
        ),
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


def request_package():
    return OracleObservationRequestPackage(
        request_id="request.astros",
        query_id="query.astros",
        query_kind="explanation",
        subject_hint="Astros strikeouts",
        profile_id="profile.market_explanation",
        acquisition_plan_hash="c" * 64,
        requested_adapter_ids=("adapter.kalshi.v1",),
        missing_need_ids=("profile.market_explanation.need.2",),
        complete_adapter_coverage=False,
        assembled_at=NOW,
        package_hash="d" * 64,
        read_only=True,
        predictive=False,
        terminal_mutation_allowed=False,
    )


class TestOI031(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_observation_request_dispatcher()
        )

    def test_dispatch(self):
        result = OracleObservationRequestDispatcher(
            engine()
        ).dispatch(
            request_package=request_package(),
            acquisition_plan=plan(),
            dispatched_at=NOW,
        )

        self.assertEqual(result.covered_need_count, 1)
        self.assertEqual(result.missing_need_count, 1)
        self.assertEqual(result.acquired_observation_count, 1)

    def test_missing_need_not_invoked(self):
        result = OracleObservationRequestDispatcher(
            engine()
        ).dispatch(
            request_package=request_package(),
            acquisition_plan=plan(),
            dispatched_at=NOW,
        )

        self.assertFalse(result.items[1].covered)
        self.assertIsNone(result.items[1].acquisition_hash)

    def test_adapter_identity_preserved(self):
        result = OracleObservationRequestDispatcher(
            engine()
        ).dispatch(
            request_package=request_package(),
            acquisition_plan=plan(),
            dispatched_at=NOW,
        )

        self.assertEqual(
            result.items[0].adapter_ids,
            ("adapter.kalshi.v1",),
        )

    def test_deterministic(self):
        dispatcher = OracleObservationRequestDispatcher(
            engine()
        )

        a = dispatcher.dispatch(
            request_package=request_package(),
            acquisition_plan=plan(),
            dispatched_at=NOW,
        )

        b = dispatcher.dispatch(
            request_package=request_package(),
            acquisition_plan=plan(),
            dispatched_at=NOW,
        )

        self.assertEqual(a.dispatch_hash, b.dispatch_hash)

    def test_side_effects(self):
        dispatcher = OracleObservationRequestDispatcher(
            engine()
        )

        self.assertTrue(dispatcher.read_only)
        self.assertFalse(dispatcher.persistence_allowed)
        self.assertFalse(dispatcher.publication_allowed)
        self.assertFalse(dispatcher.execution_allowed)
        self.assertFalse(dispatcher.qseries_execution_allowed)
        self.assertFalse(dispatcher.prediction_allowed)
        self.assertFalse(dispatcher.edge_score_allowed)
        self.assertFalse(dispatcher.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-031 CERTIFICATION TEST")
    print(" ORACLE OBSERVATION REQUEST DISPATCHER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI031
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-031")
    print(f"[PASS] Revision: {OI_031_REVISION}")
    print("[PASS] Certified observation request plans dispatch only through approved routed acquisition")
    print("[PASS] Missing capabilities are not invoked and remain explicit")
    print("[PASS] Adapter identity, evidence hash, and observation counts preserved")
    print("[PASS] Persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-031 CERTIFIED")
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
    print(" OI-031 INSTALLER")
    print(" ORACLE OBSERVATION REQUEST DISPATCHER")
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
        "[PASS] Certified OI-012, OI-029, "
        "and OI-030 verified read-only"
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
            "from .oi_031_oracle_observation_request_dispatcher import *"
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
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[PASS] Dispatch remains deterministic, read-only, "
            "and constrained to certified acquisition routes"
        )
        print("[DONE] OI-031 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-031 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
