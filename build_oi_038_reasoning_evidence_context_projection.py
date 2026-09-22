from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-038"
INSTALLER_REVISION = "OI_038_REASONING_EVIDENCE_CONTEXT_PROJECTION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_020_temporal_association.py", "OI-020"),
    (PACKAGE / "oi_036_oracle_reasoning_evidence_package.py", "OI-036"),
    (PACKAGE / "oi_037_reasoning_evidence_registry.py", "OI-037"),
)

MODULE = PACKAGE / "oi_038_reasoning_evidence_context_projection.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_038_reasoning_evidence_context_projection.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_037_reasoning_evidence_registry import ReasoningEvidenceRegistry

BUILD_ID = "OI-038"
OI_038_REVISION = "OI_038_REASONING_EVIDENCE_CONTEXT_PROJECTION_V1"

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


class ReasoningEvidenceContextProjectionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceContext:
    canonical_observation_id: str
    canonical_observation_hash: str
    adapter_id: str
    provider: str
    subject: str
    observation_type: str
    context_roles: tuple[str, ...]
    context_hash: str


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceContextProjection:
    package_hash: str
    registry_hash: str
    contexts: tuple[ReasoningEvidenceContext, ...]
    context_count: int
    projection_hash: str
    read_only: bool


class ReasoningEvidenceContextProjector:
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

    @staticmethod
    def _roles_for(
        *,
        provider: str,
        observation_type: str,
    ) -> tuple[str, ...]:
        roles = {"evidence"}

        normalized_type = " ".join(
            str(observation_type).strip().lower().split()
        )
        normalized_provider = " ".join(
            str(provider).strip().lower().split()
        )

        if normalized_type in {
            "market_snapshot",
            "spot_price",
            "orderbook",
        }:
            roles.add("market_state")

        if normalized_type in {
            "news",
            "headline",
            "filing",
            "announcement",
        }:
            roles.add("event_context")

        if normalized_type in {
            "weather",
            "forecast",
            "observation",
        }:
            roles.add("environment_context")

        if normalized_type in {
            "injury",
            "lineup",
            "roster",
            "stat",
        }:
            roles.add("sports_context")

        if normalized_provider:
            roles.add("source_context")

        return tuple(sorted(roles))

    def project(
        self,
        registry: ReasoningEvidenceRegistry,
    ) -> ReasoningEvidenceContextProjection:
        if not isinstance(
            registry,
            ReasoningEvidenceRegistry,
        ):
            raise TypeError(
                "registry must be ReasoningEvidenceRegistry"
            )

        contexts = []

        for record in registry.records:
            roles = self._roles_for(
                provider=record.provider,
                observation_type=record.observation_type,
            )

            body = {
                "canonical_observation_id": (
                    record.canonical_observation_id
                ),
                "canonical_observation_hash": (
                    record.canonical_observation_hash
                ),
                "adapter_id": record.adapter_id,
                "provider": record.provider,
                "subject": record.subject,
                "observation_type": record.observation_type,
                "context_roles": roles,
            }

            contexts.append(
                ReasoningEvidenceContext(
                    canonical_observation_id=(
                        record.canonical_observation_id
                    ),
                    canonical_observation_hash=(
                        record.canonical_observation_hash
                    ),
                    adapter_id=record.adapter_id,
                    provider=record.provider,
                    subject=record.subject,
                    observation_type=record.observation_type,
                    context_roles=roles,
                    context_hash=deterministic_sha256(body),
                )
            )

        ordered = tuple(
            sorted(
                contexts,
                key=lambda item: item.canonical_observation_id,
            )
        )

        body = {
            "package_hash": registry.package_hash,
            "registry_hash": registry.registry_hash,
            "context_hashes": tuple(
                item.context_hash
                for item in ordered
            ),
            "context_count": len(ordered),
            "read_only": True,
        }

        return ReasoningEvidenceContextProjection(
            package_hash=registry.package_hash,
            registry_hash=registry.registry_hash,
            contexts=ordered,
            context_count=len(ordered),
            projection_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_reasoning_evidence_context_projection() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-038 must remain read-only"
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
            "OI-038 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_038_REVISION",
    "ReasoningEvidenceContextProjectionError",
    "ReasoningEvidenceContext",
    "ReasoningEvidenceContextProjection",
    "ReasoningEvidenceContextProjector",
    "verify_reasoning_evidence_context_projection",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_036_oracle_reasoning_evidence_package import (
    OracleReasoningEvidenceItem,
    OracleReasoningEvidencePackage,
)
from qseries_v2.observation_intelligence.oi_037_reasoning_evidence_registry import (
    ReasoningEvidenceRegistry,
)
from qseries_v2.observation_intelligence.oi_038_reasoning_evidence_context_projection import (
    OI_038_REVISION,
    ReasoningEvidenceContextProjector,
    verify_reasoning_evidence_context_projection,
)

NOW = datetime(
    2026,
    8,
    11,
    3,
    0,
    tzinfo=timezone.utc,
)


def package():
    return OracleReasoningEvidencePackage(
        package_id="reasoning.astros",
        query_id="query.astros",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status="admitted",
        admission_hash="a" * 64,
        materialization_hash="b" * 64,
        evidence_items=(
            OracleReasoningEvidenceItem(
                canonical_observation_id="obs.market",
                canonical_observation_hash="c" * 64,
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Astros strikeouts",
                observation_type="market_snapshot",
                observed_at=NOW,
            ),
            OracleReasoningEvidenceItem(
                canonical_observation_id="obs.lineup",
                canonical_observation_hash="d" * 64,
                adapter_id="adapter.sports.v1",
                provider="SportsFeed",
                subject="Astros",
                observation_type="lineup",
                observed_at=NOW,
            ),
        ),
        missing_need_count=0,
        built_at=NOW,
        package_hash="e" * 64,
        read_only=True,
        predictive=False,
    )


class TestOI038(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_context_projection()
        )

    def test_projection(self):
        result = ReasoningEvidenceContextProjector().project(
            ReasoningEvidenceRegistry(
                package()
            )
        )

        self.assertEqual(
            result.context_count,
            2,
        )

    def test_market_role(self):
        result = ReasoningEvidenceContextProjector().project(
            ReasoningEvidenceRegistry(
                package()
            )
        )

        market = tuple(
            item
            for item in result.contexts
            if item.canonical_observation_id == "obs.market"
        )[0]

        self.assertIn(
            "market_state",
            market.context_roles,
        )

    def test_sports_role(self):
        result = ReasoningEvidenceContextProjector().project(
            ReasoningEvidenceRegistry(
                package()
            )
        )

        lineup = tuple(
            item
            for item in result.contexts
            if item.canonical_observation_id == "obs.lineup"
        )[0]

        self.assertIn(
            "sports_context",
            lineup.context_roles,
        )

    def test_deterministic(self):
        projector = ReasoningEvidenceContextProjector()

        a = projector.project(
            ReasoningEvidenceRegistry(
                package()
            )
        )

        b = projector.project(
            ReasoningEvidenceRegistry(
                package()
            )
        )

        self.assertEqual(
            a.projection_hash,
            b.projection_hash,
        )

    def test_side_effects(self):
        projector = ReasoningEvidenceContextProjector()

        self.assertTrue(projector.read_only)
        self.assertFalse(projector.network_allowed)
        self.assertFalse(projector.persistence_allowed)
        self.assertFalse(projector.publication_allowed)
        self.assertFalse(projector.execution_allowed)
        self.assertFalse(projector.qseries_execution_allowed)
        self.assertFalse(projector.prediction_allowed)
        self.assertFalse(projector.edge_score_allowed)
        self.assertFalse(projector.probability_allowed)
        self.assertFalse(projector.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-038 CERTIFICATION TEST")
    print(" REASONING EVIDENCE CONTEXT PROJECTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI038
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-038")
    print(f"[PASS] Revision: {OI_038_REVISION}")
    print("[PASS] Reasoning-ready evidence projected into deterministic structural context roles")
    print("[PASS] Market-state, sports, event, environment, and source context remain generic")
    print("[PASS] Context projection introduces no causal claim, probability, prediction, or edge score")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-038 CERTIFIED")
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
    print(" OI-038 INSTALLER")
    print(" REASONING EVIDENCE CONTEXT PROJECTION")
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
        "[PASS] Certified OI-020, OI-036, "
        "and OI-037 verified read-only"
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
            "from .oi_038_reasoning_evidence_context_projection import *"
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
            "[PASS] Context projection remains deterministic, "
            "read-only, and non-causal"
        )
        print("[DONE] OI-038 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-038 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
