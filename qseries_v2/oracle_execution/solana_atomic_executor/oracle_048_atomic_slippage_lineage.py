
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys,unittest,uuid

VERSION="ORACLE_048_ATOMIC_SLIPPAGE_LINEAGE"
PKG=Path("qseries_v2/oracle_execution/solana_atomic_executor")
NAME="oracle_048_atomic_slippage_lineage.py"
REPORT=Path("runtime_state/oracle/oracle_live_execution/ORACLE_048_SLIPPAGE.json")
V41=Path("runtime_state/oracle/oracle_live_execution/ORACLE_041_ATTESTATION.json")
CANARY=10_000_000
SAFE={"PATH","PATHEXT","SYSTEMROOT","WINDIR","SYSTEMDRIVE",
      "TEMP","TMP","COMSPEC","SOLANA_RPC_URL",
      "QSB_SOLANA_RPC_URL","SOLANA_WS_URL","QSB_SOLANA_WALLET"}

def scrub(env):
    return {k:v for k,v in env.items() if k.upper() in SAFE}

def numeric(value):
    if type(value) in (int,float) and abs(value)<10**21:
        return value
    return None

def bounds_only(value,depth=0):
    if depth>3:return None
    if type(value) in (int,float):return numeric(value)
    if isinstance(value,dict):
        out={}
        for k,v in value.items():
            name=str(k).lower()
            allowed=("amount","min","max","quote","fee","net",
                     "gross","input","output","slip","bound",
                     "raw","bps","lamport","spend")
            forbidden=("account","key","url","instruction",
                       "data","wallet","signature")
            if not any(x in name for x in allowed):continue
            if any(x in name for x in forbidden):continue
            item=bounds_only(v,depth+1)
            if item is not None:out[str(k)[:50]]=item
        return out
    if isinstance(value,(tuple,list)):
        return [x for x in
                (bounds_only(v,depth+1) for v in value[:20])
                if x is not None]
    return None

def simulation_code(err):
    if err is None:return "SIMULATION_PASS"
    if isinstance(err,dict):
        item=err.get("InstructionError")
        if isinstance(item,list) and len(item)==2:
            if isinstance(item[1],dict) and item[1].get("Custom")==6003:
                return "METEORA_SWAP2_6003"
    return "SIMULATION_REJECTED_OTHER"

def save(root,result):
    path=root/REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",
                    encoding="utf-8")
    temp.replace(path)

def child(root,seconds,run_id):
    result={
        "revision":VERSION,"run_id":run_id,"status":"HOLD",
        "stage":"IMPORTS","bounds_captured":0,"bound_samples":[],
        "simulations_observed":0,"simulation_codes":[],
        "signing":False,"broadcast":False,
        "canary_lamports":CANARY,"scanner_modified":False
    }
    patches=[]
    try:
        sys.path.insert(0,str(root.resolve()))
        if any("PRIVATE_KEY" in k.upper() or
               "SECRET_KEY" in k.upper() for k in os.environ):
            result["status"]="HOLD_SECRET_ENVIRONMENT"
            return 2
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_atomic_closeout as v20
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_041_mriya_native_attestation as v41

        original_bound=v20.build_bound
        original_rpc=core.rpc

        def capture_bound(*args,**kwargs):
            output=original_bound(*args,**kwargs)
            if (isinstance(output,(tuple,list)) and len(output)>1
                    and len(result["bound_samples"])<3):
                result["bound_samples"].append(bounds_only(output[1]))
                result["bounds_captured"]+=1
            return output

        def capture_rpc(method,params):
            response=original_rpc(method,params)
            if method=="simulateTransaction":
                result["simulations_observed"]+=1
                value=response.get("value",{}) if isinstance(response,dict) else {}
                result["simulation_codes"].append(
                    simulation_code(value.get("err")))
                result["simulation_units"]=numeric(
                    value.get("unitsConsumed"))
                result["slippage_log_seen"]=any(
                    "slippage" in str(x).lower()
                    for x in (value.get("logs") or []))
            return response

        v20.build_bound=capture_bound
        patches.append((v20,"build_bound",original_bound))
        core.rpc=capture_rpc
        patches.append((core,"rpc",original_rpc))

        result["stage"]="GUARDED_ORACLE_041"
        exit_code=v41.child(root,seconds,run_id)

        path=root/V41
        if not path.is_file():
            result["status"]="HOLD_V41_REPORT_MISSING"
            return 2
        prior=json.loads(path.read_text(encoding="utf-8"))
        if prior.get("run_id")!=run_id:
            result["status"]="HOLD_STALE_V41_REPORT"
            return 2

        for key in ("worker_candidates","ready","priced_events",
                    "positive_candidates","native_passes",
                    "shared_rpc_requests","holds"):
            result[key]=prior.get(key)
        result["oracle_041_status"]=prior.get("status")

        if result["simulations_observed"]:
            result["status"]="SIMULATION_RESULT_CAPTURED"
        elif result["bounds_captured"]:
            result["status"]="BOUNDS_CAPTURED_NO_SIMULATION"
        elif (result.get("priced_events") or 0)>0:
            result["status"]="LIVE_PRICING_NO_POSITIVE_ATOMIC_CANDIDATE"
        else:
            result["status"]="HOLD_NO_LIVE_PRICING"
        result["stage"]="RESULT"
        return exit_code
    except Exception as exc:
        result["status"]="HOLD_"+type(exc).__name__
        return 2
    finally:
        for obj,key,original in reversed(patches):
            setattr(obj,key,original)
        save(root,result)

def parent(root,seconds):
    run_id=str(uuid.uuid4())
    cmd=[sys.executable,"-I",str(Path(__file__).resolve()),
         "--child","--seconds",str(seconds),"--run-id",run_id]
    try:
        process=subprocess.run(
            cmd,cwd=root,env=scrub(os.environ),
            capture_output=True,text=True,timeout=seconds+180)
    except subprocess.TimeoutExpired:
        print("[HOLD] CHILD_TIMEOUT")
        return 2

    path=root/REPORT
    if not path.is_file():
        print("[HOLD] REPORT_MISSING")
        return 2
    row=json.loads(path.read_text(encoding="utf-8"))
    if row.get("run_id")!=run_id:
        print("[HOLD] STALE_REPORT")
        return 2

    for key in ("status","stage","oracle_041_status",
                "worker_candidates","ready","priced_events",
                "positive_candidates","native_passes",
                "bounds_captured","bound_samples",
                "simulations_observed","simulation_codes",
                "simulation_units","slippage_log_seen",
                "shared_rpc_requests","holds"):
        if key in row:
            print("["+key.upper()+"]",
                  json.dumps(row[key],sort_keys=True))
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    print("[REPORT]",path)
    return process.returncode

class Tests(unittest.TestCase):
    def test_secret_scrub(self):
        self.assertEqual(scrub({
            "PATH":"ok","QSB_SOLANA_PRIVATE_KEY":"secret"
        }),{"PATH":"ok"})
    def test_6003(self):
        self.assertEqual(simulation_code({
            "InstructionError":[5,{"Custom":6003}]
        }),"METEORA_SWAP2_6003")
    def test_other_error(self):
        self.assertEqual(simulation_code({
            "InstructionError":[3,{"Custom":7}]
        }),"SIMULATION_REJECTED_OTHER")
    def test_success(self):
        self.assertEqual(simulation_code(None),"SIMULATION_PASS")
    def test_numeric_redaction(self):
        self.assertEqual(bounds_only({
            "min_output":123,"rpc_url":"secret",
            "account_key":"secret","token_input":99
        }),{"min_output":123,"token_input":99})
    def test_canary(self):
        self.assertEqual(CANARY,10_000_000)
    def test_private_key_excluded(self):
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",SAFE)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--run",action="store_true")
    p.add_argument("--child",action="store_true")
    p.add_argument("--seconds",type=int,default=90)
    p.add_argument("--run-id",default="")
    args=p.parse_args()
    root=Path.cwd()

    if args.test:
        result=unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    if args.child:
        return child(root,args.seconds,args.run_id)
    if args.run:
        if not 60<=args.seconds<=180:
            print("[HOLD] DURATION_60_TO_180_SECONDS")
            return 2
        return parent(root,args.seconds)

    target=root/PKG/NAME
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__),target)
    print("[PASS]",VERSION)
    print("[MODE] GUARDED_MRIYA_NATIVE_SLIPPAGE_LINEAGE")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
