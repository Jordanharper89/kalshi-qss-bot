from pathlib import Path
import py_compile

ROOT=Path.cwd()
OUTDIR=ROOT/"qseries_v2/oracle_execution"

MODULE=OUTDIR/"oracle_011_adaptive_physical_breadth_scanner.py"
LAUNCHER=ROOT/"run_oracle_adaptive_physical_scanner.py"
TEST=ROOT/"test_oracle_011_adaptive_physical_breadth_scanner.py"

if not (
    OUTDIR/
    "oracle_010_continuous_physical_opportunity_scanner.py"
).is_file():
    raise SystemExit(
        "[FAIL] ORACLE-010 missing"
    )


MODULE.write_text(
r'''
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as engine
)

from qseries_v2.oracle_execution import (
    oracle_010_continuous_physical_opportunity_scanner
    as q10
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


FULL_SIZES=tuple(
    q10.SIZE_SOL
)


# Broad physical probes first.
#
# Covers micro, small, medium and original large
# operating regions without spending 13 Node/RPC
# builds on every obviously losing token.
ANCHOR_SIZES=(
    0.001,
    0.010,
    0.050,
    0.180,
    0.500,
    1.400,
)


LIVE_CANARY_SOL=0.001


OUT=Path(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_011_adaptive_physical_breadth_scanner.json"
)


def best_quote_bps(
    rows
):
    vals=[
        float(
            x[
                "quote_bps"
            ]
        )
        for x in rows
        if x.get(
            "ok"
        )
    ]

    if not vals:
        return None

    return max(
        vals
    )


def has_positive(
    rows
):
    return any(
        bool(
            x.get(
                "guaranteed_positive"
            )
        )
        for x in rows
    )


def evaluate_sizes(
    user,
    pair,
    sizes,
    stage
):
    out=[]

    for size in sizes:
        row=q10.evaluate_size(
            user,
            pair,
            size
        )

        row[
            "scan_stage"
        ]=stage

        out.append(
            row
        )

        if row.get(
            "ok"
        ):
            print(
                "[%s] "
                "token=%s "
                "size=%.3f "
                "quote=%+.9f_SOL "
                "qbps=%+.2f "
                "guaranteed=%+.9f_SOL "
                "gbps=%+.2f"%(
                    stage,
                    pair.token[:10],
                    size,

                    row[
                        "quote_net_lamports"
                    ]/1e9,

                    row[
                        "quote_bps"
                    ],

                    row[
                        "guaranteed_net_lamports"
                    ]/1e9,

                    row[
                        "guaranteed_bps"
                    ],
                ),
                flush=True
            )

        else:
            print(
                "[%s_REJECT] "
                "token=%s "
                "size=%.3f "
                "reason=%s"%(
                    stage,
                    pair.token[:10],
                    size,
                    row.get(
                        "reason"
                    ),
                ),
                flush=True
            )

    return out


def run(
    seconds=300.0
):
    root=Path.cwd()

    kp,user=(
        engine.base.require_keypair()
    )

    balance=int(
        engine.rpc(
            "getBalance",
            [
                user,
                {
                    "commitment":
                        "confirmed"
                }
            ]
        )["value"]
    )


    seconds=float(
        os.getenv(
            "ORACLE_ADAPTIVE_SCAN_SECONDS",
            str(
                seconds
            )
        )
    )


    refresh_seconds=float(
        os.getenv(
            "ORACLE_ADAPTIVE_REFRESH_SECONDS",
            "5"
        )
    )


    # If the best official quote is within this distance
    # of breakeven, spend the extra RPC/SDK work to map
    # the entire size envelope.
    refine_bps=float(
        os.getenv(
            "ORACLE_ADAPTIVE_REFINE_BPS",
            "-100"
        )
    )


    max_tokens=int(
        os.getenv(
            "ORACLE_ADAPTIVE_MAX_TOKENS_PER_CYCLE",
            "24"
        )
    )


    print(
        "[ORACLE-011] "
        "ADAPTIVE PHYSICAL BREADTH SCANNER",
        flush=True
    )

    print(
        "[MODE] "
        "PAPER_ONLY=True "
        "execution_authority=FALSE "
        "real_money_moved=FALSE",
        flush=True
    )

    print(
        "[SOURCE_OF_TRUTH] "
        "OFFICIAL_PHYSICAL_ONLY",
        flush=True
    )

    print(
        "[LEGACY_PROFIT] "
        "PROHIBITED",
        flush=True
    )

    print(
        "[WALLET] %s"%user,
        flush=True
    )

    print(
        "[BALANCE] %.9f SOL"%(
            balance/1e9
        ),
        flush=True
    )

    print(
        "[ANCHORS] %s"%(
            ",".join(
                "%.3f"%x
                for x in ANCHOR_SIZES
            )
        ),
        flush=True
    )

    print(
        "[REFINE_GATE] "
        "best_quote_bps >= %+.2f"%(
            refine_bps
        ),
        flush=True
    )

    print(
        "[FULL_ENVELOPE] %s"%(
            ",".join(
                "%.3f"%x
                for x in FULL_SIZES
            )
        ),
        flush=True
    )

    print(
        "[LIVE_CANARY] %.3f_SOL"%(
            LIVE_CANARY_SOL
        ),
        flush=True
    )


    engine._ensure_oracle_discovery(
        root,
        seconds+30.0
    )


    deadline=(
        time.monotonic()
        +seconds
    )


    cycle=0
    unique=set()
    total_anchor=0
    total_refined=0
    positive_points=[]
    best=None


    try:
        while (
            time.monotonic()
            <deadline
        ):
            cycle+=1

            print(
                "[BREADTH_CYCLE] "
                "cycle=%d"%cycle,
                flush=True
            )


            rows=(
                engine.refresh_live_universe_rows(
                    root
                )
            )


            if not rows:
                print(
                    "[BREADTH_HOLD] "
                    "no HOT exact-bound tokens",
                    flush=True
                )

                time.sleep(
                    min(
                        refresh_seconds,
                        max(
                            0.0,
                            deadline
                            -time.monotonic()
                        )
                    )
                )

                continue


            rows.sort(
                key=lambda x:
                    float(
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
            )


            rows=rows[
                :max(
                    1,
                    max_tokens
                )
            ]


            print(
                "[BREADTH_UNIVERSE] "
                "cycle=%d "
                "fresh_tokens=%d"%(
                    cycle,
                    len(
                        rows
                    )
                ),
                flush=True
            )


            pair_map=(
                engine.base.hydrate_rows(
                    root,
                    rows
                )
            )


            cycle_positive=0


            for row in rows:
                if (
                    time.monotonic()
                    >=deadline
                ):
                    break


                token=row[
                    "token"
                ]

                pair=pair_map.get(
                    token
                )

                if pair is None:
                    continue


                unique.add(
                    token
                )


                print(
                    "[BREADTH_TOKEN] "
                    "token=%s"%(
                        token[:10]
                    ),
                    flush=True
                )


                anchors=evaluate_sizes(
                    user,
                    pair,
                    ANCHOR_SIZES,
                    "ANCHOR"
                )


                total_anchor+=len(
                    anchors
                )


                peak=best_quote_bps(
                    anchors
                )


                refine=(
                    has_positive(
                        anchors
                    )
                    or (
                        peak is not None
                        and peak>=refine_bps
                    )
                )


                if not refine:
                    print(
                        "[FAST_REJECT] "
                        "token=%s "
                        "best_quote_bps=%s "
                        "gate=%+.2f"%(
                            token[:10],

                            (
                                "NONE"
                                if peak is None
                                else "%+.2f"%peak
                            ),

                            refine_bps,
                        ),
                        flush=True
                    )

                    values=anchors


                else:
                    missing=[
                        x
                        for x in FULL_SIZES
                        if x not in ANCHOR_SIZES
                    ]

                    print(
                        "[REFINE] "
                        "token=%s "
                        "best_anchor_quote_bps=%s "
                        "additional_sizes=%d"%(
                            token[:10],

                            (
                                "NONE"
                                if peak is None
                                else "%+.2f"%peak
                            ),

                            len(
                                missing
                            ),
                        ),
                        flush=True
                    )


                    extra=evaluate_sizes(
                        user,
                        pair,
                        missing,
                        "REFINE"
                    )


                    total_refined+=len(
                        extra
                    )


                    values=(
                        anchors
                        +extra
                    )


                for x in values:

                    if not x.get(
                        "guaranteed_positive"
                    ):
                        continue


                    x=dict(
                        x
                    )

                    x[
                        "cycle"
                    ]=cycle

                    x[
                        "wallet_fundable"
                    ]=(
                        balance
                        >=int(
                            x[
                                "principal_lamports"
                            ]
                        )
                    )

                    positive_points.append(
                        x
                    )

                    cycle_positive+=1


                    print(
                        "[PHYSICAL_OPPORTUNITY] "
                        "token=%s "
                        "size=%.3f "
                        "guaranteed=%+.9f_SOL "
                        "bps=%+.2f "
                        "wallet_fundable=%s"%(
                            token[:10],

                            x[
                                "size_sol"
                            ],

                            x[
                                "guaranteed_net_lamports"
                            ]/1e9,

                            x[
                                "guaranteed_bps"
                            ],

                            (
                                "YES"
                                if x[
                                    "wallet_fundable"
                                ]
                                else "NO"
                            ),
                        ),
                        flush=True
                    )


                    if (
                        best is None
                        or (
                            x[
                                "guaranteed_bps"
                            ],
                            x[
                                "guaranteed_net_lamports"
                            ],
                        )
                        >
                        (
                            best[
                                "guaranteed_bps"
                            ],
                            best[
                                "guaranteed_net_lamports"
                            ],
                        )
                    ):
                        best=dict(
                            x
                        )


            print(
                "[BREADTH_CYCLE_RESULT] "
                "cycle=%d "
                "unique_seen=%d "
                "positive=%d"%(
                    cycle,
                    len(
                        unique
                    ),
                    cycle_positive,
                ),
                flush=True
            )


            report={
                "revision":
                    "ORACLE_011",

                "paper_only":
                    True,

                "execution_authority":
                    False,

                "real_money_moved":
                    False,

                "source_of_truth":
                    "OFFICIAL_PHYSICAL_ONLY",

                "legacy_profit_admissible":
                    False,

                "live_canary_sol":
                    LIVE_CANARY_SOL,

                "anchor_sizes":
                    list(
                        ANCHOR_SIZES
                    ),

                "full_sizes":
                    list(
                        FULL_SIZES
                    ),

                "refine_gate_bps":
                    refine_bps,

                "cycles":
                    cycle,

                "unique_tokens":
                    len(
                        unique
                    ),

                "anchor_points":
                    total_anchor,

                "refined_points":
                    total_refined,

                "positive_points":
                    positive_points[-100:],

                "best":
                    best,

                "created_unix":
                    time.time(),
            }


            OUT.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            OUT.write_text(
                json.dumps(
                    report,
                    indent=2,
                    sort_keys=True
                ),
                encoding="utf-8"
            )


            time.sleep(
                min(
                    refresh_seconds,
                    max(
                        0.0,
                        deadline
                        -time.monotonic()
                    )
                )
            )


    finally:
        engine._stop_oracle_discovery()


    print(
        "[BREADTH_COMPLETE] "
        "cycles=%d "
        "unique_tokens=%d "
        "anchor_points=%d "
        "refined_points=%d "
        "positive=%d"%(
            cycle,
            len(
                unique
            ),
            total_anchor,
            total_refined,
            len(
                positive_points
            ),
        ),
        flush=True
    )


    if best is not None:

        print(
            "[BEST_PHYSICAL_OPPORTUNITY] "
            "token=%s "
            "size=%.3f "
            "guaranteed=%+.9f_SOL "
            "bps=%+.2f "
            "wallet_fundable=%s"%(
                best[
                    "token"
                ][:10],

                best[
                    "size_sol"
                ],

                best[
                    "guaranteed_net_lamports"
                ]/1e9,

                best[
                    "guaranteed_bps"
                ],

                (
                    "YES"
                    if best[
                        "wallet_fundable"
                    ]
                    else "NO"
                ),
            ),
            flush=True
        )

    else:
        print(
            "[NO_PHYSICAL_EDGE] "
            "no guaranteed-positive "
            "physical opportunity observed",
            flush=True
        )


    print(
        "[REPORT] %s"%OUT,
        flush=True
    )


    return 0


if __name__=="__main__":
    raise SystemExit(
        run()
    )
'''.strip()+"\n",
    encoding="utf-8"
)


py_compile.compile(
    str(MODULE),
    doraise=True
)


LAUNCHER.write_text(
r'''
import argparse
import getpass
import os

from qseries_v2.oracle_execution.oracle_011_adaptive_physical_breadth_scanner import (
    run
)


def main():

    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=float,
        default=300.0
    )

    a=ap.parse_args()

    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    return run(
        seconds=a.seconds
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
'''.strip()+"\n",
    encoding="utf-8"
)


py_compile.compile(
    str(LAUNCHER),
    doraise=True
)


TEST.write_text(
r'''
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_011_adaptive_physical_breadth_scanner
    as q
)


class T(unittest.TestCase):

    def test_safety(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )


    def test_canary(self):
        self.assertEqual(
            q.LIVE_CANARY_SOL,
            0.001
        )


    def test_anchor_coverage(self):
        for x in (
            0.001,
            0.01,
            0.05,
            0.18,
            0.5,
            1.4,
        ):
            self.assertIn(
                x,
                q.ANCHOR_SIZES
            )


    def test_full_envelope_preserved(self):
        self.assertGreater(
            len(
                q.FULL_SIZES
            ),
            len(
                q.ANCHOR_SIZES
            )
        )


    def test_physical_only(self):
        s=inspect.getsource(
            q.evaluate_sizes
        )

        self.assertIn(
            "q10.evaluate_size",
            s
        )


    def test_adaptive_refine(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "[FAST_REJECT]",
            s
        )

        self.assertIn(
            "[REFINE]",
            s
        )


    def test_continuous_fresh_universe(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "refresh_live_universe_rows",
            s
        )


    def test_no_legacy_profit(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "expectedOutAmount",
            s
        )

        self.assertNotIn(
            "api_pump_route",
            s
        )

        self.assertNotIn(
            "HOT_SIGNAL",
            s
        )


    def test_no_broadcast(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "sendTransaction",
            s
        )

        self.assertNotIn(
            "send_once(",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
'''.strip()+"\n",
    encoding="utf-8"
)


py_compile.compile(
    str(TEST),
    doraise=True
)


print(
    "[PASS] ORACLE-011 adaptive physical breadth scanner installed"
)

print(
    "[SOURCE_OF_TRUTH] official physical route only"
)

print(
    "[BREADTH] 6 anchor sizes per fresh token"
)

print(
    "[REFINE] full 13-size envelope only near breakeven/positive"
)

print(
    "[THROUGHPUT] obvious losers rejected before exhaustive sizing"
)

print(
    "[DISCOVERY] continuous Mriya fresh-universe refresh"
)

print(
    "[LEGACY] expectedOutAmount profitability remains retired"
)

print(
    "[LIVE_CANARY] unchanged at 0.001 SOL"
)

print(
    "[BROADCAST] disabled"
)

print(
    "[OWNER] ORACLE"
)