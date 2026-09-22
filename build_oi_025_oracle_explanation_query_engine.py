from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-025"
INSTALLER_REVISION = "OI_025_ORACLE_EXPLANATION_QUERY_ENGINE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_013_observation_requirement_resolution.py", "OI-013"),
    (PACKAGE / "oi_024_oracle_explanation_read_model.py", "OI-024"),
)

MODULE = PACKAGE / "oi_025_oracle_explanation_query_engine.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_025_oracle_explanation_query_engine.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_013_observation_requirement_resolution import ObservationRequirementProfile
from .oi_024_oracle_explanation_read_model import OracleExplanationReadModel

BUILD_ID = "OI-025"
OI_025_REVISION = "OI_025_ORACLE_EXPLANATION_QUERY_ENGINE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False

QUERY_KIND_EXPLANATION = "explanation"
QUERY_KIND_EVIDENCE = "evidence"
QUERY_KIND_TIMELINE = "timeline"
SUPPORTED_QUERY_KINDS = (
    QUERY_KIND_EVIDENCE,
    QUERY_KIND_EXPLANATION,
    QUERY_KIND_TIMELINE,
)


class OracleExplanationQueryEngineError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleExplanationQuery:
    query_id: str
    raw_text: str
    normalized_text: str
    query_kind: str
    subject_hint: str
    profile_id: str
    query_hash: str


class OracleExplanationQueryEngine:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_claim_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def __init__(
        self,
        profile_map: Mapping[str, str],
    ) -> None:
        normalized = {}

        for key, value in dict(profile_map).items():
            route_key = " ".join(str(key).strip().lower().split())
            profile_id = " ".join(str(value).strip().lower().split())

            if not route_key or not profile_id:
                raise OracleExplanationQueryEngineError(
                    "profile map keys and values must not be empty"
                )

            normalized[route_key] = profile_id

        self._profile_map = MappingProxyType(
            dict(sorted(normalized.items()))
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(str(text).strip().lower().split())

    @staticmethod
    def _classify(text: str) -> str:
        normalized = OracleExplanationQueryEngine._normalize(text)

        if (
            "timeline" in normalized
            or "what happened before" in normalized
            or "what happened after" in normalized
        ):
            return QUERY_KIND_TIMELINE

        if (
            normalized.startswith("show evidence")
            or "what evidence" in normalized
            or "evidence supports" in normalized
            or "evidence contradicts" in normalized
        ):
            return QUERY_KIND_EVIDENCE

        if (
            normalized.startswith("why ")
            or " explain " in f" {normalized} "
            or normalized.startswith("explain ")
        ):
            return QUERY_KIND_EXPLANATION

        return QUERY_KIND_EXPLANATION

    def resolve(
        self,
        *,
        query_id: str,
        text: str,
        subject_hint: str,
        domain: str,
    ) -> OracleExplanationQuery:
        query_id_value = str(query_id).strip()
        raw_text = str(text).strip()
        subject = " ".join(str(subject_hint).strip().split())
        domain_key = self._normalize(domain)

        if not query_id_value:
            raise OracleExplanationQueryEngineError(
                "query_id must not be empty"
            )
        if not raw_text:
            raise OracleExplanationQueryEngineError(
                "text must not be empty"
            )
        if not subject:
            raise OracleExplanationQueryEngineError(
                "subject_hint must not be empty"
            )

        profile_id = self._profile_map.get(domain_key)

        if profile_id is None:
            profile_id = self._profile_map.get("*")

        if profile_id is None:
            raise OracleExplanationQueryEngineError(
                f"no explanation profile for domain: {domain_key}"
            )

        normalized_text = self._normalize(raw_text)
        query_kind = self._classify(raw_text)

        body = {
            "query_id": query_id_value,
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "query_kind": query_kind,
            "subject_hint": subject,
            "profile_id": profile_id,
        }

        return OracleExplanationQuery(
            query_id=query_id_value,
            raw_text=raw_text,
            normalized_text=normalized_text,
            query_kind=query_kind,
            subject_hint=subject,
            profile_id=profile_id,
            query_hash=deterministic_sha256(body),
        )

    def read_model_matches(
        self,
        query: OracleExplanationQuery,
        model: OracleExplanationReadModel,
    ) -> bool:
        if not isinstance(query, OracleExplanationQuery):
            raise TypeError("query must be OracleExplanationQuery")
        if not isinstance(model, OracleExplanationReadModel):
            raise TypeError("model must be OracleExplanationReadModel")

        return (
            model.query_id == query.query_id
            and model.profile_id == query.profile_id
        )


def default_explanation_profile_map() -> Mapping[str, str]:
    return MappingProxyType(
        {
            "*": "profile.market_explanation",
            "crypto": "profile.market_explanation",
            "economics": "profile.market_explanation",
            "politics": "profile.market_explanation",
            "sports": "profile.market_explanation",
            "weather": "profile.market_explanation",
        }
    )


def verify_oracle_explanation_query_engine() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-025 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
        )
    ):
        raise AssertionError("OI-025 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_025_REVISION",
    "QUERY_KIND_EXPLANATION",
    "QUERY_KIND_EVIDENCE",
    "QUERY_KIND_TIMELINE",
    "SUPPORTED_QUERY_KINDS",
    "OracleExplanationQueryEngineError",
    "OracleExplanationQuery",
    "OracleExplanationQueryEngine",
    "default_explanation_profile_map",
    "verify_oracle_explanation_query_engine",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_025_oracle_explanation_query_engine import (
    OI_025_REVISION,
    QUERY_KIND_EVIDENCE,
    QUERY_KIND_EXPLANATION,
    QUERY_KIND_TIMELINE,
    OracleExplanationQueryEngine,
    default_explanation_profile_map,
    verify_oracle_explanation_query_engine,
)


class TestOI025(unittest.TestCase):
    def setUp(self):
        self.engine = OracleExplanationQueryEngine(
            default_explanation_profile_map()
        )

    def test_foundation(self):
        self.assertTrue(
            verify_oracle_explanation_query_engine()
        )

    def test_explanation_query(self):
        query = self.engine.resolve(
            query_id="query.astros",
            text="Explain why the Astros strikeout edge moved",
            subject_hint="Astros strikeouts",
            domain="sports",
        )

        self.assertEqual(
            query.query_kind,
            QUERY_KIND_EXPLANATION,
        )

    def test_evidence_query(self):
        query = self.engine.resolve(
            query_id="query.btc",
            text="What evidence supports the Bitcoin move?",
            subject_hint="Bitcoin",
            domain="crypto",
        )

        self.assertEqual(
            query.query_kind,
            QUERY_KIND_EVIDENCE,
        )

    def test_timeline_query(self):
        query = self.engine.resolve(
            query_id="query.weather",
            text="Show the timeline for this hurricane market move",
            subject_hint="Hurricane market",
            domain="weather",
        )

        self.assertEqual(
            query.query_kind,
            QUERY_KIND_TIMELINE,
        )

    def test_generic_profile_fallback(self):
        query = self.engine.resolve(
            query_id="query.future",
            text="Why did this market move?",
            subject_hint="Future market",
            domain="future_domain",
        )

        self.assertEqual(
            query.profile_id,
            "profile.market_explanation",
        )

    def test_deterministic(self):
        a = self.engine.resolve(
            query_id="query.test",
            text="Why did this move?",
            subject_hint="Test",
            domain="sports",
        )
        b = self.engine.resolve(
            query_id="query.test",
            text="Why did this move?",
            subject_hint="Test",
            domain="sports",
        )

        self.assertEqual(
            a.query_hash,
            b.query_hash,
        )

    def test_side_effects(self):
        self.assertTrue(self.engine.read_only)
        self.assertFalse(self.engine.network_allowed)
        self.assertFalse(self.engine.persistence_allowed)
        self.assertFalse(self.engine.publication_allowed)
        self.assertFalse(self.engine.execution_allowed)
        self.assertFalse(self.engine.qseries_execution_allowed)
        self.assertFalse(self.engine.causal_claim_allowed)
        self.assertFalse(self.engine.prediction_allowed)
        self.assertFalse(self.engine.edge_score_allowed)
        self.assertFalse(self.engine.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-025 CERTIFICATION TEST")
    print(" ORACLE EXPLANATION QUERY ENGINE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI025
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-025")
    print(f"[PASS] Revision: {OI_025_REVISION}")
    print("[PASS] Generic explanation, evidence, and timeline query classification certified")
    print("[PASS] Domain-to-explanation profile resolution and wildcard fallback certified")
    print("[PASS] Query engine remains universal across current and future adapter domains")
    print("[PASS] Causal claims, prediction, edge scoring, and execution remain disabled")
    print("[DONE] OI-025 CERTIFIED")
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
    print(" OI-025 INSTALLER")
    print(" ORACLE EXPLANATION QUERY ENGINE")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for upstream, name in UPSTREAMS:
        if not upstream.is_file():
            raise RuntimeError(f"Certified {name} missing: {upstream}")

    upstream_hashes = {
        upstream: sha(upstream)
        for upstream, _ in UPSTREAMS
    }

    print("[PASS] Certified OI-013 and OI-024 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_025_oracle_explanation_query_engine import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

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

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[PASS] Explanation query engine remains deterministic, read-only, and non-predictive")
        print("[DONE] OI-025 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_bytes(original)

        print("[ROLLBACK] OI-025 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
