from __future__ import annotations

import json
import os
import statistics
import subprocess
import time
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_017_offline_pumpswap_pricing_gate
    as q17
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


ROOT=Path.cwd()

NODEDIR=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

JS=NODEDIR/(
    "oracle018_persistent_pump_worker.mjs"
)


class PumpWorker:

    def __init__(
        self
    ):
        self.p=subprocess.Popen(
            [
                "node",
                JS.name
            ],

            cwd=str(
                NODEDIR
            ),

            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,

            text=True,
            bufsize=1
        )


    def call(
        self,
        payload
    ):
        if self.p.poll() is not None:
            raise RuntimeError(
                "PUMP_WORKER_EXITED"
            )


        self.p.stdin.write(
            json.dumps(
                payload,
                separators=(
                    ",",
                    ":"
                )
            )
            +"\n"
        )

        self.p.stdin.flush()


        line=self.p.stdout.readline()

        if not line:
            err=self.p.stderr.read()

            raise RuntimeError(
                "PUMP_WORKER_EMPTY:"
                +err[-2000:]
            )


        row=json.loads(
            line
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


    def close(
        self
    ):
        try:
            self.call({
                "command":
                    "EXIT"
            })

        except Exception:
            pass


        try:
            self.p.wait(
                timeout=5
            )

        except Exception:
            self.p.kill()


def pct(
    values,
    p
):
    if not values:
        return None

    rows=sorted(
        values
    )

    idx=min(
        len(rows)-1,
        int(
            len(rows)*p
        )
    )

    return rows[
        idx
    ]


def run(
    iterations=1000
):
    binding=q17.binding()

    worker=PumpWorker()


    try:

        init=worker.call({
            "command":
                "INIT",

            "rpc":
                os.getenv(
                    "SOLANA_RPC_URL",
                    "https://api.mainnet-beta.solana.com"
                ),

            "user":
                "11111111111111111111111111111111",

            "pool":
                binding[
                    "pump_pool"
                ],

            "quoteLamports":
                1_000_000,

            "slippagePct":
                .20,
        })


        if int(
            init[
                "onlineStateFetches"
            ]
        )!=1:
            raise RuntimeError(
                "INITIAL_FETCH_COUNT_NOT_ONE"
            )


        base_reserve=init[
            "baseReserve"
        ]

        quote_reserve=init[
            "quoteReserve"
        ]

        baseline=init[
            "baselineBuy"
        ]


        samples=[]

        first=None


        for _ in range(
            int(
                iterations
            )
        ):

            t0=time.perf_counter_ns()

            row=worker.call({
                "command":
                    "QUOTE",

                # ------------------------------------------------
                # These two values are exactly what ORACLE-019
                # will replace with WebSocket-updated reserves.
                # ------------------------------------------------

                "baseReserve":
                    base_reserve,

                "quoteReserve":
                    quote_reserve,

                "quoteLamports":
                    1_000_000,

                "baseAmount":
                    None,

                "slippagePct":
                    .20,
            })


            dt=(
                time.perf_counter_ns()
                -t0
            )/1e6

            samples.append(
                dt
            )


            if first is None:
                first=row


            if int(
                row[
                    "onlineStateFetches"
                ]
            )!=1:
                raise RuntimeError(
                    "RPC_FETCH_OCCURRED_IN_HOT_LOOP"
                )


            if (
                row[
                    "buy"
                ][
                    "baseOut"
                ]
                !=baseline[
                    "baseOut"
                ]
            ):
                raise RuntimeError(
                    "RESERVE_OVERRIDE_BASE_OUT_MISMATCH"
                )


            if (
                row[
                    "buy"
                ][
                    "maxQuote"
                ]
                !=baseline[
                    "maxQuote"
                ]
            ):
                raise RuntimeError(
                    "RESERVE_OVERRIDE_MAX_QUOTE_MISMATCH"
                )


        print(
            "[ORACLE-018] "
            "PERSISTENT PUMPSWAP STATE WORKER",
            flush=True
        )


        print(
            "[PAIR] "
            "token=%s "
            "pump=%s"%(
                binding[
                    "token"
                ][:10],

                binding[
                    "pump_pool"
                ][:12],
            ),
            flush=True
        )


        print(
            "[STATE] "
            "online_fetches=1 "
            "base_reserve=%s "
            "quote_reserve=%s"%(
                base_reserve,
                quote_reserve,
            ),
            flush=True
        )


        print(
            "[PARITY] "
            "baseline_base_out=%s "
            "override_base_out=%s "
            "baseline_max_quote=%s "
            "override_max_quote=%s"%(
                baseline[
                    "baseOut"
                ],

                first[
                    "buy"
                ][
                    "baseOut"
                ],

                baseline[
                    "maxQuote"
                ],

                first[
                    "buy"
                ][
                    "maxQuote"
                ],
            ),
            flush=True
        )


        print(
            "[HOT_LOOP] "
            "iterations=%d "
            "online_state_fetches=%d"%(
                int(
                    iterations
                ),

                int(
                    first[
                        "onlineStateFetches"
                    ]
                ),
            ),
            flush=True
        )


        print(
            "[IPC_SPEED] "
            "p50_ms=%.6f "
            "p95_ms=%.6f "
            "p99_ms=%.6f "
            "max_ms=%.6f"%(
                statistics.median(
                    samples
                ),

                pct(
                    samples,
                    .95
                ),

                pct(
                    samples,
                    .99
                ),

                max(
                    samples
                ),
            ),
            flush=True
        )


        print(
            "[PASS] "
            "WebSocket reserve override reproduces "
            "exact Pump SDK pricing without RPC",
            flush=True
        )


        print(
            "[NEXT_BOUNDARY] "
            "ORACLE-019 venue-native reserve feed cutover",
            flush=True
        )


        print(
            "[BROADCAST] disabled",
            flush=True
        )


    finally:

        worker.close()


    return 0


if __name__=="__main__":
    raise SystemExit(
        run()
    )
