from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering"

Q80=S/"qarb_080_single_runtime_dynamic_mriya_supervisor.py"
Q85=S/"qarb_085_two_second_executable_envelope_diagnostic.py"
Q47=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/qarb_047b_paced_dynamic_hotset_supervisor.py"
LAS=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/live_atomic_simulation.py"
Q59=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059_gav_reverse_atomic.py"

M=S/"qarb_086_two_second_dynamic_execution_binding_cutover.py"
T=R/"test_qarb_086_two_second_dynamic_execution_binding_cutover.py"
U=R/"run_qarb_086_two_second_dynamic_execution_binding_cutover.py"

for p in (Q80,Q85,Q47,LAS,Q59):
    if not p.is_file():
        raise SystemExit("[FAIL] dependency missing: "+str(p))

s80=Q80.read_text(encoding="utf-8")
s85=Q85.read_text(encoding="utf-8")
s47=Q47.read_text(encoding="utf-8")
slas=LAS.read_text(encoding="utf-8")
s59=Q59.read_text(encoding="utf-8")

guards=[
    ("080 memory","MEMORY=Path(" in s80),
    ("080 lifecycle","def lifecycle_sets(root):" in s80),
    ("080 hydration lock","def acquire_hydration_lock(" in s80),
    ("080 release lock","def release_hydration_lock(" in s80),
    ("080 rpc valve","q47.p.m.pd.c.rpc=rv.gated_rpc" in s80),
    ("047 binding universe","def binding_universe(path):" in s47),
    ("047 prepare","def prepare_from(path,root):" in s47),
    ("085 evidence","def two_second_evidence(row):" in s85),
    ("LAS compose","def compose_bound(user,pair,start_sol):" in slas),
    ("q59 sim","def attempt_candidate_simulations(" in s59),
]

bad=[x for x,ok in guards if not ok]
if bad:
    raise SystemExit("[FAIL] current source contract changed: "+repr(bad))

module=r'''from __future__ import annotations

import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_atomic_simulation as las
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_047b_paced_dynamic_hotset_supervisor as q47
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061a_shared_rpc_valve as rv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_076_active_execution_binding_materializer as q76
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_080_single_runtime_dynamic_mriya_supervisor as q80
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_085_two_second_executable_envelope_diagnostic as q85


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_086_two_second_dynamic_execution_binding_cutover.json"
)

BINDINGS=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_086_two_second_dynamic_bindings.json"
)

GENERATION_ID=86001

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


def _save(path,payload):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(
        json.dumps(payload,indent=2,sort_keys=True),
        encoding="utf-8"
    )
    tmp.replace(path)


def memory_candidates(root):
    root=Path(root)

    memory=q80._load(
        root/q80.MEMORY,
        {"rows":{}}
    ).get("rows",{})

    learned=q70._load(
        root
    ).get("tokens",{})

    sizes=q76._sizes(root)

    _,retired=q80.lifecycle_sets(root)

    rows=[]
    audit={}

    for token,row in sorted(learned.items()):
        evidence=q85.two_second_evidence(row)

        x={
            "token":token,
            "two_second":evidence,
            "memory_present":token in memory,
            "retired":token in retired,
        }

        audit[token]=x

        if not evidence["admitted"]:
            x["status"]="RESEARCH_ONLY"
            continue

        if token in retired:
            x["status"]="RETIRED"
            continue

        m=memory.get(token)

        if not m:
            x["status"]="NO_Q80_MEMORY"
            continue

        pump=m.get("pump_pool")
        meta=m.get("meteora_meta") or {}
        meteora=meta.get("address")

        if not pump or not meteora:
            x["status"]="INCOMPLETE_Q80_MEMORY"
            continue

        binding={
            "token":token,
            "pump_pool":pump,
            "meteora_meta":dict(meta),
            "lifecycle":dict(
                m.get("lifecycle") or {}
            ),
            "size_sol":float(
                sizes.get(token,0.05)
            ),
        }

        rows.append(binding)

        x.update({
            "status":"MEMORY_BOUND",
            "pump_pool":pump,
            "meteora_pool":meteora,
            "size_sol":binding["size_sol"],
        })

    return rows,audit


def hydrate(root,rows):
    root=Path(root)
    path=root/BINDINGS

    _save(
        path,
        {
            "revision":"QARB_086",
            "rows":rows,
            "execution_authority":False,
            "real_money_moved":False,
        }
    )

    # Reuse exact certified QARB-080 RPC pacing + hydration lock.
    q47.p.m.pd.c.rpc=rv.gated_rpc

    lock=q80.acquire_hydration_lock(
        root,
        GENERATION_ID
    )

    try:
        pairs,landing=q47.prepare_from(
            path,
            root
        )
    finally:
        q80.release_hydration_lock(lock)

    return pairs,landing


def classify_attempt(row):
    if row.get("profitable"):
        return "PROFITABLE_SIMULATION"

    if not row.get("compiled",False):
        return "COMPILE_FAIL:"+str(
            row.get("error")
        )

    if row.get("sim_err") is not None:
        return "SIM_ERROR:"+str(
            row.get("sim_err")
        )

    pnl=row.get("sim_pnl_lamports")

    if pnl is None:
        return "SIM_PNL_UNAVAILABLE"

    if int(pnl)<=0:
        return "SIM_PNL_NONPOSITIVE"

    bps=row.get("sim_bps")

    if bps is None:
        return "SIM_BPS_UNAVAILABLE"

    if float(bps)<float(
        las.q59.MIN_NET_BPS
    ):
        return "SIM_BPS_BELOW_GATE"

    return "UNCLASSIFIED_REJECT"


def run(root=None):
    root=Path(root or Path.cwd())

    bindings,audit=memory_candidates(root)

    print(
        "[QARB-086] 2-SECOND DYNAMIC EXECUTION BINDING CUTOVER",
        flush=True
    )

    print(
        "[SOURCE] QARB-080 durable binding memory -> QARB-047B exact hydration",
        flush=True
    )

    print(
        "[2S_BINDINGS] qualified_memory=%d"%len(bindings),
        flush=True
    )

    if not bindings:
        out={
            "revision":"QARB_086",
            "status":"HOLD",
            "reason":"NO_2S_MEMORY_BINDINGS",
            "bindings":audit,
            "execution_authority":False,
            "paper_only":True,
            "real_money_moved":False,
        }
        _save(root/STATE,out)
        print("[QARB-086 HOLD] no 2s memory bindings",flush=True)
        return 2

    try:
        pairs,landing=hydrate(
            root,
            bindings
        )
    except Exception as exc:
        out={
            "revision":"QARB_086",
            "status":"HOLD",
            "reason":"HYDRATION_EXCEPTION",
            "error":type(exc).__name__+":"+str(exc),
            "bindings":audit,
            "execution_authority":False,
            "paper_only":True,
            "real_money_moved":False,
        }
        _save(root/STATE,out)

        print(
            "[HYDRATION_HOLD] %s:%s"%(
                type(exc).__name__,
                exc
            ),
            flush=True
        )

        return 2

    print(
        "[HYDRATION] requested=%d hydrated=%d rpc_calls=%d caught_429=%d"%(
            len(bindings),
            len(pairs),
            rv.RPC_CALLS,
            rv.RPC_429
        ),
        flush=True
    )

    pair_map={
        p.token:p
        for p in pairs
    }

    kp,user=c.sim_identity()

    results={}
    profitable=0
    composed=0

    for binding in bindings:
        token=binding["token"]

        row={
            "token":token,
            "size_sol":binding["size_sol"],
            "pump_pool":binding["pump_pool"],
            "meteora_pool":
                binding["meteora_meta"]["address"],
            "hydrated":token in pair_map,
            "execution_authority":False,
            "real_money_moved":False,
        }

        results[token]=row

        pair=pair_map.get(token)

        if pair is None:
            row["status"]="HYDRATION_PAIR_MISSING"
            continue

        try:
            route=las.compose_bound(
                user,
                pair,
                float(binding["size_sol"])
            )

            composed+=1

            row["pre_sim_net_sol"]=(
                route["pre_sim_net_lamports"]/1e9
            )

            row["pre_sim_bps"]=route[
                "pre_sim_bps"
            ]

            row["candidate_count"]=len(
                route.get("candidates",[])
            )

            bh=c.rpc(
                "getLatestBlockhash",
                [{"commitment":"processed"}]
            )["value"]["blockhash"]

            winner,attempts=(
                las.q59.attempt_candidate_simulations(
                    user,
                    kp,
                    route,
                    bh
                )
            )

            analyzed=[]

            for attempt in attempts:
                a=dict(attempt)
                a["diagnostic"]=classify_attempt(a)
                analyzed.append(a)

            row["attempts"]=analyzed
            row["winner"]=winner
            row["profitable_simulation"]=bool(
                winner
                and winner.get("profitable")
            )

            if row["profitable_simulation"]:
                profitable+=1
                row["status"]="EXECUTABLE_2S_SIM_PASS"
            else:
                row["status"]="NO_PROFITABLE_SIMULATION"

        except Exception as exc:
            row["status"]="SIMULATION_EXCEPTION"
            row["error"]=(
                type(exc).__name__
                +":"
                +str(exc)
            )

    status=(
        "PASS"
        if profitable>0
        else "HOLD"
    )

    out={
        "revision":"QARB_086",
        "status":status,
        "binding_source":"QARB_080_MEMORY",
        "qualified_memory_bindings":len(bindings),
        "hydrated_pairs":len(pairs),
        "atomic_composed":composed,
        "profitable_simulations":profitable,
        "binding_audit":audit,
        "simulation_results":results,
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
        "created_unix":time.time(),
    }

    _save(root/STATE,out)

    for token,x in results.items():
        print(
            "[2S_EXEC_BINDING] token=%s size=%.6f hydrated=%s status=%s"%(
                token[:10],
                x["size_sol"],
                x["hydrated"],
                x["status"]
            ),
            flush=True
        )

        if x.get("error"):
            print(
                "[2S_EXEC_ERROR] token=%s %s"%(
                    token[:10],
                    x["error"]
                ),
                flush=True
            )

        for a in x.get("attempts",[]):
            print(
                "[2S_SIM_ATTEMPT] token=%s candidate=%s bytes=%s pnl=%s bps=%s diagnostic=%s"%(
                    token[:10],
                    a.get("name"),
                    a.get("bytes"),
                    a.get("sim_pnl_lamports"),
                    a.get("sim_bps"),
                    a.get("diagnostic")
                ),
                flush=True
            )

    print(
        "[2S_EXECUTABLE_ENVELOPE] status=%s qualified=%d hydrated=%d composed=%d profitable=%d"%(
            status,
            len(bindings),
            len(pairs),
            composed,
            profitable
        ),
        flush=True
    )

    print(
        "[MODE] simulation_only execution_authority=FALSE real_money_moved=FALSE",
        flush=True
    )

    return 0 if status=="PASS" else 2


def main():
    return run(Path.cwd())


if __name__=="__main__":
    raise SystemExit(main())
'''

tests=r'''import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_086_two_second_dynamic_execution_binding_cutover as q


class T(unittest.TestCase):

    def test_exact_memory_source(self):
        self.assertTrue(
            hasattr(q.q80,"MEMORY")
        )


    def test_exact_hydration_path(self):
        self.assertTrue(
            callable(q.q47.prepare_from)
        )


    def test_exact_hydration_lock(self):
        self.assertTrue(
            callable(q.q80.acquire_hydration_lock)
        )

        self.assertTrue(
            callable(q.q80.release_hydration_lock)
        )


    def test_rpc_valve_exists(self):
        self.assertTrue(
            callable(q.rv.gated_rpc)
        )


    def test_2s_policy_reused(self):
        self.assertEqual(
            q.q85.TARGET_HORIZON,
            "2"
        )

        self.assertEqual(
            q.q85.MIN_2S_WIN_RATE,
            0.80
        )


    def test_atomic_composer_reused(self):
        self.assertTrue(
            callable(q.las.compose_bound)
        )


    def test_candidate_simulator_reused(self):
        self.assertTrue(
            callable(
                q.las.q59.attempt_candidate_simulations
            )
        )


    def test_compile_failure_diagnostic(self):
        x=q.classify_attempt({
            "compiled":False,
            "error":"ATOMIC_TX_TOO_LARGE:1300"
        })

        self.assertTrue(
            x.startswith("COMPILE_FAIL:")
        )


    def test_sim_pnl_diagnostic(self):
        x=q.classify_attempt({
            "compiled":True,
            "sim_err":None,
            "sim_pnl_lamports":-100,
            "sim_bps":-1,
        })

        self.assertEqual(
            x,
            "SIM_PNL_NONPOSITIVE"
        )


    def test_profitable_diagnostic(self):
        x=q.classify_attempt({
            "compiled":True,
            "profitable":True,
            "sim_err":None,
            "sim_pnl_lamports":100,
            "sim_bps":100,
        })

        self.assertEqual(
            x,
            "PROFITABLE_SIMULATION"
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
    unittest.main(verbosity=2)
'''

launcher=r'''from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering.qarb_086_two_second_dynamic_execution_binding_cutover import main

if __name__=="__main__":
    raise SystemExit(main())
'''

S.mkdir(parents=True,exist_ok=True)

M.write_text(module,encoding="utf-8")
T.write_text(tests,encoding="utf-8")
U.write_text(launcher,encoding="utf-8")

for p in (M,T,U):
    py_compile.compile(
        str(p),
        doraise=True
    )

print(
    "[PASS] QARB-086 2-second dynamic execution binding cutover installed"
)
print(
    "[RETIRED] QARB-076 hotset-only binding intake from execution path"
)
print(
    "[SOURCE] QARB-080 durable binding memory"
)
print(
    "[HYDRATION] exact QARB-047B prepare_from + QARB-080 lock/RPC valve"
)
print(
    "[SIMULATION] exact existing atomic candidate ladder; no broadcast"
)
print(
    "[MODE] simulation_only execution_authority=FALSE real_money_moved=FALSE"
)