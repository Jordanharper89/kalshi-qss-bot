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
    oracle_008_physical_size_envelope_diagnostic
    as physical
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


# Discovery ladder.
#
# This is NOT the live-money limit.
# It discovers where executable physical edge exists.
SIZE_SOL=(
    0.001,
    0.002,
    0.005,
    0.010,
    0.025,
    0.050,
    0.100,
    0.180,
    0.280,
    0.500,
    0.900,
    1.100,
    1.400,
)


LIVE_CANARY_SOL=0.001


OUT=Path(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_010_continuous_physical_opportunity_scanner.json"
)


def evaluate_size(
    user,
    pair,
    size_sol
):
    principal=physical.lamports(
        size_sol
    )

    try:
        route=(
            physical.physical_route_for_size(
                user,
                pair,
                principal
            )
        )

    except Exception as exc:
        return {
            "token":
                pair.token,

            "size_sol":
                float(
                    size_sol
                ),

            "principal_lamports":
                principal,

            "ok":
                False,

            "reason":
                type(exc).__name__
                +":"
                +str(exc),
        }


    quote_net=int(
        route[
            "quote_net_lamports"
        ]
    )

    guaranteed_net=int(
        route[
            "guaranteed_net_lamports"
        ]
    )

    return {
        "token":
            pair.token,

        "size_sol":
            float(
                size_sol
            ),

        "principal_lamports":
            principal,

        "ok":
            True,

        "pump_quote_out":
            int(
                route[
                    "pump_quote_out"
                ]
            ),

        "pump_minimum_out":
            int(
                route[
                    "pump_minimum_out"
                ]
            ),

        "pump_transfer_fee":
            int(
                route[
                    "pump_transfer_fee"
                ]
            ),

        "pump_spendable_out":
            int(
                route[
                    "pump_spendable_out"
                ]
            ),

        "meteora_quote_out":
            int(
                route[
                    "meteora_quote_out"
                ]
            ),

        "meteora_min_out":
            int(
                route[
                    "meteora_min_out"
                ]
            ),

        "quote_net_lamports":
            quote_net,

        "quote_bps":
            float(
                route[
                    "quote_bps"
                ]
            ),

        "guaranteed_net_lamports":
            guaranteed_net,

        "guaranteed_bps":
            float(
                route[
                    "guaranteed_bps"
                ]
            ),

        "quote_positive":
            quote_net>0,

        "guaranteed_positive":
            guaranteed_net>0,
    }


def evaluate_token(
    user,
    pair
):
    rows=[]

    for size in SIZE_SOL:
        result=evaluate_size(
            user,
            pair,
            size
        )

        rows.append(
            result
        )

        if result.get(
            "ok"
        ):
            print(
                "[PHYSICAL_SIZE] "
                "token=%s "
                "size=%.3f "
                "quote=%+.9f_SOL "
                "qbps=%+.2f "
                "guaranteed=%+.9f_SOL "
                "gbps=%+.2f"%(
                    pair.token[:10],

                    size,

                    result[
                        "quote_net_lamports"
                    ]/1e9,

                    result[
                        "quote_bps"
                    ],

                    result[
                        "guaranteed_net_lamports"
                    ]/1e9,

                    result[
                        "guaranteed_bps"
                    ],
                ),
                flush=True
            )

        else:
            print(
                "[PHYSICAL_SIZE_REJECT] "
                "token=%s "
                "size=%.3f "
                "reason=%s"%(
                    pair.token[:10],
                    size,
                    result.get(
                        "reason"
                    ),
                ),
                flush=True
            )

    return rows


def run(
    seconds=180.0
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

    refresh_seconds=float(
        os.getenv(
            "ORACLE_PHYSICAL_SCAN_REFRESH_SECONDS",
            "10"
        )
    )

    seconds=float(
        os.getenv(
            "ORACLE_PHYSICAL_SCAN_SECONDS",
            str(
                seconds
            )
        )
    )


    print(
        "[ORACLE-010] "
        "CONTINUOUS PHYSICAL OPPORTUNITY SCANNER",
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
        "[SOURCE_OF_TRUTH] "
        "OFFICIAL_PHYSICAL_ONLY",
        flush=True
    )

    print(
        "[LEGACY_EXPECTED_OUT] "
        "PROHIBITED_FROM_PROFIT_DECISION",
        flush=True
    )

    print(
        "[LIVE_CANARY] "
        "%.3f SOL"%(
            LIVE_CANARY_SOL
        ),
        flush=True
    )

    print(
        "[SIZE_LADDER] %s"%(
            ",".join(
                "%.3f"%x
                for x in SIZE_SOL
            )
        ),
        flush=True
    )


    # Keep Mriya discovery alive throughout the scan.
    engine._ensure_oracle_discovery(
        root,
        seconds+30.0
    )


    deadline=(
        time.monotonic()
        +seconds
    )

    cycle=0

    total_points=0
    total_positive=0

    best=None

    seen_tokens=set()

    latest_results=[]


    try:
        while (
            time.monotonic()
            <deadline
        ):
            cycle+=1

            print(
                "[SCAN_CYCLE] "
                "cycle=%d"%(
                    cycle
                ),
                flush=True
            )


            rows=(
                engine.refresh_live_universe_rows(
                    root
                )
            )


            if not rows:
                print(
                    "[SCAN_HOLD] "
                    "no current HOT exact-bound "
                    "PumpSwap->Meteora tokens",
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


            print(
                "[SCAN_UNIVERSE] "
                "cycle=%d "
                "tokens=%d"%(
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


            cycle_results=[]


            for row in rows:
                token=row[
                    "token"
                ]

                pair=pair_map.get(
                    token
                )

                if pair is None:
                    print(
                        "[SCAN_TOKEN_SKIP] "
                        "token=%s "
                        "reason=PAIR_MISSING"%(
                            token[:10]
                        ),
                        flush=True
                    )

                    continue


                seen_tokens.add(
                    token
                )


                values=evaluate_token(
                    user,
                    pair
                )


                for x in values:
                    total_points+=1

                    x[
                        "cycle"
                    ]=cycle

                    x[
                        "observed_unix"
                    ]=time.time()

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

                    cycle_results.append(
                        x
                    )


                    if not x.get(
                        "guaranteed_positive"
                    ):
                        continue


                    total_positive+=1


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


            latest_results=cycle_results


            positive_now=[
                x
                for x in cycle_results
                if x.get(
                    "guaranteed_positive"
                )
            ]


            print(
                "[SCAN_CYCLE_RESULT] "
                "cycle=%d "
                "points=%d "
                "positive=%d"%(
                    cycle,
                    len(
                        cycle_results
                    ),
                    len(
                        positive_now
                    ),
                ),
                flush=True
            )


            report={
                "revision":
                    "ORACLE_010",

                "paper_only":
                    True,

                "execution_authority":
                    False,

                "real_money_moved":
                    False,

                "source_of_truth":
                    "OFFICIAL_PHYSICAL_ONLY",

                "legacy_expected_out_admissible":
                    False,

                "live_canary_sol":
                    LIVE_CANARY_SOL,

                "wallet":
                    user,

                "wallet_balance_lamports":
                    balance,

                "cycle":
                    cycle,

                "unique_tokens":
                    len(
                        seen_tokens
                    ),

                "total_points":
                    total_points,

                "total_positive_points":
                    total_positive,

                "best":
                    best,

                "latest_results":
                    latest_results,

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
        "[SCAN_COMPLETE] "
        "cycles=%d "
        "unique_tokens=%d "
        "points=%d "
        "positive=%d"%(
            cycle,
            len(
                seen_tokens
            ),
            total_points,
            total_positive,
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
            "no executable-positive "
            "PumpSwap->Meteora point observed",
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
