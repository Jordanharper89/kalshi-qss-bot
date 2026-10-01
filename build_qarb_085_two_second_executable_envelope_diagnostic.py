from pathlib import Path
import py_compile

R=Path.cwd()

S=(
    R/
    "qseries_v2/oracle_strategy_intelligence/solana_money/"
    "qarb_execution_engineering"
)

Q76=S/"qarb_076_active_execution_binding_materializer.py"
Q77=S/"qarb_077_active_atomic_candidate_composition.py"

LAS=(
    R/
    "qseries_v2/oracle_strategy_intelligence/solana_money/"
    "qarb_clean_bot/live_atomic_simulation.py"
)

Q59=(
    R/
    "qseries_v2/oracle_strategy_intelligence/solana_money/"
    "qsb059_gav_reverse_atomic.py"
)

CORE=(
    R/
    "qseries_v2/oracle_strategy_intelligence/solana_money/"
    "native_atomic_money_machine/core.py"
)

M=S/"qarb_085_two_second_executable_envelope_diagnostic.py"
T=R/"test_qarb_085_two_second_executable_envelope_diagnostic.py"
U=R/"run_qarb_085_two_second_executable_envelope_diagnostic.py"

for p in (Q76,Q77,LAS,Q59,CORE):
    if not p.is_file():
        raise SystemExit(
            "[FAIL] dependency missing: "+str(p)
        )

s76=Q76.read_text(encoding="utf-8")
s77=Q77.read_text(encoding="utf-8")
slas=LAS.read_text(encoding="utf-8")
s59=Q59.read_text(encoding="utf-8")
score=CORE.read_text(encoding="utf-8")

guards=[
    ("076 materialize","def materialize(root):" in s76),
    ("076 bound","\"bound\":p is not None" in s76),
    ("077 exact pair","pm={(p.token,p.pump_pool,p.meteora_pool):p for p in pairs}" in s77),
    ("LAS compose","def compose_bound(user,pair,start_sol):" in slas),
    ("LAS q59","q59.attempt_candidate_simulations" in slas),
    ("q59 candidate ladder","def candidate_instruction_sets(" in s59),
    ("q59 simulation","def attempt_candidate_simulations(" in s59),
    ("q59 compile","c.compile_v0(" in s59),
    ("core simulate","def simulate(raw,user,sigverify=True):" in score),
]

bad=[name for name,ok in guards if not ok]

if bad:
    raise SystemExit(
        "[FAIL] exact current execution contract changed: "
        +repr(bad)
    )

module=r'''from __future__ import annotations

import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_atomic_simulation as las
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038b_nonrecursive_mriya_hotset_runtime as hot
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_076_active_execution_binding_materializer as q76


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_085_two_second_executable_envelope.json"
)

TARGET_HORIZON="2"
MIN_2S_SAMPLES=3
MIN_2S_WIN_RATE=0.80
MIN_2S_PNL_SOL=0.0

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


def _horizon(row,target="2"):
    for k,v in row.get(
        "horizons",
        {}
    ).items():

        try:
            normalized=str(
                int(
                    float(k)
                )
            )
        except Exception:
            normalized=str(k)

        if normalized==target:
            return dict(v)

    return {}


def two_second_evidence(row):
    h=_horizon(
        row,
        TARGET_HORIZON
    )

    n=int(
        h.get(
            "samples",
            0
        )
    )

    wins=int(
        h.get(
            "wins",
            0
        )
    )

    pnl=float(
        h.get(
            "pnl_sol",
            0.0
        )
    )

    wr=(
        wins/n
        if n
        else 0.0
    )

    admitted=(
        n>=MIN_2S_SAMPLES
        and wr>=MIN_2S_WIN_RATE
        and pnl>MIN_2S_PNL_SOL
    )

    reasons=[]

    if n<MIN_2S_SAMPLES:
        reasons.append(
            "INSUFFICIENT_2S_SAMPLES"
        )

    if wr<MIN_2S_WIN_RATE:
        reasons.append(
            "2S_WIN_RATE_BELOW_GATE"
        )

    if pnl<=MIN_2S_PNL_SOL:
        reasons.append(
            "2S_PNL_NOT_POSITIVE"
        )

    return {
        "samples":n,
        "wins":wins,
        "win_rate":wr,
        "pnl_sol":pnl,
        "admitted":admitted,
        "hold_reasons":reasons,
    }


def attempt_reason(row):
    if row.get(
        "profitable"
    ):
        return "PROFITABLE_SIMULATION"

    if not row.get(
        "compiled",
        False
    ):
        return (
            "COMPILE_FAIL:"
            +str(
                row.get(
                    "error"
                )
            )
        )

    if row.get(
        "sim_err"
    ) is not None:
        return (
            "SIM_ERROR:"
            +str(
                row.get(
                    "sim_err"
                )
            )
        )

    pnl=row.get(
        "sim_pnl_lamports"
    )

    if pnl is None:
        return "SIM_PNL_UNAVAILABLE"

    if int(pnl)<=0:
        return "SIM_PNL_NONPOSITIVE"

    bps=row.get(
        "sim_bps"
    )

    if bps is None:
        return "SIM_BPS_UNAVAILABLE"

    if float(bps)<float(
        las.q59.MIN_NET_BPS
    ):
        return "SIM_BPS_BELOW_GATE"

    return "UNCLASSIFIED_REJECT"


def audit(root):
    root=Path(root)

    learned=q70._load(
        root
    ).get(
        "tokens",
        {}
    )

    bindings=q76.materialize(
        root
    )

    pairs,_=hot.priority_prepare_pairs(
        root
    )

    pair_map={
        (
            p.token,
            p.pump_pool,
            p.meteora_pool
        ):p
        for p in pairs
    }

    kp,user=c.sim_identity()

    rows={}
    admitted=0
    composed=0
    profitable=0

    for token,binding in sorted(
        bindings.get(
            "bindings",
            {}
        ).items()
    ):
        evidence=two_second_evidence(
            learned.get(
                token,
                {}
            )
        )

        row={
            "token":token,
            "size_sol":
                float(
                    binding.get(
                        "size_sol",
                        0.0
                    )
                ),
            "pump_pool":
                binding.get(
                    "pump_pool"
                ),
            "meteora_pool":
                binding.get(
                    "meteora_pool"
                ),
            "bound":
                bool(
                    binding.get(
                        "bound"
                    )
                ),
            "two_second":
                evidence,
            "execution_authority":
                False,
            "real_money_moved":
                False,
        }

        rows[token]=row

        if not evidence[
            "admitted"
        ]:
            row["status"]="RESEARCH_ONLY"
            continue

        if not binding.get(
            "bound"
        ):
            row["status"]="NO_CURRENT_BINDING"
            continue

        admitted+=1

        pair=pair_map.get(
            (
                token,
                binding.get(
                    "pump_pool"
                ),
                binding.get(
                    "meteora_pool"
                )
            )
        )

        if pair is None:
            row[
                "status"
            ]="CURRENT_EXACT_PAIR_NOT_FOUND"
            continue

        try:
            route=las.compose_bound(
                user,
                pair,
                float(
                    binding[
                        "size_sol"
                    ]
                )
            )

            composed+=1

            row[
                "pre_sim_net_sol"
            ]=(
                route[
                    "pre_sim_net_lamports"
                ]/1e9
            )

            row[
                "pre_sim_bps"
            ]=route[
                "pre_sim_bps"
            ]

            row[
                "candidate_count"
            ]=len(
                route.get(
                    "candidates",
                    []
                )
            )

            bh=c.rpc(
                "getLatestBlockhash",
                [
                    {
                        "commitment":
                            "processed"
                    }
                ]
            )[
                "value"
            ][
                "blockhash"
            ]

            winner,attempts=(
                las.q59.attempt_candidate_simulations(
                    user,
                    kp,
                    route,
                    bh
                )
            )

            analyzed=[]

            for x in attempts:
                z=dict(x)
                z[
                    "diagnostic"
                ]=attempt_reason(
                    z
                )
                analyzed.append(
                    z
                )

            row[
                "attempts"
            ]=analyzed

            row[
                "winner"
            ]=winner

            row[
                "profitable_simulation"
            ]=bool(
                winner
                and winner.get(
                    "profitable"
                )
            )

            if row[
                "profitable_simulation"
            ]:
                profitable+=1

                row[
                    "status"
                ]="EXECUTABLE_2S_SIM_PASS"

            else:
                row[
                    "status"
                ]="NO_PROFITABLE_SIMULATION"

        except Exception as exc:
            row[
                "status"
            ]="SIMULATION_EXCEPTION"

            row[
                "error"
            ]=(
                type(
                    exc
                ).__name__
                +":"
                +str(
                    exc
                )
            )

    out={
        "revision":
            "QARB_085",

        "target_horizon_seconds":
            2,

        "policy":{
            "min_samples":
                MIN_2S_SAMPLES,
            "min_win_rate":
                MIN_2S_WIN_RATE,
            "min_pnl_sol":
                MIN_2S_PNL_SOL,
            "route":
                "PUMPSWAP_TO_METEORA_DLMM",
        },

        "bound_tokens":
            len(
                bindings.get(
                    "bindings",
                    {}
                )
            ),

        "two_second_admitted":
            admitted,

        "atomic_composed":
            composed,

        "profitable_simulations":
            profitable,

        "rows":
            rows,

        "simulation_only":
            True,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "created_unix":
            time.time(),
    }

    _save(
        root,
        out
    )

    return out


def main():
    r=audit(
        Path.cwd()
    )

    print(
        "[QARB-085] 2-SECOND EXECUTABLE "
        "ENVELOPE DIAGNOSTIC"
    )

    print(
        "[POLICY] 2s samples>=%d "
        "win_rate>=%.0f%% pnl>0"%(
            MIN_2S_SAMPLES,
            MIN_2S_WIN_RATE*100
        )
    )

    print(
        "[COUNTS] bound=%d admitted_2s=%d "
        "composed=%d profitable_sim=%d"%(
            r[
                "bound_tokens"
            ],
            r[
                "two_second_admitted"
            ],
            r[
                "atomic_composed"
            ],
            r[
                "profitable_simulations"
            ]
        )
    )

    for token,x in r[
        "rows"
    ].items():

        h=x[
            "two_second"
        ]

        if not h[
            "admitted"
        ]:
            continue

        print(
            "[2S_CANDIDATE] token=%s "
            "n=%d wr=%.1f%% pnl=%+.9f "
            "size=%.6f status=%s"%(
                token[:10],
                h[
                    "samples"
                ],
                h[
                    "win_rate"
                ]*100.0,
                h[
                    "pnl_sol"
                ],
                x[
                    "size_sol"
                ],
                x.get(
                    "status"
                )
            )
        )

        for a in x.get(
            "attempts",
            []
        ):
            print(
                "[2S_SIM_ATTEMPT] token=%s "
                "candidate=%s bytes=%s "
                "sim_pnl=%s sim_bps=%s "
                "diagnostic=%s"%(
                    token[:10],
                    a.get(
                        "name"
                    ),
                    a.get(
                        "bytes"
                    ),
                    a.get(
                        "sim_pnl_lamports"
                    ),
                    a.get(
                        "sim_bps"
                    ),
                    a.get(
                        "diagnostic"
                    )
                )
            )

    status=(
        "PASS"
        if r[
            "profitable_simulations"
        ]>0
        else "HOLD"
    )

    print(
        "[2S_EXECUTABLE_ENVELOPE] "
        "status=%s profitable=%d"%(
            status,
            r[
                "profitable_simulations"
            ]
        )
    )

    print(
        "[MODE] simulation_only "
        "execution_authority=FALSE "
        "real_money_moved=FALSE"
    )

    return 0


if __name__=="__main__":
    raise SystemExit(
        main()
    )
'''

tests=r'''import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_085_two_second_executable_envelope_diagnostic as q


class T(unittest.TestCase):

    def test_2s_high_confidence_admits(self):
        r=q.two_second_evidence(
            {
                "horizons":{
                    "2.0":{
                        "samples":10,
                        "wins":9,
                        "pnl_sol":1.0
                    }
                }
            }
        )

        self.assertTrue(
            r["admitted"]
        )


    def test_2s_low_win_rate_rejects(self):
        r=q.two_second_evidence(
            {
                "horizons":{
                    "2":{
                        "samples":10,
                        "wins":7,
                        "pnl_sol":1.0
                    }
                }
            }
        )

        self.assertFalse(
            r["admitted"]
        )


    def test_2s_negative_pnl_rejects(self):
        r=q.two_second_evidence(
            {
                "horizons":{
                    "2":{
                        "samples":10,
                        "wins":9,
                        "pnl_sol":-0.1
                    }
                }
            }
        )

        self.assertFalse(
            r["admitted"]
        )


    def test_2s_sample_gate(self):
        r=q.two_second_evidence(
            {
                "horizons":{
                    "2":{
                        "samples":2,
                        "wins":2,
                        "pnl_sol":0.1
                    }
                }
            }
        )

        self.assertFalse(
            r["admitted"]
        )


    def test_compile_failure_reason(self):
        x=q.attempt_reason(
            {
                "compiled":False,
                "error":
                    "ATOMIC_TX_TOO_LARGE:1300"
            }
        )

        self.assertTrue(
            x.startswith(
                "COMPILE_FAIL:"
            )
        )


    def test_sim_error_reason(self):
        x=q.attempt_reason(
            {
                "compiled":True,
                "sim_err":{
                    "InstructionError":[
                        1,
                        "Custom"
                    ]
                },
                "sim_pnl_lamports":None,
            }
        )

        self.assertTrue(
            x.startswith(
                "SIM_ERROR:"
            )
        )


    def test_nonpositive_pnl_reason(self):
        x=q.attempt_reason(
            {
                "compiled":True,
                "sim_err":None,
                "sim_pnl_lamports":-1,
                "sim_bps":-1,
            }
        )

        self.assertEqual(
            x,
            "SIM_PNL_NONPOSITIVE"
        )


    def test_profitable_reason(self):
        x=q.attempt_reason(
            {
                "compiled":True,
                "sim_err":None,
                "sim_pnl_lamports":100,
                "sim_bps":100,
                "profitable":True,
            }
        )

        self.assertEqual(
            x,
            "PROFITABLE_SIMULATION"
        )


    def test_route_is_exact_existing_path(self):
        self.assertTrue(
            callable(
                q.las.compose_bound
            )
        )

        self.assertTrue(
            callable(
                q.las.q59.attempt_candidate_simulations
            )
        )


    def test_2s_policy(self):
        self.assertEqual(
            q.TARGET_HORIZON,
            "2"
        )

        self.assertEqual(
            q.MIN_2S_SAMPLES,
            3
        )

        self.assertEqual(
            q.MIN_2S_WIN_RATE,
            0.80
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

launcher=r'''from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering.qarb_085_two_second_executable_envelope_diagnostic import main

if __name__=="__main__":
    raise SystemExit(
        main()
    )
'''

S.mkdir(
    parents=True,
    exist_ok=True
)

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
    "[PASS] QARB-085 2-second executable-envelope diagnostic installed"
)

print(
    "[TARGET] 2s primary execution-candidate horizon"
)

print(
    "[RESEARCH] 5/15/30/60/90 unchanged and remain Oracle research"
)

print(
    "[ATOMIC] exact existing PumpSwap -> Meteora candidate ladder reused"
)

print(
    "[DIAGNOSTIC] compile/sim-error/pnl/bps rejection reasons captured"
)

print(
    "[MODE] simulation_only execution_authority=FALSE real_money_moved=FALSE"
)