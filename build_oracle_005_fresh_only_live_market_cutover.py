from pathlib import Path
import py_compile
import re

ROOT=Path.cwd()

ENGINE=ROOT/(
    "qseries_v2/oracle_execution/"
    "oracle_003_unified_physical_execution_engine.py"
)

TEST=ROOT/(
    "test_oracle_005_fresh_only_live_market_cutover.py"
)

if not ENGINE.is_file():
    raise SystemExit(
        "[FAIL] unified Oracle execution engine missing"
    )

src=ENGINE.read_text(
    encoding="utf-8"
)

# ============================================================
# ORACLE-005
#
# Execution intake rule:
#
#   LIVE MRIYA OBSERVATION
#       ->
#   <= 90 SECOND HOT TOKEN
#       ->
#   CURRENT EXACT PUMP/METEORA BINDING
#       ->
#   PHYSICAL 0.001 SOL PACKET
#       ->
#   SIGNED SIMULATION
#       ->
#   LIVE ONLY AFTER PASS
#
# QARB-080 historical binding memory remains useful to Oracle
# learning, but is NEVER an execution-candidate fallback.
# ============================================================

pat=re.compile(
    r'def live_universe_rows\(root\):'
    r'[\s\S]*?'
    r'(?=\n\ndef run\()'
)

replacement=r'''def live_universe_rows(root):
    import subprocess
    import sys

    root=Path(root)

    watch_seconds=float(
        os.getenv(
            "ORACLE_FRESH_DISCOVERY_SECONDS",
            "120"
        )
    )

    poll_seconds=float(
        os.getenv(
            "ORACLE_FRESH_DISCOVERY_POLL_SECONDS",
            "2"
        )
    )

    hot_seconds=min(
        90.0,
        float(
            q80.q45.HOT
        )
    )

    deadline=(
        time.monotonic()
        +max(
            1.0,
            watch_seconds
        )
    )

    discovery=subprocess.Popen(
        [
            sys.executable,
            "run_qarb_043b_paced_mriya_token_discovery.py",
            "--seconds",
            str(
                max(
                    1.0,
                    watch_seconds
                )
            )
        ],
        cwd=str(root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print(
        "[FRESH_DISCOVERY] "
        "source=MRIYA "
        "window=%.1fs "
        "hot_max_age=%.1fs "
        "stale_memory_execution=FALSE"%(
            watch_seconds,
            hot_seconds
        ),
        flush=True
    )

    last_status=0.0

    try:
        while (
            time.monotonic()
            <deadline
        ):
            now=time.time()

            registry=(
                q80.q45.d.load()
            )

            tokens=(
                registry.get(
                    "tokens"
                )
                or {}
            )

            recent=[]

            for token,info in tokens.items():

                age=max(
                    0.0,
                    now-float(
                        info.get(
                            "last_seen_epoch",
                            0.0
                        )
                        or 0.0
                    )
                )

                if age<=hot_seconds:
                    recent.append(
                        (
                            token,
                            age
                        )
                    )

            recent.sort(
                key=lambda x:x[1]
            )

            # Do not hammer binding RPC when Mriya has not
            # observed anything current.
            if not recent:

                elapsed=(
                    watch_seconds
                    -max(
                        0.0,
                        deadline
                        -time.monotonic()
                    )
                )

                if (
                    elapsed-last_status
                    >=10.0
                ):
                    print(
                        "[FRESH_WAIT] "
                        "elapsed=%.1fs "
                        "recent_mriya_tokens=0"%(
                            elapsed
                        ),
                        flush=True
                    )

                    last_status=elapsed

                time.sleep(
                    min(
                        poll_seconds,
                        max(
                            0.0,
                            deadline
                            -time.monotonic()
                        )
                    )
                )

                continue

            print(
                "[FRESH_SEEN] "
                "tokens=%d youngest_age=%.3fs"%(
                    len(recent),
                    recent[0][1]
                ),
                flush=True
            )

            # q45 performs CURRENT exact cross-venue binding.
            payload,active=(
                q80.q45.classify()
            )

            fresh=[]

            for row in active:

                life=(
                    row.get(
                        "lifecycle"
                    )
                    or {}
                )

                age=float(
                    life.get(
                        "seconds_since_last_seen",
                        1e18
                    )
                )

                if age>hot_seconds:
                    continue

                token=row.get(
                    "token"
                )

                pump=row.get(
                    "pump_pool"
                )

                meta=(
                    row.get(
                        "meteora_meta"
                    )
                    or {}
                )

                if not (
                    token
                    and pump
                    and meta.get(
                        "address"
                    )
                    and meta.get(
                        "token_x"
                    )
                    and meta.get(
                        "token_y"
                    )
                ):
                    continue

                x=dict(row)

                # The historical/paper size is irrelevant.
                # Oracle's first physical capital remains
                # exactly 0.001 SOL.
                x[
                    "size_sol"
                ]=MICRO_SOL

                x[
                    "micro_lamports"
                ]=MICRO_LAMPORTS

                fresh.append(
                    x
                )

            if not fresh:

                print(
                    "[FRESH_BIND_HOLD] "
                    "recent_mriya=%d "
                    "exact_bound_hot=0"%(
                        len(recent)
                    ),
                    flush=True
                )

                time.sleep(
                    min(
                        poll_seconds,
                        max(
                            0.0,
                            deadline
                            -time.monotonic()
                        )
                    )
                )

                continue

            cert=q81.certify(
                root
            )

            proven=set(
                cert.get(
                    "recyclable_proven_tokens",
                    []
                )
            )

            for row in fresh:
                row[
                    "_oracle_proven_priority"
                ]=(
                    row["token"]
                    in proven
                )

            # CURRENT physical freshness first.
            # Historical proof only breaks ties among fresh rows.
            fresh.sort(
                key=lambda x:(
                    1
                    if x.get(
                        "_oracle_proven_priority"
                    )
                    else 0,

                    -float(
                        (
                            x.get(
                                "lifecycle"
                            )
                            or {}
                        ).get(
                            "seconds_since_last_seen",
                            1e18
                        )
                    )
                ),
                reverse=True
            )

            print(
                "[FRESH_UNIVERSE] "
                "hot_exact_bound=%d "
                "proven_among_fresh=%d"%(
                    len(fresh),

                    sum(
                        bool(
                            x.get(
                                "_oracle_proven_priority"
                            )
                        )
                        for x in fresh
                    )
                ),
                flush=True
            )

            for row in fresh:

                age=float(
                    (
                        row.get(
                            "lifecycle"
                        )
                        or {}
                    ).get(
                        "seconds_since_last_seen",
                        0.0
                    )
                )

                print(
                    "[FRESH_ROW] "
                    "token=%s "
                    "age=%.3fs "
                    "proven=%s "
                    "pump=%s "
                    "meteora=%s"%(
                        row[
                            "token"
                        ][:10],

                        age,

                        bool(
                            row.get(
                                "_oracle_proven_priority"
                            )
                        ),

                        row[
                            "pump_pool"
                        ][:12],

                        row[
                            "meteora_meta"
                        ][
                            "address"
                        ][:12],
                    ),
                    flush=True
                )

            return fresh

        print(
            "[FRESH_DISCOVERY_HOLD] "
            "no <=90s exact-bound "
            "PumpSwap->Meteora candidate "
            "during %.1fs window"%(
                watch_seconds
            ),
            flush=True
        )

        return []

    finally:
        try:
            if (
                discovery.poll()
                is None
            ):
                discovery.terminate()

                discovery.wait(
                    timeout=5
                )

        except Exception:
            try:
                discovery.kill()
            except Exception:
                pass
'''

if not pat.search(src):
    raise SystemExit(
        "[FAIL] ORACLE-004 live universe seam missing"
    )

src=pat.sub(
    replacement.rstrip(),
    src,
    count=1
)

# Correct runtime label as well. ORACLE-004 revealed the
# previous label survived from ORACLE-003.
src=src.replace(
    "[ORACLE-003]",
    "[ORACLE-005]"
)

src=src.replace(
    "[ORACLE-004]",
    "[ORACLE-005]"
)

ENGINE.write_text(
    src,
    encoding="utf-8"
)

py_compile.compile(
    str(ENGINE),
    doraise=True
)


TEST.write_text(
r'''import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as q
)


class T(unittest.TestCase):

    def test_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "ORACLE"
        )


    def test_exact_micro_cap(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_fresh_only(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertIn(
            "hot_seconds",
            s
        )

        self.assertIn(
            "seconds_since_last_seen",
            s
        )

        self.assertIn(
            "age>hot_seconds",
            s
        )


    def test_no_execution_memory_fallback(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertNotIn(
            "q80.select_rows",
            s
        )

        self.assertNotIn(
            "q80.MEMORY",
            s
        )


    def test_live_mriya_discovery(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertIn(
            "run_qarb_043b_paced_mriya_token_discovery.py",
            s
        )

        self.assertIn(
            "q80.q45.classify",
            s
        )


    def test_current_binding_required(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertIn(
            'meta.get(',
            s
        )

        self.assertIn(
            '"pump_pool"',
            s
        )


    def test_strategy_unchanged(self):
        s=inspect.getsource(
            q.exact_route
        )

        self.assertIn(
            "native_pump_buy_ixs",
            s
        )

        self.assertIn(
            "meteora_swap",
            s
        )


    def test_signed_physical_gate(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
''',
    encoding="utf-8"
)

py_compile.compile(
    str(TEST),
    doraise=True
)

print(
    "[PASS] ORACLE-005 fresh-only live-market cutover installed"
)

print(
    "[DISCOVERY] Mriya remains live for up to 120 seconds"
)

print(
    "[EXEC_INTAKE] HOT <=90s exact-bound tokens ONLY"
)

print(
    "[STALE_MEMORY] execution fallback permanently disabled"
)

print(
    "[HISTORY] proven status may prioritize but never resurrect"
)

print(
    "[STRATEGY] PumpSwap -> Meteora DLMM unchanged"
)

print(
    "[PHYSICAL] exact packet + signed simulation mandatory"
)

print(
    "[CAP] exact strategy principal 0.001 SOL"
)

print(
    "[OWNER] ORACLE"
)