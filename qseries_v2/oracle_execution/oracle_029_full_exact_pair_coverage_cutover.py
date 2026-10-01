from __future__ import annotations
import argparse, json
from pathlib import Path

from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_execution import oracle_028_exact_immutable_atomic_shadow_handoff as q28

EXECUTION_AUTHORITY = False
PAPER_ONLY = True
REAL_MONEY_MOVED = False
TARGET_EXACT_PAIRS = 12

def expanded_prepare_once(root):
    root = Path(root)
    q60b = q25.q60b2.q60b
    q60b.install()
    q60b.m.pd.MAX_PAIRS = int(TARGET_EXACT_PAIRS)

    try:
        q60b.p.MAX_PAIRS = int(TARGET_EXACT_PAIRS)
    except Exception:
        pass

    try:
        q60b.m.MAX_PAIRS = int(TARGET_EXACT_PAIRS)
    except Exception:
        pass

    state = q60b.extended_prepare(root)
    cap = q60b.extended_capability(state)

    pairs = list(state.get("pairs") or [])
    if not pairs:
        raise RuntimeError("ORACLE029_NO_EXACT_PAIRS")

    print(
        "[ORACLE029_COVERAGE] exact_pairs=%d target=%d priced_tokens=%d accounts=%d"
        % (
            len(pairs),
            TARGET_EXACT_PAIRS,
            len(state.get("eps") or {}),
            len(state.get("addresses") or []),
        ),
        flush=True,
    )

    for i, pair in enumerate(pairs, 1):
        print(
            "[ORACLE029_PAIR] n=%d token=%s pump=%s meteora=%s"
            % (
                i,
                str(pair.token)[:12],
                str(pair.pump_pool)[:12],
                str(pair.meteora_pool)[:12],
            ),
            flush=True,
        )

    return state, cap

def install():
    q25.prepare_once = expanded_prepare_once
    return True

def run(seconds=300.0):
    install()

    print("[ORACLE-029] FULL EXACT-PAIR COVERAGE CUTOVER", flush=True)
    print("[EXACT_PAIR_LIMIT] 4 -> %d" % TARGET_EXACT_PAIRS, flush=True)
    print("[HYDRATION] one startup hydration only", flush=True)
    print("[PRESERVE] ORACLE-023 persistent token-net", flush=True)
    print("[PRESERVE] ORACLE-027 immutable snapshots + generation guard", flush=True)
    print("[PRESERVE] ORACLE-028 real atomic simulation shadow", flush=True)
    print("[MRIYA] replenishment only; not critical path", flush=True)
    print("[BROADCAST] disabled", flush=True)

    rc = q28.run(float(seconds))

    lane = getattr(q28.q20, "_lane", None)
    report = {
        "oracle_build": "ORACLE-029",
        "target_exact_pairs": TARGET_EXACT_PAIRS,
        "submitted": getattr(lane, "submitted", None),
        "processed": getattr(lane, "processed", None),
        "positive": getattr(lane, "positive", None),
        "scan_replaced": getattr(lane, "scan_replaced", None),
        "execution_authority": False,
        "paper_only": True,
        "real_money_moved": False,
        "broadcast": False,
    }

    report_path = Path(
        "runtime_state/oracle/oracle_live_execution/"
        "oracle_029_full_exact_pair_coverage_cutover.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("[ORACLE029_COMPLETE] " + json.dumps(report, sort_keys=True), flush=True)
    print("[REPORT] %s" % report_path, flush=True)
    return rc

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=300.0)
    args = ap.parse_args(argv)
    return run(args.seconds)

if __name__ == "__main__":
    raise SystemExit(main())
