from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT=Path.cwd().resolve()
BASELINE_RATE=0.003  # 0.30%
LINE="="*100

def database_url():
    for key in ("ORACLE_POSTGRESQL_URL","ORACLE_DATABASE_URL","DATABASE_URL","POSTGRES_URL"):
        value=os.environ.get(key)
        if value:
            return value
    env=ROOT/".env"
    if env.exists():
        for raw in env.read_text(encoding="utf-8",errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k,v=line.split("=",1)
            if k.strip() in ("ORACLE_POSTGRESQL_URL","ORACLE_DATABASE_URL","DATABASE_URL","POSTGRES_URL"):
                value=v.strip().strip('"').strip("'")
                if value:
                    return value
    raise RuntimeError("PostgreSQL URL not configured")

def fetch_open_pages(pages,limit):
    from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
    from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get

    creds=load_kalshi_credentials()
    cursor=""
    tickers=[]
    seen=set()

    for page in range(1,pages+1):
        params={"limit":limit,"status":"open"}
        if cursor:
            params["cursor"]=cursor
        response=kalshi_rest_get(creds,"/markets",params,20)
        body=response.body or {}
        rows=body.get("markets",[]) or []

        added=0
        for row in rows:
            if not isinstance(row,dict):
                continue
            ticker=str(row.get("ticker") or "")
            if ticker and ticker not in seen:
                seen.add(ticker)
                tickers.append(ticker)
                added+=1

        cursor=str(body.get("cursor") or "")
        print(f"[OPEN SAMPLE] page={page}/{pages} received={len(rows)} unique_added={added} total_unique={len(tickers)}")

        if not cursor:
            break

    return tuple(tickers)

def load_runtime_progress():
    state_path=ROOT/"runtime_state"/"oracle_pre_settlement_coverage_runtime_state.json"
    cursor_path=ROOT/"runtime_state"/"oracle_pre_settlement_coverage_universe_cursor.json"

    result={}

    if state_path.exists():
        try:
            result["runtime_state"]=json.loads(state_path.read_text(encoding="utf-8"))
        except Exception as exc:
            result["runtime_state_error"]=f"{type(exc).__name__}: {exc}"
    else:
        result["runtime_state"]=None

    if cursor_path.exists():
        try:
            result["cursor_state"]=json.loads(cursor_path.read_text(encoding="utf-8"))
        except Exception as exc:
            result["cursor_state_error"]=f"{type(exc).__name__}: {exc}"
    else:
        result["cursor_state"]=None

    return result

def postgres_coverage(sample,lookback_hours):
    import psycopg

    sample=tuple(dict.fromkeys(sample))
    if not sample:
        return {
            "sampled":0,
            "any_recent":0,
            "opc_recent":0,
            "any_rate":0.0,
            "opc_rate":0.0,
        }

    conn=psycopg.connect(database_url())
    try:
        with conn.cursor() as cur:
            # Recent canonical coverage for sampled tickers.
            cur.execute(
                """
                WITH recent AS (
                    SELECT DISTINCT
                        canonical_observation_json::jsonb
                            -> 'payload' ->> 'source_market_id' AS ticker
                    FROM public.oracle_canonical_observations
                    WHERE observed_at >= NOW() - (%s * INTERVAL '1 hour')
                      AND canonical_observation_json::jsonb
                            -> 'payload' ->> 'source_market_id' = ANY(%s)
                )
                SELECT COUNT(*)
                FROM recent
                WHERE ticker IS NOT NULL
                """,
                (float(lookback_hours),list(sample)),
            )
            any_recent=int(cur.fetchone()[0] or 0)

            # Specifically OPC-generated recent coverage.
            cur.execute(
                """
                WITH recent_opc AS (
                    SELECT DISTINCT
                        canonical_observation_json::jsonb
                            -> 'payload' ->> 'source_market_id' AS ticker
                    FROM public.oracle_canonical_observations
                    WHERE observed_at >= NOW() - (%s * INTERVAL '1 hour')
                      AND COALESCE(
                            (canonical_observation_json::jsonb
                                -> 'payload' ->> 'opc_snapshot')::boolean,
                            false
                          ) = true
                      AND canonical_observation_json::jsonb
                            -> 'payload' ->> 'source_market_id' = ANY(%s)
                )
                SELECT COUNT(*)
                FROM recent_opc
                WHERE ticker IS NOT NULL
                """,
                (float(lookback_hours),list(sample)),
            )
            opc_recent=int(cur.fetchone()[0] or 0)

            # Total distinct OPC-covered markets in the whole recent canonical store.
            cur.execute(
                """
                SELECT COUNT(DISTINCT
                    canonical_observation_json::jsonb
                        -> 'payload' ->> 'source_market_id')
                FROM public.oracle_canonical_observations
                WHERE observed_at >= NOW() - (%s * INTERVAL '1 hour')
                  AND COALESCE(
                        (canonical_observation_json::jsonb
                            -> 'payload' ->> 'opc_snapshot')::boolean,
                        false
                      ) = true
                """,
                (float(lookback_hours),),
            )
            total_recent_opc=int(cur.fetchone()[0] or 0)

    finally:
        conn.close()

    sampled=len(sample)
    return {
        "sampled":sampled,
        "any_recent":any_recent,
        "opc_recent":opc_recent,
        "any_rate":any_recent/sampled if sampled else 0.0,
        "opc_rate":opc_recent/sampled if sampled else 0.0,
        "total_recent_opc_unique_markets":total_recent_opc,
    }

def show_metric(label,data):
    print("-"*100)
    print(label)
    print("-"*100)
    print(f"[SAMPLED OPEN MARKETS] {data['sampled']}")
    print(f"[ANY RECENT CANONICAL COVERAGE] {data['any_recent']}")
    print(f"[ANY RECENT COVERAGE RATE] {data['any_rate']:.2%}")
    print(f"[OPC SNAPSHOT COVERAGE] {data['opc_recent']}")
    print(f"[OPC SNAPSHOT COVERAGE RATE] {data['opc_rate']:.2%}")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--pages",type=int,default=5)
    parser.add_argument("--limit",type=int,default=1000)
    parser.add_argument("--lookback-hours",type=float,default=24.0)
    args=parser.parse_args()

    if args.pages<1 or args.pages>20:
        raise SystemExit("--pages must be 1..20")
    if args.limit<1 or args.limit>1000:
        raise SystemExit("--limit must be 1..1000")

    print(LINE)
    print(" ORACLE CURRENT PRE-SETTLEMENT COVERAGE IMPROVEMENT MEASUREMENT")
    print(" READ-ONLY — LIVE KALSHI SAMPLE + POSTGRESQL + OPC DURABLE PROGRESS")
    print(LINE)
    print(f"[BASELINE] original_physical_coverage_rate={BASELINE_RATE:.2%}")
    print(f"[CONFIG] broad_pages={args.pages} page_limit={args.limit} lookback_hours={args.lookback_hours}")

    # Baseline-comparable first page.
    first_page=fetch_open_pages(1,args.limit)
    first=postgres_coverage(first_page,args.lookback_hours)
    show_metric(" BASELINE-COMPARABLE FIRST OPEN-MARKET PAGE",first)

    # Broader sample from the live universe.
    broad=fetch_open_pages(args.pages,args.limit)
    broad_result=postgres_coverage(broad,args.lookback_hours)
    show_metric(" BROADER LIVE OPEN-MARKET SAMPLE",broad_result)

    print("-"*100)
    print(" OPC DURABLE PRODUCTION PROGRESS")
    print("-"*100)
    progress=load_runtime_progress()
    runtime=progress.get("runtime_state")
    cursor=progress.get("cursor_state")

    if isinstance(runtime,dict):
        print(f"[RUNTIME] cycles_completed={runtime.get('cycles_completed')}")
        print(f"[RUNTIME] markets_planned={runtime.get('markets_planned')}")
        print(f"[RUNTIME] markets_persisted={runtime.get('markets_persisted')}")
        print(f"[RUNTIME] transient_failures={runtime.get('transient_failures')}")
        print(f"[RUNTIME] consecutive_failures={runtime.get('consecutive_failures')}")
        print(f"[RUNTIME] last_cycle_status={runtime.get('last_cycle_status')}")
    else:
        print("[RUNTIME] state unavailable")

    if isinstance(cursor,dict):
        print(f"[CURSOR] pages_completed={cursor.get('pages_completed')}")
        print(f"[CURSOR] markets_seen={cursor.get('markets_seen')}")
        print(f"[CURSOR] cycles_completed={cursor.get('cycles_completed')}")
        print(f"[CURSOR] terminal_wraps={cursor.get('terminal_wraps')}")
        print(f"[CURSOR] last_page_markets={cursor.get('last_page_markets')}")
    else:
        print("[CURSOR] state unavailable")

    print(f"[POSTGRES] total_recent_unique_opc_markets={broad_result['total_recent_opc_unique_markets']}")

    print("="*100)
    print(" COVERAGE IMPROVEMENT RESULT")
    print("="*100)

    current=first["any_rate"]
    delta=current-BASELINE_RATE
    multiple=(current/BASELINE_RATE) if BASELINE_RATE>0 else 0.0

    print(f"[BASELINE RATE] {BASELINE_RATE:.2%}")
    print(f"[CURRENT FIRST-PAGE RATE] {current:.2%}")
    print(f"[ABSOLUTE IMPROVEMENT] {delta:+.2%}")
    print(f"[MULTIPLE OF BASELINE] {multiple:.2f}x")
    print(f"[BROADER SAMPLE RATE] {broad_result['any_rate']:.2%}")
    print(f"[BROADER OPC-ONLY RATE] {broad_result['opc_rate']:.2%}")

    if current>BASELINE_RATE:
        print("[DIAGNOSIS] Pre-settlement coverage has improved above the original 0.30% baseline.")
    elif current==BASELINE_RATE:
        print("[DIAGNOSIS] First-page coverage is unchanged versus baseline; continue accumulating coverage.")
    else:
        print("[DIAGNOSIS] First-page sample is below baseline; use broader sample and durable progress before concluding regression.")

    if broad_result["opc_recent"]>0:
        print("[PASS] New OPC snapshot coverage is physically visible in PostgreSQL.")
    else:
        print("[OBSERVE] No OPC snapshots overlap the current broad live sample yet.")

    print("[PASS] Measurement performed read-only")
    print("[PASS] No Oracle runtime state modified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORACLE CURRENT PRE-SETTLEMENT COVERAGE IMPROVEMENT MEASUREMENT COMPLETE")

if __name__=="__main__":
    main()
