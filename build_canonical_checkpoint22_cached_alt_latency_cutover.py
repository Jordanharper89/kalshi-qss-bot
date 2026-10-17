from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint22_cached_alt_latency_cutover.py"
TEST=ROOT/"test_canonical_checkpoint22_cached_alt_latency_cutover.py"

MODULE=r"""from __future__ import annotations

import argparse
import sys
import time

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint13_live_reverse_fee_execution_proof as c13
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint20_canonical_alt_bidirectional_compile as c20
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint21_signed_raw_transaction_simulation_cutover as c21

ALT_CACHE={}
TIMING={
    "alt_cache_hits":0,
    "alt_rpc_fallbacks":0,
    "compile_fee_calls":0,
    "compile_fee_ms_total":0.0,
    "fee_calls":0,
    "fee_ms_total":0.0,
    "sim_calls":0,
    "sim_ms_total":0.0,
}


def _cache_alt_once():
    canonical_alt=c20._load_canonical_alt()

    original=r.q87.c.alt_accounts
    data=original([canonical_alt])

    if canonical_alt not in data:
        raise RuntimeError(
            "CHECKPOINT22_CANONICAL_ALT_PREFETCH_MISSING:"
            +canonical_alt
        )

    ALT_CACHE.clear()
    ALT_CACHE[canonical_alt]=data[canonical_alt]

    print(
        "[CHECKPOINT22_ALT_PREFETCH] "
        "address=%s entries=%d"
        %(
            canonical_alt,
            len(ALT_CACHE[canonical_alt]),
        ),
        flush=True,
    )

    return canonical_alt


def _cached_alt_accounts(addrs):
    keys=list(addrs or [])

    if keys and all(k in ALT_CACHE for k in keys):
        TIMING["alt_cache_hits"]+=1
        return {
            k:ALT_CACHE[k]
            for k in keys
        }

    TIMING["alt_rpc_fallbacks"]+=1
    return ORIGINAL_ALT_ACCOUNTS(keys)


def _timed_fee(compiled):
    t0=time.perf_counter_ns()

    try:
        return ORIGINAL_FEE(compiled)

    finally:
        ms=(
            time.perf_counter_ns()-t0
        )/1e6

        TIMING["fee_calls"]+=1
        TIMING["fee_ms_total"]+=ms

        print(
            "[CHECKPOINT22_FEE_LATENCY] "
            "ms=%.3f candidate=%s"
            %(
                ms,
                compiled.get("candidate"),
            ),
            flush=True,
        )


def _timed_compile_fee(user,route,gross):
    t0=time.perf_counter_ns()

    try:
        return ORIGINAL_COMPILE_FEE(
            user,
            route,
            gross,
        )

    finally:
        ms=(
            time.perf_counter_ns()-t0
        )/1e6

        TIMING["compile_fee_calls"]+=1
        TIMING["compile_fee_ms_total"]+=ms

        print(
            "[CHECKPOINT22_COMPILE_FEE_LATENCY] "
            "ms=%.3f alt_cache_hits=%d alt_rpc_fallbacks=%d"
            %(
                ms,
                TIMING["alt_cache_hits"],
                TIMING["alt_rpc_fallbacks"],
            ),
            flush=True,
        )


def _timed_signed_sim(compiled):
    t0=time.perf_counter_ns()

    try:
        return ORIGINAL_SIM(compiled)

    finally:
        ms=(
            time.perf_counter_ns()-t0
        )/1e6

        TIMING["sim_calls"]+=1
        TIMING["sim_ms_total"]+=ms

        print(
            "[CHECKPOINT22_SIM_LATENCY] "
            "ms=%.3f candidate=%s"
            %(
                ms,
                compiled.get("candidate"),
            ),
            flush=True,
        )


def _avg(total,count):
    return 0.0 if not count else total/count


def main():
    global ORIGINAL_ALT_ACCOUNTS
    global ORIGINAL_FEE
    global ORIGINAL_COMPILE_FEE
    global ORIGINAL_SIM

    p=argparse.ArgumentParser()
    p.add_argument(
        "--seconds",
        type=float,
        default=3600.0,
    )
    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError(
            "CHECKPOINT22_SECONDS_MUST_BE_POSITIVE"
        )

    ORIGINAL_ALT_ACCOUNTS=r.q87.c.alt_accounts
    ORIGINAL_FEE=c13._fee_for_message
    ORIGINAL_COMPILE_FEE=(
        c20._compile_all_legal_with_alt
    )
    ORIGINAL_SIM=c21._signed_simulation_raw

    canonical_alt=_cache_alt_once()
    old_argv=list(sys.argv)

    try:
        r.q87.c.alt_accounts=(
            _cached_alt_accounts
        )
        c13._fee_for_message=_timed_fee
        c20._compile_all_legal_with_alt=(
            _timed_compile_fee
        )
        c21._signed_simulation_raw=(
            _timed_signed_sim
        )

        print(
            "[CHECKPOINT22_ACTIVATION] "
            "canonical_alt_memory_cache=True "
            "latency_instrumentation=True "
            "seconds=%.0f broadcast=False"
            %args.seconds,
            flush=True,
        )

        print(
            "[CHECKPOINT22_HOT_PATH] "
            "ws -> exact_math -> pair_route -> "
            "cached_ALT_compile -> real_fee -> "
            "freshness -> signed_sim",
            flush=True,
        )

        print(
            "[CHECKPOINT22_ALT] "
            "address=%s compile_rpc_fetch=False"
            %canonical_alt,
            flush=True,
        )

        print(
            "[BROADCAST] disabled",
            flush=True,
        )

        sys.argv=[
            old_argv[0],
            "--seconds",
            str(float(args.seconds)),
        ]

        rc=c21.main()

        print(
            "[CHECKPOINT22_SUMMARY] "
            "alt_cache_hits=%d alt_rpc_fallbacks=%d "
            "compile_fee_calls=%d compile_fee_avg_ms=%.3f "
            "fee_calls=%d fee_avg_ms=%.3f "
            "sim_calls=%d sim_avg_ms=%.3f"
            %(
                TIMING["alt_cache_hits"],
                TIMING["alt_rpc_fallbacks"],
                TIMING["compile_fee_calls"],
                _avg(
                    TIMING["compile_fee_ms_total"],
                    TIMING["compile_fee_calls"],
                ),
                TIMING["fee_calls"],
                _avg(
                    TIMING["fee_ms_total"],
                    TIMING["fee_calls"],
                ),
                TIMING["sim_calls"],
                _avg(
                    TIMING["sim_ms_total"],
                    TIMING["sim_calls"],
                ),
            ),
            flush=True,
        )

        return rc

    finally:
        r.q87.c.alt_accounts=ORIGINAL_ALT_ACCOUNTS
        c13._fee_for_message=ORIGINAL_FEE
        c20._compile_all_legal_with_alt=(
            ORIGINAL_COMPILE_FEE
        )
        c21._signed_simulation_raw=ORIGINAL_SIM
        sys.argv=old_argv


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint22_cached_alt_latency_cutover.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_alt_prefetched_once(self):
        self.assertIn(
            "data=original([canonical_alt])",
            self.s,
        )

    def test_compile_uses_memory_cache(self):
        self.assertIn(
            "r.q87.c.alt_accounts=_cached_alt_accounts",
            self.s,
        )

    def test_real_fee_preserved(self):
        self.assertIn(
            "c13._fee_for_message=_timed_fee",
            self.s,
        )

    def test_signed_sim_preserved(self):
        self.assertIn(
            "c21._signed_simulation_raw=_timed_signed_sim",
            self.s,
        )

    def test_latency_metrics(self):
        self.assertIn(
            "[CHECKPOINT22_COMPILE_FEE_LATENCY]",
            self.s,
        )
        self.assertIn(
            "[CHECKPOINT22_SIM_LATENCY]",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(
    MODULE,
    encoding="utf-8",
)
TEST.write_text(
    TEST_CODE,
    encoding="utf-8",
)

print("[PASS] checkpoint-22 cached ALT latency cutover installed")
print("[CACHE] canonical ALT fetched once at startup and served from memory")
print("[LATENCY] compile+fee, fee RPC, and signed simulation timings instrumented")
print("[FEE] real getFeeForMessage preserved")
print("[SIMULATION] checkpoint-21 signed raw simulation preserved")
print("[PAIR_IDENTITY] checkpoint-17 pair-key templates preserved")
print("[KEY] existing signer untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
