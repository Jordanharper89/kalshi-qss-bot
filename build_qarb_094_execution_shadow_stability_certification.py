from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering"

Q93=S/"qarb_093_continuous_execution_shadow_refresh.py"

M=S/"qarb_094_execution_shadow_stability_certification.py"
T=R/"test_qarb_094_execution_shadow_stability_certification.py"
U=R/"run_qarb_094_execution_shadow_stability_certification.py"

if not Q93.is_file():
    raise SystemExit(
        "[FAIL] dependency missing: "+str(Q93)
    )

s93=Q93.read_text(
    encoding="utf-8"
)

guards=[
    (
        "093 history",
        "qarb_093_execution_shadow_history.jsonl"
        in s93
    ),
    (
        "093 current",
        "qarb_093_current_execution_shadow_bindings.json"
        in s93
    ),
    (
        "093 cycle result",
        '"results"'
        in s93
    ),
    (
        "093 active status",
        "CURRENT_EXECUTION_SHADOW_PASS"
        in s93
    ),
]

bad=[
    n
    for n,ok in guards
    if not ok
]

if bad:
    raise SystemExit(
        "[FAIL] current QARB-093 contract changed: "
        +repr(bad)
    )

module=r'''from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_093_continuous_execution_shadow_refresh as q93


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_094_execution_shadow_stability_certification.json"
)

CERTIFIED=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_094_certified_execution_shadow_set.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

MIN_CYCLES=3
MIN_PASS_RATE=1.0


def _save(path,payload):
    p=Path(path)

    p.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    tmp=p.with_suffix(
        p.suffix+".tmp"
    )

    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True
        ),
        encoding="utf-8"
    )

    tmp.replace(p)


def load_history(root):
    p=Path(root)/q93.HISTORY

    if not p.is_file():
        raise RuntimeError(
            "QARB_093_HISTORY_MISSING"
        )

    rows=[]

    with p.open(
        "r",
        encoding="utf-8"
    ) as f:
        for line in f:
            line=line.strip()

            if not line:
                continue

            rows.append(
                json.loads(line)
            )

    if not rows:
        raise RuntimeError(
            "QARB_093_HISTORY_EMPTY"
        )

    rows.sort(
        key=lambda x:
            int(
                x.get(
                    "cycle",
                    0
                )
            )
    )

    return rows


def token_universe(history):
    out=set()

    for cycle in history:
        out.update(
            (
                cycle.get(
                    "results"
                )
                or {}
            ).keys()
        )

    return sorted(out)


def observation_for(
    cycle,
    token
):
    result=(
        cycle.get(
            "results"
        )
        or {}
    ).get(
        token
    )

    if not isinstance(
        result,
        dict
    ):
        return {
            "active":False,
            "reason":"NO_RESULT",
        }

    active=(
        result.get(
            "status"
        )
        =="CURRENT_EXECUTION_SHADOW_PASS"
    )

    if not active:
        rv=result.get(
            "revalidation"
        ) or {}

        return {
            "active":False,
            "reason":(
                rv.get(
                    "reason"
                )
                or result.get(
                    "status"
                )
                or "INACTIVE"
            ),
        }

    a=result.get(
        "active"
    ) or {}

    sim=result.get(
        "simulation"
    ) or {}

    return {
        "active":True,

        "bps":
            float(
                a[
                    "fresh_net_bps"
                ]
            ),

        "net_lamports":
            int(
                a[
                    "fresh_net_lamports"
                ]
            ),

        "candidate":
            a.get(
                "candidate"
            ),

        "transaction_bytes":
            int(
                a[
                    "transaction_bytes"
                ]
            ),

        "size_sol":
            float(
                a[
                    "size_sol"
                ]
            ),

        "sim_err":
            a.get(
                "sim_err"
            ),

        "preferred_reused":
            bool(
                sim.get(
                    "preferred_reused",
                    False
                )
            ),

        "pump_pool":
            a.get(
                "pump_pool"
            ),

        "meteora_meta":
            a.get(
                "meteora_meta"
            ),
    }


def transitions(
    observations
):
    drops=0
    reentries=0
    streak=0
    max_streak=0
    prior=None

    for x in observations:
        active=bool(
            x.get(
                "active"
            )
        )

        if active:
            streak+=1
            max_streak=max(
                max_streak,
                streak
            )

        else:
            streak=0

        if prior is True and not active:
            drops+=1

        if prior is False and active:
            reentries+=1

        prior=active

    return {
        "drop_count":drops,
        "reentry_count":reentries,
        "ending_pass_streak":streak,
        "max_pass_streak":max_streak,
    }


def analyze_token(
    token,
    history
):
    observations=[
        observation_for(
            cycle,
            token
        )
        for cycle in history
    ]

    active=[
        x
        for x in observations
        if x.get(
            "active"
        )
    ]

    passes=len(active)
    total=len(
        observations
    )

    pass_rate=(
        passes/total
        if total
        else 0.0
    )

    bps=[
        x["bps"]
        for x in active
    ]

    sizes=[
        x["size_sol"]
        for x in active
    ]

    tx_bytes=[
        x[
            "transaction_bytes"
        ]
        for x in active
    ]

    candidates=[
        x.get(
            "candidate"
        )
        for x in active
        if x.get(
            "candidate"
        )
    ]

    sim_errors=[
        x.get(
            "sim_err"
        )
        for x in active
        if x.get(
            "sim_err"
        ) is not None
    ]

    reused=[
        bool(
            x.get(
                "preferred_reused"
            )
        )
        for x in active
    ]

    tr=transitions(
        observations
    )

    candidate_values=sorted(
        set(candidates)
    )

    byte_values=sorted(
        set(tx_bytes)
    )

    size_values=sorted(
        set(sizes)
    )

    reasons={}

    for x in observations:
        if x.get(
            "active"
        ):
            continue

        reason=str(
            x.get(
                "reason",
                "INACTIVE"
            )
        )

        reasons[reason]=(
            reasons.get(
                reason,
                0
            )
            +1
        )

    certified=bool(
        total>=MIN_CYCLES
        and passes==total
        and pass_rate>=MIN_PASS_RATE
        and bps
        and min(bps)>0
        and not sim_errors
        and len(
            candidate_values
        )==1
        and len(
            byte_values
        )==1
        and len(
            size_values
        )==1
    )

    return {
        "token":
            token,

        "cycles_observed":
            total,

        "passes":
            passes,

        "pass_rate":
            pass_rate,

        "drop_count":
            tr[
                "drop_count"
            ],

        "reentry_count":
            tr[
                "reentry_count"
            ],

        "ending_pass_streak":
            tr[
                "ending_pass_streak"
            ],

        "max_pass_streak":
            tr[
                "max_pass_streak"
            ],

        "bps_min":(
            min(bps)
            if bps
            else None
        ),

        "bps_max":(
            max(bps)
            if bps
            else None
        ),

        "bps_mean":(
            statistics.fmean(
                bps
            )
            if bps
            else None
        ),

        "bps_median":(
            statistics.median(
                bps
            )
            if bps
            else None
        ),

        "bps_population_std":(
            statistics.pstdev(
                bps
            )
            if len(bps)>1
            else 0.0
            if bps
            else None
        ),

        "candidate_values":
            candidate_values,

        "candidate_stable":
            len(
                candidate_values
            )==1
            if active
            else False,

        "transaction_byte_values":
            byte_values,

        "transaction_size_stable":
            len(
                byte_values
            )==1
            if active
            else False,

        "size_values":
            size_values,

        "trade_size_stable":
            len(
                size_values
            )==1
            if active
            else False,

        "preferred_reuse_passes":
            sum(
                1
                for x in reused
                if x
            ),

        "preferred_reuse_rate":(
            sum(
                1
                for x in reused
                if x
            )/len(reused)
            if reused
            else 0.0
        ),

        "sim_error_count":
            len(
                sim_errors
            ),

        "inactive_reasons":
            reasons,

        "certified_stable_shadow":
            certified,
    }


def certified_row(
    analysis,
    current_map
):
    token=analysis[
        "token"
    ]

    current=current_map.get(
        token
    )

    if not isinstance(
        current,
        dict
    ):
        return None

    return {
        "token":
            token,

        "pump_pool":
            current.get(
                "pump_pool"
            ),

        "meteora_meta":
            current.get(
                "meteora_meta"
            ),

        "size_sol":
            current.get(
                "size_sol"
            ),

        "candidate":
            current.get(
                "candidate"
            ),

        "transaction_bytes":
            current.get(
                "transaction_bytes"
            ),

        "stability":{
            "cycles":
                analysis[
                    "cycles_observed"
                ],

            "pass_rate":
                analysis[
                    "pass_rate"
                ],

            "pass_streak":
                analysis[
                    "ending_pass_streak"
                ],

            "bps_min":
                analysis[
                    "bps_min"
                ],

            "bps_mean":
                analysis[
                    "bps_mean"
                ],

            "bps_max":
                analysis[
                    "bps_max"
                ],

            "bps_population_std":
                analysis[
                    "bps_population_std"
                ],

            "preferred_reuse_rate":
                analysis[
                    "preferred_reuse_rate"
                ],
        },

        "execution_authority":
            False,

        "paper_only":
            True,
    }


def run(root=None):
    root=Path(
        root or Path.cwd()
    )

    print(
        "[QARB-094] EXECUTION-SHADOW "
        "STABILITY CERTIFICATION",
        flush=True
    )

    print(
        "[SOURCE] frozen QARB-093 "
        "JSONL history only",
        flush=True
    )

    print(
        "[MEASURE] pass streak, drops, "
        "reentries, bps distribution, "
        "candidate/tx-size stability",
        flush=True
    )

    history=load_history(
        root
    )

    current_path=(
        root/q93.CURRENT
    )

    current={}

    if current_path.is_file():
        d=json.loads(
            current_path.read_text(
                encoding="utf-8"
            )
        )

        current={
            x["token"]:x
            for x in d.get(
                "rows",
                []
            )
            if x.get(
                "token"
            )
        }

    analyses=[]

    for token in token_universe(
        history
    ):
        analyses.append(
            analyze_token(
                token,
                history
            )
        )

    certified=[
        x
        for x in analyses
        if x[
            "certified_stable_shadow"
        ]
    ]

    certified_rows=[]

    for x in certified:
        row=certified_row(
            x,
            current
        )

        if row is not None:
            certified_rows.append(
                row
            )

    certified_rows.sort(
        key=lambda x:
            (
                x[
                    "stability"
                ][
                    "bps_mean"
                ]
                or 0.0
            ),
        reverse=True
    )

    status=(
        "PASS"
        if certified_rows
        else "HOLD"
    )

    report={
        "revision":
            "QARB_094",

        "status":
            status,

        "history_cycles":
            len(history),

        "tokens_observed":
            len(analyses),

        "certified_count":
            len(
                certified_rows
            ),

        "certified_tokens":[
            x["token"]
            for x in certified_rows
        ],

        "analysis":
            analyses,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "private_key_required":
            False,

        "created_epoch":
            time.time(),
    }

    payload={
        "revision":
            "QARB_094",

        "status":
            status,

        "rows":
            certified_rows,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "private_key_required":
            False,

        "created_epoch":
            time.time(),
    }

    _save(
        root/STATE,
        report
    )

    _save(
        root/CERTIFIED,
        payload
    )

    for x in analyses:
        print(
            "[2S_STABILITY] "
            "token=%s "
            "cycles=%d passes=%d "
            "pass_rate=%.1f%% "
            "streak=%d drops=%d "
            "reentries=%d "
            "bps_min=%s "
            "bps_mean=%s "
            "bps_max=%s "
            "tx_stable=%s "
            "candidate_stable=%s "
            "reuse=%.1f%% "
            "certified=%s"%(
                x[
                    "token"
                ][:10],

                x[
                    "cycles_observed"
                ],

                x[
                    "passes"
                ],

                x[
                    "pass_rate"
                ]*100.0,

                x[
                    "ending_pass_streak"
                ],

                x[
                    "drop_count"
                ],

                x[
                    "reentry_count"
                ],

                (
                    "%.2f"
                    %x[
                        "bps_min"
                    ]
                    if x[
                        "bps_min"
                    ] is not None
                    else "NA"
                ),

                (
                    "%.2f"
                    %x[
                        "bps_mean"
                    ]
                    if x[
                        "bps_mean"
                    ] is not None
                    else "NA"
                ),

                (
                    "%.2f"
                    %x[
                        "bps_max"
                    ]
                    if x[
                        "bps_max"
                    ] is not None
                    else "NA"
                ),

                x[
                    "transaction_size_stable"
                ],

                x[
                    "candidate_stable"
                ],

                x[
                    "preferred_reuse_rate"
                ]*100.0,

                x[
                    "certified_stable_shadow"
                ],
            ),
            flush=True
        )

    print(
        "[QARB-094] status=%s "
        "history_cycles=%d "
        "tokens=%d certified=%d"%(
            status,
            len(history),
            len(analyses),
            len(certified_rows),
        ),
        flush=True
    )

    print(
        "[CERTIFIED] %s"%(
            root/CERTIFIED
        ),
        flush=True
    )

    print(
        "[MODE] evidence_certification_only "
        "private_key_required=FALSE "
        "execution_authority=FALSE "
        "real_money_moved=FALSE",
        flush=True
    )

    return (
        0
        if status=="PASS"
        else 2
    )


def main():
    return run(
        Path.cwd()
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
'''

tests=r'''import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_094_execution_shadow_stability_certification as q


class T(unittest.TestCase):

    def active(self,bps=100,bytes_=1158):
        return {
            "status":
                "CURRENT_EXECUTION_SHADOW_PASS",

            "active":{
                "fresh_net_bps":
                    bps,

                "fresh_net_lamports":
                    1000,

                "candidate":
                    "C",

                "transaction_bytes":
                    bytes_,

                "size_sol":
                    1.4,

                "sim_err":
                    None,

                "pump_pool":
                    "P",

                "meteora_meta":{
                    "address":"M"
                },
            },

            "simulation":{
                "preferred_reused":
                    True
            },
        }


    def cycle(self,n,result):
        return {
            "cycle":n,
            "results":{
                "T":result
            }
        }


    def test_three_clean_cycles_certify(self):
        h=[
            self.cycle(1,self.active(100)),
            self.cycle(2,self.active(120)),
            self.cycle(3,self.active(110)),
        ]

        x=q.analyze_token(
            "T",
            h
        )

        self.assertTrue(
            x[
                "certified_stable_shadow"
            ]
        )


    def test_partial_cycle_not_certified(self):
        h=[
            self.cycle(1,self.active()),
            self.cycle(
                2,
                {
                    "status":
                        "CURRENTLY_INACTIVE",
                    "revalidation":{
                        "reason":
                            "DLMM_PARTIAL"
                    },
                }
            ),
            self.cycle(3,self.active()),
        ]

        x=q.analyze_token(
            "T",
            h
        )

        self.assertFalse(
            x[
                "certified_stable_shadow"
            ]
        )


    def test_reentry_count(self):
        obs=[
            {"active":True},
            {"active":False},
            {"active":True},
        ]

        x=q.transitions(obs)

        self.assertEqual(
            x[
                "drop_count"
            ],
            1
        )

        self.assertEqual(
            x[
                "reentry_count"
            ],
            1
        )


    def test_candidate_instability_blocks(self):
        h=[
            self.cycle(1,self.active()),
            self.cycle(2,self.active()),
            self.cycle(3,self.active()),
        ]

        h[2][
            "results"
        ][
            "T"
        ][
            "active"
        ][
            "candidate"
        ]="OTHER"

        x=q.analyze_token(
            "T",
            h
        )

        self.assertFalse(
            x[
                "certified_stable_shadow"
            ]
        )


    def test_tx_size_instability_blocks(self):
        h=[
            self.cycle(1,self.active(bytes_=1158)),
            self.cycle(2,self.active(bytes_=1190)),
            self.cycle(3,self.active(bytes_=1158)),
        ]

        x=q.analyze_token(
            "T",
            h
        )

        self.assertFalse(
            x[
                "certified_stable_shadow"
            ]
        )


    def test_exact_093_history(self):
        self.assertTrue(
            str(
                q.q93.HISTORY
            ).endswith(
                "qarb_093_execution_shadow_history.jsonl"
            )
        )


    def test_min_cycles(self):
        self.assertEqual(
            q.MIN_CYCLES,
            3
        )


    def test_full_pass_required(self):
        self.assertEqual(
            q.MIN_PASS_RATE,
            1.0
        )


    def test_no_rpc(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "c.rpc(",
            src
        )


    def test_no_private_key(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "QSB_SOLANA_PRIVATE_KEY",
            src
        )


    def test_no_broadcast(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "sendTransaction",
            src
        )

        self.assertNotIn(
            "c.send(",
            src
        )


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


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
'''

launcher=r'''from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering.qarb_094_execution_shadow_stability_certification import main

if __name__=="__main__":
    raise SystemExit(main())
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

for p in (M,T,U):
    py_compile.compile(
        str(p),
        doraise=True
    )

print(
    "[PASS] QARB-094 execution-shadow stability certification installed"
)
print(
    "[SOURCE] frozen QARB-093 JSONL history only"
)
print(
    "[MEASURE] pass streak/drop/reentry/bps/candidate/transaction stability"
)
print(
    "[CERTIFY] >=3 cycles + 100% pass + positive bps + stable candidate/size/tx"
)
print(
    "[RPC] none"
)
print(
    "[MODE] evidence_certification_only execution_authority=FALSE real_money_moved=FALSE"
)