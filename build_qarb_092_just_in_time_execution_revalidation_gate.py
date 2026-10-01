from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering"

Q87=S/"qarb_087_two_second_compaction_liquidity_repair.py"
Q90=S/"qarb_090_current_executable_liquidity_intake_gate.py"
Q91=S/"qarb_091_current_execution_simulation_envelope.py"

M=S/"qarb_092_just_in_time_execution_revalidation_gate.py"
T=R/"test_qarb_092_just_in_time_execution_revalidation_gate.py"
U=R/"run_qarb_092_just_in_time_execution_revalidation_gate.py"

for p in (Q87,Q90,Q91):
    if not p.is_file():
        raise SystemExit("[FAIL] dependency missing: "+str(p))

s87=Q87.read_text(encoding="utf-8")
s90=Q90.read_text(encoding="utf-8")
s91=Q91.read_text(encoding="utf-8")

guards=[
    ("087 compose","def compose(" in s87),
    ("087 repaired candidates","def repaired_candidates(" in s87),
    ("087 simulator","def simulate_candidate(" in s87),
    ("090 bindings","qarb_090_current_executable_liquidity_bindings.json" in s90),
    ("091 intake_rows","def intake_rows(" in s91),
    ("091 hydration_bindings","def hydration_bindings(" in s91),
]

bad=[name for name,ok in guards if not ok]

if bad:
    raise SystemExit(
        "[FAIL] current certified source contract changed: "
        +repr(bad)
    )

module=r'''from __future__ import annotations

import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_091_current_execution_simulation_envelope as q91


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_092_just_in_time_execution_revalidation_gate.json"
)

BINDINGS=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_092_current_revalidated_execution_bindings.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
MAX_TX_BYTES=1232


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


def revalidate_route(
    user,
    pair,
    row
):
    size=float(
        row["size_sol"]
    )

    try:
        route=q87.compose(
            user,
            pair,
            size
        )

    except RuntimeError as exc:
        if str(exc)=="DLMM_PARTIAL":
            return {
                "ok":False,
                "reason":"DLMM_PARTIAL",
                "size_sol":size,
            }

        return {
            "ok":False,
            "reason":
                "COMPOSE_ERROR:"
                +str(exc),
            "size_sol":size,
        }

    except Exception as exc:
        return {
            "ok":False,
            "reason":
                "COMPOSE_EXCEPTION:"
                +type(exc).__name__
                +":"
                +str(exc),
            "size_sol":size,
        }

    net=int(
        route[
            "pre_sim_net_lamports"
        ]
    )

    bps=float(
        route[
            "pre_sim_bps"
        ]
    )

    if net<=0:
        return {
            "ok":False,
            "reason":"CURRENT_NET_NONPOSITIVE",
            "size_sol":size,
            "current_net_lamports":net,
            "current_bps":bps,
        }

    if bps<q87.las.q59.MIN_NET_BPS:
        return {
            "ok":False,
            "reason":"CURRENT_BPS_BELOW_GATE",
            "size_sol":size,
            "current_net_lamports":net,
            "current_bps":bps,
        }

    return {
        "ok":True,
        "reason":"CURRENT_ROUTE_VALID",
        "size_sol":size,
        "current_net_lamports":net,
        "current_bps":bps,
        "route":route,
    }


def candidate_score(row):
    return (
        0 if (
            row.get("compiled")
            and "sim_err" in row
            and row.get("sim_err") is None
        ) else 1,

        0 if row.get("compiled") else 1,

        int(
            row.get(
                "bytes",
                10**9
            )
        ),
    )


def compile_and_simulate(
    user,
    route,
    extra_alts
):
    bh=c.rpc(
        "getLatestBlockhash",
        [{
            "commitment":"processed"
        }]
    )[
        "value"
    ][
        "blockhash"
    ]

    options=q87.alt_sets(
        route["base_alts"],
        extra_alts
    )

    attempts=[]

    for candidate in q87.repaired_candidates(
        route
    ):
        row=q87.simulate_candidate(
            user,
            None,
            route,
            candidate,
            options,
            bh
        )

        row["diagnostic"]=(
            q87.diagnostic(row)
        )

        attempts.append(row)

    ranked=sorted(
        attempts,
        key=candidate_score
    )

    winner=next(
        (
            x
            for x in ranked
            if (
                x.get("compiled")
                and "sim_err" in x
                and x.get("sim_err") is None
                and int(
                    x.get(
                        "bytes",
                        MAX_TX_BYTES+1
                    )
                )<=MAX_TX_BYTES
            )
        ),
        None
    )

    if winner is None:
        return {
            "ok":False,
            "reason":"NO_CLEAN_UNSIGNED_SIMULATION",
            "attempts":attempts,
        }

    return {
        "ok":True,
        "reason":"UNSIGNED_SIMULATION_PASS",
        "selected_candidate":
            winner["name"],
        "selected_bytes":
            int(
                winner["bytes"]
            ),
        "selected_alt_count":
            int(
                winner.get(
                    "alt_count",
                    0
                )
            ),
        "sim_err":
            winner.get(
                "sim_err"
            ),
        "sim_units":
            winner.get(
                "sim_units"
            ),
        "attempts":
            attempts,
    }


def run(root=None):
    root=Path(
        root or Path.cwd()
    )

    print(
        "[QARB-092] JUST-IN-TIME "
        "EXECUTION REVALIDATION GATE",
        flush=True
    )

    print(
        "[SOURCE] QARB-090 admitted rows",
        flush=True
    )

    print(
        "[RULE] fresh compose must still be "
        "complete and positive before compile",
        flush=True
    )

    print(
        "[SIM] unsigned sigVerify=False "
        "private_key_required=FALSE",
        flush=True
    )

    try:
        rows=q91.intake_rows(
            root
        )

    except RuntimeError as exc:
        print(
            "[QARB-092 HOLD] %s"%(
                exc
            ),
            flush=True
        )
        return 2

    valid=[]

    for row in rows:
        ok,reason=q91.validate_intake_row(
            row
        )

        if ok:
            valid.append(row)
        else:
            print(
                "[JIT_INTAKE_REJECT] "
                "token=%s reason=%s"%(
                    str(
                        row.get(
                            "token",
                            ""
                        )
                    )[:10],
                    reason
                ),
                flush=True
            )

    if not valid:
        print(
            "[QARB-092 HOLD] "
            "no valid QARB-090 rows",
            flush=True
        )
        return 2

    bindings=q91.hydration_bindings(
        valid
    )

    try:
        pairs,_=q87.q86.hydrate(
            root,
            bindings
        )

    except Exception as exc:
        print(
            "[QARB-092 HOLD] "
            "HYDRATION_ERROR:%s:%s"%(
                type(exc).__name__,
                exc
            ),
            flush=True
        )
        return 2

    pair_map={
        p.token:p
        for p in pairs
    }

    _,user=c.sim_identity()

    try:
        extra_alts=(
            q87.las.q59.recent_mriya_alt_keys()
        )
    except Exception:
        extra_alts=[]

    results={}
    admitted=[]
    rejected=[]

    for row in valid:
        token=row["token"]

        result={
            "token":token,
            "size_sol":
                float(
                    row["size_sol"]
                ),
            "qarb_090_net_lamports":
                int(
                    row[
                        "physical_net_lamports"
                    ]
                ),
            "qarb_090_bps":
                float(
                    row[
                        "physical_net_bps"
                    ]
                ),
            "pump_pool":
                row["pump_pool"],
            "meteora_pool":
                row[
                    "meteora_meta"
                ][
                    "address"
                ],
        }

        results[token]=result

        pair=pair_map.get(
            token
        )

        if pair is None:
            result["status"]="PAIR_MISSING"

            rejected.append({
                "token":token,
                "reason":"PAIR_MISSING",
            })

            continue

        fresh=revalidate_route(
            user,
            pair,
            row
        )

        result[
            "fresh_revalidation"
        ]={
            k:v
            for k,v in fresh.items()
            if k!="route"
        }

        if not fresh["ok"]:
            result["status"]="JIT_REJECTED"

            rejected.append({
                "token":token,
                "reason":
                    fresh["reason"],
            })

            print(
                "[2S_JIT_REJECT] "
                "token=%s size=%.6f "
                "reason=%s"%(
                    token[:10],
                    float(
                        row["size_sol"]
                    ),
                    fresh["reason"],
                ),
                flush=True
            )

            continue

        sim=compile_and_simulate(
            user,
            fresh["route"],
            extra_alts
        )

        result[
            "simulation"
        ]=sim

        if not sim["ok"]:
            result["status"]="JIT_SIM_REJECTED"

            rejected.append({
                "token":token,
                "reason":
                    sim["reason"],
            })

            print(
                "[2S_JIT_SIM_REJECT] "
                "token=%s reason=%s"%(
                    token[:10],
                    sim["reason"],
                ),
                flush=True
            )

            continue

        result["status"]="JIT_EXECUTION_SHADOW_PASS"

        admitted_row={
            "token":
                token,

            "pump_pool":
                row["pump_pool"],

            "meteora_meta":
                row["meteora_meta"],

            "size_sol":
                float(
                    row["size_sol"]
                ),

            "fresh_net_lamports":
                int(
                    fresh[
                        "current_net_lamports"
                    ]
                ),

            "fresh_net_bps":
                float(
                    fresh[
                        "current_bps"
                    ]
                ),

            "candidate":
                sim[
                    "selected_candidate"
                ],

            "transaction_bytes":
                int(
                    sim[
                        "selected_bytes"
                    ]
                ),

            "sim_err":
                sim[
                    "sim_err"
                ],

            "execution_authority":
                False,

            "paper_only":
                True,
        }

        admitted.append(
            admitted_row
        )

        print(
            "[2S_JIT_PASS] "
            "token=%s size=%.6f "
            "fresh_bps=%+.2f "
            "candidate=%s bytes=%d "
            "sim_err=%s"%(
                token[:10],

                admitted_row[
                    "size_sol"
                ],

                admitted_row[
                    "fresh_net_bps"
                ],

                admitted_row[
                    "candidate"
                ],

                admitted_row[
                    "transaction_bytes"
                ],

                admitted_row[
                    "sim_err"
                ],
            ),
            flush=True
        )

    status=(
        "PASS"
        if admitted
        else "HOLD"
    )

    binding_payload={
        "revision":
            "QARB_092",

        "status":
            status,

        "rows":
            admitted,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "private_key_required":
            False,

        "created_unix":
            time.time(),
    }

    report={
        "revision":
            "QARB_092",

        "status":
            status,

        "input_rows":
            len(rows),

        "validated_rows":
            len(valid),

        "jit_admitted":
            len(admitted),

        "jit_rejected":
            len(rejected),

        "rejections":
            rejected,

        "results":
            results,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "private_key_required":
            False,

        "created_unix":
            time.time(),
    }

    _save(
        root/BINDINGS,
        binding_payload
    )

    _save(
        root/STATE,
        report
    )

    print(
        "[QARB-092] status=%s "
        "input=%d valid=%d "
        "jit_admitted=%d "
        "jit_rejected=%d"%(
            status,
            len(rows),
            len(valid),
            len(admitted),
            len(rejected),
        ),
        flush=True
    )

    print(
        "[BINDINGS] %s"%(
            root/BINDINGS
        ),
        flush=True
    )

    print(
        "[MODE] jit_unsigned_shadow_only "
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

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_092_just_in_time_execution_revalidation_gate as q


class T(unittest.TestCase):

    def test_candidate_score_clean_first(self):
        good={
            "compiled":True,
            "sim_err":None,
            "bytes":1200,
        }

        bad={
            "compiled":True,
            "sim_err":{"x":1},
            "bytes":1100,
        }

        self.assertLess(
            q.candidate_score(good),
            q.candidate_score(bad)
        )


    def test_candidate_score_smaller_clean(self):
        a={
            "compiled":True,
            "sim_err":None,
            "bytes":1190,
        }

        b={
            "compiled":True,
            "sim_err":None,
            "bytes":1229,
        }

        self.assertLess(
            q.candidate_score(a),
            q.candidate_score(b)
        )


    def test_max_tx_bytes(self):
        self.assertEqual(
            q.MAX_TX_BYTES,
            1232
        )


    def test_exact_087_compose(self):
        self.assertTrue(
            callable(
                q.q87.compose
            )
        )


    def test_exact_087_simulator(self):
        self.assertTrue(
            callable(
                q.q87.simulate_candidate
            )
        )


    def test_exact_091_intake(self):
        self.assertTrue(
            callable(
                q.q91.intake_rows
            )
        )


    def test_exact_091_validation(self):
        self.assertTrue(
            callable(
                q.q91.validate_intake_row
            )
        )


    def test_exact_086_hydration(self):
        self.assertTrue(
            callable(
                q.q87.q86.hydrate
            )
        )


    def test_no_private_key_requirement(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "require_local_identity",
            src
        )

        self.assertIn(
            "None,",
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

launcher=r'''from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering.qarb_092_just_in_time_execution_revalidation_gate import main

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
    "[PASS] QARB-092 just-in-time execution revalidation gate installed"
)
print(
    "[SOURCE] QARB-090 admitted rows + frozen QARB-087 transaction path"
)
print(
    "[JIT] route revalidated immediately before compile/simulate"
)
print(
    "[DROP] DLMM_PARTIAL/nonpositive routes rejected without poisoning execution set"
)
print(
    "[SIM] unsigned sigVerify=False; private key not required"
)
print(
    "[MODE] jit_unsigned_shadow_only execution_authority=FALSE real_money_moved=FALSE"
)