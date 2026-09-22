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
