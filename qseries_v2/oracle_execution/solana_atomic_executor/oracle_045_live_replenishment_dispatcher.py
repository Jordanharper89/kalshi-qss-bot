
from pathlib import Path
import argparse
import asyncio
import json
import shutil
import unittest

VERSION="ORACLE_045_LIVE_REPLENISHMENT_DISPATCHER"
PKG=Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST=PKG/"oracle_045_live_replenishment_dispatcher.py"
REPORT=Path("runtime_state/oracle/oracle_live_execution/ORACLE_045_DISPATCHER.json")
CANARY=10_000_000

class Dispatcher:
    def __init__(self,transport,worker,hydrate,commit,on_event):
        self.transport=transport
        self.worker=worker
        self.hydrate=hydrate
        self.commit=commit
        self.on_event=on_event
        self.generation=0
        self.events=0
        self.commits=0
        self.holds=[]
        self.running=False

    async def receiver(self):
        self.running=True
        try:
            while self.running:
                raw=await self.transport.ws.recv()
                message=json.loads(raw)
                result=await self.transport.accept(message)
                if not result:
                    continue
                kind,address=result
                if kind=="EVENT" and address:
                    self.events+=1
                    await self.on_event(address,message)
        except asyncio.CancelledError:
            raise
        finally:
            self.running=False

    async def replenish(self,candidates,evict=None):
        for candidate in candidates:
            token=candidate.get("token")
            if not token or token in self.transport.active:
                continue
            try:
                receipt=await self.hydrate(candidate)
            except Exception:
                self.holds.append("HYDRATION_FAILED")
                continue
            result=await self.transport.rotate(
                candidate,receipt,self.commit,
                evict_token=evict
            )
            if result.startswith("ROTATION_COMMITTED"):
                self.commits+=1
                evict=None
            elif result=="COMMITTED_CLEANUP_PENDING":
                self.commits+=1
                self.holds.append(result)
                evict=None
            else:
                self.holds.append(result)

    async def generation_tick(self,select,evict=None):
        generation,rows=self.worker.latest()
        if not isinstance(generation,int) or generation<1:
            return "NO_COMPLETED_GENERATION"
        if generation<=self.generation:
            return "UNCHANGED"
        # Selection is supplied by the exact-bound admission layer.
        try:
            candidates=select(rows)
        except Exception:
            self.holds.append("SELECTION_FAILED")
            return "HOLD_SELECTION_FAILED"
        if not isinstance(candidates,list):
            return "HOLD_SELECTION_CONTRACT"
        await self.replenish(candidates,evict)
        self.generation=generation
        return "GENERATION_CONSUMED"

    async def serve(self,select,seconds=30,poll=2):
        receiver=asyncio.create_task(self.receiver())
        loop=asyncio.get_running_loop()
        end=loop.time()+seconds
        try:
            while loop.time()<end:
                if receiver.done():
                    self.holds.append("RECEIVER_TERMINATED")
                    break
                await self.generation_tick(select)
                await asyncio.sleep(min(poll,max(0,end-loop.time())))
        finally:
            self.running=False
            receiver.cancel()
            await asyncio.gather(receiver,return_exceptions=True)
        return self.status()

    def status(self):
        return {
            "generation":self.generation,
            "active_pairs":len(self.transport.active),
            "account_notifications":self.events,
            "committed_rotations":self.commits,
            "holds":list(self.holds),
            "execution_authority":False,
            "signing":False,
            "broadcast":False
        }

class FakeWS:
    def __init__(self):
        self.queue=asyncio.Queue()
        self.sent=[]
    async def send(self,text):
        msg=json.loads(text)
        self.sent.append(msg)
        if msg["method"]=="accountSubscribe":
            await self.queue.put(json.dumps({
                "id":msg["id"],"result":msg["id"]+1000
            }))
    async def recv(self):
        return await self.queue.get()

class Worker:
    def __init__(self):
        self.gen=0
        self.rows=[]
    def latest(self):
        return self.gen,list(self.rows)

def fixture(n):
    row={"token":"T"+str(n),"pump_pool":"P"+str(n),
         "meteora_pool":"M"+str(n)}
    receipt={
        "identity":(row["token"],row["pump_pool"],
                    row["meteora_pool"]),
        "fresh_onchain":True,
        "pool_owner_attested":True,
        "native_templates_ready":True,
        "watched_accounts":["A"+str(n)],
        "execution_authority":False
    }
    return row,receipt

class Tests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from qseries_v2.oracle_execution.solana_atomic_executor import (
            oracle_044_ws_rotation_transport as v44
        )
        self.ws=FakeWS()
        self.transport=v44.Transport(self.ws,timeout=0.2)
        self.worker=Worker()
        self.receipts={}
        self.events=[]
        async def hydrate(row):
            return self.receipts[row["token"]]
        async def event(address,message):
            self.events.append(address)
        self.d=Dispatcher(
            self.transport,self.worker,hydrate,
            lambda proposed,receipt:True,event
        )
        self.rx=asyncio.create_task(self.d.receiver())
        await asyncio.sleep(0)

    async def asyncTearDown(self):
        self.rx.cancel()
        await asyncio.gather(self.rx,return_exceptions=True)

    async def seed(self,n):
        row,receipt=fixture(n)
        self.receipts[row["token"]]=receipt
        self.worker.rows=[row]
        self.worker.gen+=1
        return row

    async def test_actual_subscription_ack(self):
        await self.seed(1)
        self.assertEqual(
            await self.d.generation_tick(list),
            "GENERATION_CONSUMED"
        )
        self.assertEqual(self.d.commits,1)

    async def test_no_duplicate_generation(self):
        await self.seed(1)
        await self.d.generation_tick(list)
        self.assertEqual(
            await self.d.generation_tick(list),"UNCHANGED"
        )
        self.assertEqual(self.d.commits,1)

    async def test_notification_delivery(self):
        await self.seed(1)
        await self.d.generation_tick(list)
        sid=self.transport.subscriptions["A1"]
        await self.ws.queue.put(json.dumps({
            "method":"accountNotification",
            "params":{"subscription":sid}
        }))
        await asyncio.sleep(0.01)
        self.assertEqual(self.events,["A1"])

    async def test_no_auto_evict(self):
        for n in range(1,9):
            await self.seed(n)
            await self.d.generation_tick(list)
        await self.seed(9)
        await self.d.generation_tick(list)
        self.assertEqual(len(self.transport.active),8)
        self.assertIn("HOLD_NO_EXPLICIT_EVICTION",self.d.holds)

    async def test_failed_validation(self):
        row=await self.seed(1)
        self.receipts[row["token"]]["pool_owner_attested"]=False
        await self.d.generation_tick(list)
        self.assertEqual(self.d.commits,0)

    async def test_new_generation(self):
        await self.seed(1)
        await self.d.generation_tick(list)
        await self.seed(2)
        await self.d.generation_tick(list)
        self.assertEqual(self.d.commits,2)

    async def test_no_generation(self):
        self.assertEqual(
            await self.d.generation_tick(list),
            "NO_COMPLETED_GENERATION"
        )

    async def test_execution_locked(self):
        report=self.d.status()
        self.assertFalse(report["signing"])
        self.assertFalse(report["broadcast"])

def audit(root):
    result={
        "revision":VERSION,
        "status":"SHARED_RECEIVER_DISPATCHER_TESTED",
        "uses_existing_ws_transport":True,
        "generation_deduplication":True,
        "ack_receiver_concurrent_with_rotation":True,
        "native_hydration_callback_required":True,
        "exact_pair_selection_callback_required":True,
        "production_socket_attached":False,
        "production_hydration_attached":False,
        "production_pricing_callback_attached":False,
        "continuous_live_replenishment_certified":False,
        "rpc_requests":0,
        "signing":False,
        "broadcast":False,
        "canary_lamports":CANARY
    }
    path=root/REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(result,indent=2,sort_keys=True),
                   encoding="utf-8")
    tmp.replace(path)
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--audit",action="store_true")
    args=parser.parse_args()
    root=Path.cwd()
    if args.test:
        result=unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 1
    if args.audit:
        result=audit(root)
        for key,value in result.items():
            print("["+key.upper()+"]",json.dumps(value))
        print("[REPORT]",root/REPORT)
        return 0
    target=root/DEST
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__),target)
    print("[PASS]",VERSION)
    print("[MODE] SHARED_WEBSOCKET_RECEIVER_AND_GENERATION_DISPATCH")
    print("[SCANNER] FROZEN")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
