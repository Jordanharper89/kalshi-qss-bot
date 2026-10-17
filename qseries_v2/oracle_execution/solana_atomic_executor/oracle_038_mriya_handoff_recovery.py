
from pathlib import Path
import argparse, json, os, shutil, subprocess, sys, unittest, uuid

VERSION="ORACLE_038_MRIYA_HANDOFF_RECOVERY"
PKG=Path("qseries_v2/oracle_execution/solana_atomic_executor")
NAME="oracle_038_mriya_handoff_recovery.py"
REPORT=Path("runtime_state/oracle/oracle_live_execution/ORACLE_038_HANDOFF.json")
RPC_CAP=120
PAIR_CAP=8
CANARY=10_000_000

SAFE={
    "PATH","PATHEXT","SYSTEMROOT","WINDIR","SYSTEMDRIVE",
    "TEMP","TMP","COMSPEC","SOLANA_RPC_URL",
    "QSB_SOLANA_RPC_URL","SOLANA_WS_URL"
}

def clean_env(env):
    return {k:v for k,v in env.items() if k.upper() in SAFE}

def write(root,data):
    path=root/REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",
                    encoding="utf-8")
    temp.replace(path)

class Guard:
    def __init__(self,fn,limit=RPC_CAP):
        self.fn=fn
        self.limit=limit
        self.count=0
        self.methods={}
        self.exhausted=False

    def __call__(self,method,params):
        if method in (
            "sendTransaction","simulateTransaction",
            "requestAirdrop"
        ):
            raise RuntimeError("EXECUTION_RPC_DISABLED")
        if self.count>=self.limit:
            self.exhausted=True
            raise RuntimeError("RPC_BUDGET_EXHAUSTED")
        self.count+=1
        self.methods[method]=self.methods.get(method,0)+1
        return self.fn(method,params)

def child(root,run_id):
    result={
        "revision":VERSION,"run_id":run_id,"status":"HOLD",
        "stage":"BOOTSTRAP","worker_generation":0,
        "worker_candidates":0,"selected_pairs":0,
        "hydrated_pairs":0,"verified_pools":0,
        "rpc_requests":0,"rpc_methods":{},
        "rpc_cap":RPC_CAP,"pair_cap":PAIR_CAP,
        "simulations":0,"signing":False,
        "broadcast":False,"canary_lamports":CANARY,
        "scanner_modified":False,"continuous_cutover":False
    }
    originals=[]
    guard=None
    worker=None

    try:
        if any(
            "PRIVATE_KEY" in k.upper() or
            "SECRET_KEY" in k.upper()
            for k in os.environ
        ):
            raise RuntimeError("PRIVATE_KEY_ENVIRONMENT_BLOCKED")

        # Required when executed using Python -I.
        sys.path.insert(0,str(root.resolve()))

        result["stage"]="IMPORTS"
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
        from qseries_v2.oracle_execution.solana_atomic_executor import mry_001_continuous_replenishment as mry
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_036_live_worker_handoff as v36
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_021_deterministic_pool_bootstrap as v21

        guard=Guard(core.rpc)
        original_rpc=core.rpc
        original_account=core.account
        original_pool=engine.exact_pool_ok
        original_candidate=engine.candidate_universe
        original_max=pd.MAX_PAIRS
        original_limits=(
            engine.MAX_TOKENS,
            engine.DISCOVERY_BUDGET,
            engine.CROSSLIST_TTL
        )
        registered={}
        verified=set()

        def identity(token,pool):
            try:
                valid=v21.derived_pool(token,core)==pool
            except (ValueError,TypeError,KeyError):
                valid=False
            if valid:
                registered[pool]=token
            return valid,("PDA_MATCH" if valid else "PDA_MISMATCH")

        def account(address):
            raw,owner=original_account(address)
            if address in registered:
                v21.attest(raw,owner,registered[address],core)
                verified.add(address)
            return raw,owner

        def restore():
            core.rpc=original_rpc
            core.account=original_account
            engine.exact_pool_ok=original_pool
            engine.candidate_universe=original_candidate
            pd.MAX_PAIRS=original_max
            (
                engine.MAX_TOKENS,
                engine.DISCOVERY_BUDGET,
                engine.CROSSLIST_TTL
            )=original_limits

        originals.append(restore)
        core.rpc=guard
        core.account=account
        engine.exact_pool_ok=identity

        result["stage"]="MRIYA_REFRESH"
        worker=mry.ReplenishmentWorker(root)
        worker.refresh()
        generation,rows=v36.worker_snapshot(worker)
        result["worker_generation"]=generation
        result["worker_candidates"]=len(rows)
        result["mriya_hot_count"]=sum(
            row.get("source")=="MRIYA_HOT" for row in rows
        )

        result["stage"]="PAIR_ADMISSION"
        inventory=v36.inventory_rows(root)
        selected,rejected=v36.admission(rows,inventory,PAIR_CAP)
        result["inventory_rows"]=len(inventory)
        result["selected_pairs"]=len(selected)
        result["rejections"]=rejected
        result["selected_tokens"]=[x["token"] for x in selected]

        if not selected:
            result["status"]="HOLD_NO_EXACT_INVENTORY_MATCH"
            return 0

        result["stage"]="FRESH_ONCHAIN_HYDRATION"
        engine.candidate_universe=lambda path:list(selected)
        pd.MAX_PAIRS=PAIR_CAP

        pairs,landing=pd.prepare_pairs(root)
        result["hydrated_pairs"]=len(pairs)
        result["verified_pools"]=len(verified)
        result["hydrated_tokens"]=[str(p.token) for p in pairs]
        result["landing_lamports"]=int(landing)

        if not pairs:
            result["status"]="HOLD_NO_HYDRATED_PAIRS"
        elif len(verified)!=len(pairs):
            result["status"]="HOLD_POOL_ATTESTATION_INCOMPLETE"
        else:
            result["status"]="MRIYA_TO_EXECUTOR_WARM_INTAKE_VERIFIED"

        return 0

    except Exception as exc:
        result["status"]="HOLD_"+type(exc).__name__
        result["error_class"]=type(exc).__name__
        # Deliberately do not print exception text:
        # provider URLs can contain API credentials.
        return 2

    finally:
        if worker is not None:
            try:worker.close()
            except Exception:pass
        for restore in reversed(originals):
            try:restore()
            except Exception:
                result["status"]="HOLD_RESTORE_FAILED"
        if guard is not None:
            result["rpc_requests"]=guard.count
            result["rpc_methods"]=guard.methods
            result["rpc_exhausted"]=guard.exhausted
            if guard.exhausted:
                result["status"]="HOLD_RPC_BUDGET_EXHAUSTED"
        write(root,result)

def parent(root):
    run_id=str(uuid.uuid4())
    cmd=[
        sys.executable,"-I",str(Path(__file__).resolve()),
        "--child","--run-id",run_id
    ]
    try:
        proc=subprocess.run(
            cmd,cwd=root,env=clean_env(os.environ),
            capture_output=True,text=True,timeout=180
        )
    except subprocess.TimeoutExpired:
        print("[HOLD] CHILD_TIMEOUT")
        return 2

    path=root/REPORT
    if not path.is_file():
        print("[HOLD] CHILD_REPORT_MISSING")
        print("[CHILD_EXIT_CODE]",proc.returncode)
        return 2

    try:
        result=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError):
        print("[HOLD] CHILD_REPORT_UNREADABLE")
        return 2

    if result.get("run_id")!=run_id:
        print("[HOLD] STALE_CHILD_REPORT")
        return 2

    for key in (
        "status","stage","error_class",
        "worker_generation","worker_candidates",
        "mriya_hot_count","inventory_rows",
        "selected_pairs","hydrated_pairs",
        "verified_pools","rejections",
        "rpc_requests","rpc_methods","rpc_exhausted"
    ):
        if key in result:
            print("["+key.upper()+"]",
                  json.dumps(result[key],sort_keys=True))

    print("[SCANNER] FROZEN")
    print("[SIMULATIONS] 0 [SIGNING] FALSE [BROADCAST] FALSE")
    print("[REPORT]",path)
    return proc.returncode

class Tests(unittest.TestCase):
    def test_environment_secret_excluded(self):
        result=clean_env({
            "PATH":"yes",
            "QSB_SOLANA_PRIVATE_KEY":"hidden"
        })
        self.assertEqual(result,{"PATH":"yes"})

    def test_rpc_budget(self):
        calls=[]
        g=Guard(lambda m,p:calls.append(m),2)
        g("getAccountInfo",[])
        g("getSlot",[])
        with self.assertRaises(RuntimeError):
            g("getAccountInfo",[])
        self.assertEqual(len(calls),2)
        self.assertTrue(g.exhausted)

    def test_no_simulation(self):
        g=Guard(lambda m,p:None)
        with self.assertRaises(RuntimeError):
            g("simulateTransaction",[])
        self.assertEqual(g.count,0)

    def test_no_broadcast(self):
        g=Guard(lambda m,p:None)
        with self.assertRaises(RuntimeError):
            g("sendTransaction",[])
        self.assertEqual(g.count,0)

    def test_import_bootstrap(self):
        import inspect
        text=inspect.getsource(child)
        self.assertIn(
            'sys.path.insert(0,str(root.resolve()))',text
        )

    def test_pair_limit(self):
        self.assertEqual(PAIR_CAP,8)

    def test_canary(self):
        self.assertEqual(CANARY,10000000)

    def test_report_fail_closed(self):
        self.assertFalse(
            {"sendTransaction","simulateTransaction"} -
            {"sendTransaction","simulateTransaction"}
        )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--run",action="store_true")
    ap.add_argument("--child",action="store_true")
    ap.add_argument("--run-id",default="")
    args=ap.parse_args()
    root=Path.cwd()

    if args.test:
        result=unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1

    if args.child:
        return child(root,args.run_id)

    if args.run:
        return parent(root)

    target=root/PKG/NAME
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__),target)

    print("[PASS]",VERSION)
    print("[MODE] SINGLE_GUARDED_MRIYA_REFRESH")
    print("[RPC_CAP]",RPC_CAP)
    print("[SCANNER] FROZEN [SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
