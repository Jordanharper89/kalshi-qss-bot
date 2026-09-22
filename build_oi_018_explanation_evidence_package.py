from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-018"
INSTALLER_REVISION = "OI_018_EXPLANATION_EVIDENCE_PACKAGE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_015 = PACKAGE / "oi_015_reasoning_input_builder.py"
UPSTREAM_016 = PACKAGE / "oi_016_evidence_sufficiency_gate.py"
UPSTREAM_017 = PACKAGE / "oi_017_observation_change_attribution.py"
MODULE = PACKAGE / "oi_018_explanation_evidence_package.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_018_explanation_evidence_package.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_015_reasoning_input_builder import OracleReasoningInput
from .oi_016_evidence_sufficiency_gate import EvidenceSufficiencyDecision
from .oi_017_observation_change_attribution import ObservationChange

BUILD_ID = "OI-018"
OI_018_REVISION = "OI_018_EXPLANATION_EVIDENCE_PACKAGE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False


class ExplanationEvidencePackageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExplanationEvidencePackage:
    query_id: str
    profile_id: str
    built_at: datetime
    reasoning_input_hash: str
    sufficiency_decision_hash: str
    sufficient_evidence: bool
    evidence_item_count: int
    change_hashes: tuple[str, ...]
    package_hash: str
    causal_claim_allowed: bool
    predictive: bool
    read_only: bool


class ExplanationEvidencePackageBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_claim_allowed = False
    prediction_allowed = False

    def build(
        self,
        *,
        reasoning_input: OracleReasoningInput,
        sufficiency: EvidenceSufficiencyDecision,
        changes: tuple[ObservationChange, ...],
        built_at: datetime,
    ) -> ExplanationEvidencePackage:
        if not isinstance(reasoning_input, OracleReasoningInput):
            raise TypeError(
                "reasoning_input must be OracleReasoningInput"
            )
        if not isinstance(sufficiency, EvidenceSufficiencyDecision):
            raise TypeError(
                "sufficiency must be EvidenceSufficiencyDecision"
            )

        values = tuple(changes)

        if any(
            not isinstance(item, ObservationChange)
            for item in values
        ):
            raise TypeError("all changes must be ObservationChange")

        if sufficiency.input_hash != reasoning_input.input_hash:
            raise ExplanationEvidencePackageError(
                "sufficiency decision does not belong to reasoning input"
            )

        if not isinstance(built_at, datetime):
            raise TypeError("built_at must be datetime")

        if built_at.tzinfo is None:
            raise ExplanationEvidencePackageError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(timezone.utc)

        ordered_changes = tuple(
            sorted(
                values,
                key=lambda item: (
                    item.subject,
                    item.observation_type,
                    item.value_field,
                    item.prior_observation_id,
                    item.current_observation_id,
                ),
            )
        )

        change_hashes = tuple(
            item.change_hash
            for item in ordered_changes
        )

        body = {
            "query_id": reasoning_input.query_id,
            "profile_id": reasoning_input.profile_id,
            "built_at": built_at,
            "reasoning_input_hash": reasoning_input.input_hash,
            "sufficiency_decision_hash": sufficiency.decision_hash,
            "sufficient_evidence": sufficiency.sufficient,
            "evidence_item_count": len(reasoning_input.evidence_items),
            "change_hashes": change_hashes,
            "causal_claim_allowed": False,
            "predictive": False,
            "read_only": True,
        }

        return ExplanationEvidencePackage(
            query_id=reasoning_input.query_id,
            profile_id=reasoning_input.profile_id,
            built_at=built_at,
            reasoning_input_hash=reasoning_input.input_hash,
            sufficiency_decision_hash=sufficiency.decision_hash,
            sufficient_evidence=sufficiency.sufficient,
            evidence_item_count=len(reasoning_input.evidence_items),
            change_hashes=change_hashes,
            package_hash=deterministic_sha256(body),
            causal_claim_allowed=False,
            predictive=False,
            read_only=True,
        )


def verify_explanation_evidence_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-018 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            PREDICTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-018 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_018_REVISION",
    "ExplanationEvidencePackageError",
    "ExplanationEvidencePackage",
    "ExplanationEvidencePackageBuilder",
    "verify_explanation_evidence_package",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import MappingProxyType

from qseries_v2.observation_intelligence.oi_015_reasoning_input_builder import (
    OracleReasoningInput,
    ReasoningEvidenceItem,
)
from qseries_v2.observation_intelligence.oi_016_evidence_sufficiency_gate import (
    EvidenceSufficiencyGate,
    EvidenceSufficiencyPolicy,
)
from qseries_v2.observation_intelligence.oi_017_observation_change_attribution import (
    ObservationChange,
)
from qseries_v2.observation_intelligence.oi_018_explanation_evidence_package import (
    OI_018_REVISION,
    ExplanationEvidencePackageBuilder,
    verify_explanation_evidence_package,
)

NOW = datetime(2026, 8, 10, 13, 0, tzinfo=timezone.utc)


def input_value():
    item = ReasoningEvidenceItem(
        canonical_observation_id="obs.current",
        canonical_observation_hash="a" * 64,
        provider="Provider",
        adapter_id="adapter.source.a",
        observed_at=NOW,
        freshness_status="fresh",
        subject="TEST",
        observation_type="market_snapshot",
        facts=MappingProxyType({"value": 55}),
    )

    return OracleReasoningInput(
        query_id="query.explain",
        profile_id="profile.market_explanation",
        built_at=NOW,
        evidence_items=(item,),
        required_evidence_count=1,
        satisfied_evidence_count=1,
        missing_evidence_count=0,
        complete_required_evidence=True,
        input_hash="b" * 64,
        predictive=False,
        read_only=True,
    )


def sufficiency():
    return EvidenceSufficiencyGate().evaluate(
        input_value(),
        policy=EvidenceSufficiencyPolicy(
            policy_id="policy.explain",
            minimum_evidence_items=1,
            minimum_distinct_sources=1,
            allow_stale_evidence=False,
        ),
    )


def change():
    return ObservationChange(
        subject="TEST",
        observation_type="market_snapshot",
        value_field="yes_bid",
        prior_observation_id="obs.prior",
        current_observation_id="obs.current",
        prior_value=50.0,
        current_value=55.0,
        absolute_change=5.0,
        relative_change=0.1,
        direction="up",
        change_hash="c" * 64,
    )


class TestOI018(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_evidence_package()
        )

    def test_build(self):
        package = ExplanationEvidencePackageBuilder().build(
            reasoning_input=input_value(),
            sufficiency=sufficiency(),
            changes=(change(),),
            built_at=NOW,
        )

        self.assertTrue(package.sufficient_evidence)
        self.assertEqual(package.evidence_item_count, 1)
        self.assertEqual(package.change_hashes, ("c" * 64,))

    def test_non_causal(self):
        package = ExplanationEvidencePackageBuilder().build(
            reasoning_input=input_value(),
            sufficiency=sufficiency(),
            changes=(change(),),
            built_at=NOW,
        )

        self.assertFalse(package.causal_claim_allowed)
        self.assertFalse(package.predictive)
        self.assertTrue(package.read_only)

    def test_deterministic(self):
        builder = ExplanationEvidencePackageBuilder()
        a = builder.build(
            reasoning_input=input_value(),
            sufficiency=sufficiency(),
            changes=(change(),),
            built_at=NOW,
        )
        b = builder.build(
            reasoning_input=input_value(),
            sufficiency=sufficiency(),
            changes=(change(),),
            built_at=NOW,
        )
        self.assertEqual(a.package_hash, b.package_hash)

    def test_side_effects(self):
        builder = ExplanationEvidencePackageBuilder()
        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.causal_claim_allowed)
        self.assertFalse(builder.prediction_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-018 CERTIFICATION TEST")
    print(" EXPLANATION EVIDENCE PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI018
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-018")
    print(f"[PASS] Revision: {OI_018_REVISION}")
    print("[PASS] Reasoning input, evidence sufficiency, and observed changes packaged together")
    print("[PASS] Explanation package preserves evidence lineage and change lineage")
    print("[PASS] Causal claims and predictions remain explicitly disabled")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-018 CERTIFIED")
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
    print(" OI-018 INSTALLER")
    print(" EXPLANATION EVIDENCE PACKAGE")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    upstreams = (
        (UPSTREAM_015, "OI-015"),
        (UPSTREAM_016, "OI-016"),
        (UPSTREAM_017, "OI-017"),
    )

    for path, name in upstreams:
        if not path.is_file():
            raise RuntimeError(f"Certified {name} missing: {path}")

    upstream_hashes = {
        path: sha(path)
        for path, _ in upstreams
    }

    print("[PASS] Certified OI-015 through OI-017 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_018_explanation_evidence_package import *"

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
        print("[PASS] Explanation package remains deterministic, read-only, non-causal, and non-predictive")
        print("[DONE] OI-018 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-018 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
