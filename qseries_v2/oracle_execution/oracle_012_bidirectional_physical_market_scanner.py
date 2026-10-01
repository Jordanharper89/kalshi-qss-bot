from __future__ import annotations

import json
import os
import shutil
import subprocess
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

from qseries_v2.oracle_execution import (
    oracle_011_adaptive_physical_breadth_scanner
    as q11
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


PUMP_TO_METEORA=(
    "PUMP_TO_METEORA"
)

METEORA_TO_PUMP=(
    "METEORA_TO_PUMP"
)


ANCHOR_SIZES=(
    0.001,
    0.010,
    0.050,
    0.180,
    0.500,
    1.400,
)


REFINE_SIZES=tuple(
    q11.FULL_SIZES
)


NODEDIR=Path(
    "qseries_v2/"
    "oracle_strategy_intelligence/"
    "solana_money/"
    "qsb059d_pump_native"
)


METEORA_JS=(
    NODEDIR/
    "oracle003_meteora_swap.mjs"
)


PUMP_SELL_JS=(
    NODEDIR/
    "oracle012_pump_sell.mjs"
)


OUT=Path(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_012_bidirectional_physical_market_scanner.json"
)


def node_json(
    script,
    request
):
    if shutil.which(
        "node"
    ) is None:
        raise RuntimeError(
            "NODE_MISSING"
        )

    p=subprocess.run(
        [
            "node",
            str(
                Path(script).name
            )
        ],

        cwd=str(
            NODEDIR
        ),

        input=json.dumps(
            request
        ),

        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,

        text=True,
        timeout=60,
    )

    if p.returncode!=0:
        raise RuntimeError(
            "NODE_FAILED:"
            +p.stderr[-2000:]
        )

    lines=[
        x
        for x in p.stdout.splitlines()
        if x.strip()
    ]

    if not lines:
        raise RuntimeError(
            "NODE_EMPTY_OUTPUT"
        )

    try:
        row=json.loads(
            lines[-1]
        )

    except Exception:
        raise RuntimeError(
            "NODE_BAD_JSON:"
            +p.stdout[-2000:]
        )

    if not row.get(
        "ok"
    ):
        raise RuntimeError(
            str(
                row.get(
                    "reason"
                )
            )
        )

    return row


def reverse_meteora_buy(
    user,
    pair,
    principal
):
    row=node_json(
        METEORA_JS,
        {
            "rpc":
                os.getenv(
                    "SOLANA_RPC_URL",
                    "https://api.mainnet-beta.solana.com"
                ),

            "user":
                user,

            "pool":
                pair.meteora_pool,

            "inputMint":
                engine.base.q87.c.WSOL,

            "outputMint":
                pair.token,

            "amount":
                int(
                    principal
                ),

            "slippageBps":
                int(
                    engine.base.q87.las.q59
                    .SLIPPAGE_BPS
                ),
        }
    )

    consumed=int(
        row[
            "consumedIn"
        ]
    )

    if consumed!=int(
        principal
    ):
        raise RuntimeError(
            "METEORA_PARTIAL_INPUT:"
            +str(
                consumed
            )
        )

    return {
        "quote_token_out":
            int(
                row[
                    "out"
                ]
            ),

        "minimum_token_out":
            int(
                row[
                    "minOut"
                ]
            ),

        "bin_arrays":
            list(
                row.get(
                    "binArrays"
                )
                or []
            ),

        "quote_source":
            row.get(
                "quoteSource"
            ),
    }


def official_pump_sell_pair(
    user,
    pair,
    quote_token_amount,
    guaranteed_token_amount
):
    quote_token_amount=int(
        quote_token_amount
    )

    guaranteed_token_amount=int(
        guaranteed_token_amount
    )

    if (
        quote_token_amount<=0
        or guaranteed_token_amount<=0
    ):
        raise RuntimeError(
            "PUMP_SELL_NONPOSITIVE_INPUT"
        )

    if (
        guaranteed_token_amount
        >quote_token_amount
    ):
        raise RuntimeError(
            "REVERSE_TOKEN_ORDER_VIOLATION:"
            +str(
                guaranteed_token_amount
            )
            +">"
            +str(
                quote_token_amount
            )
        )

    row=node_json(
        PUMP_SELL_JS,
        {
            "rpc":
                os.getenv(
                    "SOLANA_RPC_URL",
                    "https://api.mainnet-beta.solana.com"
                ),

            "user":
                user,

            "pool":
                pair.pump_pool,

            "baseAmounts":[
                quote_token_amount,
                guaranteed_token_amount,
            ],

            "slippagePct":
                (
                    int(
                        engine.base.q87.las.q59
                        .SLIPPAGE_BPS
                    )
                    /100.0
                ),

            "pumpProgram":
                engine.base.q87.c.PUMP,
        }
    )

    if int(
        row.get(
            "stateSnapshots",
            0
        )
    )!=1:
        raise RuntimeError(
            "PUMP_STATE_NOT_SINGLE_SNAPSHOT"
        )

    first=(
        row[
            "first"
        ]
    )

    second=(
        row[
            "second"
        ]
    )

    quote_base=int(
        first[
            "baseIn"
        ]
    )

    guaranteed_base=int(
        second[
            "baseIn"
        ]
    )

    quote_min=int(
        first[
            "minQuoteOut"
        ]
    )

    guaranteed_min=int(
        second[
            "minQuoteOut"
        ]
    )

    if (
        quote_base
        !=quote_token_amount
    ):
        raise RuntimeError(
            "PUMP_QUOTE_INPUT_MISMATCH"
        )

    if (
        guaranteed_base
        !=guaranteed_token_amount
    ):
        raise RuntimeError(
            "PUMP_GUARANTEED_INPUT_MISMATCH"
        )

    # Same AMM state + larger token input MUST NOT
    # produce a smaller minimum quote output.
    if (
        quote_token_amount
        >=guaranteed_token_amount
        and quote_min
        <guaranteed_min
    ):
        raise RuntimeError(
            "PUMP_SELL_MONOTONICITY_VIOLATION:"
            +str(
                quote_min
            )
            +"<"
            +str(
                guaranteed_min
            )
        )

    return {
        "state_snapshots":
            1,

        "quote_base_in":
            quote_base,

        "quote_min_quote_out":
            quote_min,

        "guaranteed_base_in":
            guaranteed_base,

        "guaranteed_min_quote_out":
            guaranteed_min,
    }

def evaluate_reverse(
    user,
    pair,
    size_sol
):
    principal=physical.lamports(
        size_sol
    )

    try:
        meteora=reverse_meteora_buy(
            user,
            pair,
            principal
        )

        # Token-2022 transfer fees are applied when
        # Meteora delivers the token to our account.
        quote_receipt=engine.net_received(
            pair.token,
            meteora[
                "quote_token_out"
            ]
        )

        minimum_receipt=engine.net_received(
            pair.token,
            meteora[
                "minimum_token_out"
            ]
        )

        quote_tokens=int(
            quote_receipt[
                "net"
            ]
        )

        guaranteed_tokens=int(
            minimum_receipt[
                "net"
            ]
        )

        if (
            quote_tokens<=0
            or guaranteed_tokens<=0
        ):
            raise RuntimeError(
                "METEORA_NET_TOKEN_ZERO"
            )


        pump_pair=official_pump_sell_pair(
            user,
            pair,
            quote_tokens,
            guaranteed_tokens
        )

        quote_end=int(
            pump_pair[
                "quote_min_quote_out"
            ]
        )

        guaranteed_end=int(
            pump_pair[
                "guaranteed_min_quote_out"
            ]
        )

        if guaranteed_end>quote_end:
            raise RuntimeError(
                "REVERSE_END_MONOTONICITY_VIOLATION:"
                +str(
                    guaranteed_end
                )
                +">"
                +str(
                    quote_end
                )
            )


        quote_net=(
            quote_end
            -principal
        )

        guaranteed_net=(
            guaranteed_end
            -principal
        )


        return {
            "ok":
                True,

            "direction":
                METEORA_TO_PUMP,

            "token":
                pair.token,

            "size_sol":
                float(
                    size_sol
                ),

            "principal_lamports":
                principal,

            "meteora_quote_token_out":
                meteora[
                    "quote_token_out"
                ],

            "meteora_minimum_token_out":
                meteora[
                    "minimum_token_out"
                ],

            "quote_token_after_transfer_fee":
                quote_tokens,

            "guaranteed_token_after_transfer_fee":
                guaranteed_tokens,

            "pump_state_snapshots":
                int(
                    pump_pair[
                        "state_snapshots"
                    ]
                ),

            "quote_end_lamports":
                quote_end,

            "guaranteed_end_lamports":
                guaranteed_end,

            "quote_net_lamports":
                quote_net,

            "guaranteed_net_lamports":
                guaranteed_net,

            "quote_bps":
                quote_net
                /principal
                *10000.0,

            "guaranteed_bps":
                guaranteed_net
                /principal
                *10000.0,

            "quote_positive":
                quote_net>0,

            "guaranteed_positive":
                guaranteed_net>0,
        }

    except Exception as exc:

        return {
            "ok":
                False,

            "direction":
                METEORA_TO_PUMP,

            "token":
                pair.token,

            "size_sol":
                float(
                    size_sol
                ),

            "principal_lamports":
                principal,

            "reason":
                type(exc).__name__
                +":"
                +str(exc),
        }


def evaluate_forward(
    user,
    pair,
    size_sol
):
    row=physical.physical_route_for_size(
        user,
        pair,
        physical.lamports(
            size_sol
        )
    )

    return {
        "ok":
            True,

        "direction":
            PUMP_TO_METEORA,

        "token":
            pair.token,

        "size_sol":
            float(
                size_sol
            ),

        "principal_lamports":
            physical.lamports(
                size_sol
            ),

        "quote_net_lamports":
            int(
                row[
                    "quote_net_lamports"
                ]
            ),

        "guaranteed_net_lamports":
            int(
                row[
                    "guaranteed_net_lamports"
                ]
            ),

        "quote_bps":
            float(
                row[
                    "quote_bps"
                ]
            ),

        "guaranteed_bps":
            float(
                row[
                    "guaranteed_bps"
                ]
            ),

        "quote_positive":
            int(
                row[
                    "quote_net_lamports"
                ]
            )>0,

        "guaranteed_positive":
            int(
                row[
                    "guaranteed_net_lamports"
                ]
            )>0,
    }


def safe_forward(
    user,
    pair,
    size
):
    try:
        return evaluate_forward(
            user,
            pair,
            size
        )

    except Exception as exc:
        return {
            "ok":
                False,

            "direction":
                PUMP_TO_METEORA,

            "token":
                pair.token,

            "size_sol":
                float(
                    size
                ),

            "principal_lamports":
                physical.lamports(
                    size
                ),

            "reason":
                type(exc).__name__
                +":"
                +str(exc),
        }


def print_point(
    row
):
    if not row.get(
        "ok"
    ):
        print(
            "[BI_REJECT] "
            "dir=%s "
            "token=%s "
            "size=%.3f "
            "reason=%s"%(
                row[
                    "direction"
                ],

                row[
                    "token"
                ][:10],

                row[
                    "size_sol"
                ],

                row.get(
                    "reason"
                ),
            ),
            flush=True
        )

        return


    print(
        "[BI_POINT] "
        "dir=%s "
        "token=%s "
        "size=%.3f "
        "quote=%+.9f_SOL "
        "qbps=%+.2f "
        "guaranteed=%+.9f_SOL "
        "gbps=%+.2f"%(
            row[
                "direction"
            ],

            row[
                "token"
            ][:10],

            row[
                "size_sol"
            ],

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


def run(
    seconds=300.0
):
    root=Path.cwd()

    kp,user=(
        engine.base.require_keypair()
    )

    seconds=float(
        seconds
    )

    refine_gate=float(
        os.getenv(
            "ORACLE_BIDIRECTIONAL_REFINE_BPS",
            "-100"
        )
    )

    refresh=float(
        os.getenv(
            "ORACLE_BIDIRECTIONAL_REFRESH_SECONDS",
            "5"
        )
    )


    print(
        "[ORACLE-012] "
        "BIDIRECTIONAL PHYSICAL MARKET SCANNER",
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
        "[DIRECTIONS] "
        "PUMP_TO_METEORA + "
        "METEORA_TO_PUMP",
        flush=True
    )

    print(
        "[SOURCE_OF_TRUTH] "
        "OFFICIAL_PHYSICAL_ONLY",
        flush=True
    )

    print(
        "[REFINE_GATE] %+.2f_bps"%(
            refine_gate
        ),
        flush=True
    )

    print(
        "[BROADCAST] disabled",
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
    points=0
    positive=[]
    best=None


    try:

        while (
            time.monotonic()
            <deadline
        ):
            cycle+=1

            rows=(
                engine.refresh_live_universe_rows(
                    root
                )
            )

            if not rows:

                print(
                    "[BI_HOLD] "
                    "cycle=%d "
                    "no HOT exact-bound tokens"%(
                        cycle
                    ),
                    flush=True
                )

                time.sleep(
                    min(
                        refresh,
                        max(
                            0.0,
                            deadline
                            -time.monotonic()
                        )
                    )
                )

                continue


            pair_map=(
                engine.base.hydrate_rows(
                    root,
                    rows
                )
            )


            print(
                "[BI_UNIVERSE] "
                "cycle=%d "
                "tokens=%d"%(
                    cycle,
                    len(
                        rows
                    )
                ),
                flush=True
            )


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


                token_rows=[]


                for size in ANCHOR_SIZES:

                    f=safe_forward(
                        user,
                        pair,
                        size
                    )

                    r=evaluate_reverse(
                        user,
                        pair,
                        size
                    )

                    print_point(
                        f
                    )

                    print_point(
                        r
                    )

                    token_rows.extend(
                        [
                            f,
                            r,
                        ]
                    )

                    points+=2


                best_quote=max(
                    [
                        float(
                            x[
                                "quote_bps"
                            ]
                        )

                        for x in token_rows

                        if x.get(
                            "ok"
                        )
                    ]
                    or [
                        -1e99
                    ]
                )


                if best_quote>=refine_gate:

                    already=set(
                        ANCHOR_SIZES
                    )

                    missing=[
                        x
                        for x in REFINE_SIZES
                        if x not in already
                    ]

                    print(
                        "[BI_REFINE] "
                        "token=%s "
                        "best_quote_bps=%+.2f "
                        "extra_sizes=%d"%(
                            token[:10],
                            best_quote,
                            len(
                                missing
                            ),
                        ),
                        flush=True
                    )


                    for size in missing:

                        f=safe_forward(
                            user,
                            pair,
                            size
                        )

                        r=evaluate_reverse(
                            user,
                            pair,
                            size
                        )

                        print_point(
                            f
                        )

                        print_point(
                            r
                        )

                        token_rows.extend(
                            [
                                f,
                                r,
                            ]
                        )

                        points+=2


                for x in token_rows:

                    if not x.get(
                        "guaranteed_positive"
                    ):
                        continue


                    y=dict(
                        x
                    )

                    y[
                        "cycle"
                    ]=cycle

                    positive.append(
                        y
                    )


                    print(
                        "[BIDIRECTIONAL_PHYSICAL_OPPORTUNITY] "
                        "dir=%s "
                        "token=%s "
                        "size=%.3f "
                        "guaranteed=%+.9f_SOL "
                        "bps=%+.2f"%(
                            y[
                                "direction"
                            ],

                            token[:10],

                            y[
                                "size_sol"
                            ],

                            y[
                                "guaranteed_net_lamports"
                            ]/1e9,

                            y[
                                "guaranteed_bps"
                            ],
                        ),
                        flush=True
                    )


                    if (
                        best is None
                        or (
                            y[
                                "guaranteed_bps"
                            ],
                            y[
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
                            y
                        )


            report={
                "revision":
                    "ORACLE_012",

                "paper_only":
                    True,

                "execution_authority":
                    False,

                "real_money_moved":
                    False,

                "directions":[
                    PUMP_TO_METEORA,
                    METEORA_TO_PUMP,
                ],

                "cycles":
                    cycle,

                "unique_tokens":
                    len(
                        unique
                    ),

                "points":
                    points,

                "positive_points":
                    positive[-100:],

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
                    refresh,
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
        "[BI_COMPLETE] "
        "cycles=%d "
        "unique_tokens=%d "
        "points=%d "
        "positive=%d"%(
            cycle,
            len(
                unique
            ),
            points,
            len(
                positive
            ),
        ),
        flush=True
    )


    if best is not None:

        print(
            "[BEST_BIDIRECTIONAL_PHYSICAL] "
            "dir=%s "
            "token=%s "
            "size=%.3f "
            "guaranteed=%+.9f_SOL "
            "bps=%+.2f"%(
                best[
                    "direction"
                ],

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
            ),
            flush=True
        )

    else:

        print(
            "[NO_BIDIRECTIONAL_PHYSICAL_EDGE]",
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
