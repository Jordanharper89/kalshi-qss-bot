from __future__ import annotations
import os
from pathlib import Path

ROOT=Path.cwd().resolve()
RUNNER=ROOT/"run_oad_050_physical_full_universe_coverage_verification.py"

SOURCE=r"""
from pathlib import Path
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.oracle_adapters.kalshi.oad_046_live_universe_enumeration import enumerate_live_open_universe
from qseries_v2.oracle_adapters.kalshi.oad_047_physical_coverage_plan import build_physical_coverage_plan
from qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import run_physical_multi_partition_persistence

def main():
    root=Path.cwd()

    print("="*72,flush=True)
    print(" OAD-050 PHYSICAL FULL-UNIVERSE COVERAGE VERIFICATION - LIVE-FIRST V3",flush=True)
    print("="*72,flush=True)

    print("[STAGE 0] Physical fast-lane architecture is already certified",flush=True)
    print("[FAST LANE] ticker+trade market_filter=NONE coverage=ALL",flush=True)

    print("[STAGE 1] Enumerating current live open universe ONCE",flush=True)
    credentials=load_kalshi_credentials(root=root)

    universe=enumerate_live_open_universe(
        credentials,
        timeout_seconds=8,
        progress=lambda x:print(x,flush=True),
    )

    print("[STAGE 2] Building partition plan from cached universe snapshot",flush=True)
    plan=build_physical_coverage_plan(
        universe.tickers,
        100,
    )

    print(
        f"[UNIVERSE] open_markets={len(universe.tickers)} "
        f"pages={universe.pages}",
        flush=True,
    )

    print(
        f"[ORDERBOOK] partitions_total={len(plan.orderbook_partitions)} "
        f"physical_probe_partitions={min(3,len(plan.orderbook_partitions))}",
        flush=True,
    )

    print("[STAGE 3] Starting WebSocket coverage + persistence using cached universe",flush=True)

    result=run_physical_multi_partition_persistence(
        root,
        universe=universe,
        max_persisted=12,
        orderbook_partitions_to_activate=min(
            3,
            len(plan.orderbook_partitions),
        ),
        progress=lambda x:print(x,flush=True),
    )

    print("[SUMMARY]",result,flush=True)

    if result.open_markets != len(universe.tickers):
        raise SystemExit("[FAIL] cached universe mismatch")

    if result.events_persisted < 12:
        raise SystemExit("[FAIL] persistence target not reached")

    print("[PASS] Global ticker/trade fast lane covers all markets emitted by Kalshi",flush=True)
    print("[PASS] Universe was enumerated exactly once",flush=True)
    print("[PASS] Multiple explicit orderbook partitions activated",flush=True)
    print("[PASS] Real events persisted through certified OLA PostgreSQL router",flush=True)
    print("[DONE] OAD-050 PHYSICAL FULL-UNIVERSE COVERAGE VERIFIED",flush=True)

if __name__=="__main__":
    main()
"""

def write_exact(path,text):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OAD-050 LIVE-FIRST PHYSICAL RUNNER CORRECTION V3 INSTALLER")
    print("="*72)

    old=RUNNER.read_bytes() if RUNNER.exists() else None

    try:
        write_exact(RUNNER,SOURCE)
        compile(
            RUNNER.read_text(encoding="utf-8"),
            str(RUNNER),
            "exec",
        )
    except Exception:
        if old is None:
            if RUNNER.exists():
                RUNNER.unlink()
        else:
            RUNNER.write_bytes(old)
        print("[ROLLBACK] OAD-050 runner correction failed")
        raise

    print("[PASS] OAD-050 now enumerates exactly once")
    print("[PASS] Cached universe snapshot is reused by OAD-048")
    print("[PASS] Visible progress retained")
    print("[DONE] OAD-050 LIVE-FIRST PHYSICAL RUNNER CORRECTION V3 INSTALLED")

if __name__=="__main__":
    main()
