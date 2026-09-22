from __future__ import annotations

import json
import os
from pathlib import Path

ROOT=Path.cwd().resolve()
LINE="="*104

EXPECTED_HASH="b29adbbef946a860c9bde3f21fa0a1753699662f05d52ca7127e0b75531cdf9c"
ACTUAL_PRIOR_HASH="c2317e49460988e426da204d8abea2fe41fd212d5ed838704da516066699a1d6"

def database_url():
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

    raise RuntimeError("PostgreSQL URL not configured")

def extract_ticker(raw):
    try:
        if isinstance(raw,str):
            raw=json.loads(raw)
        if not isinstance(raw,dict):
            return None
        payload=raw.get("payload")
        if isinstance(payload,dict):
            return (
                payload.get("source_market_id")
                or payload.get("source_symbol")
                or payload.get("ticker")
            )
    except Exception:
        pass
    return None

def main():
    print(LINE)
    print(" OPC-042 PHYSICAL COMPETING WRITER IDENTIFICATION DIAGNOSTIC")
    print(" READ-ONLY — TRACE EXACT CANONICAL CHAIN MOVEMENT")
    print(LINE)
    print(f"[EXPECTED STALE HEAD] {EXPECTED_HASH}")
    print(f"[ACTUAL PRIOR HEAD]    {ACTUAL_PRIOR_HASH}")

    import psycopg
    conn=psycopg.connect(database_url())

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sequence_number,
                    observation_id,
                    source_id,
                    observation_type,
                    observed_at,
                    acquired_at,
                    persisted_at,
                    previous_chain_hash,
                    chain_hash,
                    canonical_observation_json
                FROM public.oracle_canonical_observations
                WHERE chain_hash = %s
                   OR previous_chain_hash = %s
                   OR chain_hash = %s
                   OR previous_chain_hash = %s
                ORDER BY sequence_number
                """,
                (
                    EXPECTED_HASH,
                    EXPECTED_HASH,
                    ACTUAL_PRIOR_HASH,
                    ACTUAL_PRIOR_HASH,
                ),
            )

            rows=cur.fetchall()

        print(f"[MATCHING ROWS] {len(rows)}")

        if not rows:
            print("[DIAGNOSIS] Neither captured chain hash is present in canonical observation rows.")
            print("[CLASSIFICATION] Backend chain-state representation differs from row-level chain hashes.")
            print("[NEXT] Inspect canonical backend chain-head storage directly.")
            return 0

        parsed=[]
        for row in rows:
            (
                seq,
                observation_id,
                source_id,
                observation_type,
                observed_at,
                acquired_at,
                persisted_at,
                previous_chain_hash,
                chain_hash,
                canonical_json,
            )=row

            ticker=extract_ticker(canonical_json)

            item={
                "sequence_number":seq,
                "observation_id":observation_id,
                "source_id":source_id,
                "observation_type":observation_type,
                "ticker":ticker,
                "observed_at":observed_at,
                "acquired_at":acquired_at,
                "persisted_at":persisted_at,
                "previous_chain_hash":previous_chain_hash,
                "chain_hash":chain_hash,
            }
            parsed.append(item)

            print("-"*104)
            for key,value in item.items():
                print(f"[ROW] {key}={value}")

        print("="*104)
        print(" CHAIN MOVEMENT ANALYSIS")
        print("="*104)

        expected_row=None
        actual_row=None

        for item in parsed:
            if item["chain_hash"]==EXPECTED_HASH:
                expected_row=item
            if item["chain_hash"]==ACTUAL_PRIOR_HASH:
                actual_row=item

        if expected_row:
            print("[EXPECTED HEAD OWNER]")
            print(f"  sequence={expected_row['sequence_number']}")
            print(f"  source_id={expected_row['source_id']}")
            print(f"  observation_type={expected_row['observation_type']}")
            print(f"  ticker={expected_row['ticker']}")
            print(f"  observation_id={expected_row['observation_id']}")
        else:
            print("[EXPECTED HEAD OWNER] not found as row chain_hash")

        if actual_row:
            print("[ACTUAL HEAD OWNER]")
            print(f"  sequence={actual_row['sequence_number']}")
            print(f"  source_id={actual_row['source_id']}")
            print(f"  observation_type={actual_row['observation_type']}")
            print(f"  ticker={actual_row['ticker']}")
            print(f"  observation_id={actual_row['observation_id']}")
        else:
            print("[ACTUAL HEAD OWNER] not found as row chain_hash")

        if expected_row and actual_row:
            delta=actual_row["sequence_number"]-expected_row["sequence_number"]
            print(f"[SEQUENCE ADVANCE] {delta}")

            if delta==1:
                print("[DIAGNOSIS] Exactly one canonical observation advanced the chain between coverage read and append.")
                print(
                    "[COMPETING WRITER] "
                    f"source_id={actual_row['source_id']} "
                    f"type={actual_row['observation_type']} "
                    f"ticker={actual_row['ticker']}"
                )
            elif delta>1:
                print("[DIAGNOSIS] Multiple canonical observations advanced the chain before coverage append.")
                print("[CLASSIFICATION] Coverage critical section is not isolated from one or more other writers.")
            else:
                print("[DIAGNOSIS] Captured hashes do not form a forward sequence in row storage.")
        else:
            print("[DIAGNOSIS] Partial hash ownership recovered; one more backend-state trace may be required.")

        # Show every row strictly between the two hashes when sequence ownership is known.
        if expected_row and actual_row and actual_row["sequence_number"]>expected_row["sequence_number"]:
            import psycopg
            conn2=psycopg.connect(database_url())
            try:
                with conn2.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            sequence_number,
                            observation_id,
                            source_id,
                            observation_type,
                            canonical_observation_json,
                            previous_chain_hash,
                            chain_hash,
                            persisted_at
                        FROM public.oracle_canonical_observations
                        WHERE sequence_number > %s
                          AND sequence_number <= %s
                        ORDER BY sequence_number
                        LIMIT 100
                        """,
                        (
                            expected_row["sequence_number"],
                            actual_row["sequence_number"],
                        ),
                    )
                    between=cur.fetchall()
            finally:
                conn2.close()

            print("-"*104)
            print(f"[ROWS BETWEEN HEADS] {len(between)}")

            families={}
            for row in between:
                seq,oid,sid,otype,cjson,prev,chash,pts=row
                ticker=extract_ticker(cjson)
                key=(sid,otype)
                families[key]=families.get(key,0)+1
                print(
                    f"[BETWEEN] sequence={seq} source_id={sid} "
                    f"type={otype} ticker={ticker} "
                    f"observation_id={oid} persisted_at={pts}"
                )

            print(f"[WRITER FAMILY SUMMARY] {families}")

        print("[PASS] PostgreSQL inspection performed read-only")
        print("[PASS] No Oracle source files modified")
        print("[PASS] Frozen OLA/OLR untouched")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OPC-042 COMPETING WRITER IDENTIFICATION COMPLETE")
        return 0

    finally:
        conn.close()

if __name__=="__main__":
    raise SystemExit(main())
