from pathlib import Path
import py_compile

ROOT=Path.cwd()

OUTDIR=ROOT/"qseries_v2/oracle_execution"

MODULE=OUTDIR/(
    "oracle_009_legacy_vs_physical_truth_audit.py"
)

LAUNCHER=ROOT/(
    "run_oracle_legacy_physical_truth_audit.py"
)

TEST=ROOT/(
    "test_oracle_009_legacy_vs_physical_truth_audit.py"
)

Q8=OUTDIR/(
    "oracle_008_physical_size_envelope_diagnostic.py"
)

if not Q8.is_file():
    raise SystemExit(
        "[FAIL] ORACLE-008 missing"
    )


MODULE.write_text(
r'''
from __future__ import annotations

import json
import time
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as engine
)

from qseries_v2.oracle_execution import (
    oracle_008_physical_size_envelope_diagnostic
    as physical
)

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    live_atomic_simulation
    as legacy
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


# Keep the comparison broad enough to cover the
# original profitable operating sizes without
# wasting RPC on every intermediate point.
SIZE_SOL=(
    0.001,
    0.005,
    0.010,
    0.050,
    0.100,
    0.180,
    0.280,
    0.500,
    0.900,
    1.400,
)


OUT=Path(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_009_legacy_vs_physical_truth_audit.json"
)


def classify_divergence(row):
    old_net=row.get(
        "legacy_net_lamports"
    )

    new_quote=row.get(
        "physical_quote_net_lamports"
    )

    new_guaranteed=row.get(
        "physical_guaranteed_net_lamports"
    )

    old_pump=row.get(
        "legacy_pump_token_out"
    )

    new_pump_quote=row.get(
        "physical_pump_quote_out"
    )

    new_pump_min=row.get(
        "physical_pump_minimum_out"
    )

    new_spendable=row.get(
        "physical_pump_spendable_out"
    )

    if (
        old_net is None
        or new_quote is None
    ):
        return "INCOMPLETE_COMPARISON"

    if (
        old_net>0
        and new_quote<=0
    ):
        if (
            old_pump is not None
            and new_pump_quote is not None
            and old_pump>new_pump_quote
        ):
            return (
                "LEGACY_PUMP_OUTPUT_OVERSTATES_"
                "OFFICIAL_QUOTE"
            )

        if (
            new_pump_min is not None
            and new_spendable is not None
            and new_spendable<new_pump_min
        ):
            return (
                "TOKEN2022_NET_RECEIPT_REDUCES_"
                "SELL_INPUT"
            )

        return (
            "LEGACY_POSITIVE_PHYSICAL_QUOTE_NEGATIVE"
        )

    if (
        new_quote>0
        and new_guaranteed is not None
        and new_guaranteed<=0
    ):
        return (
            "QUOTE_POSITIVE_BUT_SLIPPAGE_"
            "GUARANTEE_NEGATIVE"
        )

    if (
        old_net>0
        and new_guaranteed is not None
        and new_guaranteed>0
    ):
        return "BOTH_POSITIVE"

    if (
        old_net<=0
        and new_quote<=0
    ):
        return "BOTH_NEGATIVE"

    return "MIXED"


def compare_one(
    user,
    pair,
    size_sol
):
    principal=physical.lamports(
        size_sol
    )

    result={
        "token":
            pair.token,

        "size_sol":
            float(
                size_sol
            ),

        "principal_lamports":
            principal,
    }

    # --------------------------------------------------------
    # LEGACY PATH
    #
    # This is the same composition seam used by the old
    # atomic paper/simulation lane:
    #
    # api_pump_route
    # -> pump_token_out
    # -> _live_dlmm_quote
    #
    # No broadcast.
    # --------------------------------------------------------

    try:
        old=legacy.compose_bound(
            user,
            pair,
            float(
                size_sol
            )
        )

        result.update({
            "legacy_ok":
                True,

            "legacy_pump_token_out":
                int(
                    old[
                        "pump_token_out_raw"
                    ]
                ),

            "legacy_meteora_end_lamports":
                int(
                    old[
                        "meteora_end_lamports"
                    ]
                ),

            "legacy_net_lamports":
                int(
                    old[
                        "pre_sim_net_lamports"
                    ]
                ),

            "legacy_bps":
                float(
                    old[
                        "pre_sim_bps"
                    ]
                ),
        })

    except Exception as exc:
        result.update({
            "legacy_ok":
                False,

            "legacy_error":
                type(exc).__name__
                +":"
                +str(exc),
        })


    # --------------------------------------------------------
    # CURRENT PHYSICAL PATH
    #
    # official Pump instruction
    # -> Pump quote/minimum
    # -> Token-2022 net receipt
    # -> official Meteora quote
    # -> Meteora minOut
    #
    # No transaction compile and no broadcast.
    # --------------------------------------------------------

    try:
        new=physical.physical_route_for_size(
            user,
            pair,
            principal
        )

        result.update({
            "physical_ok":
                True,

            "physical_pump_quote_out":
                int(
                    new[
                        "pump_quote_out"
                    ]
                ),

            "physical_pump_minimum_out":
                int(
                    new[
                        "pump_minimum_out"
                    ]
                ),

            "physical_transfer_fee":
                int(
                    new[
                        "pump_transfer_fee"
                    ]
                ),

            "physical_pump_spendable_out":
                int(
                    new[
                        "pump_spendable_out"
                    ]
                ),

            "physical_meteora_quote_out":
                int(
                    new[
                        "meteora_quote_out"
                    ]
                ),

            "physical_meteora_min_out":
                int(
                    new[
                        "meteora_min_out"
                    ]
                ),

            "physical_quote_net_lamports":
                int(
                    new[
                        "quote_net_lamports"
                    ]
                ),

            "physical_quote_bps":
                float(
                    new[
                        "quote_bps"
                    ]
                ),

            "physical_guaranteed_net_lamports":
                int(
                    new[
                        "guaranteed_net_lamports"
                    ]
                ),

            "physical_guaranteed_bps":
                float(
                    new[
                        "guaranteed_bps"
                    ]
                ),
        })

    except Exception as exc:
        result.update({
            "physical_ok":
                False,

            "physical_error":
                type(exc).__name__
                +":"
                +str(exc),
        })


    result[
        "divergence"
    ]=classify_divergence(
        result
    )

    return result


def print_row(row):
    token=row[
        "token"
    ][:10]

    size=row[
        "size_sol"
    ]

    if not row.get(
        "legacy_ok"
    ):
        old_text=(
            "ERR:"
            +row.get(
                "legacy_error",
                "UNKNOWN"
            )[:90]
        )
    else:
        old_text=(
            "%+.9f_SOL/%+.2f_bps"%(
                row[
                    "legacy_net_lamports"
                ]/1e9,

                row[
                    "legacy_bps"
                ],
            )
        )

    if not row.get(
        "physical_ok"
    ):
        new_text=(
            "ERR:"
            +row.get(
                "physical_error",
                "UNKNOWN"
            )[:90]
        )
    else:
        new_text=(
            "quote=%+.9f/%+.2f "
            "guaranteed=%+.9f/%+.2f"%(
                row[
                    "physical_quote_net_lamports"
                ]/1e9,

                row[
                    "physical_quote_bps"
                ],

                row[
                    "physical_guaranteed_net_lamports"
                ]/1e9,

                row[
                    "physical_guaranteed_bps"
                ],
            )
        )

    print(
        "[TRUTH_POINT] "
        "token=%s "
        "size=%.3f "
        "legacy=%s "
        "physical=%s "
        "class=%s"%(
            token,
            size,
            old_text,
            new_text,
            row[
                "divergence"
            ],
        ),
        flush=True
    )


def run():
    root=Path.cwd()

    kp,user=(
        engine.base.require_keypair()
    )

    print(
        "[ORACLE-009] "
        "LEGACY VS PHYSICAL TRUTH AUDIT",
        flush=True
    )

    print(
        "[MODE] PAPER_ONLY=True "
        "execution_authority=FALSE "
        "real_money_moved=FALSE",
        flush=True
    )

    print(
        "[WALLET] %s"%user,
        flush=True
    )

    print(
        "[PURPOSE] "
        "same token + same size + same live state",
        flush=True
    )

    print(
        "[LEGACY] "
        "api_pump_route -> legacy DLMM quote",
        flush=True
    )

    print(
        "[PHYSICAL] "
        "official Pump -> Token2022 -> "
        "official Meteora",
        flush=True
    )

    print(
        "[BROADCAST] disabled",
        flush=True
    )

    rows=engine.live_universe_rows(
        root
    )

    if not rows:
        print(
            "[HOLD] "
            "no fresh exact-bound "
            "PumpSwap->Meteora candidates",
            flush=True
        )

        return 2

    pair_map=(
        engine.base.hydrate_rows(
            root,
            rows
        )
    )

    results=[]

    for row in rows:
        token=row[
            "token"
        ]

        pair=pair_map.get(
            token
        )

        if pair is None:
            print(
                "[TRUTH_SKIP] "
                "token=%s "
                "reason=PAIR_MISSING"%(
                    token[:10]
                ),
                flush=True
            )

            continue

        print(
            "[TRUTH_TOKEN] "
            "token=%s"%(
                token[:10]
            ),
            flush=True
        )

        for size in SIZE_SOL:
            x=compare_one(
                user,
                pair,
                size
            )

            results.append(
                x
            )

            print_row(
                x
            )


    both_positive=[
        x for x in results
        if x.get(
            "divergence"
        )=="BOTH_POSITIVE"
    ]

    legacy_only=[
        x for x in results
        if (
            x.get(
                "legacy_net_lamports",
                0
            )>0
            and x.get(
                "physical_quote_net_lamports",
                0
            )<=0
        )
    ]

    quote_only=[
        x for x in results
        if (
            x.get(
                "physical_quote_net_lamports",
                0
            )>0
            and x.get(
                "physical_guaranteed_net_lamports",
                0
            )<=0
        )
    ]

    both_negative=[
        x for x in results
        if x.get(
            "divergence"
        )=="BOTH_NEGATIVE"
    ]

    classes={}

    for x in results:
        k=x[
            "divergence"
        ]

        classes[k]=(
            classes.get(
                k,
                0
            )
            +1
        )


    report={
        "revision":
            "ORACLE_009",

        "paper_only":
            True,

        "execution_authority":
            False,

        "real_money_moved":
            False,

        "sizes_sol":
            list(
                SIZE_SOL
            ),

        "results":
            results,

        "class_counts":
            classes,

        "both_positive":
            len(
                both_positive
            ),

        "legacy_positive_physical_quote_nonpositive":
            len(
                legacy_only
            ),

        "physical_quote_positive_guarantee_nonpositive":
            len(
                quote_only
            ),

        "both_negative":
            len(
                both_negative
            ),

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


    print(
        "[TRUTH_SUMMARY] "
        "points=%d "
        "both_positive=%d "
        "legacy_only_positive=%d "
        "quote_only_positive=%d "
        "both_negative=%d"%(
            len(
                results
            ),

            len(
                both_positive
            ),

            len(
                legacy_only
            ),

            len(
                quote_only
            ),

            len(
                both_negative
            ),
        ),
        flush=True
    )

    print(
        "[CLASS_COUNTS] %s"%(
            json.dumps(
                classes,
                sort_keys=True
            )
        ),
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
import getpass
import os

from qseries_v2.oracle_execution.oracle_009_legacy_vs_physical_truth_audit import (
    run
)


def main():
    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    return run()


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
    oracle_009_legacy_vs_physical_truth_audit
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


    def test_original_sizes_present(self):
        for x in (
            0.05,
            0.1,
            0.18,
            0.28,
            0.5,
            0.9,
            1.4,
        ):
            self.assertIn(
                x,
                q.SIZE_SOL
            )


    def test_legacy_exact_path(self):
        s=inspect.getsource(
            q.compare_one
        )

        self.assertIn(
            "legacy.compose_bound",
            s
        )


    def test_physical_exact_path(self):
        s=inspect.getsource(
            q.compare_one
        )

        self.assertIn(
            "physical.physical_route_for_size",
            s
        )


    def test_stage_accounting_present(self):
        s=inspect.getsource(
            q.compare_one
        )

        for name in (
            "legacy_pump_token_out",
            "physical_pump_quote_out",
            "physical_pump_minimum_out",
            "physical_transfer_fee",
            "physical_pump_spendable_out",
            "physical_meteora_quote_out",
            "physical_meteora_min_out",
        ):
            self.assertIn(
                name,
                s
            )


    def test_no_packet_compile(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "compile_signed",
            s
        )

        self.assertNotIn(
            "getLatestBlockhash",
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
    "[PASS] ORACLE-009 legacy-vs-physical truth audit installed"
)

print(
    "[COMPARE] identical fresh token / size / observation window"
)

print(
    "[LEGACY] old api_pump_route + old DLMM quote"
)

print(
    "[PHYSICAL] official Pump + Token2022 + official Meteora"
)

print(
    "[STAGES] Pump output, transfer fee, Meteora quote/minimum exposed"
)

print(
    "[RPC] no transaction compilation / blockhash requests"
)

print(
    "[BROADCAST] disabled"
)

print(
    "[OWNER] ORACLE"
)