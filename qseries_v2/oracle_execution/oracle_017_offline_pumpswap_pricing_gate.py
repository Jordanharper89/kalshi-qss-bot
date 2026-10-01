from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


ROOT=Path.cwd()

NODEDIR=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

JS=NODEDIR/(
    "oracle017_offline_pump_gate.mjs"
)

BINDINGS=ROOT/(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_014_fast_lane_bindings.json"
)


def binding():
    if not BINDINGS.is_file():
        raise RuntimeError(
            "ORACLE014_BINDINGS_MISSING"
        )

    data=json.loads(
        BINDINGS.read_text(
            encoding="utf-8"
        )
    )

    rows=(
        data.get(
            "rows"
        )
        or []
    )

    for row in rows:

        pool=row.get(
            "pump_pool"
        )

        token=row.get(
            "token"
        )

        if pool and token:

            return {
                "token":
                    token,

                "pump_pool":
                    pool,
            }

    raise RuntimeError(
        "NO_PUMP_BINDING"
    )


def run():
    b=binding()

    req={
        "rpc":
            os.getenv(
                "SOLANA_RPC_URL",
                "https://api.mainnet-beta.solana.com"
            ),

        # Valid public key only.
        # No signer/private key required for this gate.
        "user":
            "11111111111111111111111111111111",

        "pool":
            b[
                "pump_pool"
            ],

        "quoteLamports":
            1_000_000,

        "slippagePct":
            .20,

        "iterations":
            1000,
    }


    p=subprocess.run(
        [
            "node",
            JS.name
        ],

        cwd=str(
            NODEDIR
        ),

        input=json.dumps(
            req
        ),

        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,

        text=True,
        timeout=90,
    )


    if p.returncode!=0:

        raise RuntimeError(
            "ORACLE017_NODE_FAIL:"
            +p.stderr[-3000:]
        )


    lines=[
        x
        for x in p.stdout.splitlines()
        if x.strip()
    ]


    if not lines:

        raise RuntimeError(
            "ORACLE017_EMPTY_OUTPUT"
        )


    row=json.loads(
        lines[-1]
    )


    if not row.get(
        "ok"
    ):

        raise RuntimeError(
            "ORACLE017_OFFLINE_FAIL"
        )


    if int(
        row[
            "onlineStateFetches"
        ]
    )!=1:

        raise RuntimeError(
            "ONLINE_FETCH_COUNT_NOT_ONE"
        )


    if int(
        row[
            "offlineIterations"
        ]
    )<1000:

        raise RuntimeError(
            "OFFLINE_LOOP_TOO_SMALL"
        )


    print(
        "[ORACLE-017] "
        "OFFLINE PUMPSWAP PRICING GATE",
        flush=True
    )


    print(
        "[PAIR] "
        "token=%s "
        "pump=%s"%(
            b[
                "token"
            ][:10],

            b[
                "pump_pool"
            ][:12],
        ),
        flush=True
    )


    print(
        "[STATE_FETCH] "
        "online_once=%d"%(
            row[
                "onlineStateFetches"
            ]
        ),
        flush=True
    )


    print(
        "[OFFLINE_ITERATIONS] %d"%(
            row[
                "offlineIterations"
            ]
        ),
        flush=True
    )


    print(
        "[PUMP_BUY] "
        "quote_in=%s "
        "base_out=%s "
        "max_quote=%s"%(
            row[
                "quoteInput"
            ],

            row[
                "buyBaseOut"
            ],

            row[
                "buyMaxQuote"
            ],
        ),
        flush=True
    )


    print(
        "[PUMP_SELL] "
        "base_in=%s "
        "ui_quote=%s "
        "min_quote=%s"%(
            row[
                "sellBaseIn"
            ],

            row[
                "sellUiQuote"
            ],

            row[
                "sellMinQuote"
            ],
        ),
        flush=True
    )


    print(
        "[PURE_PUMP_ROUNDTRIP] "
        "net_lamports=%s"%(
            row[
                "pureRoundTripNetLamports"
            ]
        ),
        flush=True
    )


    print(
        "[OFFLINE_SPEED] "
        "p50_ms=%.6f "
        "p95_ms=%.6f "
        "p99_ms=%.6f "
        "max_ms=%.6f"%(
            float(
                row[
                    "p50Ms"
                ]
            ),

            float(
                row[
                    "p95Ms"
                ]
            ),

            float(
                row[
                    "p99Ms"
                ]
            ),

            float(
                row[
                    "maxMs"
                ]
            ),
        ),
        flush=True
    )


    print(
        "[PASS] "
        "PumpSwap exact SDK pricing runs "
        "offline after one state acquisition",
        flush=True
    )


    print(
        "[NEXT_BOUNDARY] "
        "feed WebSocket-updated reserves into "
        "this exact SDK math",
        flush=True
    )


    print(
        "[BROADCAST] disabled",
        flush=True
    )


    return 0


if __name__=="__main__":
    raise SystemExit(
        run()
    )
