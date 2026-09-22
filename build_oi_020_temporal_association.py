from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-020"
INSTALLER_REVISION = "OI_020_TEMPORAL_ASSOCIATION_FOUNDATION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_007 = PACKAGE / "oi_007_observation_history.py"
UPSTREAM_017 = PACKAGE / "oi_017_observation_change_attribution.py"
UPSTREAM_019 = PACKAGE / "oi_019_evidence_contradiction_registry.py"
MODULE = PACKAGE / "oi_020_temporal_association.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_020_temporal_association.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_017_observation_change_attribution import ObservationChange

BUILD_ID = "OI-020"
OI_020_REVISION = "OI_020_TEMPORAL_ASSOCIATION_FOUNDATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_INFERENCE_ALLOWED = False
PREDICTION_ALLOWED = False


class TemporalAssociationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TemporalAssociation:
    change_hash: str
    evidence_observation_id: str
    evidence_subject: str
    evidence_observation_type: str
    evidence_observed_at: datetime
    seconds_from_change_observation: int
    temporal_relation: str
    association_hash: str


class TemporalAssociationEngine:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_inference_allowed = False
    prediction_allowed = False

    def associate(
        self,
        *,
        change: ObservationChange,
        change_observed_at: datetime,
        evidence: tuple[CanonicalLiveObservation, ...],
        max_window_seconds: int,
    ) -> tuple[TemporalAssociation, ...]:
        if not isinstance(change, ObservationChange):
            raise TypeError(
                "change must be ObservationChange"
            )

        if not isinstance(change_observed_at, datetime):
            raise TypeError(
                "change_observed_at must be datetime"
            )

        if change_observed_at.tzinfo is None:
            raise TemporalAssociationError(
                "change_observed_at must be timezone-aware"
            )

        if (
            not isinstance(max_window_seconds, int)
            or max_window_seconds < 0
        ):
            raise TemporalAssociationError(
                "max_window_seconds must be a non-negative integer"
            )

        values = tuple(evidence)

        if any(
            not isinstance(item, CanonicalLiveObservation)
            for item in values
        ):
            raise TypeError(
                "all evidence must be CanonicalLiveObservation"
            )

        associations = []

        for item in values:
            delta = int(
                (
                    item.observed_at
                    - change_observed_at
                ).total_seconds()
            )

            if abs(delta) > max_window_seconds:
                continue

            if delta < 0:
                relation = "before"
            elif delta > 0:
                relation = "after"
            else:
                relation = "simultaneous"

            body = {
                "change_hash": change.change_hash,
                "evidence_observation_id": (
                    item.canonical_observation_id
                ),
                "evidence_subject": item.subject,
                "evidence_observation_type": (
                    item.observation_type
                ),
                "evidence_observed_at": item.observed_at,
                "seconds_from_change_observation": delta,
                "temporal_relation": relation,
            }

            associations.append(
                TemporalAssociation(
                    change_hash=change.change_hash,
                    evidence_observation_id=(
                        item.canonical_observation_id
                    ),
                    evidence_subject=item.subject,
                    evidence_observation_type=(
                        item.observation_type
                    ),
                    evidence_observed_at=item.observed_at,
                    seconds_from_change_observation=delta,
                    temporal_relation=relation,
                    association_hash=(
                        deterministic_sha256(body)
                    ),
                )
            )

        return tuple(
            sorted(
                associations,
                key=lambda item: (
                    abs(
                        item.seconds_from_change_observation
                    ),
                    item.evidence_observation_id,
                ),
            )
        )


def verify_temporal_association() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-020 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_INFERENCE_ALLOWED,
            PREDICTION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-020 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_020_REVISION",
    "TemporalAssociationError",
    "TemporalAssociation",
    "TemporalAssociationEngine",
    "verify_temporal_association",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_002_source_adapter_registry import (
    SourceAdapterDescriptor,
    SourceAdapterRegistry,
)
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_017_observation_change_attribution import (
    ObservationChange,
)
from qseries_v2.observation_intelligence.oi_020_temporal_association import (
    OI_020_REVISION,
    TemporalAssociationEngine,
    verify_temporal_association,
)

BASE = datetime(
    2026,
    8,
    10,
    14,
    0,
    tzinfo=timezone.utc,
)


def registry():
    return SourceAdapterRegistry(
        (
            SourceAdapterDescriptor(
                adapter_id="adapter.news.a",
                source_id="news.a",
                source_kind="news",
                provider="News A",
                adapter_version="1",
                capabilities=("news",),
                enabled_for_intake=True,
            ),
        )
    )


def evidence(
    external_id: str,
    offset_seconds: int,
):
    envelope = RawObservationEnvelope(
        source=ObservationSourceIdentity(
            source_id="news.a",
            source_kind="news",
            provider="News A",
            adapter_id="adapter.news.a",
        ),
        external_observation_id=external_id,
        observed_at=(
            BASE
            + timedelta(
                seconds=offset_seconds
            )
        ),
        subject="Astros",
        observation_type="news",
        payload={
            "headline": external_id,
        },
        metadata={},
    )

    return CanonicalLiveObservationGateway(
        registry()
    ).canonicalize(
        envelope
    ).canonical_observation


def change():
    return ObservationChange(
        subject="Astros strikeouts",
        observation_type="market_snapshot",
        value_field="yes_bid",
        prior_observation_id="obs.prior",
        current_observation_id="obs.current",
        prior_value=50.0,
        current_value=56.0,
        absolute_change=6.0,
        relative_change=0.12,
        direction="up",
        change_hash="c" * 64,
    )


class TestOI020(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_temporal_association()
        )

    def test_before(self):
        values = (
            TemporalAssociationEngine()
            .associate(
                change=change(),
                change_observed_at=BASE,
                evidence=(
                    evidence(
                        "before",
                        -30,
                    ),
                ),
                max_window_seconds=60,
            )
        )

        self.assertEqual(
            values[0].temporal_relation,
            "before",
        )

    def test_after(self):
        values = (
            TemporalAssociationEngine()
            .associate(
                change=change(),
                change_observed_at=BASE,
                evidence=(
                    evidence(
                        "after",
                        20,
                    ),
                ),
                max_window_seconds=60,
            )
        )

        self.assertEqual(
            values[0].temporal_relation,
            "after",
        )

    def test_outside_window_excluded(self):
        values = (
            TemporalAssociationEngine()
            .associate(
                change=change(),
                change_observed_at=BASE,
                evidence=(
                    evidence(
                        "far",
                        120,
                    ),
                ),
                max_window_seconds=60,
            )
        )

        self.assertEqual(
            values,
            (),
        )

    def test_nearest_first(self):
        values = (
            TemporalAssociationEngine()
            .associate(
                change=change(),
                change_observed_at=BASE,
                evidence=(
                    evidence(
                        "near",
                        10,
                    ),
                    evidence(
                        "farther",
                        -30,
                    ),
                ),
                max_window_seconds=60,
            )
        )

        self.assertEqual(
            values[0].seconds_from_change_observation,
            10,
        )

    def test_deterministic(self):
        engine = TemporalAssociationEngine()

        a = engine.associate(
            change=change(),
            change_observed_at=BASE,
            evidence=(
                evidence(
                    "near",
                    10,
                ),
            ),
            max_window_seconds=60,
        )

        b = engine.associate(
            change=change(),
            change_observed_at=BASE,
            evidence=(
                evidence(
                    "near",
                    10,
                ),
            ),
            max_window_seconds=60,
        )

        self.assertEqual(
            a[0].association_hash,
            b[0].association_hash,
        )

    def test_side_effects(self):
        engine = TemporalAssociationEngine()
        self.assertTrue(engine.read_only)
        self.assertFalse(engine.network_allowed)
        self.assertFalse(engine.persistence_allowed)
        self.assertFalse(engine.publication_allowed)
        self.assertFalse(engine.execution_allowed)
        self.assertFalse(engine.qseries_execution_allowed)
        self.assertFalse(engine.causal_inference_allowed)
        self.assertFalse(engine.prediction_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-020 CERTIFICATION TEST")
    print(" TEMPORAL ASSOCIATION FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI020
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-020")
    print(f"[PASS] Revision: {OI_020_REVISION}")
    print("[PASS] Before, simultaneous, and after temporal relationships certified")
    print("[PASS] Bounded association windows and nearest-event ordering certified")
    print("[PASS] Temporal association explicitly does not imply causation")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-020 CERTIFIED")
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
    print(" OI-020 INSTALLER")
    print(" TEMPORAL ASSOCIATION FOUNDATION")
    print("=" * 72)

    print(
        f"[BOOT] Revision: "
        f"{INSTALLER_REVISION}"
    )

    print(
        f"[ROOT] {ROOT}"
    )

    upstreams = (
        (UPSTREAM_007, "OI-007"),
        (UPSTREAM_017, "OI-017"),
        (UPSTREAM_019, "OI-019"),
    )

    for upstream, name in upstreams:
        if not upstream.is_file():
            raise RuntimeError(
                f"Certified {name} missing: "
                f"{upstream}"
            )

    upstream_hashes = {
        upstream: sha(upstream)
        for upstream, _ in upstreams
    }

    print(
        "[PASS] Certified OI-007, OI-017, "
        "and OI-019 verified read-only"
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
            "from .oi_020_temporal_association import *"
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
            "[PASS] Temporal association remains "
            "deterministic, read-only, non-causal, "
            "and non-predictive"
        )

        print(
            "[DONE] OI-020 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OI-020 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
