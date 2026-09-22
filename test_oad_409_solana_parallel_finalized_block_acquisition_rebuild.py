import threading,time,unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_318_solana_native_finalized_block_stream as m
class T(unittest.TestCase):
    def test_parallel_getblock_preserves_slot_order(self):
        lock=threading.Lock(); active=0; peak=0
        def rpc(method,params,timeout):
            nonlocal active,peak
            if method=="getSlot": return 200
            if method=="getBlocks": return list(range(101,109))
            if method=="getBlock":
                slot=params[0]
                with lock:
                    active+=1; peak=max(peak,active)
                time.sleep(.03)
                with lock: active-=1
                return {"transactions":[{"slot":slot}]}
            raise AssertionError(method)
        with patch.object(m,"_rpc",side_effect=rpc):
            x=m.acquire_finalized_block_batch(101,8,2,max_workers=4)
        self.assertGreater(peak,1)
        self.assertEqual(tuple(s for s,_ in x.blocks),tuple(range(101,109)))
        self.assertEqual(x.transaction_count,8)
    def test_limit_stays_bounded(self):
        calls=[]
        def rpc(method,params,timeout):
            calls.append((method,params));
            if method=="getSlot": return 100
            if method=="getBlocks": return []
        with patch.object(m,"_rpc",side_effect=rpc): m.acquire_finalized_block_batch(1,999,2)
        gb=[x for x in calls if x[0]=="getBlocks"][0]
        self.assertEqual(gb[1][1],32)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-409 parallel finalized-block acquisition rebuild certified")
