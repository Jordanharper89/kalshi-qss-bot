
"""Disarmed, isolated, direct-route simulation without a market scanner."""
import argparse
import json
import os
from pathlib import Path
from . import runtime as r
from . import oracle181_direct_swap2_certification as q181

OUT = Path("runtime_state/oracle/oracle_live_execution/ORACLE183_DIRECT_RESULTS.json")
DIRECTIONS = ("METEORA_TO_PUMP", "PUMP_TO_METEORA")

def make_report(rows, status, reason=None):
    result = {
        "build": "ORACLE183",
        "status": status,
        "reason": reason,
        "routes": rows,
        "scanner_started": False,
        "broadcast": False,
        "execution_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("[ORACLE183_RESULT]", status, "routes=", len(rows),
          "broadcast=FALSE", flush=True)
    print("[REPORT]", OUT)

def guard():
    if os.getenv("QSB_LIVE_ARM", "").upper() == "YES":
        raise RuntimeError("HOLD_ORACLE183_LIVE_ARM_ENABLED")
    source = Path(r.__file__).read_text(encoding="utf-8")
    for marker in (
        "ORACLE180_SWAP2_BIN_ARRAY_CORRECTION",
        "ORACLE179_NORMALIZED_SIM_VERDICT",
        "ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED",
    ):
        if marker not in source:
            raise RuntimeError("HOLD_ORACLE183_MISSING_" + marker)
    armed = getattr(r, "_live_010_armed", None)
    if not callable(armed) or armed():
        raise RuntimeError("HOLD_ORACLE183_CANNOT_PROVE_DISARMED")

def bootstrap():
    root = Path.cwd()
    state, _ = r.q25.prepare_once(root)
    r.q25.bind_cached_state(state)
    warmed = r.install_proven_hot_math(state)

    _, user = r.q87.c.sim_identity()
    if not user:
        raise RuntimeError("HOLD_ORACLE183_WALLET_UNAVAILABLE")

    r.USER = user
    r.prebuild_templates(state, user)
    r.prebuild_meteora_templates(state, user, warmed)

    usable = []
    for pair in state.get("pairs", []):
        token = str(pair.token)
        if token not in r.READY_TOKENS:
            continue
        try:
            r.q18.worker().warm(str(pair.pump_pool))
            usable.append(pair)
        except Exception as exc:
            print("[ORACLE183_PAIR_HOLD]", token[:10],
                  type(exc).__name__, flush=True)

    if not usable:
        raise RuntimeError("HOLD_ORACLE183_NO_WARM_PAIRS")

    r.BLOCKHASH.refresh()
    return usable, user

def diagnostic(max_pairs):
    guard()
    rpc = r.q87.c.rpc

    def restricted_rpc(method, *args, **kwargs):
        method = str(method).lower()
        if method.startswith("send") or method in (
            "requestairdrop", "simulatebundle", "sendbundle"
        ):
            raise RuntimeError("ORACLE183_BROADCAST_FORBIDDEN")
        return rpc(method, *args, **kwargs)

    # Guard the shared RPC entry point for every startup and simulation call.
    r.q87.c.rpc = restricted_rpc
    rows = []
    certified = set()
    status = "HOLD"
    reason = None

    try:
        usable, user = bootstrap()
        for pair in usable[:max_pairs]:
            token = str(pair.token)
            try:
                snap = r.immutable_snapshot(pair)
                quotes = r.q18.exact_snapshot_opportunities(snap, 0.050)
            except Exception as exc:
                rows.append({
                    "token": token[:10],
                    "stage": "QUOTE_HOLD",
                    "error": type(exc).__name__
                })
                continue

            for direction in DIRECTIONS:
                if direction in certified:
                    continue
                opp = next(
                    (x for x in quotes
                     if x.get("direction") == direction
                     and x.get("start") == 50_000_000),
                    None
                )
                if opp is None:
                    continue

                row = {
                    "token": token[:10],
                    "direction": direction,
                    "stage": "START",
                }
                try:
                    guard()
                    route = r.same_snapshot_route(user, snap, opp)
                    # Diagnostic only. A positive trade is NOT required.
                    # Existing native slippage and amount guards still apply.
                    target = max(1, int(opp.get("local_end", 0) * 0.90))
                    route, _, _ = r._fast_010_profit_lock_route(
                        route, direction, target
                    )
                    row.update(q181.inspect_route(route))
                    row["stage"] = "COMPILE"
                    compiled = r.compile_current(user, route)

                    if not isinstance(compiled, dict) or not compiled.get("ok"):
                        row["stage"] = "COMPILE_HOLD"
                        row["reason"] = "NO_LEGAL_NATIVE_PACKET"
                    else:
                        raw = compiled.get("raw")
                        row["packet_bytes"] = (
                            len(raw) if isinstance(raw, (bytes, bytearray))
                            else None
                        )
                        if (row["packet_bytes"] is None
                                or row["packet_bytes"] > 1232
                                or compiled.get("oracle176_packet_verified") is not True):
                            raise RuntimeError("HOLD_UNVERIFIED_SIGNED_PACKET")
                        guard()
                        sim = r.simulate_current(compiled, user)
                        outcome, units, failure = q181.classify_sim(sim)
                        row.update({
                            "stage": outcome,
                            "compute_units": units,
                            "failure": failure
                        })
                        certified.add(direction)

                except Exception as exc:
                    row["stage"] = "HOLD"
                    row["reason"] = type(exc).__name__
                    error = str(exc)
                    if (error.isascii() and len(error) < 100
                            and error.replace("_", "").isalnum()
                            and error.upper() == error):
                        row["reason_code"] = error

                rows.append(row)
                print(
                    "[ORACLE183_DIRECT] direction=%s stage=%s bytes=%s "
                    "failure=%s broadcast=FALSE" % (
                        direction, row["stage"],
                        row.get("packet_bytes"),
                        row.get("failure") or row.get("reason_code", "NONE")
                    ),
                    flush=True
                )

            if len(certified) == 2:
                break

        status = "COMPLETED_DIRECT_ATTEMPTS"

    except Exception as exc:
        reason = type(exc).__name__
        status = "HOLD_BOOTSTRAP"
        print("[ORACLE183_BOOTSTRAP_HOLD]", reason, flush=True)

    finally:
        r.q87.c.rpc = rpc
        worker = getattr(r.q18, "_worker", None)
        if worker is not None:
            try:
                worker.close()
                r.q18._worker = None
            except Exception:
                pass
        make_report(rows, status, reason)

def test():
    assert "r.run(" not in diagnostic.__code__.co_names
    assert DIRECTIONS == ("METEORA_TO_PUMP", "PUMP_TO_METEORA")
    assert len(DIRECTIONS) == 2
    assert "sendTransaction" not in diagnostic.__code__.co_names
    print("[TEST PASS] ORACLE183 isolated bootstrap, both directions, no scanner")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--run", action="store_true")
    p.add_argument("--max-pairs", type=int, default=11)
    args = p.parse_args()
    if args.test:
        test()
    elif args.run:
        diagnostic(max(1, min(args.max_pairs, 25)))
    else:
        p.error("Use --test or --run")
