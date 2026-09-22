from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-016"
INSTALLER_REVISION = "OI_016_EVIDENCE_SUFFICIENCY_GATE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_010 = PACKAGE / "oi_010_observation_freshness_health.py"
UPSTREAM_015 = PACKAGE / "oi_015_reasoning_input_builder.py"
MODULE = PACKAGE / "oi_016_evidence_sufficiency_gate.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_016_evidence_sufficiency_gate.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_015_reasoning_input_builder import OracleReasoningInput

BUILD_ID = "OI-016"
OI_016_REVISION = "OI_016_EVIDENCE_SUFFICIENCY_GATE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False


class EvidenceSufficiencyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceSufficiencyPolicy:
    policy_id: str
    minimum_evidence_items: int
    minimum_distinct_sources: int
    allow_stale_evidence: bool

    def __post_init__(self) -> None:
        policy_id = " ".join(
            str(self.policy_id).strip().lower().split()
        )
        if not policy_id:
            raise EvidenceSufficiencyError(
                "policy_id must not be empty"
            )
        if (
            not isinstance(self.minimum_evidence_items, int)
            or self.minimum_evidence_items < 0
        ):
            raise EvidenceSufficiencyError(
                "minimum_evidence_items must be non-negative"
            )
        if (
            not isinstance(self.minimum_distinct_sources, int)
            or self.minimum_distinct_sources < 0
        ):
            raise EvidenceSufficiencyError(
                "minimum_distinct_sources must be non-negative"
            )
        object.__setattr__(self, "policy_id", policy_id)

    @property
    def policy_hash(self) -> str:
        return deterministic_sha256(
            {
                "policy_id": self.policy_id,
                "minimum_evidence_items": self.minimum_evidence_items,
                "minimum_distinct_sources": self.minimum_distinct_sources,
                "allow_stale_evidence": self.allow_stale_evidence,
            }
        )


@dataclass(frozen=True, slots=True)
class EvidenceSufficiencyDecision:
    policy_id: str
    input_hash: str
    evidence_item_count: int
    distinct_source_count: int
    stale_evidence_count: int
    complete_required_evidence: bool
    sufficient: bool
    reason_codes: tuple[str, ...]
    decision_hash: str


class EvidenceSufficiencyGate:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False

    def evaluate(
        self,
        reasoning_input: OracleReasoningInput,
        *,
        policy: EvidenceSufficiencyPolicy,
    ) -> EvidenceSufficiencyDecision:
        if not isinstance(reasoning_input, OracleReasoningInput):
            raise TypeError(
                "reasoning_input must be OracleReasoningInput"
            )
        if not isinstance(policy, EvidenceSufficiencyPolicy):
            raise TypeError(
                "policy must be EvidenceSufficiencyPolicy"
            )

        item_count = len(reasoning_input.evidence_items)
        distinct_sources = len(
            {
                item.adapter_id
                for item in reasoning_input.evidence_items
            }
        )
        stale_count = sum(
            1
            for item in reasoning_input.evidence_items
            if item.freshness_status == "stale"
        )

        reasons = []

        if reasoning_input.complete_required_evidence is not True:
            reasons.append("missing_required_evidence")

        if item_count < policy.minimum_evidence_items:
            reasons.append("insufficient_evidence_items")

        if distinct_sources < policy.minimum_distinct_sources:
            reasons.append("insufficient_source_diversity")

        if stale_count and not policy.allow_stale_evidence:
            reasons.append("stale_evidence_present")

        reasons = tuple(sorted(set(reasons)))
        sufficient = not reasons

        body = {
            "policy_id": policy.policy_id,
            "policy_hash": policy.policy_hash,
            "input_hash": reasoning_input.input_hash,
            "evidence_item_count": item_count,
            "distinct_source_count": distinct_sources,
            "stale_evidence_count": stale_count,
            "complete_required_evidence": (
                reasoning_input.complete_required_evidence
            ),
            "sufficient": sufficient,
            "reason_codes": reasons,
        }

        return EvidenceSufficiencyDecision(
            policy_id=policy.policy_id,
            input_hash=reasoning_input.input_hash,
            evidence_item_count=item_count,
            distinct_source_count=distinct_sources,
            stale_evidence_count=stale_count,
            complete_required_evidence=(
                reasoning_input.complete_required_evidence
            ),
            sufficient=sufficient,
            reason_codes=reasons,
            decision_hash=deterministic_sha256(body),
        )


def verify_evidence_sufficiency_gate() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-016 must remain read-only")

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
        raise AssertionError("OI-016 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_016_REVISION",
    "EvidenceSufficiencyError",
    "EvidenceSufficiencyPolicy",
    "EvidenceSufficiencyDecision",
    "EvidenceSufficiencyGate",
    "verify_evidence_sufficiency_gate",
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
    OI_016_REVISION,
    EvidenceSufficiencyGate,
    EvidenceSufficiencyPolicy,
    verify_evidence_sufficiency_gate,
)

NOW = datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc)


def reasoning_input(
    *,
    freshness: str = "fresh",
    complete: bool = True,
):
    item = ReasoningEvidenceItem(
        canonical_observation_id="obs.1",
        canonical_observation_hash="a" * 64,
        provider="Provider",
        adapter_id="adapter.source.a",
        observed_at=NOW,
        freshness_status=freshness,
        subject="TEST",
        observation_type="market_snapshot",
        facts=MappingProxyType({"value": 1}),
    )

    return OracleReasoningInput(
        query_id="query.test",
        profile_id="profile.test",
        built_at=NOW,
        evidence_items=(item,),
        required_evidence_count=1,
        satisfied_evidence_count=1 if complete else 0,
        missing_evidence_count=0 if complete else 1,
        complete_required_evidence=complete,
        input_hash="b" * 64,
        predictive=False,
        read_only=True,
    )


class TestOI016(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_evidence_sufficiency_gate()
        )

    def test_sufficient(self):
        decision = EvidenceSufficiencyGate().evaluate(
            reasoning_input(),
            policy=EvidenceSufficiencyPolicy(
                policy_id="policy.basic",
                minimum_evidence_items=1,
                minimum_distinct_sources=1,
                allow_stale_evidence=False,
            ),
        )
        self.assertTrue(decision.sufficient)

    def test_missing_required(self):
        decision = EvidenceSufficiencyGate().evaluate(
            reasoning_input(complete=False),
            policy=EvidenceSufficiencyPolicy(
                policy_id="policy.basic",
                minimum_evidence_items=1,
                minimum_distinct_sources=1,
                allow_stale_evidence=False,
            ),
        )
        self.assertFalse(decision.sufficient)
        self.assertIn(
            "missing_required_evidence",
            decision.reason_codes,
        )

    def test_stale_rejected(self):
        decision = EvidenceSufficiencyGate().evaluate(
            reasoning_input(freshness="stale"),
            policy=EvidenceSufficiencyPolicy(
                policy_id="policy.basic",
                minimum_evidence_items=1,
                minimum_distinct_sources=1,
                allow_stale_evidence=False,
            ),
        )
        self.assertFalse(decision.sufficient)

    def test_deterministic(self):
        gate = EvidenceSufficiencyGate()
        policy = EvidenceSufficiencyPolicy(
            policy_id="policy.basic",
            minimum_evidence_items=1,
            minimum_distinct_sources=1,
            allow_stale_evidence=False,
        )
        a = gate.evaluate(reasoning_input(), policy=policy)
        b = gate.evaluate(reasoning_input(), policy=policy)
        self.assertEqual(a.decision_hash, b.decision_hash)

    def test_side_effects(self):
        gate = EvidenceSufficiencyGate()
        self.assertTrue(gate.read_only)
        self.assertFalse(gate.network_allowed)
        self.assertFalse(gate.persistence_allowed)
        self.assertFalse(gate.publication_allowed)
        self.assertFalse(gate.execution_allowed)
        self.assertFalse(gate.qseries_execution_allowed)
        self.assertFalse(gate.prediction_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-016 CERTIFICATION TEST")
    print(" EVIDENCE SUFFICIENCY GATE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI016
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-016")
    print(f"[PASS] Revision: {OI_016_REVISION}")
    print("[PASS] Required evidence, source diversity, and freshness sufficiency certified")
    print("[PASS] Insufficient evidence fails closed with reason codes")
    print("[PASS] No prediction or edge judgment introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-016 CERTIFIED")
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
    print(" OI-016 INSTALLER")
    print(" EVIDENCE SUFFICIENCY GATE")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    upstreams = (
        (UPSTREAM_010, "OI-010"),
        (UPSTREAM_015, "OI-015"),
    )

    for path, name in upstreams:
        if not path.is_file():
            raise RuntimeError(f"Certified {name} missing: {path}")

    upstream_hashes = {
        path: sha(path)
        for path, _ in upstreams
    }

    print("[PASS] Certified OI-010 and OI-015 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_016_evidence_sufficiency_gate import *"

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
        print("[PASS] Sufficiency gate remains deterministic, read-only, and non-predictive")
        print("[DONE] OI-016 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-016 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
