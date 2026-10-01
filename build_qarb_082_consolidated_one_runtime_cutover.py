from pathlib import Path
import py_compile

R=Path.cwd()

S=(
    R/
    "qseries_v2/oracle_strategy_intelligence/solana_money/"
    "qarb_execution_engineering"
)

Q80=S/"qarb_080_single_runtime_dynamic_mriya_supervisor.py"
Q81=S/"qarb_081_proven_arbitrage_lifecycle_certification.py"
M=S/"qarb_082_consolidated_one_runtime_cutover.py"

T=R/"test_qarb_082_consolidated_one_runtime_cutover.py"
U=R/"run_qarb_082_consolidated_one_runtime_cutover.py"

for p in (Q80,Q81):
    if not p.is_file():
        raise SystemExit(
            "[FAIL] dependency missing: "+str(p)
        )

s80=Q80.read_text(encoding="utf-8")
s81=Q81.read_text(encoding="utf-8")

guards=[
    ("QARB-080 run","def run(" in s80),
    ("QARB-080 dynamic","def select_rows(" in s80),
    ("QARB-080 presence","PRESENCE=Path(" in s80),
    ("QARB-080 transport","WS_TRANSPORT_FINAL" in s80),
    ("QARB-080 safety","REAL_MONEY_MOVED=False" in s80),
    ("QARB-081 certify","def certify(root):" in s81),
    ("QARB-081 proven","PROVEN_PAPER_ARBITRAGE" in s81),
    ("QARB-081 recheck","requires_live_recheck" in s81),
    ("QARB-081 safety","REAL_MONEY_MOVED=False" in s81),
]

bad=[
    name
    for name,ok in guards
    if not ok
]

if bad:
    raise SystemExit(
        "[FAIL] exact current runtime contract changed: "
        +repr(bad)
    )

module=r'''from __future__ import annotations

import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_080_single_runtime_dynamic_mriya_supervisor as q80
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_081_proven_arbitrage_lifecycle_certification as q81


STATE=Path(
    "runtime_state/qseries/"
    "qarb_execution_engineering/"
    "qarb_082_consolidated_one_runtime_cutover.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


def _save(root,payload):
    p=Path(root)/STATE

    p.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    t=p.with_suffix(
        p.suffix+".tmp"
    )

    t.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True
        ),
        encoding="utf-8"
    )

    t.replace(p)


def certification_summary(root):
    r=q81.certify(
        Path(root)
    )

    return {
        "proven_count":
            int(
                r.get(
                    "proven_count",
                    0
                )
            ),
        "research_count":
            int(
                r.get(
                    "research_count",
                    0
                )
            ),
        "proven_tokens":
            sorted(
                r.get(
                    "proven_tokens",
                    {}
                )
            ),
        "recyclable_proven_tokens":
            sorted(
                r.get(
                    "recyclable_proven_tokens",
                    []
                )
            ),
        "restart_continuity":
            dict(
                r.get(
                    "restart_continuity",
                    {}
                )
            ),
        "execution_authority":
            False,
    }


def run(
    seconds=None,
    refresh_seconds=60.0,
    drain_seconds=155.0
):
    root=Path.cwd()

    before=certification_summary(
        root
    )

    print(
        "[QARB-082] CONSOLIDATED ONE-RUNTIME CUTOVER",
        flush=True
    )

    print(
        "[CORE] QARB-080 owns discovery, rotation, "
        "hydration, WS transport, paper outcomes and learning",
        flush=True
    )

    print(
        "[CLASSIFIER] QARB-081 proven/research "
        "certification is internal to this launcher",
        flush=True
    )

    print(
        "[PRECHECK] proven=%d research=%d "
        "recyclable=%d"%(
            before[
                "proven_count"
            ],
            before[
                "research_count"
            ],
            len(
                before[
                    "recyclable_proven_tokens"
                ]
            )
        ),
        flush=True
    )

    _save(
        root,
        {
            "revision":
                "QARB_082",
            "phase":
                "STARTING",
            "started_unix":
                time.time(),
            "precheck":
                before,
            "single_manual_launcher":
                True,
            "runtime_core":
                "QARB_080",
            "classification_core":
                "QARB_081",
            "execution_authority":
                False,
            "paper_only":
                True,
            "real_money_moved":
                False,
        }
    )

    rc=q80.run(
        seconds=seconds,
        refresh_seconds=
            refresh_seconds,
        drain_seconds=
            drain_seconds
    )

    after=certification_summary(
        root
    )

    continuity=(
        after.get(
            "restart_continuity",
            {}
        ).get(
            "status"
        )
    )

    runtime_ok=(
        rc in (
            None,
            0
        )
    )

    certification_ok=(
        continuity in (
            "PASS",
            "BASELINE"
        )
    )

    status=(
        "PASS"
        if (
            runtime_ok
            and certification_ok
        )
        else "HOLD"
    )

    _save(
        root,
        {
            "revision":
                "QARB_082",
            "phase":
                "COMPLETE",
            "completed_unix":
                time.time(),
            "precheck":
                before,
            "postcheck":
                after,
            "runtime_return_code":
                rc,
            "single_manual_launcher":
                True,
            "runtime_core":
                "QARB_080",
            "classification_core":
                "QARB_081",
            "status":
                status,
            "execution_authority":
                False,
            "paper_only":
                True,
            "real_money_moved":
                False,
        }
    )

    print(
        "[POSTCHECK] proven=%d research=%d "
        "recyclable=%d continuity=%s"%(
            after[
                "proven_count"
            ],
            after[
                "research_count"
            ],
            len(
                after[
                    "recyclable_proven_tokens"
                ]
            ),
            continuity
        ),
        flush=True
    )

    print(
        "[ONE_RUNTIME] status=%s "
        "manual_launchers=1"%status,
        flush=True
    )

    print(
        "[MODE] PAPER_ONLY=True "
        "execution_authority=FALSE "
        "real_money_moved=FALSE",
        flush=True
    )

    return (
        0
        if status=="PASS"
        else 2
    )


def main(argv=None):
    import argparse

    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=float,
        default=None
    )

    ap.add_argument(
        "--refresh-seconds",
        type=float,
        default=60.0
    )

    ap.add_argument(
        "--drain-seconds",
        type=float,
        default=155.0
    )

    a=ap.parse_args(
        argv
    )

    return run(
        seconds=
            a.seconds,
        refresh_seconds=
            a.refresh_seconds,
        drain_seconds=
            a.drain_seconds
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
'''

tests=r'''import inspect
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_082_consolidated_one_runtime_cutover as q


class T(unittest.TestCase):

    def test_runtime_core_is_080(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "q80.run(",
            s
        )


    def test_classifier_is_081(self):
        s=inspect.getsource(
            q.certification_summary
        )

        self.assertIn(
            "q81.certify",
            s
        )


    def test_no_second_manual_runtime(self):
        s=inspect.getsource(
            q.run
        )

        self.assertNotIn(
            "subprocess.Popen",
            s
        )

        self.assertNotIn(
            "run_qarb_081",
            s
        )


    def test_dynamic_080_contract(self):
        self.assertTrue(
            callable(
                q.q80.select_rows
            )
        )

        self.assertTrue(
            callable(
                q.q80.run
            )
        )


    def test_proven_classifier_contract(self):
        self.assertTrue(
            callable(
                q.q81.certify
            )
        )

        self.assertEqual(
            q.q81.MIN_TOKEN_SAMPLES,
            30
        )

        self.assertEqual(
            q.q81.MIN_TOKEN_WIN_RATE,
            0.80
        )


    def test_080_transport_contract(self):
        self.assertGreaterEqual(
            q.q80.WS_CONNECTION_STAGGER_SECONDS,
            2.0
        )


    def test_080_horizon_contract(self):
        self.assertEqual(
            q.q80.MAX_HORIZON_SECONDS,
            90.0
        )


    def test_authority_false_everywhere(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertFalse(
            q.q80.EXECUTION_AUTHORITY
        )

        self.assertFalse(
            q.q81.EXECUTION_AUTHORITY
        )


    def test_paper_only(self):
        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertTrue(
            q.q80.PAPER_ONLY
        )

        self.assertTrue(
            q.q81.PAPER_ONLY
        )


    def test_no_real_money(self):
        self.assertFalse(
            q.REAL_MONEY_MOVED
        )

        self.assertFalse(
            q.q80.REAL_MONEY_MOVED
        )

        self.assertFalse(
            q.q81.REAL_MONEY_MOVED
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
'''

launcher=r'''from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering.qarb_082_consolidated_one_runtime_cutover import main

if __name__=="__main__":
    raise SystemExit(
        main()
    )
'''

M.write_text(
    module,
    encoding="utf-8"
)

T.write_text(
    tests,
    encoding="utf-8"
)

U.write_text(
    launcher,
    encoding="utf-8"
)

for p in (
    M,
    T,
    U
):
    py_compile.compile(
        str(p),
        doraise=True
    )

print(
    "[PASS] QARB-082 consolidated one-runtime cutover installed"
)

print(
    "[CORE] QARB-080 remains sole live runtime core"
)

print(
    "[CLASSIFIER] QARB-081 internal proven/research certification"
)

print(
    "[LAUNCH] one manual launcher; no separate 081 runtime window"
)

print(
    "[PRESERVE] dynamic discovery + profitable-token recycling + 2/5/15/30/60/90 learning"
)

print(
    "[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE"
)