from __future__ import annotations

import argparse
import json
import os
import subprocess
import threading
import time
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_015_latest_state_physical_handoff
    as q15
)

from qseries_v2.oracle_execution import (
    oracle_014_venue_native_fast_lane
    as q14
)

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import (
    core
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


NODEDIR=Path(
    "qseries_v2/"
    "oracle_strategy_intelligence/"
    "solana_money/"
    "qsb059d_pump_native"
)

WORKER_JS=(
    NODEDIR/
    "sae003_pump_exact_quote_worker.mjs"
)

SLIPPAGE_PCT=.20

_worker=None


class PumpSdkWorker:

    def __init__(
        self
    ):
        env=dict(
            os.environ
        )

        self.proc=subprocess.Popen(
            [
                "node",
                WORKER_JS.name
            ],

            cwd=str(
                NODEDIR
            ),

            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,

            text=True,
            bufsize=1,
            env=env,
        )

        self.lock=threading.Lock()
        self.seq=0


    def request(
        self,
        payload
    ):
        with self.lock:

            self.seq+=1

            req={
                "id":
                    self.seq,

                **payload,
            }


            self.proc.stdin.write(
                json.dumps(
                    req,
                    separators=(
                        ",",
                        ":"
                    )
                )
                +"\n"
            )

            self.proc.stdin.flush()


            line=self.proc.stdout.readline()


            if not line:

                err=""

                try:
                    err=self.proc.stderr.read()
                except Exception:
                    pass

                raise RuntimeError(
                    "PUMP_SDK_WORKER_DIED:"
                    +err[-2000:]
                )


            row=json.loads(
                line
            )


            if int(
                row.get(
                    "id",
                    -1
                )
            )!=self.seq:

                raise RuntimeError(
                    "PUMP_SDK_RESPONSE_ORDER"
                )


            if not row.get(
                "ok"
            ):

                raise RuntimeError(
                    "PUMP_SDK_WORKER:"
                    +str(
                        row.get(
                            "reason"
                        )
                    )
                )


            return row


    def warm(
        self,
        pool
    ):
        return self.request({
            "op":
                "warm",

            "pool":
                pool,
        })


    def buy(
        self,
        snap,
        amount
    ):
        return self.request({
            "op":
                "buy",

            "pool":
                snap[
                    "pump_pool"
                ],

            "baseReserve":
                int(
                    snap[
                        "pump_base_reserve"
                    ]
                ),

            "quoteReserve":
                int(
                    snap[
                        "pump_quote_reserve"
                    ]
                ),

            "amount":
                int(
                    amount
                ),

            "slippagePct":
                SLIPPAGE_PCT,
        })


    def sell(
        self,
        snap,
        amount
    ):
        return self.request({
            "op":
                "sell",

            "pool":
                snap[
                    "pump_pool"
                ],

            "baseReserve":
                int(
                    snap[
                        "pump_base_reserve"
                    ]
                ),

            "quoteReserve":
                int(
                    snap[
                        "pump_quote_reserve"
                    ]
                ),

            "amount":
                int(
                    amount
                ),

            "slippagePct":
                SLIPPAGE_PCT,
        })


    def close(
        self
    ):
        try:

            if self.proc.poll() is None:
                self.proc.terminate()

                self.proc.wait(
                    timeout=3
                )

        except Exception:

            try:
                self.proc.kill()
            except Exception:
                pass


def worker():
    global _worker

    if _worker is None:
        _worker=PumpSdkWorker()

    return _worker


def token_net(
    token,
    gross
):
    row=q14.engine.net_received(
        token,
        int(
            gross
        )
    )

    return int(
        row[
            "net"
        ]
    )


def exact_snapshot_opportunities(
    snap,
    size_sol
):
    token=snap[
        "token"
    ]

    start=int(
        round(
            float(
                size_sol
            )
            *1e9
        )
    )


    # ========================================================
    # DIRECTION 1
    #
    # Meteora buys token with SOL.
    # Apply actual token receipt semantics.
    # Exact Pump SDK sells received token.
    # ========================================================

    meteora_buy=(
        core.dlmm_quote_snapshot(
            snap,
            start,
            core.WSOL
        )
    )


    reverse_token_in=token_net(
        token,
        meteora_buy[
            "raw_out"
        ]
    )


    if reverse_token_in<=0:
        raise RuntimeError(
            "REVERSE_TOKEN_NET_ZERO"
        )


    pump_sell=worker().sell(
        snap,
        reverse_token_in
    )


    reverse_end=int(
        pump_sell[
            "uiQuote"
        ]
    )


    reverse_min_end=int(
        pump_sell[
            "minQuote"
        ]
    )


    reverse_net=(
        reverse_end
        -start
    )


    reverse_min_net=(
        reverse_min_end
        -start
    )


    reverse={
        "token":
            token,

        "pump_pool":
            snap[
                "pump_pool"
            ],

        "meteora":
            snap[
                "meteora"
            ],

        "start":
            start,

        "size_sol":
            float(
                size_sol
            ),

        "direction":
            "METEORA_TO_PUMP",

        "mq":
            meteora_buy,

        "gross_token":
            int(
                meteora_buy[
                    "raw_out"
                ]
            ),

        "net_token":
            reverse_token_in,

        "local_end":
            reverse_end,

        "local_min_end":
            reverse_min_end,

        "local_net":
            reverse_net,

        "local_min_net":
            reverse_min_net,

        "local_bps":
            reverse_net
            /start
            *10000.0,

        "local_min_bps":
            reverse_min_net
            /start
            *10000.0,

        "pump_model":
            "SAE003_PUMPSWAP_EXACT_QUOTE_IN",
    }


    # ========================================================
    # DIRECTION 2
    #
    # Exact Pump SDK buys token with SOL.
    # Apply actual token receipt semantics.
    # Hydrated Meteora state sells the received token.
    # ========================================================

    pump_buy=worker().buy(
        snap,
        start
    )


    forward_gross=int(
        pump_buy[
            "baseOut"
        ]
    )


    forward_token_in=token_net(
        token,
        forward_gross
    )


    if forward_token_in<=0:
        raise RuntimeError(
            "FORWARD_TOKEN_NET_ZERO"
        )


    meteora_sell=(
        core.dlmm_quote_snapshot(
            snap,
            forward_token_in,
            token
        )
    )


    forward_end=int(
        meteora_sell[
            "raw_out"
        ]
    )


    forward_net=(
        forward_end
        -start
    )


    forward={
        "token":
            token,

        "pump_pool":
            snap[
                "pump_pool"
            ],

        "meteora":
            snap[
                "meteora"
            ],

        "start":
            start,

        "size_sol":
            float(
                size_sol
            ),

        "direction":
            "PUMP_TO_METEORA",

        "mq":
            meteora_sell,

        "pump_base_out_gross":
            forward_gross,

        "pump_base_out_net":
            forward_token_in,

        "pump_max_quote":
            int(
                pump_buy[
                    "maxQuote"
                ]
            ),

        "local_end":
            forward_end,

        "local_net":
            forward_net,

        "local_bps":
            forward_net
            /start
            *10000.0,

        "pump_model":
            "EXACT_PUMPSWAP_SDK",
    }


    return sorted(
        [
            reverse,
            forward,
        ],

        key=lambda x:
            x[
                "local_net"
            ],

        reverse=True
    )


def install_exact_hot_math():

    if not hasattr(
        q14.persistent.m,
        "c"
    ):
        raise RuntimeError(
            "MERGED_RUNTIME_CORE_MISSING"
        )


    runtime_core=(
        q14.persistent.m.c
    )


    if not hasattr(
        runtime_core,
        "sized_snapshot_opportunities"
    ):
        raise RuntimeError(
            "SNAPSHOT_PRICER_SEAM_MISSING"
        )


    runtime_core.sized_snapshot_opportunities=(
        exact_snapshot_opportunities
    )


    core.sized_snapshot_opportunities=(
        exact_snapshot_opportunities
    )


    return runtime_core


def prewarm_previous_bindings():
    path=Path(
        "runtime_state/oracle/"
        "oracle_live_execution/"
        "oracle_014_fast_lane_bindings.json"
    )


    if not path.is_file():
        return 0


    try:
        data=json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return 0


    pools=[]


    for row in (
        data.get(
            "rows"
        )
        or []
    ):
        pool=row.get(
            "pump_pool"
        )

        if (
            pool
            and pool not in pools
        ):
            pools.append(
                pool
            )


    warmed=0


    for pool in pools:

        try:

            worker().warm(
                pool
            )

            warmed+=1

            print(
                "[SDK_WARM] "
                "pump=%s"%(
                    pool[:12]
                ),
                flush=True
            )

        except Exception as exc:

            print(
                "[SDK_WARM_SKIP] "
                "pump=%s "
                "%s:%s"%(
                    pool[:12],
                    type(exc).__name__,
                    str(exc)[:160],
                ),
                flush=True
            )


    return warmed


def run(
    seconds=300.0
):
    runtime_core=(
        install_exact_hot_math()
    )


    warmed=(
        prewarm_previous_bindings()
    )


    print(
        "[ORACLE-018] "
        "EXACT SDK HOT-LANE CUTOVER",
        flush=True
    )


    print(
        "[RETIRED] "
        "PUMP_FEE_BPS constant-product "
        "snapshot profitability",
        flush=True
    )


    print(
        "[PUMP_MODEL] "
        "EXACT_PUMPSWAP_SDK",
        flush=True
    )


    print(
        "[PUMP_STATE] "
        "static config warm once; "
        "WebSocket reserves supplied per quote",
        flush=True
    )


    print(
        "[TOKEN2022] "
        "net receipt applied before second venue",
        flush=True
    )


    print(
        "[METEORA] "
        "existing hydrated DLMM state",
        flush=True
    )


    print(
        "[SDK_PREWARM] pools=%d"%(
            warmed
        ),
        flush=True
    )


    print(
        "[CALIBRATION_LAYER] retired",
        flush=True
    )


    print(
        "[PHYSICAL_AUTHORITY] "
        "ORACLE-015 official verifier preserved",
        flush=True
    )


    print(
        "[BROADCAST] disabled",
        flush=True
    )


    try:

        return q15.run(
            seconds
        )

    finally:

        global _worker

        if _worker is not None:
            _worker.close()
            _worker=None


def main(
    argv=None
):
    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=float,
        default=300.0
    )

    a=ap.parse_args(
        argv
    )

    return run(
        a.seconds
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
