
from pathlib import Path
from contextlib import contextmanager
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
import uuid

VERSION="ORACLE_037_GUARDED_MRIYA_WARM_CUTOVER"
PKG=Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST=PKG/"oracle_037_mriya_warm_cutover.py"
REPORT=Path("runtime_state/oracle/oracle_live_execution/ORACLE_037_CUTOVER.json")

RPC_LIMIT=120
PAIR_LIMIT=8
CANARY=10_000_000

SAFE={
    "PATH","PATHEXT","SYSTEMROOT","WINDIR","SYSTEMDRIVE",
    "TEMP","TMP","COMSPEC","SOLANA_RPC_URL",
    "QSB_SOLANA_RPC_URL","SOLANA_WS_URL"
}

def clean_environment(env):
    return {
        key:value for key,value in env.items()
        if key.upper() in SAFE
    }

class RequestGuard:
    def __init__(self,original,limit=RPC_LIMIT):
        self.original=original
        self.limit=limit
        self.calls=0
        self.methods={}
        self.exhausted=False

    def __call__(self,method,params):
        if method in (
            "simulateTransaction","sendTransaction",
            "requestAirdrop"
        ):
            raise RuntimeError("EXECUTION_RPC_FORBIDDEN")

        if self.calls>=self.limit:
            self.exhausted=True
            raise RuntimeError("RPC_BUDGET_EXHAUSTED")

        self.calls+=1
        self.methods[method]=self.methods.get(method,0)+1
        return self.original(method,params)

def save(root,result):
    path=root/REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",
        encoding="utf-8"
    )
    tmp.replace(path)

def select(worker_rows,inventory,limit=PAIR_LIMIT):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_036_live_worker_handoff as v36
    )
    selected,rejected=v36.admission(
        worker_rows,inventory,limit
    )
    return selected,rejected

@contextmanager
def scoped_intake(engine,selected):
    original=engine.candidate_universe
    engine.candidate_universe=lambda root:list(selected)
    try:
        yield
    finally:
        engine.candidate_universe=original

def perform(root,rid):
    result={
        "revision":VERSION,
        "run_id":rid,
        "status":"HOLD",
        "worker_generation":0,
        "worker_candidates":0,
        "selected_pairs":0,
        "hydrated_pairs":0,
        "rejections":{},
        "rpc_requests":0,
        "rpc_methods":{},
        "rpc_limit":RPC_LIMIT,
        "pair_limit":PAIR_LIMIT,
        "scanner_modified":False,
        "continuous_cutover":False,
        "signing":False,
        "broadcast":False,
        "simulations":0,
        "canary_lamports":CANARY
    }

    if any(
        "PRIVATE_KEY" in key.upper()
        or "SECRET_KEY" in key.upper()
        for key in os.environ
    ):
        result["status"]="HOLD_SECRET_ENVIRONMENT"
        save(root,result)
        return 2

    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine,live_account_stream as pd
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        mry_001_continuous_replenishment as mry,
        oracle_036_live_worker_handoff as v36,
        oracle_021_deterministic_pool_bootstrap as v21
    )

    original_rpc=core.rpc
    original_account=core.account
    original_pool=engine.exact_pool_ok
    original_pair_limit=pd.MAX_PAIRS

    original_engine_limits=(
        engine.MAX_TOKENS,
        engine.DISCOVERY_BUDGET,
        engine.CROSSLIST_TTL
    )
    original_cross_cache=dict(engine._cross_cache)
    original_hot_cache=dict(engine._hot_cache)

    guard=RequestGuard(original_rpc)
    worker=mry.ReplenishmentWorker(root)
    registered={}
    verified=set()

    def exact_identity(token,pool):
        try:
            good=v21.derived_pool(token,core)==pool
        except (ValueError,TypeError,KeyError):
            good=False
        if good:
            registered[pool]=token
        return good,("PDA_MATCH" if good else "PDA_MISMATCH")

    def verified_account(address):
        raw,owner=original_account(address)
        if address in registered:
            v21.attest(raw,owner,registered[address],core)
            verified.add(address)
        return raw,owner

    try:
        core.rpc=guard
        core.account=verified_account
        engine.exact_pool_ok=exact_identity

        # Exactly one Mriya worker discovery refresh.
        worker.refresh()
        generation,rows=v36.worker_snapshot(worker)

        result["worker_generation"]=generation
        result["worker_candidates"]=len(rows)
        result["mriya_hot_count"]=sum(
            x.get("source")=="MRIYA_HOT" for x in rows
        )

        # Existing metadata supplies identities, not prices.
        inventory=v36.inventory_rows(root)
        selected,rejected=select(rows,inventory)

        result["inventory_rows"]=len(inventory)
        result["selected_pairs"]=len(selected)
        result["rejections"]=rejected
        result["selected_tokens"]=[
            x["token"] for x in selected
        ]

        if not selected:
            result["status"]="HOLD_NO_MATCHED_WARM_PAIRS"
            return 0

        pd.MAX_PAIRS=PAIR_LIMIT

        # Existing production hydration receives Mriya-selected
        # identities, then fetches fresh on-chain account state.
        with scoped_intake(engine,selected):
            pairs,landing=pd.prepare_pairs(root)

        result["hydrated_pairs"]=len(pairs)
        result["verified_pump_pools"]=len(verified)
        result["landing_lamports"]=int(landing)
        result["hydrated_tokens"]=[
            str(x.token) for x in pairs
        ]

        if len(verified)!=len(pairs):
            result["status"]="HOLD_POOL_ATTESTATION_INCOMPLETE"
        elif not pairs:
            result["status"]="HOLD_NO_HYDRATED_PAIRS"
        else:
            result["status"]="MRIYA_TO_WARM_INTAKE_PHYSICALLY_VERIFIED"

        return 0

    except Exception as exc:
        result["status"]="HOLD_"+type(exc).__name__
        result["hold_reason"]=str(exc).split(":")[0][:100]
        return 2

    finally:
        worker.close()

        core.rpc=original_rpc
        core.account=original_account
        engine.exact_pool_ok=original_pool
        pd.MAX_PAIRS=original_pair_limit

        (
            engine.MAX_TOKENS,
            engine.DISCOVERY_BUDGET,
            engine.CROSSLIST_TTL
        )=original_engine_limits

        engine._cross_cache.clear()
        engine._cross_cache.update(original_cross_cache)
        engine._hot_cache.clear()
        engine._hot_cache.update(original_hot_cache)

        result["rpc_requests"]=guard.calls
        result["rpc_methods"]=guard.methods
        result["rpc_budget_exhausted"]=guard.exhausted

        if guard.exhausted:
            result["status"]="HOLD_RPC_BUDGET_EXHAUSTED"

        save(root,result)

def parent(root):
    rid=str(uuid.uuid4())
    cmd=[
        sys.executable,"-I",str(Path(__file__).resolve()),
        "--child","--run-id",rid
    ]
    result=subprocess.run(
        cmd,cwd=root,env=clean_environment(os.environ),
        capture_output=True,text=True,timeout=180
    )

    path=root/REPORT
    if not path.is_file():
        print("[HOLD] NO_REPORT")
        return 2

    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("run_id")!=rid:
        print("[HOLD] STALE_REPORT")
        return 2

    for key in (
        "status","worker_generation","worker_candidates",
        "mriya_hot_count","inventory_rows","selected_pairs",
        "hydrated_pairs","verified_pump_pools","rejections",
        "rpc_requests","rpc_methods","rpc_budget_exhausted",
        "hold_reason"
    ):
        if key in data:
            print(
                "["+key.upper()+"]",
                json.dumps(data[key],sort_keys=True)
            )

    print("[SCANNER] FROZEN")
    print("[SIMULATIONS] 0")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    print("[REPORT]",path)
    return result.returncode

class Tests(unittest.TestCase):
    def test_rpc_limit(self):
        calls=[]
        guard=RequestGuard(
            lambda m,p:calls.append(m),limit=2
        )
        guard("getAccountInfo",[])
        guard("getSlot",[])
        with self.assertRaises(RuntimeError):
            guard("getAccountInfo",[])
        self.assertEqual(len(calls),2)

    def test_execution_rpc_refused(self):
        guard=RequestGuard(lambda m,p:None)
        for method in (
            "simulateTransaction","sendTransaction"
        ):
            with self.assertRaises(RuntimeError):
                guard(method,[])
        self.assertEqual(guard.calls,0)

    def test_environment_scrub(self):
        result=clean_environment({
            "PATH":"present",
            "QSB_SOLANA_PRIVATE_KEY":"secret"
        })
        self.assertEqual(result,{"PATH":"present"})

    def test_scoped_restoration(self):
        class Fake:
            candidate_universe=lambda self,root:["old"]
        fake=Fake()
        old=fake.candidate_universe
        with scoped_intake(fake,[{"token":"test"}]):
            self.assertEqual(
                fake.candidate_universe(Path("."))[0]["token"],
                "test"
            )
        self.assertEqual(
            fake.candidate_universe(Path(".")),["old"]
        )
        self.assertEqual(fake.candidate_universe,old)

    def test_actual_worker_contract(self):
        from qseries_v2.oracle_execution.solana_atomic_executor import (
            mry_001_continuous_replenishment as mry
        )
        worker=mry.ReplenishmentWorker(Path.cwd())
        self.assertEqual(worker.latest(),(0,[]))

    def test_pair_limit(self):
        self.assertEqual(PAIR_LIMIT,8)

    def test_canary(self):
        self.assertEqual(CANARY,10_000_000)

    def test_no_signing_api(self):
        import inspect
        src=inspect.getsource(perform)
        self.assertNotIn("sendTransaction",src)
        self.assertNotIn("signed_tx(",src)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--run",action="store_true")
    p.add_argument("--child",action="store_true")
    p.add_argument("--run-id",default="")
    args=p.parse_args()
    root=Path.cwd()

    if args.test:
        tests=unittest.TextTestRunner(
            verbosity=2
        ).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if tests.wasSuccessful() else 1

    if args.child:
        return perform(root,args.run_id)

    if args.run:
        return parent(root)

    target=root/DEST
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2

    if target.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__),target)

    print("[PASS]",VERSION)
    print("[MODE] ONE_MRIYA_REFRESH_TO_EXISTING_WARM_INTAKE")
    print("[RPC_LIMIT]",RPC_LIMIT)
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
