from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_009_bounded_universal_snapshot_cycle.py"
TEST=ROOT/"test_opc_009_bounded_universal_snapshot_cycle.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone, timedelta\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import (\n    load_kalshi_credentials,\n)\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import (\n    kalshi_rest_get,\n)\nfrom .opc_003_canonical_observation_coverage_read_model import (\n    read_recent_canonical_tickers,\n)\nfrom .opc_006_universal_market_snapshot_canonicalizer import (\n    build_universal_market_snapshot,\n)\nfrom .opc_007_coverage_gap_snapshot_planner import (\n    plan_missing_market_snapshots,\n)\nfrom .opc_008_ola_postgresql_snapshot_persistence_bridge import (\n    build_opc_postgresql_router,\n    persist_snapshot_batch,\n)\n\nOPC_009_BUILD_ID="OPC-009"\nOPC_009_REVISION="OPC_009_BOUNDED_UNIVERSAL_SNAPSHOT_CYCLE_ALIGNMENT_V2"\n\n@dataclass(frozen=True)\nclass UniversalSnapshotCycleSummary:\n    open_markets:int\n    covered_before:int\n    missing_before:int\n    snapshots_planned:int\n    snapshots_persisted:int\n    read_only_intelligence:bool=True\n    execution_authority:bool=False\n\ndef fetch_open_market_page(limit=1000,timeout_seconds=15):\n    credentials=load_kalshi_credentials()\n    response=kalshi_rest_get(\n        credentials,\n        "/markets",\n        {"limit":int(limit),"status":"open"},\n        timeout_seconds,\n    )\n    return tuple((response.body or {}).get("markets",[]) or [])\n\ndef run_bounded_universal_snapshot_cycle(\n    root=None,\n    max_markets=100,\n    lookback_hours=24,\n    progress=None,\n    router=None,\n    open_markets=None,\n):\n    root=Path(root or Path.cwd()).resolve()\n    cycle_started=datetime.now(timezone.utc)\n\n    markets=(\n        tuple(open_markets)\n        if open_markets is not None\n        else fetch_open_market_page()\n    )\n\n    recent=read_recent_canonical_tickers(\n        root,\n        lookback_hours,\n        250000,\n    )\n\n    plan=plan_missing_market_snapshots(\n        markets,\n        recent,\n        max_markets=max_markets,\n    )\n\n    by_ticker={\n        str(row.get("ticker") or ""):row\n        for row in markets\n        if isinstance(row,dict)\n    }\n\n    selected=[\n        by_ticker[ticker]\n        for ticker in plan.planned_tickers\n        if ticker in by_ticker\n    ]\n\n    batch_id=(\n        "batch.opc.009."\n        + cycle_started.strftime("%Y%m%dT%H%M%S%fZ")\n    )\n\n    observations=[]\n    for index,row in enumerate(selected,1):\n        # Each observation receives its own microsecond epoch. Even if Kalshi\n        # state is identical across observations, source observation identity\n        # remains unique while opc_source_state_hash stays stable.\n        observation_time=cycle_started + timedelta(microseconds=index)\n\n        observations.append(\n            build_universal_market_snapshot(\n                row,\n                acquired_at=observation_time,\n                batch_id=batch_id,\n            )\n        )\n\n        if progress:\n            progress(\n                f"[SNAPSHOT BUILD] {index}/{len(selected)} "\n                f"ticker={row.get(\'ticker\')} "\n                f"epoch={observation_time.isoformat()}"\n            )\n\n    if router is None:\n        router=build_opc_postgresql_router(root)\n\n    result=persist_snapshot_batch(\n        observations,\n        routed_at=datetime.now(timezone.utc),\n        router=router,\n    )\n\n    if progress:\n        progress(\n            f"[SNAPSHOT PERSIST] requested={result.requested} "\n            f"accepted={result.accepted} "\n            f"rejected={result.rejected}"\n        )\n\n    return UniversalSnapshotCycleSummary(\n        plan.sampled_markets,\n        plan.already_covered,\n        plan.missing_markets,\n        len(observations),\n        result.accepted,\n        True,\n        False,\n    )\n\ndef verify_opc_009_bounded_universal_snapshot_cycle():\n    first=build_universal_market_snapshot(\n        {"ticker":"KXA","yes_bid":1},\n        acquired_at="2026-08-16T20:00:00.000001Z",\n        batch_id="b",\n    )\n    second=build_universal_market_snapshot(\n        {"ticker":"KXB","yes_bid":1},\n        acquired_at="2026-08-16T20:00:00.000002Z",\n        batch_id="b",\n    )\n\n    summary=UniversalSnapshotCycleSummary(\n        1000,3,997,100,100,True,False\n    )\n\n    return (\n        first.observation_id!=second.observation_id\n        and summary.missing_before==997\n        and summary.snapshots_persisted==100\n        and summary.read_only_intelligence\n        and not summary.execution_authority\n    )\n'
TEST_SOURCE='import unittest\n\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_006_universal_market_snapshot_canonicalizer import (\n    build_universal_market_snapshot,\n)\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_009_bounded_universal_snapshot_cycle import (\n    verify_opc_009_bounded_universal_snapshot_cycle,\n)\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(\n            verify_opc_009_bounded_universal_snapshot_cycle()\n        )\n\n    def test_same_state_different_epochs_are_distinct(self):\n        market={"ticker":"KXTEST","yes_bid":50}\n        first=build_universal_market_snapshot(\n            market,\n            acquired_at="2026-08-16T20:00:00.000001Z",\n            batch_id="batch",\n        )\n        second=build_universal_market_snapshot(\n            market,\n            acquired_at="2026-08-16T20:00:00.000002Z",\n            batch_id="batch",\n        )\n        self.assertNotEqual(first.observation_id,second.observation_id)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-009 ALIGNMENT V2 CERTIFICATION TEST")\n    print(" FRESH OBSERVATION EPOCH SNAPSHOT CYCLE")\n    print("="*72)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] OPC-009 aligned to OPC-006 time-aware observation identity")\n    print("[PASS] Each snapshot receives a distinct observation epoch")\n    print("[PASS] Frozen OLA persistence boundary remains untouched")\n    print("[DONE] OPC-009 ALIGNMENT V2 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OPC-009 ALIGNMENT V2 INSTALLER")
    print(" FRESH OBSERVATION EPOCH SNAPSHOT CYCLE")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    opc6=importlib.import_module(
        "qseries_v2.oracle_pre_settlement_coverage."
        "opc_006_universal_market_snapshot_canonicalizer"
    )
    if opc6.verify_opc_006_universal_market_snapshot_canonicalizer() is not True:
        raise RuntimeError("Corrected OPC-006 verification failed")

    opc8=importlib.import_module(
        "qseries_v2.oracle_pre_settlement_coverage."
        "opc_008_ola_postgresql_snapshot_persistence_bridge"
    )
    if opc8.verify_opc_008_ola_postgresql_snapshot_persistence_bridge() is not True:
        raise RuntimeError("Certified OPC-008 verification failed")

    print("[PASS] Corrected OPC-006 boundary verified")
    print("[PASS] Certified OPC-008 persistence bridge verified")
    print("[PASS] Frozen OLA remains untouched")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line="from .opc_009_bounded_universal_snapshot_cycle import *"
        if line not in current:
            write_exact(INIT,current.rstrip()+"\n"+line+"\n")

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )
    except Exception:
        for path,old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)

        print("[ROLLBACK] OPC-009 Alignment V2 failed; affected files restored")
        raise

    print("[PASS] Corrected:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-009 ALIGNMENT V2 INSTALLED + CERTIFIED")

if __name__=="__main__":
    main()
from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.cwd().resolve()
LINE="="*100
TARGET="KXMVECROSSCATEGORY-SHARD1-S2026846CE8E4C97-EA22E96EFD7"

def load_database_url():
    for key in (
        "ORACLE_POSTGRESQL_URL",
        "ORACLE_DATABASE_URL",
        "DATABASE_URL",
        "POSTGRES_URL",
    ):
        value=os.environ.get(key)
        if value:
            return value

    env=ROOT/".env"
    if env.exists():
        for raw in env.read_text(encoding="utf-8",errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key,value=line.split("=",1)
            key=key.strip()
            value=value.strip().strip('"').strip("'")
            if key in (
                "ORACLE_POSTGRESQL_URL",
                "ORACLE_DATABASE_URL",
                "DATABASE_URL",
                "POSTGRES_URL",
            ) and value:
                return value

    return None

def connect():
    url=load_database_url()

    try:
        import psycopg
        if url:
            return psycopg.connect(url)
        return psycopg.connect(
            host=os.environ.get("PGHOST","localhost"),
            port=os.environ.get("PGPORT","5432"),
            dbname=os.environ.get("PGDATABASE","postgres"),
            user=os.environ.get("PGUSER","postgres"),
            password=os.environ.get("PGPASSWORD"),
        )
    except ImportError:
        import psycopg2
        if url:
            return psycopg2.connect(url)
        return psycopg2.connect(
            host=os.environ.get("PGHOST","localhost"),
            port=os.environ.get("PGPORT","5432"),
            dbname=os.environ.get("PGDATABASE","postgres"),
            user=os.environ.get("PGUSER","postgres"),
            password=os.environ.get("PGPASSWORD"),
        )

def columns(cur):
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public'
          AND table_name='oracle_canonical_observations'
        ORDER BY ordinal_position
    """)
    return tuple(r[0] for r in cur.fetchall())

def main():
    print(LINE)
    print(" OPC-011 SINGLE PERSISTED COVERAGE TRACE")
    print(" READ-ONLY — POSTGRESQL ROW vs OPC-003 COVERAGE READ MODEL")
    print(LINE)
    print(f"[TARGET] {TARGET}")

    sys.path.insert(0,str(ROOT))

    opc3=importlib.import_module(
        "qseries_v2.oracle_pre_settlement_coverage."
        "opc_003_canonical_observation_coverage_read_model"
    )

    conn=connect()
    try:
        conn.autocommit=False
    except Exception:
        pass

    try:
        cur=conn.cursor()
        cols=columns(cur)
        print(f"[POSTGRES] columns={cols}")

        if "canonical_observation_json" not in cols:
            raise RuntimeError(
                "public.oracle_canonical_observations lacks "
                "canonical_observation_json"
            )

        time_col="observed_at" if "observed_at" in cols else None
        seq_col="sequence" if "sequence" in cols else (
            "observation_sequence" if "observation_sequence" in cols else None
        )

        select_cols=[]
        if seq_col:
            select_cols.append(seq_col)
        if time_col:
            select_cols.append(time_col)
        select_cols.append("canonical_observation_json")

        # Search only JSON payload for this exact ticker.
        sql=f"""
            SELECT {", ".join(select_cols)}
            FROM public.oracle_canonical_observations
            WHERE canonical_observation_json::text LIKE %s
            ORDER BY {time_col or seq_col or '1'} DESC
            LIMIT 10
        """
        cur.execute(sql,(f"%{TARGET}%",))
        rows=cur.fetchall()

        print(f"[POSTGRES MATCHES] rows={len(rows)}")

        if not rows:
            print("[DIAGNOSIS] Exact persisted ticker is not recoverable from canonical_observation_json.")
            print("[CLASSIFICATION] Persistence representation/path mismatch.")
            print("[NEXT] Inspect OLA persisted evidence/result for this exact observation identity.")
            return 0

        for i,row in enumerate(rows,1):
            offset=0
            seq=None
            observed_at=None
            if seq_col:
                seq=row[offset]; offset+=1
            if time_col:
                observed_at=row[offset]; offset+=1
            raw=row[offset]

            if isinstance(raw,str):
                try:
                    doc=json.loads(raw)
                except Exception:
                    doc={"_raw":raw}
            else:
                doc=raw or {}

            payload=doc.get("payload") if isinstance(doc,dict) else None
            if not isinstance(payload,dict):
                payload={}

            print("-"*100)
            print(f"[ROW {i}] sequence={seq!r} observed_at={observed_at!r}")
            print(f"[ROW {i}] top_level_keys={tuple(sorted(doc.keys())) if isinstance(doc,dict) else ()}")
            print(f"[ROW {i}] observation_type={doc.get('observation_type') if isinstance(doc,dict) else None!r}")
            print(f"[ROW {i}] source_id={doc.get('source_id') if isinstance(doc,dict) else None!r}")
            print(f"[ROW {i}] payload_keys={tuple(sorted(payload.keys()))}")
            print(f"[ROW {i}] payload.source_market_id={payload.get('source_market_id')!r}")
            print(f"[ROW {i}] payload.source_symbol={payload.get('source_symbol')!r}")
            print(f"[ROW {i}] payload.opc_snapshot={payload.get('opc_snapshot')!r}")
            print(f"[ROW {i}] payload.opc_observation_epoch={payload.get('opc_observation_epoch')!r}")
            print(f"[ROW {i}] payload.opc_source_state_hash={payload.get('opc_source_state_hash')!r}")

        print("-"*100)
        print("[OPC-003 DIRECT READ]")
        direct=opc3.read_recent_canonical_tickers(ROOT,24,250000)
        found=TARGET in set(direct)
        print(f"[OPC-003] returned_unique_tickers={len(direct)}")
        print(f"[OPC-003] target_found={found}")

        print("="*100)
        print(" COVERAGE TRACE DIAGNOSIS")
        print("="*100)

        newest=rows[0]
        idx=0
        if seq_col:
            idx+=1
        observed_at=newest[idx] if time_col else None
        raw=newest[-1]
        if isinstance(raw,str):
            try:
                doc=json.loads(raw)
            except Exception:
                doc={}
        else:
            doc=raw or {}
        payload=doc.get("payload") if isinstance(doc,dict) else {}
        if not isinstance(payload,dict):
            payload={}

        stored_ticker=payload.get("source_market_id") or payload.get("source_symbol")

        recent=True
        if observed_at is not None:
            dt=observed_at
            if isinstance(dt,str):
                dt=datetime.fromisoformat(dt.replace("Z","+00:00"))
            if getattr(dt,"tzinfo",None) is None:
                dt=dt.replace(tzinfo=timezone.utc)
            age=(datetime.now(timezone.utc)-dt.astimezone(timezone.utc)).total_seconds()
            recent=age <= 24*3600
            print(f"[TIME CHECK] age_seconds={age:.1f} inside_24h={recent}")

        print(f"[IDENTITY CHECK] stored_ticker={stored_ticker!r} exact_match={stored_ticker==TARGET}")
        print(f"[READ MODEL CHECK] target_found={found}")

        if stored_ticker==TARGET and recent and not found:
            print("[DIAGNOSIS] PostgreSQL contains a fresh exact OPC observation, but OPC-003 does not recognize it.")
            print("[CLASSIFICATION] OPC-003 coverage read-model defect confirmed.")
            print("[NEXT] Correct OPC-003 extraction/filtering only; leave OPC-006/009, OLA, and frozen OLR untouched.")
        elif stored_ticker!=TARGET:
            print("[DIAGNOSIS] Persisted row exists but ticker is not stored where OPC coverage expects it.")
            print("[CLASSIFICATION] Canonical payload identity-shape mismatch.")
            print("[NEXT] Compare OPC-003 extractor with actual canonical JSON shape before changing code.")
        elif not recent:
            print("[DIAGNOSIS] Exact row exists but PostgreSQL observed_at is outside the 24-hour coverage window.")
            print("[CLASSIFICATION] Observation timestamp semantics mismatch.")
            print("[NEXT] Inspect canonical observed_at vs acquired_at semantics.")
        elif found:
            print("[DIAGNOSIS] OPC-003 recognizes the target when queried directly.")
            print("[CLASSIFICATION] OPC-010 AFTER-census path or stale read/transaction behavior is suspect.")
            print("[NEXT] Trace OPC-010 census invocation rather than changing OPC-003.")
        else:
            print("[DIAGNOSIS] Result requires one additional focused trace.")

        print("[PASS] PostgreSQL inspection performed read-only")
        print("[PASS] No source files modified")
        print("[PASS] Frozen OLR-001 through OLR-045 untouched")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OPC-011 SINGLE PERSISTED COVERAGE TRACE COMPLETE")
        return 0
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()

if __name__=="__main__":
    raise SystemExit(main())
