from pathlib import Path

p=Path("mtr_137_continuous_live_divergence_lane.py")

p.write_text(r'''from __future__ import annotations
import argparse,json,time
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_020_latest_state_exact_pricing_worker as q20,
    oracle_025_single_hydration_exact_live_reuse as q25,
)

SIZES=(0.010,0.015,0.020,0.025,0.030)
OUT=Path("mtr_137_continuous_live_divergence_lane.json")

def configure():
    q20.FULL_SIZE_CURVE=SIZES
    q20.FAST_SIZES=SIZES
    q20.EXPAND_SIZES=()
    q20.EXPAND_GATE_BPS=-1000000.0
    q20.PREFERRED_SIZE_SOL=0.010
    q20.MAX_START_AGE_MS=750.0

    if tuple(q20.FAST_SIZES)!=SIZES:
        raise RuntimeError("MTR137_SIZE_POLICY_NOT_BOUND")

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=300.0)
    a=ap.parse_args(argv)

    configure()

    print("[MTR-137] CONTINUOUS LIVE DIVERGENCE LANE",flush=True)
    print("[SOURCE] ORACLE-025 single hydration + ORACLE-020 latest-state WebSocket lane",flush=True)
    print("[SIZES] 0.010,0.015,0.020,0.025,0.030 SOL",flush=True)
    print("[DIRECTIONS] PUMP_TO_METEORA + METEORA_TO_PUMP",flush=True)
    print("[COALESCE] newest snapshot wins per token",flush=True)
    print("[MID_SCAN] newer snapshot aborts older size scan",flush=True)
    print("[STALE_START] >750ms rejected",flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)

    started=time.time()
    rc=q25.run(seconds=float(a.seconds))

    report_path=Path(
        "runtime_state/oracle/oracle_live_execution/"
        "oracle_020_latest_state_exact_pricing_worker.json"
    )

    if not report_path.is_file():
        raise RuntimeError("MTR137_ORACLE020_REPORT_MISSING")

    live=json.loads(report_path.read_text(encoding="utf-8"))
    best=live.get("best")

    out={
        "mtr":"MTR-137",
        "seconds":time.time()-started,
        "sizes_sol":list(SIZES),
        "submitted":live.get("submitted"),
        "replaced":live.get("replaced_before_start"),
        "processed":live.get("processed"),
        "stale_drops":live.get("stale_drops"),
        "scan_replaced":live.get("scan_replaced"),
        "evaluations":live.get("evaluations"),
        "positive":live.get("positive"),
        "p99_event_start_ms":live.get("p99_event_start_ms"),
        "p99_scan_ms":live.get("p99_scan_ms"),
        "best":best,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(out,indent=2,sort_keys=True,default=str),
        encoding="utf-8",
    )

    print(
        "[MTR137_SUMMARY] submitted=%s replaced=%s processed=%s "
        "stale=%s scan_replaced=%s evaluations=%s positive=%s"
        %(
            out["submitted"],out["replaced"],out["processed"],
            out["stale_drops"],out["scan_replaced"],
            out["evaluations"],out["positive"],
        ),
        flush=True,
    )

    if best:
        print(
            "[MTR137_BEST] token=%s dir=%s size=%.3f "
            "net=%+d bps=%+.2f"
            %(
                str(best.get("token",""))[:10],
                best.get("direction"),
                float(best.get("size_sol") or 0),
                int(best.get("local_net") or 0),
                float(best.get("local_bps") or 0),
            ),
            flush=True,
        )

    if best and int(best.get("local_net") or 0)>0:
        print("[RESULT] LIVE_DIVERGENCE_CANDIDATE_OBSERVED",flush=True)
        print("[NEXT] OFFICIAL_PROTECTED_REVALIDATION_REQUIRED",flush=True)
    else:
        print("[RESULT] NO_LIVE_DIVERGENCE_CANDIDATE_IN_WINDOW",flush=True)

    print("[OUTPUT] "+str(OUT))
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[MTR-137] COMPLETE")

    return rc

if __name__=="__main__":
    raise SystemExit(main())
''',encoding="utf-8")

print("[BUILD] wrote",p)
print("[BUILD] continuous live divergence-first pricing lane")
print("[SIZES] 0.010-0.030 SOL")
print("[SCOPE] WebSocket/latest-state only; no key; no signing; no send")