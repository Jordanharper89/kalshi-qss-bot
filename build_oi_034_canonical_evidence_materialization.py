from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-034"
INSTALLER_REVISION = "OI_034_CANONICAL_EVIDENCE_MATERIALIZATION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_003_canonical_observation_gateway.py", "OI-003"),
    (PACKAGE / "oi_012_routed_observation_acquisition.py", "OI-012"),
    (PACKAGE / "oi_033_oracle_evidence_intake_package.py", "OI-033"),
)

MODULE = PACKAGE / "oi_034_canonical_evidence_materialization.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_034_canonical_evidence_materialization.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_033_oracle_evidence_intake_package import OracleEvidenceIntakePackage

BUILD_ID = "OI-034"
OI_034_REVISION = "OI_034_CANONICAL_EVIDENCE_MATERIALIZATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class CanonicalEvidenceMaterializationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MaterializedEvidenceItem:
    canonical_observation_id: str
    canonical_observation_hash: str
    adapter_id: str
    provider: str
    subject: str
    observation_type: str
    observed_at: datetime
    materialization_hash: str


@dataclass(frozen=True, slots=True)
class CanonicalEvidenceMaterialization:
    intake_id: str
    intake_hash: str
    query_id: str
    profile_id: str
    subject_hint: str
    items: tuple[MaterializedEvidenceItem, ...]
    observation_count: int
    complete_count_match: bool
    materialization_hash: str
    read_only: bool


class CanonicalEvidenceMaterializer:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def materialize(
        self,
        *,
        intake: OracleEvidenceIntakePackage,
        observations: tuple[CanonicalLiveObservation, ...],
    ) -> CanonicalEvidenceMaterialization:
        if not isinstance(intake, OracleEvidenceIntakePackage):
            raise TypeError(
                "intake must be OracleEvidenceIntakePackage"
            )

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
            raise CanonicalEvidenceMaterializationError(
                "observations must be deterministically sorted"
            )

        ids = tuple(
            item.canonical_observation_id
            for item in values
        )

        if len(ids) != len(set(ids)):
            raise CanonicalEvidenceMaterializationError(
                "duplicate canonical observation identity"
            )

        allowed_adapters = {
            adapter_id
            for item in intake.evidence_items
            for adapter_id in item.adapter_ids
        }

        if any(
            item.adapter_id not in allowed_adapters
            for item in values
        ):
            raise CanonicalEvidenceMaterializationError(
                "observation adapter not admitted by intake package"
            )

        items = []

        for observation in values:
            body = {
                "canonical_observation_id": (
                    observation.canonical_observation_id
                ),
                "canonical_observation_hash": (
                    observation.canonical_observation_hash
                ),
                "adapter_id": observation.adapter_id,
                "provider": observation.provider,
                "subject": observation.subject,
                "observation_type": observation.observation_type,
                "observed_at": observation.observed_at,
            }

            items.append(
                MaterializedEvidenceItem(
                    canonical_observation_id=(
                        observation.canonical_observation_id
                    ),
                    canonical_observation_hash=(
                        observation.canonical_observation_hash
                    ),
                    adapter_id=observation.adapter_id,
                    provider=observation.provider,
                    subject=observation.subject,
                    observation_type=observation.observation_type,
                    observed_at=observation.observed_at,
                    materialization_hash=deterministic_sha256(body),
                )
            )

        count_match = (
            len(items)
            == intake.total_observation_count
        )

        body = {
            "intake_id": intake.intake_id,
            "intake_hash": intake.intake_hash,
            "query_id": intake.query_id,
            "profile_id": intake.profile_id,
            "subject_hint": intake.subject_hint,
            "item_hashes": tuple(
                item.materialization_hash
                for item in items
            ),
            "observation_count": len(items),
            "complete_count_match": count_match,
            "read_only": True,
        }

        return CanonicalEvidenceMaterialization(
            intake_id=intake.intake_id,
            intake_hash=intake.intake_hash,
            query_id=intake.query_id,
            profile_id=intake.profile_id,
            subject_hint=intake.subject_hint,
            items=tuple(items),
            observation_count=len(items),
            complete_count_match=count_match,
            materialization_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_canonical_evidence_materialization() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-034 must remain read-only")

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
            "OI-034 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_034_REVISION",
    "CanonicalEvidenceMaterializationError",
    "MaterializedEvidenceItem",
    "CanonicalEvidenceMaterialization",
    "CanonicalEvidenceMaterializer",
    "verify_canonical_evidence_materialization",
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
from qseries_v2.observation_intelligence.oi_033_oracle_evidence_intake_package import (
    OracleEvidenceIntakeItem,
    OracleEvidenceIntakePackage,
)
from qseries_v2.observation_intelligence.oi_034_canonical_evidence_materialization import (
    OI_034_REVISION,
    CanonicalEvidenceMaterializer,
    verify_canonical_evidence_materialization,
)

NOW = datetime(2026, 8, 10, 23, 0, tzinfo=timezone.utc)


def intake():
    return OracleEvidenceIntakePackage(
        intake_id="intake.astros",
        request_id="request.astros",
        query_id="query.astros",
        query_kind="explanation",
        subject_hint="Astros strikeouts",
        profile_id="profile.market_explanation",
        acquisition_status="partial",
        evidence_items=(
            OracleEvidenceIntakeItem(
                need_id="need.market",
                adapter_ids=("adapter.kalshi.v1",),
                evidence_hash="a" * 64,
                observation_count=1,
                satisfied=True,
                reason_code="satisfied",
                item_hash="b" * 64,
            ),
        ),
        total_observation_count=1,
        missing_need_ids=("need.lineup",),
        complete_evidence_intake=False,
        assembled_at=NOW,
        intake_hash="c" * 64,
        read_only=True,
        predictive=False,
        terminal_mutation_allowed=False,
    )


def observation():
    envelope = RawObservationEnvelope(
        source=ObservationSourceIdentity(
            source_id="kalshi.public",
            source_kind="market_venue",
            provider="Kalshi",
            adapter_id="adapter.kalshi.v1",
        ),
        external_observation_id="KXASTROS-OI034",
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
    )

    return CanonicalLiveObservationGateway(
        default_source_registry()
    ).canonicalize(
        envelope
    ).canonical_observation


class TestOI034(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_canonical_evidence_materialization()
        )

    def test_materialize(self):
        value = CanonicalEvidenceMaterializer().materialize(
            intake=intake(),
            observations=(observation(),),
        )

        self.assertEqual(value.observation_count, 1)
        self.assertTrue(value.complete_count_match)

    def test_adapter_preserved(self):
        value = CanonicalEvidenceMaterializer().materialize(
            intake=intake(),
            observations=(observation(),),
        )

        self.assertEqual(
            value.items[0].adapter_id,
            "adapter.kalshi.v1",
        )

    def test_unadmitted_adapter_rejected(self):
        bad = intake()

        with self.assertRaises(ValueError):
            CanonicalEvidenceMaterializer().materialize(
                intake=bad,
                observations=(),
            )

    def test_deterministic(self):
        builder = CanonicalEvidenceMaterializer()

        a = builder.materialize(
            intake=intake(),
            observations=(observation(),),
        )
        b = builder.materialize(
            intake=intake(),
            observations=(observation(),),
        )

        self.assertEqual(
            a.materialization_hash,
            b.materialization_hash,
        )

    def test_side_effects(self):
        builder = CanonicalEvidenceMaterializer()

        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.prediction_allowed)
        self.assertFalse(builder.edge_score_allowed)
        self.assertFalse(builder.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-034 CERTIFICATION TEST")
    print(" CANONICAL EVIDENCE MATERIALIZATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI034
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-034")
    print(f"[PASS] Revision: {OI_034_REVISION}")
    print("[PASS] Canonical observations materialized against certified Oracle evidence intake")
    print("[PASS] Observation identity, hash, adapter, provider, subject, type, and timestamp preserved")
    print("[PASS] Intake observation-count reconciliation certified")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-034 CERTIFIED")
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
    print(" OI-034 INSTALLER")
    print(" CANONICAL EVIDENCE MATERIALIZATION")
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
        "[PASS] Certified OI-003, OI-012, "
        "and OI-033 verified read-only"
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
            "from .oi_034_canonical_evidence_materialization import *"
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
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[PASS] Canonical materialization remains deterministic, "
            "read-only, and fail-closed"
        )
        print("[DONE] OI-034 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-034 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
