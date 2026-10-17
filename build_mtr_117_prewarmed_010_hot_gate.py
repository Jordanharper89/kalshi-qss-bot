from pathlib import Path

Path("mtr_117_prewarmed_010_hot_gate.py").write_text(r'''from __future__ import annotations
import json,time
from pathlib import Path

import mtr_116_fast_gate_route_queue_hardening as b116

from qseries_v2.oracle_execution import (
    oracle_018_exact_sdk_hot_lane_cutover as q18,
    oracle_020_latest_state_exact_pricing_worker as q20,
    oracle_025_single_hydration_exact_live_reuse as q25,
)
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_060b_existing_runtime_multidex_cutover as q60b,
)

OUT=Path("mtr_117_prewarmed_010_hot_gate.json")
PAIRS=[]
PREWARM={"pools":0,"failures":0,"ms":0.0}

orig_prepare=b116.prepare
orig_install=q20.install

def prepare(root):
    global PAIRS
    state=orig_prepare(root)
    PAIRS=list(state.get("pairs") or [])
    return state

def install():
    lane=orig_install()

    seen=set()
    started=time.perf_counter_ns()

    for p in PAIRS:
        pool=str(p.pump_pool)
        if pool in seen:
            continue
        seen.add(pool)

        t=time.perf_counter_ns()
        try:
            q18.worker().warm(pool)
            lane.warmed.add(pool)
            PREWARM["pools"]+=1
            print(
                "[MTR117_POOL_PREWARM] pool=%s warm_ms=%.3f"
                %(pool[:12],(time.perf_counter_ns()-t)/1e6),
                flush=True,
            )
        except Exception as e:
            PREWARM["failures"]+=1
            print(
                "[MTR117_POOL_PREWARM_HOLD] pool=%s reason=%s:%s"
                %(pool[:12],type(e).__name__,str(e)[:160]),
                flush=True,
            )

    PREWARM["ms"]=(time.perf_counter_ns()-started)/1e6

    print(
        "[MTR117_PREWARM_COMPLETE] pools=%d failures=%d total_ms=%.3f"
        %(PREWARM["pools"],PREWARM["failures"],PREWARM["ms"]),
        flush=True,
    )
    return lane

def main():
    print("[MTR-117] START",flush=True)
    print("[HOT_GATE] exact_size_sol=0.010",flush=True)
    print("[ARCH] all Pump pools prewarmed before WebSocket serve",flush=True)

    # Reuse physically proven MTR-116 exact-route hydration/fanout.
    b116.FAST=(0.010,)
    q20.FAST_SIZES=(0.010,)
    q20.FULL_SIZE_CURVE=(0.010,)
    q20.EXPAND_SIZES=()

    # Preserve route-keyed multi-link event fanout.
    q20._patched_process_event=b116.process

    # Replace only the underlying exact-pair inventory preparation.
    q60b._ORIG_PREPARE=prepare

    # Prewarm every Pump pool before persistent.serve begins receiving events.
    q20.install=install

    rc=q25.run(seconds=60.0)

    rp=Path(
        "runtime_state/oracle/oracle_live_execution/"
        "oracle_020_latest_state_exact_pricing_worker.json"
    )
    r=json.loads(rp.read_text(encoding="utf-8"))

    result={
        "mtr":"MTR-117",
        "pairs":len(PAIRS),
        "unique_pump_pools":len({str(p.pump_pool) for p in PAIRS}),
        "prewarmed_pools":PREWARM["pools"],
        "prewarm_failures":PREWARM["failures"],
        "submitted":r.get("submitted"),
        "processed":r.get("processed"),
        "replaced":r.get("replaced_before_start"),
        "scan_replaced":r.get("scan_replaced"),
        "stale":r.get("stale_drops"),
        "positive":r.get("positive"),
        "p99_start_ms":r.get("p99_event_start_ms"),
        "p99_scan_ms":r.get("p99_scan_ms"),
        "best":r.get("best"),
        "return_code":rc,
        "execution_authority":False,
        "broadcast":False,
        "private_key_used":False,
    }

    OUT.write_text(
        json.dumps(result,indent=2,sort_keys=True,default=str),
        encoding="utf-8",
    )

    print(
        "[SUMMARY] pairs=%s pumps=%s prewarmed=%s failures=%s "
        "submitted=%s processed=%s stale=%s positive=%s "
        "p99_start_ms=%s p99_scan_ms=%s"
        %(
            result["pairs"],
            result["unique_pump_pools"],
            result["prewarmed_pools"],
            result["prewarm_failures"],
            result["submitted"],
            result["processed"],
            result["stale"],
            result["positive"],
            result["p99_start_ms"],
            result["p99_scan_ms"],
        ),
        flush=True,
    )

    age=result["p99_start_ms"]
    scan=result["p99_scan_ms"]

    ok=(
        result["pairs"]==12
        and result["prewarm_failures"]==0
        and result["prewarmed_pools"]==result["unique_pump_pools"]
        and int(result["processed"] or 0)>0
        and int(result["stale"] or 0)==0
        and age is not None
        and float(age)<250.0
        and scan is not None
        and float(scan)<15.0
    )

    print(
        "[RESULT] PREWARMED_010_HOT_GATE_PASS"
        if ok else
        "[RESULT] PREWARMED_010_HOT_GATE_NOT_CERTIFIED",
        flush=True,
    )
    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-117] COMPLETE",flush=True)

if __name__=="__main__":
    main()
''',encoding="utf-8")

print("[BUILD] wrote mtr_117_prewarmed_010_hot_gate.py")
print("[BUILD] prewarmed exact 0.010-SOL hot gate")
print("[SCOPE] route-keyed warm state; no signing; no sending")