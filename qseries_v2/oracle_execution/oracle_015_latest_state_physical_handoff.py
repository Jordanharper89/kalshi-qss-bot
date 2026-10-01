from __future__ import annotations

import argparse
import os
import threading
import time

from time import perf_counter_ns

from qseries_v2.oracle_execution import (
    oracle_014_venue_native_fast_lane
    as q14
)

from qseries_v2.oracle_execution import (
    oracle_012_bidirectional_physical_market_scanner
    as bi
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


# ------------------------------------------------------------
# IN-MEMORY SCREEN
#
# This is NOT execution authority.
# It exists only to decide whether an event deserves one
# official physical recheck.
# ------------------------------------------------------------

SCREEN_GATE_BPS=float(
    os.getenv(
        "ORACLE_015_SCREEN_GATE_BPS",
        "-100"
    )
)


# An official check may START only while the originating
# event is still genuinely fresh.
VERIFY_START_MAX_AGE_MS=float(
    os.getenv(
        "ORACLE_015_VERIFY_START_MAX_AGE_MS",
        "750"
    )
)


class LatestStatePhysicalLane:

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

        self.cv=threading.Condition()

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # No FIFO event queue.
        #
        # At most ONE pending candidate per token.
        # A newer observation replaces an older observation.
        # ----------------------------------------------------

        self.latest={}

        self.stop=False

        self.screen_events=0
        self.screen_candidates=0

        self.coalesced=0
        self.stale_discarded=0

        self.official_attempts=0
        self.official_positive=0
        self.official_failures=0

        self.best=None

        self.screen_latency_ms=[]
        self.verify_start_age_ms=[]
        self.verify_duration_ms=[]

        self.thread=threading.Thread(
            target=self._worker,
            name="oracle015-latest-state-verifier",
            daemon=True
        )

        self.thread.start()


    def screen(
        self,
        state,
        pair,
        ev
    ):
        started=perf_counter_ns()

        self.screen_events+=1

        token=pair.token


        # ----------------------------------------------------
        # Reuse the EXISTING hydrated pair state.
        #
        # No HTTP.
        # No Node.
        # No getLatestBlockhash.
        # No fresh pool download.
        #
        # This screen is deliberately NOT called physical
        # execution truth. Official verification remains the
        # authority.
        # ----------------------------------------------------

        row=q14.persistent.m.evaluate_token(
            token,
            state[
                "eps"
            ].get(
                token,
                ()
            ),
            state[
                "landing"
            ],
            ev[
                "received_ns"
            ]
        )


        elapsed_ms=(
            perf_counter_ns()
            -started
        )/1e6

        self.screen_latency_ms.append(
            elapsed_ms
        )


        if not row:
            return


        print(
            "[INMEM_SCREEN] "
            "token=%s "
            "dir=%s->%s "
            "size=%.6f "
            "bps=%+.2f "
            "decision_ms=%.3f"%(
                token[:10],

                row.get(
                    "buy_venue"
                ),

                row.get(
                    "sell_venue"
                ),

                float(
                    row.get(
                        "size_sol"
                    )
                    or 0
                ),

                float(
                    row.get(
                        "net_bps"
                    )
                    or 0
                ),

                elapsed_ms,
            ),
            flush=True
        )


        if float(
            row.get(
                "net_bps"
            )
            or -1e99
        )<SCREEN_GATE_BPS:

            return


        buy=row.get(
            "buy_venue"
        )

        sell=row.get(
            "sell_venue"
        )


        if (
            buy=="PUMPSWAP"
            and sell=="METEORA_DLMM"
        ):
            direction=(
                bi.PUMP_TO_METEORA
            )

        elif (
            buy=="METEORA_DLMM"
            and sell=="PUMPSWAP"
        ):
            direction=(
                bi.METEORA_TO_PUMP
            )

        else:
            return


        candidate={
            "token":
                token,

            "direction":
                direction,

            "size_sol":
                float(
                    row[
                        "size_sol"
                    ]
                ),

            "screen_bps":
                float(
                    row[
                        "net_bps"
                    ]
                ),

            "received_ns":
                int(
                    ev[
                        "received_ns"
                    ]
                ),

            "slot":
                int(
                    ev[
                        "slot"
                    ]
                ),

            "address":
                ev[
                    "address"
                ],
        }


        self.screen_candidates+=1


        with self.cv:

            if token in self.latest:
                self.coalesced+=1

            self.latest[
                token
            ]=candidate

            self.cv.notify()


        print(
            "[VERIFY_ADMIT] "
            "token=%s "
            "dir=%s "
            "size=%.6f "
            "screen_bps=%+.2f "
            "slot=%d"%(
                token[:10],

                direction,

                candidate[
                    "size_sol"
                ],

                candidate[
                    "screen_bps"
                ],

                candidate[
                    "slot"
                ],
            ),
            flush=True
        )


    def _take_latest(
        self
    ):
        with self.cv:

            while (
                not self.latest
                and not self.stop
            ):
                self.cv.wait(
                    timeout=.25
                )


            if (
                self.stop
                and not self.latest
            ):
                return None


            # Process the newest pending candidate globally.
            token,candidate=max(
                self.latest.items(),
                key=lambda kv:
                    kv[1][
                        "received_ns"
                    ]
            )


            self.latest.pop(
                token,
                None
            )


            # ------------------------------------------------
            # Anything older than the selected market state is
            # useless if that same token already has a newer
            # pending observation.
            # ------------------------------------------------

            return candidate


    def _verify(
        self,
        candidate
    ):
        now_ns=perf_counter_ns()

        age_ms=max(
            0.0,
            (
                now_ns
                -candidate[
                    "received_ns"
                ]
            )/1e6
        )


        self.verify_start_age_ms.append(
            age_ms
        )


        if (
            age_ms
            >VERIFY_START_MAX_AGE_MS
        ):

            self.stale_discarded+=1

            print(
                "[VERIFY_STALE_DROP] "
                "token=%s "
                "slot=%d "
                "age_ms=%.3f"%(
                    candidate[
                        "token"
                    ][:10],

                    candidate[
                        "slot"
                    ],

                    age_ms,
                ),
                flush=True
            )

            return


        pair=self.pairs.get(
            candidate[
                "token"
            ]
        )

        if pair is None:
            return


        started=perf_counter_ns()

        self.official_attempts+=1


        print(
            "[OFFICIAL_VERIFY_START] "
            "token=%s "
            "dir=%s "
            "size=%.6f "
            "screen_bps=%+.2f "
            "event_age_ms=%.3f"%(
                candidate[
                    "token"
                ][:10],

                candidate[
                    "direction"
                ],

                candidate[
                    "size_sol"
                ],

                candidate[
                    "screen_bps"
                ],

                age_ms,
            ),
            flush=True
        )


        try:

            if (
                candidate[
                    "direction"
                ]
                ==bi.PUMP_TO_METEORA
            ):

                row=bi.safe_forward(
                    self.user,
                    pair,
                    candidate[
                        "size_sol"
                    ]
                )

            else:

                row=bi.evaluate_reverse(
                    self.user,
                    pair,
                    candidate[
                        "size_sol"
                    ]
                )


            elapsed_ms=(
                perf_counter_ns()
                -started
            )/1e6

            self.verify_duration_ms.append(
                elapsed_ms
            )


            if not row.get(
                "ok"
            ):

                self.official_failures+=1

                print(
                    "[OFFICIAL_VERIFY_REJECT] "
                    "token=%s "
                    "reason=%s "
                    "verify_ms=%.3f"%(
                        candidate[
                            "token"
                        ][:10],

                        row.get(
                            "reason"
                        ),

                        elapsed_ms,
                    ),
                    flush=True
                )

                return


            print(
                "[OFFICIAL_VERIFY] "
                "token=%s "
                "dir=%s "
                "size=%.6f "
                "screen_bps=%+.2f "
                "quote_bps=%+.2f "
                "guaranteed_bps=%+.2f "
                "verify_ms=%.3f"%(
                    candidate[
                        "token"
                    ][:10],

                    candidate[
                        "direction"
                    ],

                    candidate[
                        "size_sol"
                    ],

                    candidate[
                        "screen_bps"
                    ],

                    row[
                        "quote_bps"
                    ],

                    row[
                        "guaranteed_bps"
                    ],

                    elapsed_ms,
                ),
                flush=True
            )


            if not row.get(
                "guaranteed_positive"
            ):
                return


            self.official_positive+=1


            result=dict(
                row
            )

            result.update({
                "trigger_slot":
                    candidate[
                        "slot"
                    ],

                "screen_bps":
                    candidate[
                        "screen_bps"
                    ],

                "verification_started_event_age_ms":
                    age_ms,

                "verification_duration_ms":
                    elapsed_ms,
            })


            if (
                self.best is None
                or (
                    result[
                        "guaranteed_bps"
                    ],
                    result[
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
                self.best=result


            print(
                "[OFFICIAL_PHYSICAL_OPPORTUNITY] "
                "token=%s "
                "dir=%s "
                "size=%.6f "
                "guaranteed=%+.9f_SOL "
                "bps=%+.2f "
                "slot=%d"%(
                    result[
                        "token"
                    ][:10],

                    result[
                        "direction"
                    ],

                    result[
                        "size_sol"
                    ],

                    result[
                        "guaranteed_net_lamports"
                    ]/1e9,

                    result[
                        "guaranteed_bps"
                    ],

                    result[
                        "trigger_slot"
                    ],
                ),
                flush=True
            )


        except Exception as exc:

            self.official_failures+=1

            elapsed_ms=(
                perf_counter_ns()
                -started
            )/1e6

            self.verify_duration_ms.append(
                elapsed_ms
            )

            print(
                "[OFFICIAL_VERIFY_ERROR] "
                "token=%s %s:%s "
                "verify_ms=%.3f"%(
                    candidate[
                        "token"
                    ][:10],

                    type(exc).__name__,

                    str(exc)[:200],

                    elapsed_ms,
                ),
                flush=True
            )


    def _worker(
        self
    ):
        while True:

            candidate=(
                self._take_latest()
            )

            if candidate is None:
                return

            self._verify(
                candidate
            )


    def close(
        self
    ):
        with self.cv:

            # Never drain obsolete candidates at shutdown.
            self.latest.clear()

            self.stop=True

            self.cv.notify_all()


        self.thread.join(
            timeout=10
        )


    def summary(
        self
    ):
        def p99(
            values
        ):
            if not values:
                return None

            x=sorted(
                values
            )

            return x[
                min(
                    len(x)-1,
                    int(
                        len(x)*.99
                    )
                )
            ]


        return {
            # ORACLE-014 compatibility fields
            "events_admitted":
                self.screen_candidates,

            "evaluations":
                self.official_attempts,

            "queue_drops":
                0,

            "physical_positive_points":
                self.official_positive,

            "best":
                self.best,

            "p99_event_to_physical_start_ms":
                p99(
                    self.verify_start_age_ms
                ),

            "p99_physical_scan_ms":
                p99(
                    self.verify_duration_ms
                ),

            # ORACLE-015 evidence
            "screen_events":
                self.screen_events,

            "screen_candidates":
                self.screen_candidates,

            "coalesced":
                self.coalesced,

            "stale_discarded":
                self.stale_discarded,

            "official_attempts":
                self.official_attempts,

            "official_failures":
                self.official_failures,

            "official_positive":
                self.official_positive,

            "p99_inmemory_screen_ms":
                p99(
                    self.screen_latency_ms
                ),
        }


def install_event_trigger(
    lane
):
    original_apply=(
        q14.persistent.m.pd
        .apply_account_event
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

                    # ----------------------------------------
                    # CRITICAL CUTOVER:
                    #
                    # Screen synchronously from the already
                    # updated in-memory state.
                    #
                    # No slow physical queue between the WS
                    # event and this decision.
                    # ----------------------------------------

                    lane.screen(
                        state,
                        pair,
                        ev
                    )


            except Exception as exc:

                counters[
                    "event_errors"
                ]+=1

                print(
                    "[015_EVENT_ERROR] "
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

            counters[
                "lat"
            ].append(
                max(
                    0.0,
                    (
                        perf_counter_ns()
                        -ev[
                            "received_ns"
                        ]
                    )/1e6
                )
            )


    q14.persistent._process_event=(
        process_event
    )


    # Old paper initial HOT_SIGNAL remains disabled.
    q14.persistent._initial_scan=(
        lambda state,counters,sim_lane:
            None
    )


def install():

    q14.PhysicalFastLane=(
        LatestStatePhysicalLane
    )

    q14.install_event_trigger=(
        install_event_trigger
    )

    return q14


def run(
    seconds=300.0
):
    install()

    print(
        "[ORACLE-015] "
        "LATEST-STATE PHYSICAL HANDOFF",
        flush=True
    )

    print(
        "[HOT_PATH] "
        "venue event -> in-memory screen",
        flush=True
    )

    print(
        "[QUEUE] "
        "FIFO_DISABLED latest-state-per-token",
        flush=True
    )

    print(
        "[SCREEN_GATE] %+.2f_bps"%(
            SCREEN_GATE_BPS
        ),
        flush=True
    )

    print(
        "[VERIFY_MAX_START_AGE] %.1f_ms"%(
            VERIFY_START_MAX_AGE_MS
        ),
        flush=True
    )

    print(
        "[OFFICIAL] "
        "one exact size/direction only",
        flush=True
    )

    print(
        "[BROADCAST] disabled",
        flush=True
    )

    return q14.run(
        seconds
    )


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
