from __future__ import annotations

import argparse
import asyncio
import json
import os
import queue
import threading
import time
from pathlib import Path
from time import perf_counter_ns

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as engine
)

from qseries_v2.oracle_execution import (
    oracle_012_bidirectional_physical_market_scanner
    as bi
)

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    persistent_profit_runtime as persistent
)

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_047b_paced_dynamic_hotset_supervisor
    as q47
)

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_061d_subscription_cap_aware_ws_valves
    as q61d
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

FAST_SIZES=(
    0.001,
    0.010,
    0.050,
)

EXPANSION_SIZES=(
    0.180,
    0.500,
    1.400,
)

EXPAND_GATE_BPS=float(
    os.getenv(
        "ORACLE_FAST_LANE_EXPAND_GATE_BPS",
        "-100"
    )
)

DEBOUNCE_SECONDS=float(
    os.getenv(
        "ORACLE_FAST_LANE_DEBOUNCE_SECONDS",
        "0.20"
    )
)

QUEUE_MAX=int(
    os.getenv(
        "ORACLE_FAST_LANE_QUEUE_MAX",
        "256"
    )
)

WARM_SECONDS=float(
    os.getenv(
        "ORACLE_FAST_LANE_WARM_SECONDS",
        "120"
    )
)

BINDINGS=Path(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_014_fast_lane_bindings.json"
)

REPORT=Path(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_014_venue_native_fast_lane.json"
)


class NullSimulationLane:

    def __init__(
        self,
        root,
        state
    ):
        self.best=None
        self.attempts=0
        self.profitable=0
        self.failures=0
        self.drops=0

    async def worker(
        self,
        stop
    ):
        while not stop.is_set():
            await asyncio.sleep(
                .25
            )

    def submit(
        self,
        row
    ):
        return None


class PhysicalFastLane:

    def __init__(
        self,
        user,
        pairs
    ):
        self.user=user

        self.pairs={
            p.token:p
            for p in pairs
        }

        self.q=queue.Queue(
            maxsize=QUEUE_MAX
        )

        self.stop=threading.Event()

        self.last_submit={}

        self.lock=threading.Lock()

        self.events=0
        self.evaluations=0
        self.drops=0
        self.positives=0

        self.best=None

        self.event_to_start_ms=[]
        self.scan_ms=[]

        self.thread=threading.Thread(
            target=self._worker,
            name="oracle014-physical-fast-lane",
            daemon=True
        )

        self.thread.start()


    def submit(
        self,
        token,
        received_ns,
        address,
        slot
    ):
        now=time.monotonic()

        with self.lock:

            prior=self.last_submit.get(
                token,
                0.0
            )

            if (
                now-prior
                <DEBOUNCE_SECONDS
            ):
                return False

            self.last_submit[
                token
            ]=now


        item={
            "token":
                token,

            "received_ns":
                int(
                    received_ns
                ),

            "address":
                address,

            "slot":
                int(
                    slot
                ),
        }


        try:
            self.q.put_nowait(
                item
            )

            self.events+=1

            return True

        except queue.Full:

            self.drops+=1

            print(
                "[FAST_QUEUE_DROP] "
                "token=%s"%(
                    token[:10]
                ),
                flush=True
            )

            return False


    def _point(
        self,
        pair,
        size,
        direction
    ):
        if (
            direction
            ==bi.PUMP_TO_METEORA
        ):
            return bi.safe_forward(
                self.user,
                pair,
                size
            )

        return bi.evaluate_reverse(
            self.user,
            pair,
            size
        )


    def _scan_size(
        self,
        pair,
        size
    ):
        rows=[]

        for direction in (
            bi.PUMP_TO_METEORA,
            bi.METEORA_TO_PUMP,
        ):

            row=self._point(
                pair,
                size,
                direction
            )

            rows.append(
                row
            )

            if not row.get(
                "ok"
            ):
                print(
                    "[FAST_REJECT] "
                    "dir=%s "
                    "token=%s "
                    "size=%.3f "
                    "reason=%s"%(
                        direction,
                        pair.token[:10],
                        size,
                        row.get(
                            "reason"
                        ),
                    ),
                    flush=True
                )

                continue


            print(
                "[FAST_PHYSICAL] "
                "dir=%s "
                "token=%s "
                "size=%.3f "
                "quote_bps=%+.2f "
                "guaranteed_bps=%+.2f"%(
                    direction,
                    pair.token[:10],
                    size,
                    row[
                        "quote_bps"
                    ],
                    row[
                        "guaranteed_bps"
                    ],
                ),
                flush=True
            )

        return rows


    def _record_positive(
        self,
        row,
        event
    ):
        if not row.get(
            "guaranteed_positive"
        ):
            return


        self.positives+=1

        candidate=dict(
            row
        )

        candidate.update({
            "trigger_slot":
                event[
                    "slot"
                ],

            "trigger_address":
                event[
                    "address"
                ],

            "detected_unix":
                time.time(),
        })


        if (
            self.best is None
            or (
                candidate[
                    "guaranteed_bps"
                ],
                candidate[
                    "guaranteed_net_lamports"
                ],
            )
            >
            (
                self.best[
                    "guaranteed_bps"
                ],
                self.best[
                    "guaranteed_net_lamports"
                ],
            )
        ):
            self.best=candidate


        print(
            "[FAST_PHYSICAL_OPPORTUNITY] "
            "dir=%s "
            "token=%s "
            "size=%.3f "
            "guaranteed=%+.9f_SOL "
            "bps=%+.2f "
            "slot=%d"%(
                candidate[
                    "direction"
                ],

                candidate[
                    "token"
                ][:10],

                candidate[
                    "size_sol"
                ],

                candidate[
                    "guaranteed_net_lamports"
                ]/1e9,

                candidate[
                    "guaranteed_bps"
                ],

                candidate[
                    "trigger_slot"
                ],
            ),
            flush=True
        )


    def _evaluate(
        self,
        event
    ):
        token=event[
            "token"
        ]

        pair=self.pairs.get(
            token
        )

        if pair is None:
            return


        started_ns=perf_counter_ns()

        latency_ms=max(
            0.0,
            (
                started_ns
                -event[
                    "received_ns"
                ]
            )/1e6
        )

        self.event_to_start_ms.append(
            latency_ms
        )


        print(
            "[VENUE_EVENT_TRIGGER] "
            "token=%s "
            "slot=%d "
            "event_to_physical_ms=%.3f"%(
                token[:10],
                event[
                    "slot"
                ],
                latency_ms,
            ),
            flush=True
        )


        points=[]


        for size in FAST_SIZES:

            rows=self._scan_size(
                pair,
                size
            )

            points.extend(
                rows
            )

            for row in rows:
                self._record_positive(
                    row,
                    event
                )


        quote_bps=[
            float(
                x[
                    "quote_bps"
                ]
            )

            for x in points

            if x.get(
                "ok"
            )
        ]


        best_quote=(
            max(
                quote_bps
            )
            if quote_bps
            else -1e99
        )


        if best_quote>=EXPAND_GATE_BPS:

            print(
                "[FAST_EXPAND] "
                "token=%s "
                "best_quote_bps=%+.2f"%(
                    token[:10],
                    best_quote
                ),
                flush=True
            )

            for size in EXPANSION_SIZES:

                rows=self._scan_size(
                    pair,
                    size
                )

                points.extend(
                    rows
                )

                for row in rows:
                    self._record_positive(
                        row,
                        event
                    )


        elapsed_ms=(
            perf_counter_ns()
            -started_ns
        )/1e6

        self.scan_ms.append(
            elapsed_ms
        )

        self.evaluations+=1


        print(
            "[FAST_SCAN_DONE] "
            "token=%s "
            "points=%d "
            "best_quote_bps=%+.2f "
            "scan_ms=%.3f"%(
                token[:10],
                len(
                    points
                ),
                best_quote,
                elapsed_ms,
            ),
            flush=True
        )


    def _worker(
        self
    ):
        while (
            not self.stop.is_set()
            or not self.q.empty()
        ):

            try:
                item=self.q.get(
                    timeout=.25
                )

            except queue.Empty:
                continue

            try:

                self._evaluate(
                    item
                )

            except Exception as exc:

                print(
                    "[FAST_LANE_ERROR] "
                    "token=%s %s:%s"%(
                        item[
                            "token"
                        ][:10],

                        type(exc).__name__,

                        str(exc)[:240],
                    ),
                    flush=True
                )

            finally:
                self.q.task_done()


    def close(
        self
    ):
        self.stop.set()

        try:
            self.q.join()

        except Exception:
            pass

        self.thread.join(
            timeout=5
        )


    def summary(
        self
    ):
        def p99(values):

            if not values:
                return None

            rows=sorted(
                values
            )

            return rows[
                min(
                    len(rows)-1,
                    int(
                        len(rows)*.99
                    )
                )
            ]


        return {
            "events_admitted":
                self.events,

            "evaluations":
                self.evaluations,

            "queue_drops":
                self.drops,

            "physical_positive_points":
                self.positives,

            "best":
                self.best,

            "p99_event_to_physical_start_ms":
                p99(
                    self.event_to_start_ms
                ),

            "p99_physical_scan_ms":
                p99(
                    self.scan_ms
                ),
        }


def warm_exact_pairs(
    root
):
    root=Path(
        root
    )


    engine._ensure_oracle_discovery(
        root,
        WARM_SECONDS+60.0
    )


    deadline=(
        time.monotonic()
        +WARM_SECONDS
    )


    rows=[]


    while (
        time.monotonic()
        <deadline
    ):

        try:
            rows=(
                engine.refresh_live_universe_rows(
                    root
                )
            )

        except Exception as exc:

            print(
                "[FAST_WARM_RETRY] "
                "%s:%s"%(
                    type(exc).__name__,
                    str(exc)[:180]
                ),
                flush=True
            )

            rows=[]


        if rows:
            break


        print(
            "[FAST_WARM_WAIT] "
            "waiting_for_exact_bound_pair=True",
            flush=True
        )

        time.sleep(
            3.0
        )


    if not rows:
        raise RuntimeError(
            "NO_FRESH_EXACT_BOUND_PAIRS"
        )


    BINDINGS.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    BINDINGS.write_text(
        json.dumps(
            {
                "revision":
                    "ORACLE_014",

                "rows":
                    rows,

                "created_epoch":
                    time.time(),

                "execution_authority":
                    False,
            },
            indent=2,
            sort_keys=True
        ),
        encoding="utf-8"
    )


    pairs,landing=(
        q47.prepare_from(
            BINDINGS,
            root
        )
    )


    if not pairs:
        raise RuntimeError(
            "FAST_LANE_HYDRATION_EMPTY"
        )


    print(
        "[FAST_WARM] "
        "exact_bound=%d "
        "hydrated=%d "
        "landing_lamports=%d"%(
            len(
                rows
            ),
            len(
                pairs
            ),
            int(
                landing
            ),
        ),
        flush=True
    )


    for pair in pairs:

        print(
            "[FAST_PAIR] "
            "token=%s "
            "pump=%s "
            "meteora=%s"%(
                pair.token[:10],
                pair.pump_pool[:12],
                pair.meteora_pool[:12],
            ),
            flush=True
        )


    return pairs,landing


def install_event_trigger(
    physical_lane
):
    original_apply=(
        persistent.m.pd.apply_account_event
    )


    def process_event(
        state,
        ev,
        counters,
        simulation_lane
    ):
        address=ev[
            "address"
        ]

        priced=False


        # PumpSwap + Meteora DLMM both live in preg.
        if address in state[
            "preg"
        ]:

            index,key=state[
                "preg"
            ][
                address
            ]

            pair=state[
                "pairs"
            ][
                index
            ]


            try:

                changed=original_apply(
                    pair,
                    key,
                    address,
                    ev[
                        "raw"
                    ],
                    ev[
                        "slot"
                    ],
                    ev[
                        "received_ns"
                    ]
                )


                if changed:

                    priced=True

                    physical_lane.submit(
                        pair.token,
                        ev[
                            "received_ns"
                        ],
                        address,
                        ev[
                            "slot"
                        ]
                    )


            except Exception as exc:

                counters[
                    "event_errors"
                ]+=1

                print(
                    "[FAST_EVENT_ERROR] "
                    "token=%s %s:%s"%(
                        pair.token[:10],
                        type(exc).__name__,
                        str(exc)[:160],
                    ),
                    flush=True
                )


        if priced:

            counters[
                "priced_events"
            ]+=1

            latency_ms=max(
                0.0,
                (
                    perf_counter_ns()
                    -ev[
                        "received_ns"
                    ]
                )/1e6
            )

            counters[
                "lat"
            ].append(
                latency_ms
            )


    persistent._process_event=(
        process_event
    )

    # Permanently prohibit old paper HOT_SIGNAL startup
    # from deciding anything inside this Oracle lane.
    persistent._initial_scan=(
        lambda state,counters,sim_lane:
            None
    )


def run(
    seconds=300.0
):
    root=Path.cwd()

    kp,user=(
        engine.base.require_keypair()
    )


    print(
        "[ORACLE-014] "
        "VENUE-NATIVE PHYSICAL FAST LANE",
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
        "[DISCOVERY_ROLE] "
        "PAIR_REPLENISHMENT_ONLY",
        flush=True
    )

    print(
        "[CRITICAL_PATH] "
        "Pump/Meteora account event "
        "-> physical repricing",
        flush=True
    )

    print(
        "[OLD_HOT_SIGNAL] "
        "PROHIBITED_FROM_ADMISSION",
        flush=True
    )

    print(
        "[FAST_SIZES] %s"%(
            ",".join(
                "%.3f"%x
                for x in FAST_SIZES
            )
        ),
        flush=True
    )

    print(
        "[EXPAND_GATE] %+.2f_bps"%(
            EXPAND_GATE_BPS
        ),
        flush=True
    )


    pairs,landing=(
        warm_exact_pairs(
            root
        )
    )


    fast_lane=PhysicalFastLane(
        user,
        pairs
    )


    def cached_prepare(
        _root
    ):
        return (
            pairs,
            landing
        )


    # One warm hydration, then account events maintain state.
    persistent.m.pd.prepare_pairs=(
        cached_prepare
    )

    persistent.SimulationLane=(
        NullSimulationLane
    )


    # Reuse the already-certified WS subscription valves.
    q61d.install()

    persistent.m._shards=(
        q61d.capped_valves
    )

    persistent._worker=(
        q61d.staggered_worker
    )


    install_event_trigger(
        fast_lane
    )


    print(
        "[WS] "
        "existing QARB-061D account stream reused",
        flush=True
    )

    print(
        "[VENUES] "
        "PumpSwap + Meteora DLMM direct",
        flush=True
    )

    print(
        "[BROADCAST] disabled",
        flush=True
    )


    try:

        result=asyncio.run(
            persistent.serve(
                root,
                float(
                    seconds
                )
            )
        )

    finally:

        fast_lane.close()

        engine._stop_oracle_discovery()


    summary=fast_lane.summary()


    report={
        "revision":
            "ORACLE_014",

        "paper_only":
            True,

        "execution_authority":
            False,

        "real_money_moved":
            False,

        "discovery_role":
            "PAIR_REPLENISHMENT_ONLY",

        "critical_path":
            "VENUE_ACCOUNT_EVENT_TO_PHYSICAL",

        "physical_fast_lane":
            summary,

        "transport":
            result,

        "created_unix":
            time.time(),
    }


    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    REPORT.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True
        ),
        encoding="utf-8"
    )


    print(
        "[FAST_COMPLETE] "
        "events=%d "
        "evaluations=%d "
        "drops=%d "
        "positive=%d "
        "p99_event_start_ms=%s "
        "p99_scan_ms=%s"%(
            summary[
                "events_admitted"
            ],

            summary[
                "evaluations"
            ],

            summary[
                "queue_drops"
            ],

            summary[
                "physical_positive_points"
            ],

            str(
                summary[
                    "p99_event_to_physical_start_ms"
                ]
            ),

            str(
                summary[
                    "p99_physical_scan_ms"
                ]
            ),
        ),
        flush=True
    )


    if summary[
        "best"
    ]:

        b=summary[
            "best"
        ]

        print(
            "[BEST_FAST_PHYSICAL] "
            "dir=%s "
            "token=%s "
            "size=%.3f "
            "guaranteed=%+.9f_SOL "
            "bps=%+.2f"%(
                b[
                    "direction"
                ],

                b[
                    "token"
                ][:10],

                b[
                    "size_sol"
                ],

                b[
                    "guaranteed_net_lamports"
                ]/1e9,

                b[
                    "guaranteed_bps"
                ],
            ),
            flush=True
        )

    else:

        print(
            "[FAST_NO_PHYSICAL_EDGE]",
            flush=True
        )


    print(
        "[REPORT] %s"%REPORT,
        flush=True
    )


    return 0


def main(
    argv=None
):
    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=float,
        default=300.0
    )

    args=ap.parse_args(
        argv
    )

    return run(
        args.seconds
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
