
from pathlib import Path
from contextlib import contextmanager
import argparse, json, shutil, unittest

VERSION="ORACLE_036_REAL_MRIYA_WORKER_HANDOFF"
PKG=Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST=PKG/"oracle_036_live_worker_handoff.py"
INVENTORY=Path("runtime_state/oracle/solana_atomic_executor/full_surface_replenishment_inventory.json")
REPORT=Path("runtime_state/oracle/oracle_live_execution/ORACLE_036_HANDOFF.json")
WSOL="So11111111111111111111111111111111111111112"
ABC="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
CANARY=10_000_000
CAP=8

def pubkey(s):
    if not isinstance(s,str) or not 32<=len(s)<=44:
        return False
    try:
        n=0
        for c in s:n=n*58+ABC.index(c)
        raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
        return len(b"\0"*(len(s)-len(s.lstrip("1")))+raw)==32
    except (ValueError,OverflowError):
        return False

def worker_snapshot(worker):
    value=worker.latest()
    if not isinstance(value,tuple) or len(value)!=2:
        raise RuntimeError("WORKER_LATEST_CONTRACT_MISMATCH")
    generation,rows=value
    if not isinstance(generation,int) or generation<1:
        raise RuntimeError("NO_COMPLETED_MRIYA_GENERATION")
    if not isinstance(rows,list):
        raise RuntimeError("WORKER_ROWS_NOT_LIST")
    return generation,[dict(x) for x in rows if isinstance(x,dict)]

def inventory_rows(root):
    path=Path(root)/INVENTORY
    if not path.is_file():return []
    data=json.loads(path.read_text(encoding="utf-8"))
    return data.get("rows",[]) if isinstance(data.get("rows"),list) else []

def admission(worker_rows,inventory,cap=CAP):
    indexed={}
    for row in inventory:
        if not isinstance(row,dict):continue
        t,p,m=row.get("token"),row.get("pump_pool"),row.get("meteora_pool")
        if not all(pubkey(x) for x in (t,p,m)):continue
        if len({t,p,m})!=3:continue
        if {row.get("token_x"),row.get("token_y")}!={t,WSOL}:continue
        try:
            dx=int(row["decimals_x"]);dy=int(row["decimals_y"])
        except (KeyError,TypeError,ValueError):continue
        if not 0<=dx<=18 or not 0<=dy<=18:continue
        indexed[(t,p,m)]=row
    accepted=[];seen=set();reject={}
    for row in worker_rows:
        t,p,m=row.get("token"),row.get("pump_pool"),row.get("meteora_pool")
        key=(t,p,m)
        if key not in indexed:
            reason="NO_EXACT_LOCAL_METADATA"
        elif t in seen:
            reason="DUPLICATE_TOKEN"
        else:
            meta=indexed[key]
            accepted.append({
                "token":t,"pump_pool":p,"meteora_pool":m,
                "meteora_meta":{
                    "address":m,
                    "token_x":meta["token_x"],
                    "token_y":meta["token_y"],
                    "decimals_x":int(meta["decimals_x"]),
                    "decimals_y":int(meta["decimals_y"])
                },
                "source":"MRIYA_WORKER",
                "crosslisted":True,
                "execution_authority":False,
                "requires_fresh_onchain_attestation":True
            })
            seen.add(t)
            if len(accepted)>=cap:break
            continue
        reject[reason]=reject.get(reason,0)+1
    return accepted,reject

@contextmanager
def scoped_handoff(engine,worker,inventory,telemetry=None):
    """Only for an explicitly controlled, nonconcurrent hydration call."""
    thread=getattr(worker,"thread",None)
    if thread is not None and thread.is_alive():
        raise RuntimeError("ACTIVE_WORKER_CONCURRENT_PATCH_REFUSED")
    generation,rows=worker_snapshot(worker)
    selected,rejected=admission(rows,inventory)
    original=engine.candidate_universe
    def intake(root):
        return [dict(x) for x in selected]
    if telemetry is not None:
        telemetry.update({
            "generation":generation,
            "worker_rows":len(rows),
            "accepted_for_hydration":len(selected),
            "rejections":rejected,
            "fresh_onchain_attestation_completed":False,
            "execution_authority":False
        })
    engine.candidate_universe=intake
    try:yield selected
    finally:engine.candidate_universe=original

def audit(root):
    from qseries_v2.oracle_execution.solana_atomic_executor import mry_001_continuous_replenishment as mry
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine

    worker=mry.ReplenishmentWorker(root)
    inventory=inventory_rows(root)
    result={
        "revision":VERSION,
        "status":"OFFLINE_WORKER_TO_EXECUTOR_CONTRACT_READY",
        "worker_class":type(worker).__name__,
        "worker_latest_shape":"generation,rows",
        "worker_generation":worker.latest()[0],
        "inventory_rows":len(inventory),
        "consumer_interface":"engine.candidate_universe",
        "hydration_interface":"live_account_stream.prepare_pairs",
        "offline_scope_tested":False,
        "live_hydration_certified":False,
        "worker_started":False,
        "rpc_requests":0,
        "scanner_modified":False,
        "execution_authority":False,
        "signing":False,
        "broadcast":False,
        "canary_lamports":CANARY
    }
    original=engine.candidate_universe
    with scoped_fixture(worker,engine,inventory) as diagnostics:
        result["offline_scope_tested"]=True
        result["fixture_handoff"]=diagnostics
    if engine.candidate_universe is not original:
        raise RuntimeError("ORIGINAL_DISCOVERY_NOT_RESTORED")
    path=Path(root)/REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    temp.replace(path)
    return result

@contextmanager
def scoped_fixture(worker,engine,inventory):
    original=worker.latest
    worker.latest=lambda:(1,[])
    try:
        diagnostics={}
        with scoped_handoff(engine,worker,inventory,diagnostics):
            yield diagnostics
    finally:
        worker.latest=original

class Tests(unittest.TestCase):
    T="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    P="11111111111111111111111111111111"
    M="MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

    def fixture(self):
        w=[{"token":self.T,"pump_pool":self.P,"meteora_pool":self.M}]
        i=[{"token":self.T,"pump_pool":self.P,"meteora_pool":self.M,
            "token_x":self.T,"token_y":WSOL,"decimals_x":9,"decimals_y":6}]
        return w,i

    def test_pubkeys(self):
        self.assertTrue(all(pubkey(x) for x in (self.T,self.P,self.M)))
        self.assertFalse(pubkey("invalid"))

    def test_real_latest_tuple(self):
        class Worker:
            def latest(self):return (4,[{"token":"example"}])
        g,r=worker_snapshot(Worker())
        self.assertEqual((g,len(r)),(4,1))

    def test_empty_generation_refused(self):
        class Worker:
            def latest(self):return (0,[])
        with self.assertRaises(RuntimeError):worker_snapshot(Worker())

    def test_exact_identity(self):
        w,i=self.fixture()
        rows,reject=admission(w,i)
        self.assertEqual(len(rows),1)
        self.assertFalse(rows[0]["execution_authority"])

    def test_mismatched_pool(self):
        w,i=self.fixture()
        w[0]["meteora_pool"]=self.P
        rows,reject=admission(w,i)
        self.assertEqual(len(rows),0)
        self.assertEqual(reject["NO_EXACT_LOCAL_METADATA"],1)

    def test_deduplication(self):
        w,i=self.fixture()
        self.assertEqual(len(admission(w+w,i)[0]),1)

    def test_restore(self):
        class Engine:
            def candidate_universe(self,root):return ["original"]
        class Worker:
            thread=None
            def latest(self):return (1,[{"token":"example"}])
        e=Engine();old=e.candidate_universe.__func__
        with scoped_handoff(e,Worker(),[],{}):
            self.assertEqual(e.candidate_universe(Path(".")),[])
        self.assertIs(e.candidate_universe.__func__,old)

    def test_real_worker_offline(self):
        from qseries_v2.oracle_execution.solana_atomic_executor import mry_001_continuous_replenishment as m
        w=m.ReplenishmentWorker(Path.cwd())
        self.assertEqual(w.latest(),(0,[]))
        self.assertIsNone(w.thread)

    def test_report_locked(self):
        row=audit(Path.cwd())
        self.assertFalse(row["signing"])
        self.assertFalse(row["broadcast"])
        self.assertEqual(row["rpc_requests"],0)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--audit",action="store_true")
    a=p.parse_args()
    root=Path.cwd()
    if a.test:
        result=unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    if a.audit:
        row=audit(root)
        for key,value in row.items():
            print("["+key.upper()+"]",json.dumps(value,sort_keys=True))
        print("[REPORT]",root/REPORT)
        return 0
    destination=root/DEST
    if not destination.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if destination.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__),destination)
    print("[PASS]",VERSION)
    print("[MODE] REAL_WORKER_CONTRACT; FRESH_HYDRATION_REQUIRED")
    print("[SCANNER] FROZEN [RPC] 0 [SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
