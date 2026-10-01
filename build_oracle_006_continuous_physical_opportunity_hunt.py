from pathlib import Path
import py_compile
import re

ROOT=Path.cwd()

ENGINE=ROOT/(
    "qseries_v2/oracle_execution/"
    "oracle_003_unified_physical_execution_engine.py"
)

TEST=ROOT/(
    "test_oracle_006_continuous_physical_opportunity_hunt.py"
)

if not ENGINE.is_file():
    raise SystemExit(
        "[FAIL] Oracle unified physical engine missing"
    )

src=ENGINE.read_text(
    encoding="utf-8"
)

# ============================================================
# 1. Give every fresh candidate an absolute HOT expiry.
#
# Mriya only introduces/replenishes the candidate.
# Once admitted, Oracle keeps repricing the actual Pump and
# Meteora pools until the candidate's 90-second freshness
# boundary expires.
# ============================================================

old='''                x[
                    "micro_lamports"
                ]=MICRO_LAMPORTS

                fresh.append(
                    x
                )'''

new='''                x[
                    "micro_lamports"
                ]=MICRO_LAMPORTS

                x[
                    "_oracle_hot_valid_until"
                ]=(
                    time.time()
                    +max(
                        0.0,
                        hot_seconds-age
                    )
                )

                fresh.append(
                    x
                )'''

if old not in src:
    if "_oracle_hot_valid_until" not in src:
        raise SystemExit(
            "[FAIL] fresh candidate admission seam missing"
        )
else:
    src=src.replace(
        old,
        new,
        1
    )

# ============================================================
# 2. Add physical hunt counters.
# ============================================================

old2='''    sends=0
    confirmed=0
    rejects=0

    while (
        time.monotonic()
        <deadline
    ):'''

new2='''    sends=0
    confirmed=0
    rejects=0
    hunt_round=0

    while (
        time.monotonic()
        <deadline
    ):
        hunt_round+=1

        now_epoch=time.time()

        rows=[
            row
            for row in rows
            if float(
                row.get(
                    "_oracle_hot_valid_until",
                    now_epoch
                )
            ) > now_epoch
        ]

        if not rows:
            print(
                "[ORACLE-006 HOLD] "
                "fresh candidate set expired "
                "without executable profit",
                flush=True
            )

            save({
                "revision":
                    "ORACLE_006",

                "status":
                    "HOT_SET_EXPIRED_NO_EXECUTABLE_PROFIT",

                "execution_owner":
                    "ORACLE",

                "sends":
                    sends,

                "confirmed":
                    confirmed,

                "rejects":
                    rejects,

                "hunt_rounds":
                    hunt_round-1,
            })

            return 2

        print(
            "[HUNT_ROUND] "
            "round=%d active=%d"%(
                hunt_round,
                len(rows)
            ),
            flush=True
        )'''

if old2 not in src:
    if "hunt_round=0" not in src:
        raise SystemExit(
            "[FAIL] execution loop seam missing"
        )
else:
    src=src.replace(
        old2,
        new2,
        1
    )

# ============================================================
# 3. Replace one-shot PAPER_HOLD with continuous repricing.
# ============================================================

pattern=re.compile(
    r'''        if not prepared:
            if mode=="PAPER":
                print\(
                    "\[PAPER_HOLD\] "
                    "no currently executable "
                    "PumpSwap->Meteora packet",
                    flush=True
                \)

                save\(\{
[\s\S]*?
                return 2

            time\.sleep\(
                min\(
                    scan_seconds,
                    max\(
                        0,
                        deadline
                        -time\.monotonic\(\)
                    \)
                \)
            \)

            continue'''
)

replacement='''        if not prepared:
            remaining_hot=max(
                0.0,
                max(
                    float(
                        row.get(
                            "_oracle_hot_valid_until",
                            time.time()
                        )
                    )
                    for row in rows
                )
                -time.time()
            )

            print(
                "[HUNT_HOLD] "
                "round=%d "
                "no_executable_now=True "
                "remaining_hot=%.1fs "
                "next_reprice=%.1fs"%(
                    hunt_round,
                    remaining_hot,
                    max(
                        3.0,
                        float(
                            scan_seconds
                        )
                    )
                ),
                flush=True
            )

            sleep_for=min(
                max(
                    3.0,
                    float(
                        scan_seconds
                    )
                ),
                remaining_hot,
                max(
                    0.0,
                    deadline
                    -time.monotonic()
                )
            )

            if sleep_for<=0:
                continue

            time.sleep(
                sleep_for
            )

            continue'''

if pattern.search(src):
    src=pattern.sub(
        replacement,
        src,
        count=1
    )
elif "[HUNT_HOLD]" not in src:
    raise SystemExit(
        "[FAIL] one-shot PAPER_HOLD seam missing"
    )

# ============================================================
# 4. PAPER success message stays immediate.
#    LIVE success still broadcasts only after exact signed sim.
# ============================================================

src=src.replace(
    "[ORACLE-005]",
    "[ORACLE-006]"
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


    def test_micro_cap(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_hot_expiry(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertIn(
            "_oracle_hot_valid_until",
            s
        )

        self.assertIn(
            "hot_seconds-age",
            s
        )


    def test_continuous_hunt(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "[HUNT_ROUND]",
            s
        )

        self.assertIn(
            "[HUNT_HOLD]",
            s
        )

        self.assertIn(
            "hunt_round",
            s
        )


    def test_no_one_shot_paper_hold(self):
        s=inspect.getsource(
            q.run
        )

        self.assertNotIn(
            "[PAPER_HOLD]",
            s
        )


    def test_strategy(self):
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


    def test_signed_sim_required(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


    def test_no_new_alt(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "createLookupTable",
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
    "[PASS] ORACLE-006 continuous physical opportunity hunt installed"
)

print(
    "[DISCOVERY] fresh Mriya replenishment preserved"
)

print(
    "[HUNT] every fresh Pump/Meteora candidate repeatedly repriced"
)

print(
    "[WINDOW] candidate remains eligible only inside HOT <=90s"
)

print(
    "[MARKET] Pump and Meteora state rebuilt each hunt round"
)

print(
    "[PROFIT] guaranteed physical net must remain positive"
)

print(
    "[SIM] exact signed simulation remains mandatory"
)

print(
    "[PAPER] zero broadcast"
)

print(
    "[LIVE] first passing candidate still limited to one canary"
)

print(
    "[CAP] 0.001 SOL principal"
)

print(
    "[OWNER] ORACLE"
)