import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from email.message import Message
from qseries_v2.oracle_adapters.independent import oad_318_solana_native_finalized_block_stream as m

class Clock:
    def __init__(self):self.t=0.0;self.sleeps=[]
    def now(self):return self.t
    def sleep(self,x):self.sleeps.append(float(x));self.t+=float(x)

class T(unittest.TestCase):
    def test_serial_rate_pacing_preserves_order(self):
        c=Clock();calls=[]
        def rpc(method,params,timeout):
            if method=="getSlot":return 200
            if method=="getBlocks":return [101,102,103,104]
            if method=="getBlock":calls.append((params[0],c.now()));return {"transactions":[{"slot":params[0]}]}
            raise AssertionError(method)
        with patch.object(m,"_rpc",side_effect=rpc):
            x=m.acquire_finalized_block_batch(101,4,2,min_interval_seconds=.30,sleep_fn=c.sleep,monotonic_fn=c.now)
        self.assertEqual(tuple(s for s,_ in x.blocks),(101,102,103,104))
        self.assertEqual([s for s,_ in calls],[101,102,103,104])
        self.assertTrue(all((calls[i][1]-calls[i-1][1])>=.299 for i in range(1,len(calls))))

    def test_429_honors_retry_after_then_recovers(self):
        c=Clock();n=0
        def rpc(method,params,timeout):
            nonlocal n
            if method=="getSlot":return 100
            if method=="getBlocks":return [90]
            if method=="getBlock":
                n+=1
                if n==1:
                    h=Message();h["Retry-After"]="2"
                    raise HTTPError("https://api.mainnet.solana.com",429,"Too Many Requests",h,None)
                return {"transactions":[]}
        with patch.object(m,"_rpc",side_effect=rpc):
            x=m.acquire_finalized_block_batch(90,1,2,sleep_fn=c.sleep,monotonic_fn=c.now)
        self.assertEqual(tuple(s for s,_ in x.blocks),(90,))
        self.assertIn(2.0,c.sleeps)

    def test_transient_retry_is_bounded(self):
        c=Clock()
        def rpc(method,params,timeout):
            if method=="getSlot":return 100
            if method=="getBlocks":return [90]
            if method=="getBlock":raise RuntimeError("HTTP 429 Too Many Requests")
        with patch.object(m,"_rpc",side_effect=rpc):
            with self.assertRaises(RuntimeError):m.acquire_finalized_block_batch(90,1,2,max_attempts_per_slot=3,sleep_fn=c.sleep,monotonic_fn=c.now)
        self.assertEqual(len(c.sleeps),2)

    def test_hard_error_fails_closed(self):
        c=Clock()
        def rpc(method,params,timeout):
            if method=="getSlot":return 100
            if method=="getBlocks":return [90]
            if method=="getBlock":raise ValueError("malformed response")
        with patch.object(m,"_rpc",side_effect=rpc):
            with self.assertRaises(ValueError):m.acquire_finalized_block_batch(90,1,2,sleep_fn=c.sleep,monotonic_fn=c.now)

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
    print("[PASS] OAD-413 public-RPC rate-paced final acquisition rebuild certified")
    print("[PASS] getBlock calls are serial and paced below published single-method limit")
    print("[PASS] HTTP 429 Retry-After honored; bounded fallback backoff preserved")
