from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

from qseries_v2.oracle_execution import oracle_014_venue_native_fast_lane as q14
from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18

EXECUTION_AUTHORITY = False
PAPER_ONLY = True
REAL_MONEY_MOVED = False

FAST_SIZES = (0.001, 0.010, 0.050)
EXPAND_SIZES = (0.180, 0.500, 1.400)
EXPAND_GATE_BPS = -100.0

persistent = q14.persistent
_original_process_event = None
_warmed_pools = set()
stats = {
    "events": 0,
    "evaluations": 0,
    "positive": 0,
    "drops": 0,
    "event_start_ms": [],
    "scan_ms": [],
    "best": None,
}

def _pair_snapshot(pair):
    return {
        "token": pair.token,
        "pump_pool": pair.pump_pool,
        "meteora": {
            "address": pair.meteora_pool,
            "token_x": pair.token_x,
            "token_y": pair.token_y,
            "decimals_x": pair.decimals_x,
            "decimals_y": pair.decimals_y,
        },
        "dlmm_state": pair.dlmm_state,
        "pump_base_reserve": int(pair.pump_base_reserve),
        "pump_quote_reserve": int(pair.pump_quote_reserve),
    }

def _pct(values, p):
    if not values:
        return None
    rows = sorted(values)
    return rows[min(len(rows) - 1, int(len(rows) * p))]

def _warm(pair):
    if pair.pump_pool in _warmed_pools:
        return
    q18.worker().warm(pair.pump_pool)
    _warmed_pools.add(pair.pump_pool)
    print(
        "[ORACLE019_WARM] token=%s pump=%s"
        % (pair.token[:10], pair.pump_pool[:12]),
        flush=True,
    )

def _exact_process_event(state, ev, c, sim_lane):
    global _original_process_event

    address = ev["address"]
    preg = state.get("preg", {})

    # Preserve every non PumpSwap/Meteora path exactly as it already exists.
    if address not in preg:
        return _original_process_event(state, ev, c, sim_lane)

    i, kind = preg[address]
    pair = state["pairs"][i]

    try:
        changed = persistent.m.pd.apply_account_event(
            pair,
            kind,
            address,
            ev["raw"],
            ev["slot"],
            ev["received_ns"],
        )
    except Exception as exc:
        c["event_errors"] += 1
        stats["drops"] += 1
        print(
            "[ORACLE019_EVENT_REJECT] token=%s reason=%s:%s"
            % (pair.token[:10], type(exc).__name__, str(exc)[:180]),
            flush=True,
        )
        return

    if not changed:
        return

    c["priced_events"] += 1
    stats["events"] += 1

    now_ns = time.perf_counter_ns()
    event_start_ms = max(0.0, (now_ns - int(ev["received_ns"])) / 1e6)
    stats["event_start_ms"].append(event_start_ms)

    try:
        _warm(pair)
        snap = _pair_snapshot(pair)

        started = time.perf_counter_ns()
        rows = []

        for size in FAST_SIZES:
            rows.extend(q18.exact_snapshot_opportunities(snap, size))
            stats["evaluations"] += 2

        best = max(rows, key=lambda x: x["local_net"])

        if float(best["local_bps"]) >= EXPAND_GATE_BPS:
            for size in EXPAND_SIZES:
                rows.extend(q18.exact_snapshot_opportunities(snap, size))
                stats["evaluations"] += 2
            best = max(rows, key=lambda x: x["local_net"])

        scan_ms = (time.perf_counter_ns() - started) / 1e6
        stats["scan_ms"].append(scan_ms)

        if stats["best"] is None or int(best["local_net"]) > int(stats["best"]["local_net"]):
            stats["best"] = dict(best)

        if int(best["local_net"]) > 0:
            stats["positive"] += 1

        print(
            "[ORACLE019_EXACT_EVENT] token=%s slot=%s dir=%s size=%.3f "
            "bps=%+.2f net=%+d event_start_ms=%.3f scan_ms=%.3f"
            % (
                pair.token[:10],
                ev["slot"],
                best["direction"],
                float(best["size_sol"]),
                float(best["local_bps"]),
                int(best["local_net"]),
                event_start_ms,
                scan_ms,
            ),
            flush=True,
        )

    except Exception as exc:
        stats["drops"] += 1
        print(
            "[ORACLE019_EXACT_REJECT] token=%s reason=%s:%s"
            % (pair.token[:10], type(exc).__name__, str(exc)[:220]),
            flush=True,
        )

def install():
    global _original_process_event

    if not hasattr(persistent, "_process_event"):
        raise RuntimeError("PERSISTENT_PROCESS_EVENT_SEAM_MISSING")
    if not hasattr(persistent, "m"):
        raise RuntimeError("PERSISTENT_MERGED_RUNTIME_MISSING")
    if not hasattr(persistent.m, "pd"):
        raise RuntimeError("ACCOUNT_EVENT_DECODER_MISSING")

    current = persistent._process_event
    if getattr(current, "_oracle019_exact_feed", False):
        return current

    _original_process_event = current
    _exact_process_event._oracle019_exact_feed = True
    _exact_process_event._oracle019_original = current
    persistent._process_event = _exact_process_event
    return current

def _report():
    best = stats["best"]
    payload = {
        "oracle_build": "ORACLE-019",
        "execution_authority": False,
        "paper_only": True,
        "real_money_moved": False,
        "events": stats["events"],
        "evaluations": stats["evaluations"],
        "positive": stats["positive"],
        "drops": stats["drops"],
        "p99_event_start_ms": _pct(stats["event_start_ms"], 0.99),
        "p99_scan_ms": _pct(stats["scan_ms"], 0.99),
        "best": best,
        "broadcast": False,
    }
    out = Path(
        "runtime_state/oracle/oracle_live_execution/"
        "oracle_019_venue_native_reserve_feed_cutover.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload, out

async def _serve(seconds):
    result = persistent.serve(Path.cwd(), seconds)
    if hasattr(result, "__await__"):
        return await result
    return result

def run(seconds=60.0):
    q18.install_exact_hot_math()
    install()

    print("[ORACLE-019] VENUE-NATIVE RESERVE FEED CUTOVER", flush=True)
    print("[TRANSPORT] existing QARB-061D WebSocket stream", flush=True)
    print("[EVENT_SEAM] persistent._process_event", flush=True)
    print("[STATE_MUTATION] existing m.pd.apply_account_event", flush=True)
    print("[PUMP] exact ORACLE-018 PumpSwap SDK worker", flush=True)
    print("[METEORA] current hydrated PairState DLMM state", flush=True)
    print("[LEGACY_PUMP_DLMM_ECONOMICS] bypassed on direct venue events", flush=True)
    print("[NON_TARGET_DEX_PATHS] preserved", flush=True)
    print("[PRIVATE_KEY] not required", flush=True)
    print("[BROADCAST] disabled", flush=True)

    try:
        asyncio.run(_serve(float(seconds)))
    finally:
        payload, out = _report()

        print(
            "[ORACLE019_COMPLETE] events=%d evaluations=%d drops=%d positive=%d "
            "p99_event_start_ms=%s p99_scan_ms=%s"
            % (
                payload["events"],
                payload["evaluations"],
                payload["drops"],
                payload["positive"],
                str(payload["p99_event_start_ms"]),
                str(payload["p99_scan_ms"]),
            ),
            flush=True,
        )
        print("[REPORT] %s" % out, flush=True)
        print("[BROADCAST] disabled", flush=True)

        global _warmed_pools
        _warmed_pools = set()
        if getattr(q18, "_worker", None) is not None:
            q18._worker.close()
            q18._worker = None

    return 0

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=60.0)
    args = ap.parse_args(argv)
    return run(args.seconds)

if __name__ == "__main__":
    raise SystemExit(main())
