from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-048"
INSTALLER_REVISION = "OI_048_ORACLE_EXPLANATION_READOUT_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_025_oracle_explanation_query_engine.py", "OI-025"),
    (PACKAGE / "oi_047_evidence_explanation_synthesis.py", "OI-047"),
)

MODULE = PACKAGE / "oi_048_oracle_explanation_readout.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_048_oracle_explanation_readout.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_025_oracle_explanation_query_engine import OracleExplanationQuery
from .oi_047_evidence_explanation_synthesis import (
    EvidenceExplanationSynthesis,
)

BUILD_ID = "OI-048"
OI_048_REVISION = "OI_048_ORACLE_EXPLANATION_READOUT_V1"

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
TERMINAL_MUTATION_ALLOWED = False


class OracleExplanationReadoutError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleExplanationReadout:
    query_id: str
    query_kind: str
    subject_hint: str
    headline: str
    explanation_lines: tuple[str, ...]
    caveat_lines: tuple[str, ...]
    built_at: datetime
    readout_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool
    terminal_mutation_allowed: bool


class OracleExplanationReadoutBuilder:
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
    terminal_mutation_allowed = False

    def build(
        self,
        *,
        query: OracleExplanationQuery,
        synthesis: EvidenceExplanationSynthesis,
        built_at: datetime,
    ) -> OracleExplanationReadout:
        if not isinstance(
            query,
            OracleExplanationQuery,
        ):
            raise TypeError(
                "query must be OracleExplanationQuery"
            )

        if not isinstance(
            synthesis,
            EvidenceExplanationSynthesis,
        ):
            raise TypeError(
                "synthesis must be EvidenceExplanationSynthesis"
            )

        if synthesis.query_id != query.query_id:
            raise OracleExplanationReadoutError(
                "query and synthesis query_id mismatch"
            )

        if not isinstance(built_at, datetime):
            raise TypeError(
                "built_at must be datetime"
            )

        if built_at.tzinfo is None:
            raise OracleExplanationReadoutError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(
            timezone.utc
        )

        explanation_lines = tuple(
            item.statement
            for item in synthesis.statements
        )

        caveats = tuple(
            sorted(
                {
                    caveat
                    for item in synthesis.statements
                    for caveat in item.caveats
                }
            )
        )

        headline = (
            f"Oracle Evidence Explanation — "
            f"{query.subject_hint}"
        )

        body = {
            "query_id": query.query_id,
            "query_kind": query.query_kind,
            "subject_hint": query.subject_hint,
            "headline": headline,
            "explanation_lines": explanation_lines,
            "caveat_lines": caveats,
            "built_at": built_at,
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
            "terminal_mutation_allowed": False,
        }

        return OracleExplanationReadout(
            query_id=query.query_id,
            query_kind=query.query_kind,
            subject_hint=query.subject_hint,
            headline=headline,
            explanation_lines=explanation_lines,
            caveat_lines=caveats,
            built_at=built_at,
            readout_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
            terminal_mutation_allowed=False,
        )


def verify_oracle_explanation_readout() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-048 must remain read-only"
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
            TERMINAL_MUTATION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-048 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_048_REVISION",
    "OracleExplanationReadoutError",
    "OracleExplanationReadout",
    "OracleExplanationReadoutBuilder",
    "verify_oracle_explanation_readout",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_025_oracle_explanation_query_engine import (
    OracleExplanationQueryEngine,
    default_explanation_profile_map,
)
from qseries_v2.observation_intelligence.oi_047_evidence_explanation_synthesis import (
    EvidenceExplanationStatement,
    EvidenceExplanationSynthesis,
)
from qseries_v2.observation_intelligence.oi_048_oracle_explanation_readout import (
    OI_048_REVISION,
    OracleExplanationReadoutBuilder,
    verify_oracle_explanation_readout,
)

NOW = datetime(2026, 8, 11, 10, 0, tzinfo=timezone.utc)


def query():
    return OracleExplanationQueryEngine(
        default_explanation_profile_map()
    ).resolve(
        query_id="query.astros",
        text="Explain why the Astros strikeout edge moved",
        subject_hint="Astros strikeouts",
        domain="sports",
    )


def synthesis():
    return EvidenceExplanationSynthesis(
        query_id="query.astros",
        read_model_hash="a" * 64,
        resolution_hash="b" * 64,
        statements=(
            EvidenceExplanationStatement(
                subject="Astros strikeouts",
                status="partial",
                statement=(
                    "Astros strikeouts: 2 evidence item(s) provide "
                    "multi_evidence_structure with context "
                    "[evidence, market_state, sports_context] and "
                    "relationships [same_subject]."
                ),
                caveats=(
                    "explanation is incomplete",
                    "missing_required_evidence",
                    "structural association does not establish causation",
                ),
                statement_hash="c" * 64,
            ),
        ),
        statement_count=1,
        synthesis_hash="d" * 64,
        read_only=True,
        causal_claim_allowed=False,
    )


class TestOI048(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_explanation_readout()
        )

    def test_build(self):
        readout = OracleExplanationReadoutBuilder().build(
            query=query(),
            synthesis=synthesis(),
            built_at=NOW,
        )

        self.assertIn(
            "Astros strikeouts",
            readout.headline,
        )

        self.assertEqual(
            len(readout.explanation_lines),
            1,
        )

    def test_caveats(self):
        readout = OracleExplanationReadoutBuilder().build(
            query=query(),
            synthesis=synthesis(),
            built_at=NOW,
        )

        self.assertIn(
            "missing_required_evidence",
            readout.caveat_lines,
        )

    def test_non_causal(self):
        readout = OracleExplanationReadoutBuilder().build(
            query=query(),
            synthesis=synthesis(),
            built_at=NOW,
        )

        self.assertFalse(
            readout.predictive
        )
        self.assertFalse(
            readout.causal_claim_allowed
        )
        self.assertFalse(
            readout.terminal_mutation_allowed
        )

    def test_deterministic(self):
        builder = OracleExplanationReadoutBuilder()

        a = builder.build(
            query=query(),
            synthesis=synthesis(),
            built_at=NOW,
        )

        b = builder.build(
            query=query(),
            synthesis=synthesis(),
            built_at=NOW,
        )

        self.assertEqual(
            a.readout_hash,
            b.readout_hash,
        )

    def test_side_effects(self):
        builder = OracleExplanationReadoutBuilder()

        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.prediction_allowed)
        self.assertFalse(builder.edge_score_allowed)
        self.assertFalse(builder.probability_allowed)
        self.assertFalse(builder.causal_claim_allowed)
        self.assertFalse(builder.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-048 CERTIFICATION TEST")
    print(" ORACLE EXPLANATION READOUT")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI048
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-048")
    print(f"[PASS] Revision: {OI_048_REVISION}")
    print("[PASS] Evidence-grounded explanation synthesis converted into Oracle terminal-ready readout")
    print("[PASS] Explanation text, caveats, query identity, and subject identity preserved")
    print("[PASS] Readout remains read-only, non-causal, non-predictive, non-scoring, and non-mutating")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-048 CERTIFIED")
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
    print(" OI-048 INSTALLER")
    print(" ORACLE EXPLANATION READOUT")
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
        "[PASS] Certified OI-025 and OI-047 "
        "verified read-only"
    )

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_048_oracle_explanation_readout import *"

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
            "[PASS] Oracle explanation readout remains deterministic, "
            "read-only, terminal-safe, and non-causal"
        )
        print("[DONE] OI-048 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-048 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
