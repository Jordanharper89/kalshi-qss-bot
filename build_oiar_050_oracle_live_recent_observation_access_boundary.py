from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / "qseries_v2/oracle_intelligence_analytics_runtime/oiar_050_oracle_live_recent_observation_access_boundary.py"
TEST = ROOT / "test_oiar_050_oracle_live_recent_observation_access_boundary.py"
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash\n\nOIAR_050_BUILD_ID = "OIAR-050"\nOIAR_050_REVISION = "OIAR_050_ORACLE_LIVE_RECENT_OBSERVATION_ACCESS_BOUNDARY_V1"\nSTAGE = "oracle_live_recent_observed_market_universe"\nINDEX_NAME = "idx_oracle_canonical_live_recent_seq"\nEXECUTION_AUTHORITY = False\n\ndef index_status(root=None):\n    root = Path(root or Path.cwd()).resolve()\n    with connect(root, autocommit=True) as c:\n        with c.cursor() as cur:\n            cur.execute("""\n                SELECT i.indisvalid, i.indisready, i.indislive\n                FROM pg_index i\n                JOIN pg_class c ON c.oid=i.indexrelid\n                JOIN pg_namespace n ON n.oid=c.relnamespace\n                WHERE n.nspname=\'public\' AND c.relname=%s\n            """, (INDEX_NAME,))\n            row = cur.fetchone()\n    if not row:\n        return (False, False, False, False)\n    return (True, bool(row[0]), bool(row[1]), bool(row[2]))\n\ndef ensure_recent_observation_index(root=None):\n    root = Path(root or Path.cwd()).resolve()\n    before = index_status(root)\n    if all(before):\n        return before, before\n    with connect(root, autocommit=True) as c:\n        with c.cursor() as cur:\n            cur.execute(f"""\n                CREATE INDEX CONCURRENTLY IF NOT EXISTS {INDEX_NAME}\n                ON public.oracle_canonical_observations (sequence_number DESC)\n                WHERE observation_type IN (\'ticker\',\'trade\')\n            """)\n    after = index_status(root)\n    if not all(after):\n        raise RuntimeError("OIAR-050 recent ticker/trade index is not valid/ready/live")\n    return before, after\n\ndef _payload(obj):\n    if not isinstance(obj, dict):\n        return {}\n    raw = obj.get("raw_observation")\n    if isinstance(raw, dict) and isinstance(raw.get("payload"), dict):\n        return raw["payload"]\n    p = obj.get("payload")\n    return p if isinstance(p, dict) else {}\n\ndef _message(payload):\n    m = payload.get("message")\n    return m if isinstance(m, dict) else payload\n\ndef _ticker(payload):\n    m = _message(payload)\n    return str(\n        payload.get("source_market_id")\n        or m.get("market_ticker")\n        or m.get("ticker")\n        or ""\n    ).strip().upper()\n\ndef read_recent_oracle_live_markets(root=None, scan_limit=100000, max_age_seconds=1800):\n    root = Path(root or Path.cwd()).resolve()\n    scan = max(1000, min(int(scan_limit), 250000))\n    now = datetime.now(timezone.utc)\n\n    if not all(index_status(root)):\n        raise RuntimeError("OIAR-050 recent ticker/trade index is not healthy")\n\n    with connect(root, autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute("SET LOCAL statement_timeout=\'5000ms\'")\n            cur.execute(f"""\n                SELECT sequence_number, observation_type, observed_at, canonical_observation_json\n                FROM public.oracle_canonical_observations\n                WHERE observation_type IN (\'ticker\',\'trade\')\n                ORDER BY sequence_number DESC\n                LIMIT %s\n            """, (scan,))\n            rows = cur.fetchall() or []\n        c.rollback()\n\n    by_market = {}\n    for seq, observation_type, observed_at, obj in rows:\n        p = _payload(obj)\n        ticker = _ticker(p)\n        if not ticker:\n            continue\n\n        observed_utc = observed_at.astimezone(timezone.utc)\n        age = max(0.0, (now - observed_utc).total_seconds())\n        if age > float(max_age_seconds):\n            continue\n\n        rec = by_market.setdefault(ticker, {\n            "market_ticker": ticker,\n            "latest_sequence": 0,\n            "latest_observed_at": "",\n            "freshness_seconds": age,\n            "ticker_observations": 0,\n            "trade_observations": 0,\n            "latest_payload": {},\n        })\n\n        if observation_type == "ticker":\n            rec["ticker_observations"] += 1\n        elif observation_type == "trade":\n            rec["trade_observations"] += 1\n\n        if int(seq) > int(rec["latest_sequence"]):\n            rec["latest_sequence"] = int(seq)\n            rec["latest_observed_at"] = observed_utc.isoformat()\n            rec["freshness_seconds"] = age\n            rec["latest_payload"] = p\n\n    markets = sorted(\n        by_market.values(),\n        key=lambda x: (x["freshness_seconds"], -x["latest_sequence"], x["market_ticker"])\n    )\n    if not markets:\n        raise RuntimeError("OIAR-050 found no recent Oracle Live ticker/trade markets")\n\n    return tuple(markets)\n\ndef materialize_recent_observed_market_universe(root=None):\n    root = Path(root or Path.cwd()).resolve()\n    markets = read_recent_oracle_live_markets(root)\n\n    payload = {\n        "schema_version": "OIAR-050",\n        "stage": STAGE,\n        "market_count": len(markets),\n        "markets": list(markets),\n        "read_only_source": True,\n        "execution_authority": False,\n    }\n    h = stable_hash(payload)\n    snapshot_id = "oiar-050-" + h[:32]\n\n    with connect(root, autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute(f"""\n                INSERT INTO public.{SNAPSHOT_TABLE}\n                (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,\n                 market_count,payload_json,payload_hash,read_only_source,execution_authority)\n                VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE)\n                ON CONFLICT(snapshot_id) DO NOTHING\n            """, (\n                snapshot_id, STAGE, "OIAR-050", OIAR_050_BUILD_ID,\n                len(markets), json.dumps(payload, sort_keys=True, default=str), h\n            ))\n        c.commit()\n\n    return snapshot_id, payload\n\ndef physical_probe(root=None):\n    snapshot_id, payload = materialize_recent_observed_market_universe(root)\n    return {\n        "snapshot_id": snapshot_id,\n        "observed_markets": payload["market_count"],\n        "ticker_markets": sum(x["ticker_observations"] > 0 for x in payload["markets"]),\n        "trade_markets": sum(x["trade_observations"] > 0 for x in payload["markets"]),\n        "execution_authority": False,\n    }\n'
TEST_SOURCE = '\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_050_oracle_live_recent_observation_access_boundary as m\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(m.OIAR_050_BUILD_ID, "OIAR-050")\n\n    def test_stage(self):\n        self.assertEqual(m.STAGE, "oracle_live_recent_observed_market_universe")\n\n    def test_index_contract(self):\n        self.assertEqual(m.INDEX_NAME, "idx_oracle_canonical_live_recent_seq")\n\n    def test_boundary(self):\n        self.assertFalse(m.EXECUTION_AUTHORITY)\n\nif __name__ == "__main__":\n    print("="*88)\n    print(" OIAR-050 CERTIFICATION TEST")\n    print(" ORACLE LIVE RECENT OBSERVATION ACCESS BOUNDARY")\n    print("="*88)\n    r = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] indexed recent ticker/trade access contract certified")\n'

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def main():
    print("="*88)
    print(" OIAR-050 INSTALLER")
    print(" ORACLE LIVE RECENT OBSERVATION ACCESS BOUNDARY")
    print("="*88)
    print("[ROOT]", ROOT)

    required = [
        ROOT / "qseries_v2/oracle_intelligence_analytics_runtime/oiar_001_production_analytics_snapshot_foundation.py",
        ROOT / "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
    ]
    for p in required:
        if not p.is_file():
            raise RuntimeError(f"Required proven upstream missing: {p}")

    old_mod = MOD.read_bytes() if MOD.exists() else None
    old_test = TEST.read_bytes() if TEST.exists() else None
    created_index = False

    try:
        ast.parse(MODULE_SOURCE, filename=str(MOD))
        ast.parse(TEST_SOURCE, filename=str(TEST))
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True, timeout=30)

        importlib.invalidate_caches()
        m = importlib.import_module(
            "qseries_v2.oracle_intelligence_analytics_runtime.oiar_050_oracle_live_recent_observation_access_boundary"
        )

        before = m.index_status(ROOT)
        print("[INDEX BEFORE]", before)

        started = time.monotonic()
        _, after = m.ensure_recent_observation_index(ROOT)
        created_index = not before[0]
        print("[INDEX AFTER]", after, "elapsed_seconds=", round(time.monotonic()-started, 2))

        if not all(after):
            raise RuntimeError("OIAR-050 recent observation index unhealthy")

        started = time.monotonic()
        x = m.physical_probe(ROOT)
        print("[PHYSICAL]", x, "elapsed_seconds=", round(time.monotonic()-started, 3))

        if x["observed_markets"] <= 0:
            raise RuntimeError("OIAR-050 observed universe empty")

    except Exception:
        if created_index:
            try:
                importlib.invalidate_caches()
                m = importlib.import_module(
                    "qseries_v2.oracle_intelligence_analytics_runtime.oiar_050_oracle_live_recent_observation_access_boundary"
                )
                from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
                with connect(ROOT, autocommit=True) as c:
                    with c.cursor() as cur:
                        cur.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {m.INDEX_NAME}")
            except Exception:
                pass
        restore(MOD, old_mod)
        restore(TEST, old_test)
        print("[ROLLBACK] OIAR-050 failed; affected repository files restored")
        raise

    print("[PASS] Oracle Live remains unmodified")
    print("[PASS] recent ticker/trade market universe physically readable")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-050 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
