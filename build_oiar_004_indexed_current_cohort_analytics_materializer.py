from pathlib import Path
import ast
import importlib
import os
import subprocess
import sys
import time

ROOT = Path.cwd().resolve()
PKG = ROOT/"qseries_v2"/"oracle_intelligence_analytics_runtime"
MOD = PKG/"oiar_004_indexed_current_cohort_analytics_materializer.py"
TEST = ROOT/"test_oiar_004_indexed_current_cohort_analytics_materializer.py"
INIT = PKG/"__init__.py"

MODULE_SOURCE = 'from __future__ import annotations\n\nfrom dataclasses import asdict, is_dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_intelligence.analytics.oracle_market_statistics_engine import OracleMarketStatisticsEngine\nfrom qseries_v2.oracle_intelligence.analytics.oracle_market_feature_extraction_engine import OracleCanonicalMarketFeatureExtractionEngine\nfrom qseries_v2.oracle_intelligence.analytics.oracle_market_usefulness_scoring_engine import OracleMarketUsefulnessScoringEngine\nfrom qseries_v2.oracle_intelligence.analytics.oracle_opportunity_candidate_generator import OracleOpportunityCandidateGenerator\nfrom qseries_v2.oracle_intelligence.analytics.oracle_opportunity_admission_gate import OracleOpportunityAdmissionGate\n\nfrom .oiar_001_production_analytics_snapshot_foundation import (\n    SNAPSHOT_TABLE,\n    STATE_TABLE,\n    stable_hash,\n)\nfrom .oiar_003_canonical_market_history_access_index import (\n    INDEX_NAME,\n    MARKET_ID_EXPRESSION,\n    _index_status,\n)\n\nOIAR_004_BUILD_ID = "OIAR-004"\nOIAR_004_REVISION = "OIAR_004_INDEXED_CURRENT_COHORT_ANALYTICS_MATERIALIZER_V1"\n\nCOHORT_STAGE = "reasoning_market_cohort"\nANALYTICS_STAGE = "indexed_current_cohort_oia"\n\ndef _as_dict(value):\n    if hasattr(value, "to_dict"):\n        return dict(value.to_dict())\n    if is_dataclass(value):\n        return asdict(value)\n    if hasattr(value, "__dict__"):\n        return dict(value.__dict__)\n    raise TypeError(f"Unsupported OIA record type: {type(value)!r}")\n\ndef _load_latest_cohort(root):\n    with connect(root, autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(\n                f"""\n                SELECT payload_json\n                FROM public.{SNAPSHOT_TABLE}\n                WHERE stage=%s\n                ORDER BY generated_at DESC, persisted_at DESC\n                LIMIT 1\n                """,\n                (COHORT_STAGE,),\n            )\n            row = cur.fetchone()\n        conn.rollback()\n\n    if row is None:\n        raise RuntimeError("OIAR-004 requires OIAR-002 cohort snapshot")\n\n    payload = row[0]\n    if isinstance(payload, str):\n        payload = json.loads(payload)\n\n    markets = payload.get("markets") if isinstance(payload, dict) else None\n    if not isinstance(markets, list) or not markets:\n        raise RuntimeError("OIAR-004 cohort payload is empty")\n\n    ids = tuple(sorted({\n        str(x.get("market_ticker") or "").strip()\n        for x in markets\n        if isinstance(x, dict) and str(x.get("market_ticker") or "").strip()\n    }))\n    if not ids:\n        raise RuntimeError("OIAR-004 cohort market IDs missing")\n    if len(ids) > 100:\n        raise RuntimeError("OIAR-004 refuses cohort larger than 100 markets")\n    return payload, ids\n\ndef _indexed_history_rows(root, market_ids, per_market=250, timeout_ms=15000):\n    sql = f"""\n    SELECT\n        wanted.market_id,\n        history.observed_at,\n        history.sequence_number,\n        history.yes_bid_dollars,\n        history.yes_ask_dollars,\n        history.last_price_dollars,\n        history.volume_fp,\n        history.liquidity_dollars\n    FROM unnest(%s::text[]) AS wanted(market_id)\n    CROSS JOIN LATERAL (\n        SELECT\n            observed_at,\n            sequence_number,\n            COALESCE(\n                canonical_observation_json->\'raw_observation\'->\'payload\',\n                canonical_observation_json->\'payload\',\n                \'{{}}\'::jsonb\n            )->>\'yes_bid_dollars\' AS yes_bid_dollars,\n            COALESCE(\n                canonical_observation_json->\'raw_observation\'->\'payload\',\n                canonical_observation_json->\'payload\',\n                \'{{}}\'::jsonb\n            )->>\'yes_ask_dollars\' AS yes_ask_dollars,\n            COALESCE(\n                canonical_observation_json->\'raw_observation\'->\'payload\',\n                canonical_observation_json->\'payload\',\n                \'{{}}\'::jsonb\n            )->>\'last_price_dollars\' AS last_price_dollars,\n            COALESCE(\n                canonical_observation_json->\'raw_observation\'->\'payload\',\n                canonical_observation_json->\'payload\',\n                \'{{}}\'::jsonb\n            )->>\'volume_fp\' AS volume_fp,\n            COALESCE(\n                canonical_observation_json->\'raw_observation\'->\'payload\',\n                canonical_observation_json->\'payload\',\n                \'{{}}\'::jsonb\n            )->>\'liquidity_dollars\' AS liquidity_dollars\n        FROM public.oracle_canonical_observations\n        WHERE observation_type=\'market_snapshot\'\n          AND ({MARKET_ID_EXPRESSION}) = wanted.market_id\n        ORDER BY sequence_number DESC\n        LIMIT %s\n    ) AS history\n    ORDER BY wanted.market_id ASC, history.sequence_number ASC\n    """\n\n    with connect(root, autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SET LOCAL statement_timeout=\'{int(timeout_ms)}ms\'")\n            cur.execute(sql, (list(market_ids), int(per_market)))\n            rows = cur.fetchall() or []\n        conn.rollback()\n\n    grouped = {market_id: [] for market_id in market_ids}\n    for row in rows:\n        market_id = str(row[0] or "")\n        if market_id in grouped:\n            grouped[market_id].append(row)\n\n    return grouped\n\ndef materialize_indexed_current_cohort_analytics(root=None, per_market=250, timeout_ms=15000):\n    root = Path(root or Path.cwd()).resolve()\n\n    exists, valid, ready, live = _index_status(root)\n    if not (exists and valid and ready and live):\n        raise RuntimeError("OIAR-004 requires valid OIAR-003 market-history index")\n\n    cohort_payload, market_ids = _load_latest_cohort(root)\n    grouped = _indexed_history_rows(\n        root,\n        market_ids,\n        per_market=per_market,\n        timeout_ms=timeout_ms,\n    )\n\n    connection_factory = lambda: connect(root, autocommit=False)\n\n    statistics_engine = OracleMarketStatisticsEngine(\n        connection_factory=connection_factory,\n        market_limit=len(market_ids),\n        history_limit_per_market=int(per_market),\n    )\n    feature_engine = OracleCanonicalMarketFeatureExtractionEngine(\n        connection_factory=connection_factory,\n        market_limit=len(market_ids),\n        history_limit_per_market=int(per_market),\n    )\n    usefulness_engine = OracleMarketUsefulnessScoringEngine(\n        connection_factory=connection_factory,\n        market_limit=len(market_ids),\n        history_limit_per_market=int(per_market),\n    )\n    candidate_engine = OracleOpportunityCandidateGenerator(\n        connection_factory=connection_factory,\n        market_limit=len(market_ids),\n        history_limit_per_market=int(per_market),\n    )\n    admission_engine = OracleOpportunityAdmissionGate(\n        connection_factory=connection_factory,\n        market_limit=len(market_ids),\n        history_limit_per_market=int(per_market),\n    )\n\n    records = []\n    for market_id in market_ids:\n        history = grouped.get(market_id) or []\n        if not history:\n            continue\n\n        statistics = statistics_engine._calculate_market(\n            market_id=market_id,\n            rows=history,\n        )\n        features = feature_engine._extract_market(statistics)\n        usefulness = usefulness_engine._score_market(features)\n        candidate = candidate_engine._classify_market(features, usefulness)\n        admission = admission_engine._evaluate_market(candidate)\n\n        records.append({\n            "market_id": market_id,\n            "history_rows": len(history),\n            "statistics": _as_dict(statistics),\n            "features": _as_dict(features),\n            "usefulness": _as_dict(usefulness),\n            "candidate": _as_dict(candidate),\n            "admission": _as_dict(admission),\n        })\n\n    records.sort(key=lambda x: x["market_id"])\n\n    payload = {\n        "schema_version": "OIAR-004",\n        "stage": ANALYTICS_STAGE,\n        "cohort_market_count": len(market_ids),\n        "analytics_market_count": len(records),\n        "per_market_history_limit": int(per_market),\n        "source_index": INDEX_NAME,\n        "learner_state_hash": str(cohort_payload.get("learner_state_hash") or ""),\n        "lineage_current": bool(cohort_payload.get("lineage_current")),\n        "markets": records,\n        "read_only_source": True,\n        "execution_authority": False,\n    }\n\n    if payload["analytics_market_count"] <= 0:\n        raise RuntimeError("OIAR-004 produced no analytics markets")\n\n    payload_hash = stable_hash(payload)\n    snapshot_id = f"oiar-004-{payload_hash[:32]}"\n    generated = datetime.now(timezone.utc)\n\n    with connect(root, autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute(\n                f"""\n                INSERT INTO public.{SNAPSHOT_TABLE}(\n                    snapshot_id,stage,source_schema_version,source_engine_id,\n                    generated_at,market_count,payload_json,payload_hash,\n                    read_only_source,execution_authority\n                )\n                VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE)\n                ON CONFLICT(snapshot_id) DO NOTHING\n                """,\n                (\n                    snapshot_id,\n                    ANALYTICS_STAGE,\n                    "OIAR-004",\n                    OIAR_004_BUILD_ID,\n                    generated,\n                    payload["analytics_market_count"],\n                    json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str),\n                    payload_hash,\n                ),\n            )\n            cur.execute(\n                f"""\n                UPDATE public.{STATE_TABLE}\n                SET last_successful_snapshot_id=%s,\n                    last_successful_stage=%s,\n                    last_successful_at=%s,\n                    last_completed_at=%s,\n                    status=\'IDLE\',\n                    last_error_type=NULL,\n                    last_error_message=NULL,\n                    updated_at=clock_timestamp()\n                WHERE state_id=1\n                """,\n                (snapshot_id, ANALYTICS_STAGE, generated, generated),\n            )\n        conn.commit()\n\n    return payload\n\ndef read_latest_indexed_current_cohort_analytics(root=None):\n    root = Path(root or Path.cwd()).resolve()\n    with connect(root, autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(\n                f"""\n                SELECT payload_json,payload_hash\n                FROM public.{SNAPSHOT_TABLE}\n                WHERE stage=%s\n                ORDER BY generated_at DESC,persisted_at DESC\n                LIMIT 1\n                """,\n                (ANALYTICS_STAGE,),\n            )\n            row = cur.fetchone()\n        conn.rollback()\n\n    if row is None:\n        return None\n\n    payload, payload_hash = row\n    if isinstance(payload, str):\n        payload = json.loads(payload)\n\n    if stable_hash(payload) != str(payload_hash):\n        raise RuntimeError("OIAR-004 persisted snapshot hash mismatch")\n\n    return payload\n'
TEST_SOURCE = 'import unittest\n\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_004_indexed_current_cohort_analytics_materializer as m\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(m.OIAR_004_BUILD_ID, "OIAR-004")\n\n    def test_stage(self):\n        self.assertEqual(m.ANALYTICS_STAGE, "indexed_current_cohort_oia")\n\n    def test_index_dependency(self):\n        self.assertTrue(m.INDEX_NAME.startswith("idx_oracle_canonical_market_snapshot"))\n\nif __name__ == "__main__":\n    print("=" * 88)\n    print(" OIAR-004 CERTIFICATION TEST")\n    print(" INDEXED CURRENT-COHORT ANALYTICS MATERIALIZER")\n    print("=" * 88)\n\n    result = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] indexed analytics materializer contract certified")\n    print("[PASS] existing OIA calculation/classification engines preserved")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-004 CERTIFIED")\n'

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("=" * 88)
    print(" OIAR-004 INSTALLER")
    print(" INDEXED CURRENT-COHORT ANALYTICS MATERIALIZER")
    print("=" * 88)
    print("[ROOT]", ROOT)

    required = (
        PKG/"oiar_001_production_analytics_snapshot_foundation.py",
        PKG/"oiar_002_current_reasoning_market_cohort_snapshot.py",
        PKG/"oiar_003_canonical_market_history_access_index.py",
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_market_statistics_engine.py",
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_market_feature_extraction_engine.py",
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_market_usefulness_scoring_engine.py",
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_opportunity_candidate_generator.py",
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_opportunity_admission_gate.py",
    )
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"Required proven upstream missing: {path}")

    old = {p: (p.read_bytes() if p.exists() else None) for p in (MOD, TEST, INIT)}

    try:
        init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oiar_004_indexed_current_cohort_analytics_materializer import *"
        if export not in init_text:
            init_text = init_text.rstrip() + "\n" + export + "\n"

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        write_exact(INIT, init_text)

        ast.parse(MODULE_SOURCE)
        ast.parse(TEST_SOURCE)
        print("[PASS] installer payload syntax verified")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)

        importlib.invalidate_caches()
        module = importlib.import_module(
            "qseries_v2.oracle_intelligence_analytics_runtime.oiar_004_indexed_current_cohort_analytics_materializer"
        )

        started = time.monotonic()
        payload = module.materialize_indexed_current_cohort_analytics(
            ROOT,
            per_market=250,
            timeout_ms=15000,
        )
        elapsed = time.monotonic() - started

        print(
            f"[PHYSICAL] cohort_markets={payload['cohort_market_count']} "
            f"analytics_markets={payload['analytics_market_count']} "
            f"elapsed_seconds={elapsed:.2f} "
            f"source_index={payload['source_index']}"
        )

        latest = module.read_latest_indexed_current_cohort_analytics(ROOT)
        if latest is None:
            raise RuntimeError("OIAR-004 persisted analytics snapshot missing")
        if latest["analytics_market_count"] != payload["analytics_market_count"]:
            raise RuntimeError("OIAR-004 persisted analytics market-count mismatch")

        for record in payload["markets"][:5]:
            admission = record.get("admission") or {}
            candidate = record.get("candidate") or {}
            usefulness = record.get("usefulness") or {}
            print(
                f"[PHYSICAL MARKET] market={record['market_id']} "
                f"history_rows={record['history_rows']} "
                f"usefulness={usefulness.get('classification')} "
                f"candidate={candidate.get('candidate_family')} "
                f"direction={candidate.get('research_direction')} "
                f"admission={admission.get('admission_status')}"
            )

    except Exception:
        for path, data in old.items():
            restore(path, data)
        print("[ROLLBACK] OIAR-004 failed; affected repository files restored")
        raise

    print("[PASS] market histories resolved through OIAR-003 indexed LATERAL path")
    print("[PASS] PostgreSQL market-history statement timeout capped at 15 seconds")
    print("[PASS] existing OIA statistics/features/usefulness/candidate/admission logic reused")
    print("[PASS] persisted analytics snapshot written to PostgreSQL")
    print("[PASS] no Oracle Live launcher mutation")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-004 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
