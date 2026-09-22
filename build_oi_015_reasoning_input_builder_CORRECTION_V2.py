from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-015"
INSTALLER_REVISION = "OI_015_REASONING_INPUT_BUILDER_INSTALLER_CORRECTION_V2"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAM_009 = PACKAGE / "oi_009_observation_evidence_assembly.py"
UPSTREAM_014 = PACKAGE / "oi_014_routed_evidence_orchestrator.py"

MODULE = PACKAGE / "oi_015_reasoning_input_builder.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_015_reasoning_input_builder.py"


MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_014_routed_evidence_orchestrator import (
    RoutedEvidenceOrchestration,
)

BUILD_ID = "OI-015"
OI_015_REVISION = "OI_015_REASONING_INPUT_BUILDER_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False


class ReasoningInputBuilderError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceItem:
    canonical_observation_id: str
    canonical_observation_hash: str
    provider: str
    adapter_id: str
    observed_at: datetime
    freshness_status: str
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
class OracleReasoningInput:
    query_id: str
    profile_id: str
    built_at: datetime
    evidence_items: tuple[ReasoningEvidenceItem, ...]
    required_evidence_count: int
    satisfied_evidence_count: int
    missing_evidence_count: int
    complete_required_evidence: bool
    input_hash: str
    predictive: bool
    read_only: bool


class OracleReasoningInputBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False

    def build(
        self,
        orchestration: RoutedEvidenceOrchestration,
        *,
        built_at: datetime,
    ) -> OracleReasoningInput:
        if not isinstance(
            orchestration,
            RoutedEvidenceOrchestration,
        ):
            raise TypeError(
                "orchestration must be RoutedEvidenceOrchestration"
            )

        if not isinstance(built_at, datetime):
            raise TypeError("built_at must be datetime")

        if built_at.tzinfo is None:
            raise ReasoningInputBuilderError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(timezone.utc)

        evidence_items = []

        for requirement in orchestration.results:
            health_by_id = {
                item.canonical_observation_id: item
                for item in requirement.health
            }

            for observation in requirement.acquisition.observations:
                health = health_by_id.get(
                    observation.canonical_observation_id
                )

                if health is None:
                    raise ReasoningInputBuilderError(
                        "observation missing freshness health"
                    )

                evidence_items.append(
                    ReasoningEvidenceItem(
                        canonical_observation_id=(
                            observation.canonical_observation_id
                        ),
                        canonical_observation_hash=(
                            observation.canonical_observation_hash
                        ),
                        provider=observation.provider,
                        adapter_id=observation.adapter_id,
                        observed_at=observation.observed_at,
                        freshness_status=health.freshness_status,
                        subject=observation.subject,
                        observation_type=observation.observation_type,
                        facts=dict(observation.facts),
                    )
                )

        ordered = tuple(
            sorted(
                evidence_items,
                key=lambda item: (
                    item.observed_at,
                    item.canonical_observation_id,
                ),
            )
        )

        complete = orchestration.missing_count == 0

        body = {
            "query_id": orchestration.query_id,
            "profile_id": orchestration.profile_id,
            "built_at": built_at,
            "evidence_hashes": tuple(
                item.canonical_observation_hash
                for item in ordered
            ),
            "freshness": tuple(
                item.freshness_status
                for item in ordered
            ),
            "required_evidence_count": orchestration.required_count,
            "satisfied_evidence_count": orchestration.satisfied_count,
            "missing_evidence_count": orchestration.missing_count,
            "complete_required_evidence": complete,
            "predictive": False,
            "read_only": True,
        }

        return OracleReasoningInput(
            query_id=orchestration.query_id,
            profile_id=orchestration.profile_id,
            built_at=built_at,
            evidence_items=ordered,
            required_evidence_count=orchestration.required_count,
            satisfied_evidence_count=orchestration.satisfied_count,
            missing_evidence_count=orchestration.missing_count,
            complete_required_evidence=complete,
            input_hash=deterministic_sha256(body),
            predictive=False,
            read_only=True,
        )


def verify_reasoning_input_builder() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-015 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            PREDICTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-015 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_015_REVISION",
    "ReasoningInputBuilderError",
    "ReasoningEvidenceItem",
    "OracleReasoningInput",
    "OracleReasoningInputBuilder",
    "verify_reasoning_input_builder",
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
    RoutedEvidenceOrchestrator,
)
from qseries_v2.observation_intelligence.oi_015_reasoning_input_builder import (
    OI_015_REVISION,
    OracleReasoningInputBuilder,
    verify_reasoning_input_builder,
)

NOW = datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc)


def acquire(request):
    return (
        RawObservationEnvelope(
            source=ObservationSourceIdentity(
                source_id="coinbase.public.spot",
                source_kind="market_data",
                provider="Coinbase",
                adapter_id="adapter.coinbase.spot.v1",
            ),
            external_observation_id="BTC-USD-OI015",
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


def orchestration():
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

    resolver = ObservationRequirementResolver(
        (profile,)
    )

    registry = default_source_registry()

    router = ObservationSourceRoutingRegistry(
        registry,
        default_observation_route_rules(),
    )

    acquisition_engine = RoutedObservationAcquisitionEngine(
        adapter_registry=registry,
        routing_registry=router,
        bindings=(
            AdapterAcquisitionBinding(
                adapter_id="adapter.coinbase.spot.v1",
                acquire_callable=acquire,
            ),
            AdapterAcquisitionBinding(
                adapter_id="adapter.kalshi.v1",
                acquire_callable=lambda request: (),
            ),
        ),
    )

    return RoutedEvidenceOrchestrator(
        requirement_resolver=resolver,
        acquisition_engine=acquisition_engine,
    ).orchestrate(
        profile_id="profile.asset_state",
        query_id="query.asset.reasoning",
        evaluated_at=NOW,
    )


class TestOI015(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_input_builder()
        )

    def test_build(self):
        value = OracleReasoningInputBuilder().build(
            orchestration(),
            built_at=NOW,
        )

        self.assertEqual(
            len(value.evidence_items),
            1,
        )

        self.assertTrue(
            value.complete_required_evidence
        )

        self.assertEqual(
            value.missing_evidence_count,
            0,
        )

    def test_non_predictive(self):
        value = OracleReasoningInputBuilder().build(
            orchestration(),
            built_at=NOW,
        )

        self.assertFalse(
            value.predictive
        )

        self.assertTrue(
            value.read_only
        )

    def test_lineage(self):
        value = OracleReasoningInputBuilder().build(
            orchestration(),
            built_at=NOW,
        )

        item = value.evidence_items[0]

        self.assertEqual(
            item.adapter_id,
            "adapter.coinbase.spot.v1",
        )

        self.assertEqual(
            item.freshness_status,
            "fresh",
        )

    def test_deterministic(self):
        builder = OracleReasoningInputBuilder()

        a = builder.build(
            orchestration(),
            built_at=NOW,
        )

        b = builder.build(
            orchestration(),
            built_at=NOW,
        )

        self.assertEqual(
            a.input_hash,
            b.input_hash,
        )

    def test_side_effects(self):
        builder = OracleReasoningInputBuilder()

        self.assertTrue(
            builder.read_only
        )

        self.assertFalse(
            builder.network_allowed
        )

        self.assertFalse(
            builder.persistence_allowed
        )

        self.assertFalse(
            builder.publication_allowed
        )

        self.assertFalse(
            builder.execution_allowed
        )

        self.assertFalse(
            builder.qseries_execution_allowed
        )

        self.assertFalse(
            builder.prediction_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-015 CERTIFICATION TEST")
    print(" ORACLE REASONING INPUT BUILDER — CORRECTION V2")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI015
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-015")
    print(f"[PASS] Revision: {OI_015_REVISION}")
    print("[PASS] Routed evidence converts to deterministic Oracle reasoning input")
    print("[PASS] Source lineage, freshness, facts, and missing-evidence state preserved")
    print("[PASS] Reasoning input remains evidence-only and non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-015 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def write_checked(
    path: Path,
    source: str,
) -> None:
    text = source.lstrip()

    ast.parse(
        text,
        filename=str(path),
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[PASS] Wrote: "
        f"{path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OI-015 INSTALLER")
    print(" ORACLE REASONING INPUT BUILDER — CORRECTION V2")
    print("=" * 72)

    print(
        f"[BOOT] Revision: "
        f"{INSTALLER_REVISION}"
    )

    print(
        f"[ROOT] {ROOT}"
    )

    upstreams = (
        (UPSTREAM_009, "OI-009"),
        (UPSTREAM_014, "OI-014"),
    )

    for upstream, name in upstreams:
        if not upstream.is_file():
            raise RuntimeError(
                f"Certified {name} missing: {upstream}"
            )

    upstream_hashes = {
        upstream: sha(upstream)
        for upstream, _ in upstreams
    }

    print(
        "[PASS] Certified OI-009 and OI-014 "
        "verified read-only"
    )

    affected = (
        MODULE,
        TEST,
        INIT,
    )

    backups = {
        item: (
            item.read_bytes()
            if item.exists()
            else None
        )
        for item in affected
    }

    try:
        write_checked(
            MODULE,
            MODULE_SOURCE,
        )

        write_checked(
            TEST,
            TEST_SOURCE,
        )

        current = (
            INIT.read_text(
                encoding="utf-8"
            )
            if INIT.exists()
            else ""
        )

        export = (
            "from .oi_015_reasoning_input_builder import *"
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
            MODULE.read_text(
                encoding="utf-8"
            ),
            str(MODULE),
            "exec",
        )

        compile(
            TEST.read_text(
                encoding="utf-8"
            ),
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
            "[PASS] Reasoning input remains evidence-only, "
            "read-only, and non-predictive"
        )

        print(
            "[DONE] OI-015 INSTALLATION COMPLETE"
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
                item.write_bytes(
                    original
                )

        print(
            "[ROLLBACK] OI-015 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
