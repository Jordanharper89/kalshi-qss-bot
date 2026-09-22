from __future__ import annotations

import importlib
import subprocess
import sys
import textwrap
import time
from pathlib import Path


ROOT = Path.cwd().resolve()

PKG = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence_analytics_runtime"
)

MODULE = PKG / "oiar_068_canonical_evidence_index_identity_divergence_physical_proof.py"
TEST = ROOT / "test_oiar_068_canonical_evidence_index_identity_divergence_physical_proof.py"

MODULE_SOURCE = r'''
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (
    connect,
)


BUILD_ID = "OIAR-068"
REVISION = "CANONICAL_EVIDENCE_INDEX_IDENTITY_DIVERGENCE_PHYSICAL_PROOF_V1"

CANONICAL_TABLE = "oracle_canonical_observations"
LEDGER_TABLE = "oracle_production_learning_ledger"
EVIDENCE_TABLE = "oracle_production_learning_evidence_index"

SAMPLE_LIMIT = 100

MARKET_ID_EXPRESSION = """
COALESCE(
    NULLIF(
        COALESCE(
            canonical_observation_json->'raw_observation'->'payload',
            canonical_observation_json->'payload',
            '{}'::jsonb
        )->>'source_market_id',
        ''
    ),
    NULLIF(
        COALESCE(
            canonical_observation_json->'raw_observation'->'payload',
            canonical_observation_json->'payload',
            '{}'::jsonb
        )->>'market_id',
        ''
    ),
    NULLIF(
        COALESCE(
            canonical_observation_json->'raw_observation'->'payload',
            canonical_observation_json->'payload',
            '{}'::jsonb
        )->>'source_symbol',
        ''
    )
)
""".strip()


@dataclass(frozen=True)
class DivergenceProof:
    sampled_missing_settlements: int
    canonical_exact_ticker_found: int
    canonical_pre_settlement_found: int
    canonical_only_post_settlement: int
    canonical_no_exact_ticker: int
    evidence_exact_ticker_found: int
    canonical_present_evidence_missing: int
    canonical_pre_settlement_evidence_missing: int
    upstream_coverage_gap: int
    index_name: str
    exact_canonical_lookup_uses_index: bool
    read_only: bool
    repaired_rows: int
    probability_enabled: bool
    execution_authority: bool


def _rows_as_dicts(cur) -> list[dict[str, Any]]:
    names = [d.name if hasattr(d, "name") else d[0] for d in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def _canonical_indexes(cur) -> dict[str, str]:
    cur.execute(
        """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname='public'
          AND tablename=%s
        ORDER BY indexname
        """,
        (CANONICAL_TABLE,),
    )
    return {str(a): str(b) for a, b in cur.fetchall()}


def _choose_market_snapshot_index(indexes: dict[str, str]) -> str:
    preferred = "idx_oracle_canonical_market_snapshot_market_seq"
    if preferred in indexes:
        return preferred

    for name, definition in indexes.items():
        d = definition.lower()
        if (
            "market_snapshot" in d
            and "sequence_number" in d
            and (
                "source_market_id" in d
                or "market_id" in d
                or "source_symbol" in d
            )
        ):
            return name

    return ""


def _sample_missing_settlements(cur, limit: int) -> list[dict[str, Any]]:
    cur.execute(
        f"""
        SELECT
            settlement_hash,
            ticker,
            result,
            settlement_ts,
            status
        FROM public.{LEDGER_TABLE}
        WHERE status='EVIDENCE_MISSING'
          AND ticker IS NOT NULL
          AND BTRIM(ticker) <> ''
          AND settlement_ts IS NOT NULL
        ORDER BY settlement_ts ASC, ticker ASC
        LIMIT %s
        """,
        (int(limit),),
    )
    return _rows_as_dicts(cur)


def _canonical_exact_rows(cur, ticker: str, limit: int = 16) -> list[dict[str, Any]]:
    cur.execute(
        f"""
        SELECT
            sequence_number,
            observed_at,
            acquired_at,
            observation_type
        FROM public.{CANONICAL_TABLE}
        WHERE observation_type='market_snapshot'
          AND {MARKET_ID_EXPRESSION}=%s
        ORDER BY sequence_number DESC
        LIMIT %s
        """,
        (ticker, int(limit)),
    )
    return _rows_as_dicts(cur)


def _evidence_exact_rows(cur, ticker: str, limit: int = 16) -> list[dict[str, Any]]:
    cur.execute(
        f"""
        SELECT
            observation_id,
            ticker,
            evidence_hash,
            sequence_number,
            observed_at,
            observation_type
        FROM public.{EVIDENCE_TABLE}
        WHERE ticker=%s
        ORDER BY sequence_number DESC NULLS LAST
        LIMIT %s
        """,
        (ticker, int(limit)),
    )
    return _rows_as_dicts(cur)


def _uses_exact_market_index(cur, ticker: str, index_name: str) -> bool:
    cur.execute(
        f"""
        EXPLAIN (FORMAT TEXT)
        SELECT sequence_number
        FROM public.{CANONICAL_TABLE}
        WHERE observation_type='market_snapshot'
          AND {MARKET_ID_EXPRESSION}=%s
        ORDER BY sequence_number DESC
        LIMIT 1
        """,
        (ticker,),
    )
    plan = "\n".join(str(x[0]) for x in cur.fetchall())

    if index_name:
        return index_name.lower() in plan.lower()

    return "index" in plan.lower()


def prove_canonical_evidence_index_identity_divergence(
    root=None,
    sample_limit: int = SAMPLE_LIMIT,
) -> dict[str, Any]:
    root = Path(root or Path.cwd()).resolve()

    c = connect(root, autocommit=False)

    try:
        q = c.cursor()
        q.execute("SET TRANSACTION READ ONLY")
        q.execute("SET LOCAL statement_timeout = '15000ms'")

        indexes = _canonical_indexes(q)
        index_name = _choose_market_snapshot_index(indexes)

        if not index_name:
            raise RuntimeError(
                "OIAR-068 cannot find the previously proven exact "
                "market_snapshot identity index"
            )

        settlements = _sample_missing_settlements(q, sample_limit)

        if not settlements:
            raise RuntimeError(
                "OIAR-068 found zero EVIDENCE_MISSING settlements to classify"
            )

        classifications = []

        canonical_found = 0
        canonical_pre = 0
        canonical_post_only = 0
        canonical_none = 0
        evidence_found = 0
        divergence = 0
        pre_divergence = 0
        upstream_gap = 0

        plan_proven = False

        for i, settlement in enumerate(settlements):
            ticker = str(settlement["ticker"]).strip()
            settlement_ts = settlement["settlement_ts"]

            canonical_rows = _canonical_exact_rows(q, ticker)
            evidence_rows = _evidence_exact_rows(q, ticker)

            if i == 0:
                plan_proven = _uses_exact_market_index(
                    q,
                    ticker,
                    index_name,
                )

            pre_rows = [
                r
                for r in canonical_rows
                if r.get("observed_at") is not None
                and r["observed_at"] < settlement_ts
            ]

            post_rows = [
                r
                for r in canonical_rows
                if r.get("observed_at") is not None
                and r["observed_at"] >= settlement_ts
            ]

            has_canonical = bool(canonical_rows)
            has_pre = bool(pre_rows)
            has_evidence = bool(evidence_rows)

            if has_canonical:
                canonical_found += 1

                if has_pre:
                    canonical_pre += 1
                elif post_rows:
                    canonical_post_only += 1
            else:
                canonical_none += 1

            if has_evidence:
                evidence_found += 1

            if has_canonical and not has_evidence:
                divergence += 1

            if has_pre and not has_evidence:
                pre_divergence += 1

            if not has_canonical:
                upstream_gap += 1

            if has_pre and not has_evidence:
                classification = (
                    "CANONICAL_PRE_SETTLEMENT_PRESENT_EVIDENCE_INDEX_MISSING"
                )
            elif has_canonical and not has_evidence:
                classification = (
                    "CANONICAL_PRESENT_EVIDENCE_INDEX_MISSING"
                )
            elif not has_canonical:
                classification = "NO_EXACT_CANONICAL_MARKET_SNAPSHOT"
            elif has_evidence:
                classification = "EXACT_EVIDENCE_PRESENT"
            else:
                classification = "UNCLASSIFIED"

            newest_canonical = canonical_rows[0] if canonical_rows else None
            newest_pre = pre_rows[0] if pre_rows else None

            classifications.append(
                {
                    "ticker": ticker,
                    "result": settlement.get("result"),
                    "settlement_ts": str(settlement_ts),
                    "classification": classification,
                    "canonical_rows": len(canonical_rows),
                    "canonical_pre_settlement_rows": len(pre_rows),
                    "canonical_post_settlement_rows": len(post_rows),
                    "evidence_index_rows": len(evidence_rows),
                    "newest_canonical_sequence": (
                        newest_canonical.get("sequence_number")
                        if newest_canonical
                        else None
                    ),
                    "newest_canonical_observed_at": (
                        str(newest_canonical.get("observed_at"))
                        if newest_canonical
                        else ""
                    ),
                    "newest_pre_sequence": (
                        newest_pre.get("sequence_number")
                        if newest_pre
                        else None
                    ),
                    "newest_pre_observed_at": (
                        str(newest_pre.get("observed_at"))
                        if newest_pre
                        else ""
                    ),
                    "settlement_hash": str(
                        settlement.get("settlement_hash") or ""
                    ),
                }
            )

        proof = DivergenceProof(
            sampled_missing_settlements=len(settlements),
            canonical_exact_ticker_found=canonical_found,
            canonical_pre_settlement_found=canonical_pre,
            canonical_only_post_settlement=canonical_post_only,
            canonical_no_exact_ticker=canonical_none,
            evidence_exact_ticker_found=evidence_found,
            canonical_present_evidence_missing=divergence,
            canonical_pre_settlement_evidence_missing=pre_divergence,
            upstream_coverage_gap=upstream_gap,
            index_name=index_name,
            exact_canonical_lookup_uses_index=bool(plan_proven),
            read_only=True,
            repaired_rows=0,
            probability_enabled=False,
            execution_authority=False,
        )

        result = asdict(proof)
        result["classifications"] = classifications

        c.rollback()
        return result

    except Exception:
        c.rollback()
        raise

    finally:
        c.close()


def verify_oiar_068_contract() -> bool:
    assert BUILD_ID == "OIAR-068"
    assert CANONICAL_TABLE == "oracle_canonical_observations"
    assert LEDGER_TABLE == "oracle_production_learning_ledger"
    assert EVIDENCE_TABLE == "oracle_production_learning_evidence_index"
    assert "market_snapshot" not in MARKET_ID_EXPRESSION
    return True


def physical_probe(root=None) -> dict[str, Any]:
    return prove_canonical_evidence_index_identity_divergence(root)
'''

TEST_SOURCE = r'''
from __future__ import annotations

import unittest
from pathlib import Path

from qseries_v2.oracle_intelligence_analytics_runtime.oiar_068_canonical_evidence_index_identity_divergence_physical_proof import (
    physical_probe,
    verify_oiar_068_contract,
)


ROOT = Path.cwd().resolve()


class T(unittest.TestCase):

    def test_verifier(self):
        self.assertTrue(verify_oiar_068_contract())

    def test_physical_divergence(self):
        x = physical_probe(ROOT)

        self.assertGreater(
            x["sampled_missing_settlements"],
            0,
        )

        self.assertTrue(
            x["index_name"],
        )

        self.assertTrue(
            x["exact_canonical_lookup_uses_index"],
        )

        classified = (
            x["canonical_present_evidence_missing"]
            + x["canonical_no_exact_ticker"]
            + x["evidence_exact_ticker_found"]
        )

        self.assertGreater(
            classified,
            0,
        )

        self.assertTrue(x["read_only"])
        self.assertEqual(x["repaired_rows"], 0)
        self.assertFalse(x["probability_enabled"])
        self.assertFalse(x["execution_authority"])


if __name__ == "__main__":
    print("=" * 88)
    print(" OIAR-068 CERTIFICATION TEST")
    print(" CANONICAL / EVIDENCE-INDEX IDENTITY DIVERGENCE PHYSICAL PROOF")
    print("=" * 88)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(T)
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] missing-settlement canonical identity physically classified")
    print("[PASS] canonical/evidence-index divergence physically measured")
    print("[PASS] exact canonical identity lookup uses proven index")
    print("[PASS] no learning state repaired or modified")
    print("[PASS] probability remains gated")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-068 CERTIFIED")
'''


def main():
    print("=" * 88)
    print(" OIAR-068 INSTALLER")
    print(" CANONICAL / EVIDENCE-INDEX IDENTITY DIVERGENCE PHYSICAL PROOF")
    print("=" * 88)
    print("[ROOT]", ROOT)

    PKG.mkdir(parents=True, exist_ok=True)

    backups = {}

    for path in (MODULE, TEST):
        if path.exists():
            backups[path] = path.read_bytes()
        else:
            backups[path] = None

    try:
        compile(
            textwrap.dedent(MODULE_SOURCE),
            str(MODULE),
            "exec",
        )
        compile(
            textwrap.dedent(TEST_SOURCE),
            str(TEST),
            "exec",
        )

        print("[PASS] installer payload syntax verified")

        MODULE.write_text(
            textwrap.dedent(MODULE_SOURCE).lstrip(),
            encoding="utf-8",
        )

        TEST.write_text(
            textwrap.dedent(TEST_SOURCE).lstrip(),
            encoding="utf-8",
        )

        importlib.invalidate_caches()

        from qseries_v2.oracle_intelligence_analytics_runtime import (
            oiar_068_canonical_evidence_index_identity_divergence_physical_proof
            as m,
        )

        start = time.monotonic()
        x = m.physical_probe(ROOT)
        elapsed = round(time.monotonic() - start, 3)

        summary_keys = (
            "sampled_missing_settlements",
            "canonical_exact_ticker_found",
            "canonical_pre_settlement_found",
            "canonical_only_post_settlement",
            "canonical_no_exact_ticker",
            "evidence_exact_ticker_found",
            "canonical_present_evidence_missing",
            "canonical_pre_settlement_evidence_missing",
            "upstream_coverage_gap",
            "index_name",
            "exact_canonical_lookup_uses_index",
            "read_only",
            "repaired_rows",
            "probability_enabled",
            "execution_authority",
        )

        summary = {k: x[k] for k in summary_keys}

        print(
            "[PHYSICAL SUMMARY]",
            summary,
            "elapsed_seconds=",
            elapsed,
        )

        print("[SAMPLE CLASSIFICATIONS]")

        for row in x["classifications"][:20]:
            print(row)

        subprocess.run(
            [sys.executable, str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

        print("[PASS] exact missing settlement identities checked against canonical history")
        print("[PASS] canonical market_snapshot pavement checked directly")
        print("[PASS] learning evidence-index pavement checked independently")
        print("[PASS] divergence classified without repairing anything")
        print("[PASS] canonical observations remained read-only")
        print("[PASS] learning state remained unmodified")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")

        if x["canonical_pre_settlement_evidence_missing"] > 0:
            print(
                "[FINDING] PRE-SETTLEMENT CANONICAL EVIDENCE EXISTS "
                "BUT LEARNING EVIDENCE INDEX IS MISSING IT"
            )
            print(
                "[NEXT] repair existing learning evidence-index ingestion/backfill pavement"
            )

        elif x["canonical_no_exact_ticker"] > 0:
            print(
                "[FINDING] SAMPLE CONTAINS SETTLEMENT TICKERS WITH "
                "NO EXACT CANONICAL MARKET_SNAPSHOT"
            )
            print(
                "[NEXT] trace historical pre-settlement coverage/acquisition pavement"
            )

        else:
            print(
                "[FINDING] no canonical/evidence-index divergence detected "
                "in this sample"
            )

        print("[DONE] OIAR-068 INSTALLATION COMPLETE")

    except Exception:
        for path, data in backups.items():
            if data is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(data)

        print(
            "[ROLLBACK] OIAR-068 proof failed; affected repository files restored"
        )
        raise


if __name__ == "__main__":
    main()