from pathlib import Path
import json, subprocess, sys

SECONDS=60

cmd=[
    sys.executable,
    "-m",
    "qseries_v2.oracle_execution.oracle_025_single_hydration_exact_live_reuse",
    "--seconds",
    str(SECONDS),
]

print("[PROFIT_RECOVERY] restored October-1 positive-producing stack",flush=True)
print("[WINDOW] %ds"%SECONDS,flush=True)
print("[BROADCAST] disabled",flush=True)

rc=subprocess.call(cmd)

report=Path(
    "runtime_state/oracle/oracle_live_execution/"
    "oracle_020_latest_state_exact_pricing_worker.json"
)

if not report.is_file():
    print("[PROFIT_GATE] CLOSED reason=ORACLE020_REPORT_MISSING",flush=True)
    raise SystemExit(2 if rc==0 else rc)

data=json.loads(report.read_text(encoding="utf-8"))
processed=int(data.get("processed") or 0)
positive=int(data.get("positive") or 0)
best=data.get("best") or {}

print(
    "[PROFIT_GATE_RESULT] processed=%d positive=%d best_net=%s best_bps=%s direction=%s size=%s"
    %(
        processed,
        positive,
        str(best.get("local_net")),
        str(best.get("local_bps")),
        str(best.get("direction")),
        str(best.get("size_sol")),
    ),
    flush=True,
)

if processed<=0:
    print("[PROFIT_GATE] CLOSED reason=PRICING_NOT_PROCESSING",flush=True)
    raise SystemExit(3)

if positive<=0:
    print("[PROFIT_GATE] CLOSED reason=NO_CURRENT_POSITIVE_IN_WINDOW",flush=True)
    raise SystemExit(4)

print("[PROFIT_GATE] OPEN current_live_positive_observed=True",flush=True)
print("[NEXT] reconnect this exact positive route to signed-sim/fee gate before broadcast",flush=True)
print("[BROADCAST] disabled",flush=True)
raise SystemExit(0)
