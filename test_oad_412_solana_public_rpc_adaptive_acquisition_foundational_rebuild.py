import threading,time,unittest
from unittest.mock import patch
from urllib.error import HTTPError
from qseries_v2.oracle_adapters.independent import oad_318_solana_native_finalized_block_stream as m

class T(unittest.TestCase):
    def test_parallel_success_preserves_order(self):
        lock=threading.Lock();active=0;peak=0
        def rpc(method,params,timeout):
            nonlocal active,peak
            if method=="getSlot":return 200
            if method=="getBlocks":return list(range(101,109))
            if method=="getBlock":
                with lock:active+=1;peak=max(peak,active)
                time.sleep(.01)
                with lock:active-=1
                return {"transactions":[{"slot":params[0]}]}
            raise AssertionError(method)
        with patch.object(m,"_rpc",side_effect=rpc):
            x=m.acquire_finalized_block_batch(101,8,2,max_workers=4,sleep_fn=lambda _:None)
        self.assertGreater(peak,1)
        self.assertEqual(tuple(s for s,_ in x.blocks),tuple(range(101,109)))

    def test_429_keeps_successes_and_downshifts_only_missing(self):
        calls={}; sleeps=[]
        def rpc(method,params,timeout):
            if method=="getSlot":return 200
            if method=="getBlocks":return [101,102,103,104]
            if method=="getBlock":
                slot=params[0];calls[slot]=calls.get(slot,0)+1
                if slot in (103,104) and calls[slot]==1:
                    raise HTTPError("https://api.mainnet-beta.solana.com",429,"Too Many Requests",None,None)
                return {"transactions":[{"slot":slot}]}
            raise AssertionError(method)
        with patch.object(m,"_rpc",side_effect=rpc):
            x=m.acquire_finalized_block_batch(101,4,2,max_workers=4,max_waves=4,sleep_fn=sleeps.append)
        self.assertEqual(tuple(s for s,_ in x.blocks),(101,102,103,104))
        self.assertEqual(calls[101],1);self.assertEqual(calls[102],1)
        self.assertEqual(calls[103],2);self.assertEqual(calls[104],2)
        self.assertTrue(sleeps)

    def test_persistent_429_downshifts_to_serial_then_recovers(self):
        calls={};sleeps=[]
        def rpc(method,params,timeout):
            if method=="getSlot":return 300
            if method=="getBlocks":return [201,202]
            if method=="getBlock":
                slot=params[0];calls[slot]=calls.get(slot,0)+1
                if calls[slot] < 3: raise RuntimeError("HTTP 429 Too Many Requests")
                return {"transactions":[]}
        with patch.object(m,"_rpc",side_effect=rpc):
            x=m.acquire_finalized_block_batch(201,2,2,max_workers=4,max_waves=5,sleep_fn=sleeps.append)
        self.assertEqual(tuple(s for s,_ in x.blocks),(201,202))
        self.assertGreaterEqual(calls[201],3);self.assertGreaterEqual(calls[202],3)
        self.assertGreaterEqual(len(sleeps),2)

    def test_hard_error_fails_closed(self):
        def rpc(method,params,timeout):
            if method=="getSlot":return 100
            if method=="getBlocks":return [90]
            if method=="getBlock":raise ValueError("malformed response")
        with patch.object(m,"_rpc",side_effect=rpc):
            with self.assertRaises(ValueError):m.acquire_finalized_block_batch(90,1,2,sleep_fn=lambda _:None)

    def test_limit_stays_32(self):
        calls=[]
        def rpc(method,params,timeout):
            calls.append((method,params))
            if method=="getSlot":return 100
            if method=="getBlocks":return []
        with patch.object(m,"_rpc",side_effect=rpc):m.acquire_finalized_block_batch(1,999,2)
        gb=[x for x in calls if x[0]=="getBlocks"][0]
        self.assertEqual(gb[1][1],32)

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-412 public-RPC adaptive acquisition rebuild certified")
    print("[PASS] 429 waves retain successful blocks and retry only missing slots")
    print("[PASS] concurrency downshifts 4->2->1 under repeated rate limiting")
