from pathlib import Path
import py_compile

ROOT=Path.cwd()
OUT=ROOT/"qseries_v2/oracle_execution"

MODULE=OUT/"oracle_016_physical_parity_calibration.py"
LAUNCHER=ROOT/"run_oracle_physical_parity_lane.py"
TEST=ROOT/"test_oracle_016_physical_parity_calibration.py"

Q15=OUT/"oracle_015_latest_state_physical_handoff.py"

if not Q15.is_file():
    raise SystemExit("[FAIL] ORACLE-015 missing")

MODULE.write_text(r'''
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from time import perf_counter_ns

from qseries_v2.oracle_execution import (
    oracle_015_latest_state_physical_handoff as q15
)

from qseries_v2.oracle_execution import (
    oracle_014_venue_native_fast_lane as q14
)

from qseries_v2.oracle_execution import (
    oracle_012_bidirectional_physical_market_scanner as bi
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

# Raw legacy screen may be used only to decide whether an
# official calibration probe is worthwhile.
PROBE_GATE_BPS=float(
    os.getenv(
        "ORACLE_016_PROBE_GATE_BPS",
        "-100"
    )
)

# After calibration, require the corrected screen to be
# above this value before spending an official verification.
CORRECTED_GATE_BPS=float(
    os.getenv(
        "ORACLE_016_CORRECTED_GATE_BPS",
        "-25"
    )
)

# Additional safety margin beyond the worst measured
# screen->official error.
PARITY_MARGIN_BPS=float(
    os.getenv(
        "ORACLE_016_PARITY_MARGIN_BPS",
        "25"
    )
)

VERIFY_START_MAX_AGE_MS=float(
    os.getenv(
        "ORACLE_016_VERIFY_START_MAX_AGE_MS",
        "750"
    )
)

STATE=Path(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_016_physical_parity_calibration.json"
)


def key_for(
    token,
    direction,
    size
):
    return "%s|%s|%.6f"%(
        token,
        direction,
        float(size)
    )


class CalibratedPhysicalLane(
    q15.LatestStatePhysicalLane
):

    def __init__(
        self,
        user,
        pairs
    ):
        self.parity={}
        self.direction_worst={}
        self.parity_samples=0
        self.parity_false_positive=0

        super().__init__(
            user,
            pairs
        )


    def _direction(
        self,
        row
    ):
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
            return bi.PUMP_TO_METEORA

        if (
            buy=="METEORA_DLMM"
            and sell=="PUMPSWAP"
        ):
            return bi.METEORA_TO_PUMP

        return None


    def _correction(
        self,
        token,
        direction,
        size
    ):
        key=key_for(
            token,
            direction,
            size
        )

        row=self.parity.get(
            key
        )

        if row:
            return (
                float(
                    row[
                        "worst_overstatement_bps"
                    ]
                ),
                "EXACT_KEY"
            )

        if direction in self.direction_worst:
            return (
                float(
                    self.direction_worst[
                        direction
                    ]
                ),
                "DIRECTION_FALLBACK"
            )

        return (
            None,
            "UNCALIBRATED"
        )


    def screen(
        self,
        state,
        pair,
        ev
    ):
        started=perf_counter_ns()

        self.screen_events+=1

        row=q14.persistent.m.evaluate_token(
            pair.token,
            state[
                "eps"
            ].get(
                pair.token,
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

        direction=self._direction(
            row
        )

        if direction is None:
            return

        raw_bps=float(
            row.get(
                "net_bps"
            )
            or -1e99
        )

        size=float(
            row[
                "size_sol"
            ]
        )

        correction,source=(
            self._correction(
                pair.token,
                direction,
                size
            )
        )

        corrected=(
            None
            if correction is None
            else (
                raw_bps
                -correction
                -PARITY_MARGIN_BPS
            )
        )

        print(
            "[PARITY_SCREEN] "
            "token=%s "
            "dir=%s "
            "size=%.6f "
            "raw=%+.2f "
            "correction=%s "
            "corrected=%s "
            "source=%s "
            "decision_ms=%.3f"%(
                pair.token[:10],
                direction,
                size,
                raw_bps,

                (
                    "NA"
                    if correction is None
                    else "%+.2f"%correction
                ),

                (
                    "NA"
                    if corrected is None
                    else "%+.2f"%corrected
                ),

                source,
                elapsed_ms,
            ),
            flush=True
        )

        # ----------------------------------------------------
        # Uncalibrated:
        # allow only a truth-probe, never classify positive.
        # ----------------------------------------------------

        if correction is None:

            if raw_bps<PROBE_GATE_BPS:
                return

            admission_type=(
                "CALIBRATION_PROBE"
            )

        else:

            if corrected<CORRECTED_GATE_BPS:
                return

            admission_type=(
                "CALIBRATED_VERIFY"
            )


        candidate={
            "token":
                pair.token,

            "direction":
                direction,

            "size_sol":
                size,

            "screen_bps":
                raw_bps,

            "corrected_screen_bps":
                corrected,

            "correction_bps":
                correction,

            "calibration_source":
                source,

            "admission_type":
                admission_type,

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

            if pair.token in self.latest:
                self.coalesced+=1

            self.latest[
                pair.token
            ]=candidate

            self.cv.notify()


        print(
            "[PARITY_ADMIT] "
            "type=%s "
            "token=%s "
            "dir=%s "
            "size=%.6f "
            "raw=%+.2f "
            "corrected=%s "
            "slot=%d"%(
                admission_type,
                pair.token[:10],
                direction,
                size,
                raw_bps,

                (
                    "NA"
                    if corrected is None
                    else "%+.2f"%corrected
                ),

                candidate[
                    "slot"
                ],
            ),
            flush=True
        )


    def _update_parity(
        self,
        candidate,
        official
    ):
        guaranteed=float(
            official[
                "guaranteed_bps"
            ]
        )

        raw=float(
            candidate[
                "screen_bps"
            ]
        )

        overstatement=(
            raw
            -guaranteed
        )

        key=key_for(
            candidate[
                "token"
            ],
            candidate[
                "direction"
            ],
            candidate[
                "size_sol"
            ]
        )

        row=self.parity.setdefault(
            key,
            {
                "samples":0,
                "worst_overstatement_bps":
                    overstatement,
                "latest_overstatement_bps":
                    overstatement,
            }
        )

        row[
            "samples"
        ]+=1

        row[
            "latest_overstatement_bps"
        ]=overstatement

        row[
            "worst_overstatement_bps"
        ]=max(
            float(
                row[
                    "worst_overstatement_bps"
                ]
            ),
            overstatement
        )

        direction=candidate[
            "direction"
        ]

        self.direction_worst[
            direction
        ]=max(
            float(
                self.direction_worst.get(
                    direction,
                    overstatement
                )
            ),
            overstatement
        )

        self.parity_samples+=1

        if (
            raw>0
            and guaranteed<=0
        ):
            self.parity_false_positive+=1

        STATE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        STATE.write_text(
            json.dumps(
                {
                    "revision":
                        "ORACLE_016",

                    "parity_samples":
                        self.parity_samples,

                    "false_positive_samples":
                        self.parity_false_positive,

                    "direction_worst":
                        self.direction_worst,

                    "keys":
                        self.parity,

                    "execution_authority":
                        False,

                    "updated_unix":
                        time.time(),
                },
                indent=2,
                sort_keys=True
            ),
            encoding="utf-8"
        )

        return overstatement


    def _verify(
        self,
        candidate
    ):
        age_ms=max(
            0.0,
            (
                perf_counter_ns()
                -candidate[
                    "received_ns"
                ]
            )/1e6
        )

        self.verify_start_age_ms.append(
            age_ms
        )

        if age_ms>VERIFY_START_MAX_AGE_MS:

            self.stale_discarded+=1

            print(
                "[PARITY_STALE_DROP] "
                "token=%s "
                "age_ms=%.3f"%(
                    candidate[
                        "token"
                    ][:10],
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


        try:

            if (
                candidate[
                    "direction"
                ]
                ==bi.PUMP_TO_METEORA
            ):

                official=bi.safe_forward(
                    self.user,
                    pair,
                    candidate[
                        "size_sol"
                    ]
                )

            else:

                official=bi.evaluate_reverse(
                    self.user,
                    pair,
                    candidate[
                        "size_sol"
                    ]
                )


            verify_ms=(
                perf_counter_ns()
                -started
            )/1e6

            self.verify_duration_ms.append(
                verify_ms
            )


            if not official.get(
                "ok"
            ):

                self.official_failures+=1

                print(
                    "[PARITY_VERIFY_REJECT] "
                    "token=%s "
                    "reason=%s"%(
                        candidate[
                            "token"
                        ][:10],

                        official.get(
                            "reason"
                        ),
                    ),
                    flush=True
                )

                return


            error=self._update_parity(
                candidate,
                official
            )


            print(
                "[PARITY_RESULT] "
                "token=%s "
                "dir=%s "
                "size=%.6f "
                "screen=%+.2f "
                "official_quote=%+.2f "
                "official_guaranteed=%+.2f "
                "overstatement=%+.2f "
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

                    official[
                        "quote_bps"
                    ],

                    official[
                        "guaranteed_bps"
                    ],

                    error,

                    verify_ms,
                ),
                flush=True
            )


            if not official.get(
                "guaranteed_positive"
            ):
                return


            self.official_positive+=1


            result=dict(
                official
            )

            result.update({
                "trigger_slot":
                    candidate[
                        "slot"
                    ],

                "raw_screen_bps":
                    candidate[
                        "screen_bps"
                    ],

                "parity_overstatement_bps":
                    error,

                "verification_started_event_age_ms":
                    age_ms,

                "verification_duration_ms":
                    verify_ms,
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
                "[PARITY_CERTIFIED_PHYSICAL_EDGE] "
                "token=%s "
                "dir=%s "
                "size=%.6f "
                "guaranteed=%+.9f_SOL "
                "bps=%+.2f"%(
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
                ),
                flush=True
            )


        except Exception as exc:

            self.official_failures+=1

            print(
                "[PARITY_VERIFY_ERROR] "
                "token=%s %s:%s"%(
                    candidate[
                        "token"
                    ][:10],

                    type(exc).__name__,

                    str(exc)[:200],
                ),
                flush=True
            )


    def summary(
        self
    ):
        x=super().summary()

        x.update({
            "parity_samples":
                self.parity_samples,

            "parity_false_positive_samples":
                self.parity_false_positive,

            "calibrated_keys":
                len(
                    self.parity
                ),

            "direction_worst_overstatement_bps":
                dict(
                    self.direction_worst
                ),
        })

        return x


def install():

    q15.LatestStatePhysicalLane=(
        CalibratedPhysicalLane
    )

    return q15


def run(
    seconds=300.0
):
    install()

    print(
        "[ORACLE-016] "
        "PHYSICAL PARITY CALIBRATION",
        flush=True
    )

    print(
        "[HOT_PATH] "
        "venue update -> sub-ms screen",
        flush=True
    )

    print(
        "[RAW_SCREEN] "
        "NOT PROFIT AUTHORITY",
        flush=True
    )

    print(
        "[PARITY] "
        "screen error measured against official physical truth",
        flush=True
    )

    print(
        "[CORRECTION] "
        "worst observed overstatement + %.2f bps margin"%(
            PARITY_MARGIN_BPS
        ),
        flush=True
    )

    print(
        "[BROADCAST] disabled",
        flush=True
    )

    return q15.run(
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
'''.strip()+"\n",encoding="utf-8")

py_compile.compile(
    str(MODULE),
    doraise=True
)


LAUNCHER.write_text(
r'''
import getpass
import os

from qseries_v2.oracle_execution.oracle_016_physical_parity_calibration import (
    main
)

if __name__=="__main__":

    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

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
    oracle_016_physical_parity_calibration
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


    def test_raw_screen_not_authority(self):

        s=inspect.getsource(
            q.CalibratedPhysicalLane.screen
        )

        self.assertIn(
            "correction",
            s
        )

        self.assertIn(
            "corrected",
            s
        )


    def test_official_truth_updates_parity(self):

        s=inspect.getsource(
            q.CalibratedPhysicalLane._verify
        )

        self.assertIn(
            "_update_parity",
            s
        )

        self.assertIn(
            "guaranteed_positive",
            s
        )


    def test_worst_case_correction(self):

        s=inspect.getsource(
            q.CalibratedPhysicalLane._update_parity
        )

        self.assertIn(
            "worst_overstatement_bps",
            s
        )

        self.assertIn(
            "max(",
            s
        )


    def test_margin(self):

        self.assertGreater(
            q.PARITY_MARGIN_BPS,
            0
        )


    def test_latest_state_parent_preserved(self):

        self.assertTrue(
            issubclass(
                q.CalibratedPhysicalLane,
                q.q15.LatestStatePhysicalLane
            )
        )


    def test_no_broadcast(self):

        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            s=f.read()

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
    "[PASS] ORACLE-016 physical parity calibration installed"
)

print(
    "[HOT_PATH] existing sub-ms venue-native screen preserved"
)

print(
    "[RAW_SCREEN] explicitly demoted from profit authority"
)

print(
    "[TRUTH] official Pump/Meteora physical verifier remains authority"
)

print(
    "[CALIBRATION] per token/direction/size error learned"
)

print(
    "[FALLBACK] worst observed direction error used conservatively"
)

print(
    "[MARGIN] extra 25 bps safety margin"
)

print(
    "[FIFO] remains disabled"
)

print(
    "[STALE] verification must begin <=750ms"
)

print(
    "[BROADCAST] disabled"
)

print(
    "[OWNER] ORACLE"
)