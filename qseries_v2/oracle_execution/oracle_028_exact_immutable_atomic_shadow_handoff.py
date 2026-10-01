from __future__ import annotations
import argparse, json, threading, time
from pathlib import Path

from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_execution import oracle_027_immutable_snapshot_generation_guard as q27
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as atomic

EXECUTION_AUTHORITY = False
PAPER_ONLY = True
REAL_MONEY_MOVED = False

DEBOUNCE_SECONDS = 2.0
BASE_429_BACKOFF_SECONDS = 2.0
MAX_429_BACKOFF_SECONDS = 30.0

class AtomicShadow:
    def __init__(self):
        self.cv = threading.Condition()
        self.latest = {}
        self.stop = False
        self.attempts = 0
        self.composed = 0
        self.compiled = 0
        self.simulated = 0
        self.profitable = 0
        self.rejected = 0
        self.coalesced = 0
        self.debounced = 0
        self.rate_limited = 0
        self.last_submit = {}
        self.backoff_until = {}
        self.rows = []
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def submit(self, best):
        if best.get("direction") != "PUMP_TO_METEORA":
            return False
        if int(best.get("local_net", 0)) <= 0:
            return False

        token = str(best["token"])
        now = time.monotonic()
        key = (
            token,
            round(float(best["size_sol"]), 9),
            str(best["pump_pool"]),
            str(best["meteora"]["address"]),
        )

        with self.cv:
            if now < float(self.backoff_until.get(token, 0.0)):
                self.debounced += 1
                return False

            if now - float(self.last_submit.get(key, 0.0)) < DEBOUNCE_SECONDS:
                self.debounced += 1
                return False

            self.last_submit[key] = now
            if token in self.latest:
                self.coalesced += 1
            self.latest[token] = dict(best)
            self.cv.notify()

        return True

    def _take(self):
        with self.cv:
            while not self.stop and not self.latest:
                self.cv.wait(timeout=0.2)

            if not self.latest:
                return None

            token = next(iter(self.latest))
            return self.latest.pop(token)

    def _mark_429(self, token):
        self.rate_limited += 1
        prior = max(
            0.0,
            float(self.backoff_until.get(token, 0.0)) - time.monotonic(),
        )
        delay = min(
            MAX_429_BACKOFF_SECONDS,
            max(
                BASE_429_BACKOFF_SECONDS,
                prior * 2.0 if prior else BASE_429_BACKOFF_SECONDS,
            ),
        )
        self.backoff_until[token] = time.monotonic() + delay
        return delay

    def _loop(self):
        while True:
            best = self._take()
            if best is None:
                if self.stop:
                    break
                continue

            self.attempts += 1

            token = str(best["token"])
            pump = str(best["pump_pool"])
            meteora = str(best["meteora"]["address"])
            size = float(best["size_sol"])

            try:
                kp, user = atomic.c.sim_identity()

                route = atomic.compose_reverse_candidates(
                    user,
                    token,
                    pump,
                    meteora,
                    size,
                )
                self.composed += 1

                bh = atomic.c.rpc(
                    "getLatestBlockhash",
                    [{"commitment": "processed"}],
                )["value"]["blockhash"]

                winner, attempts = atomic.attempt_candidate_simulations(
                    user,
                    kp,
                    route,
                    bh,
                )

                compiled = sum(1 for row in attempts if row.get("compiled"))
                self.compiled += compiled
                self.simulated += compiled

                if winner:
                    self.profitable += 1
                else:
                    self.rejected += 1

                self.rows.append({
                    "token": token,
                    "pump_pool": pump,
                    "meteora_pool": meteora,
                    "direction": "PUMP_TO_METEORA",
                    "size_sol": size,
                    "exact_local_net": int(best["local_net"]),
                    "exact_local_bps": float(best["local_bps"]),
                    "attempts": attempts,
                    "winner": winner,
                })

                print(
                    "[ORACLE028_ATOMIC_SHADOW] token=%s size=%.3f exact_bps=%+.2f compiled=%d profitable=%s"
                    % (
                        token[:10],
                        size,
                        float(best["local_bps"]),
                        compiled,
                        bool(winner),
                    ),
                    flush=True,
                )

            except Exception as exc:
                text = "%s:%s" % (type(exc).__name__, str(exc)[:500])

                if "429" in text or "Too Many Requests" in text:
                    delay = self._mark_429(token)
                    print(
                        "[ORACLE028_RATE_LIMIT] token=%s size=%.3f backoff_s=%.1f reason=%s"
                        % (token[:10], size, delay, text[:220]),
                        flush=True,
                    )
                else:
                    self.rejected += 1
                    print(
                        "[ORACLE028_ATOMIC_REJECT] token=%s size=%.3f reason=%s"
                        % (token[:10], size, text[:220]),
                        flush=True,
                    )

                self.rows.append({
                    "token": token,
                    "pump_pool": pump,
                    "meteora_pool": meteora,
                    "direction": "PUMP_TO_METEORA",
                    "size_sol": size,
                    "exact_local_net": int(best["local_net"]),
                    "exact_local_bps": float(best["local_bps"]),
                    "error": text,
                })

    def close(self):
        with self.cv:
            self.stop = True
            self.cv.notify_all()
        self.thread.join(timeout=30)

class ShadowLane(q27.ImmutableLatestStateLane):
    def __init__(self, shadow):
        super().__init__()
        self.shadow = shadow

    def _price(self, token, row):
        snap, slot, received_ns, generation = row

        start_ms = max(
            0.0,
            (time.perf_counter_ns() - received_ns) / 1e6,
        )
        self.event_start_ms.append(start_ms)

        if start_ms > q20.MAX_START_AGE_MS:
            self.stale_drops += 1
            print(
                "[ORACLE028_STALE_DROP] token=%s slot=%s age_ms=%.3f"
                % (token[:10], slot, start_ms),
                flush=True,
            )
            return

        t0 = time.perf_counter_ns()
        snap = q27.materialize_snapshot(snap)
        materialize_ms = (time.perf_counter_ns() - t0) / 1e6
        self.materialize_ms.append(materialize_ms)

        self._warm(snap)
        started = time.perf_counter_ns()
        rows = []

        for size in q20.FAST_SIZES:
            rows.extend(q18.exact_snapshot_opportunities(snap, size))
            self.evaluations += 2
            if self.superseded(token, generation):
                self.scan_replaced += 1
                return

        best = max(rows, key=lambda x: x["local_net"])

        if float(best["local_bps"]) >= q20.EXPAND_GATE_BPS:
            for size in q20.EXPAND_SIZES:
                rows.extend(q18.exact_snapshot_opportunities(snap, size))
                self.evaluations += 2
                if self.superseded(token, generation):
                    self.scan_replaced += 1
                    return
            best = max(rows, key=lambda x: x["local_net"])

        if self.superseded(token, generation):
            self.end_generation_drops += 1
            return

        scan_ms = (time.perf_counter_ns() - started) / 1e6
        self.scan_ms.append(scan_ms)
        self.processed += 1

        if int(best["local_net"]) > 0:
            self.positive += 1

        if self.best is None or int(best["local_net"]) > int(self.best["local_net"]):
            self.best = dict(best)

        print(
            "[ORACLE028_EXACT_CURRENT] token=%s slot=%s dir=%s size=%.3f "
            "bps=%+.2f net=%+d start_ms=%.3f materialize_ms=%.3f scan_ms=%.3f"
            % (
                token[:10],
                slot,
                best["direction"],
                float(best["size_sol"]),
                float(best["local_bps"]),
                int(best["local_net"]),
                start_ms,
                materialize_ms,
                scan_ms,
            ),
            flush=True,
        )

        if int(best["local_net"]) > 0 and best["direction"] == "PUMP_TO_METEORA":
            if self.shadow.submit(best):
                print(
                    "[ORACLE028_HANDOFF_CURRENT] token=%s slot=%s size=%.3f bps=%+.2f"
                    % (
                        token[:10],
                        slot,
                        float(best["size_sol"]),
                        float(best["local_bps"]),
                    ),
                    flush=True,
                )

def install(shadow):
    q23.install_hot_token_net()
    q20._pair_snapshot = q27.patched_pair_snapshot
    q20.LatestStateLane = lambda: ShadowLane(shadow)

def run(seconds=60.0):
    root = Path.cwd()
    state, cap = q25.prepare_once(root)
    q25.bind_cached_state(state)
    q25.install_hot_math_and_prewarm(state)

    shadow = AtomicShadow()
    install(shadow)

    print("[ORACLE-028] FULL REPLACEMENT CURRENT-SCAN ATOMIC SHADOW", flush=True)
    print("[HANDOFF] current immutable scan result only", flush=True)
    print("[QUEUE] latest-only per token + exact-size debounce", flush=True)
    print("[429] per-token backoff", flush=True)
    print("[BROADCAST] disabled", flush=True)

    try:
        rc = q20.run(float(seconds))
    finally:
        shadow.close()

    payload = {
        "oracle_build": "ORACLE-028",
        "revision": "CURRENT_SCAN_FULL_REPLACEMENT",
        "shadow_attempts": shadow.attempts,
        "composed": shadow.composed,
        "compiled_candidates": shadow.compiled,
        "simulated_candidates": shadow.simulated,
        "profitable_simulations": shadow.profitable,
        "rejected": shadow.rejected,
        "coalesced": shadow.coalesced,
        "debounced": shadow.debounced,
        "rate_limited": shadow.rate_limited,
        "rows": shadow.rows[-50:],
        "execution_authority": False,
        "paper_only": True,
        "real_money_moved": False,
        "broadcast": False,
    }

    report = Path(
        "runtime_state/oracle/oracle_live_execution/"
        "oracle_028_exact_immutable_atomic_shadow_handoff.json"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    print(
        "[ORACLE028_COMPLETE] attempts=%d composed=%d compiled=%d simulated=%d "
        "profitable=%d rejected=%d coalesced=%d debounced=%d rate_limited=%d"
        % (
            shadow.attempts,
            shadow.composed,
            shadow.compiled,
            shadow.simulated,
            shadow.profitable,
            shadow.rejected,
            shadow.coalesced,
            shadow.debounced,
            shadow.rate_limited,
        ),
        flush=True,
    )
    print("[REPORT] %s" % report, flush=True)
    print("[BROADCAST] disabled", flush=True)
    return rc

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=60.0)
    args = ap.parse_args(argv)
    return run(args.seconds)

if __name__ == "__main__":
    raise SystemExit(main())
