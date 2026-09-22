import ast
import unittest
from pathlib import Path
from unittest.mock import patch

import qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream as m

class T(unittest.TestCase):
    def test_bounded_getblocks_range_contract(self):
        calls=[]

        def fake_rpc(method, params=None, timeout_seconds=20.0):
            calls.append((method, params))
            if method == "getSlot":
                return 500000
            if method == "getBlocks":
                start, end, opts = params
                self.assertLessEqual(end - start + 1, 4)
                return [start, start+1, start+2, start+3]
            if method == "getBlock":
                slot=params[0]
                return {
                    "blockTime": 1700000000,
                    "blockhash": "hash"+str(slot),
                    "previousBlockhash": "prev"+str(slot),
                    "parentSlot": slot-1,
                    "transactions": [],
                }
            raise AssertionError(method)

        with patch.object(m, "_rpc", side_effect=fake_rpc):
            batch=m.acquire_finalized_block_batch(
                start_slot=100,
                limit=4,
                timeout_seconds=1.0,
            )

        getblocks=[x for x in calls if x[0]=="getBlocks"]
        self.assertEqual(len(getblocks),1)
        start,end,_=getblocks[0][1]
        print("[GETBLOCKS RANGE]",start,"->",end,"width=",end-start+1)
        self.assertEqual((start,end),(100,103))

    def test_large_head_never_expands_request_window(self):
        calls=[]
        def fake_rpc(method, params=None, timeout_seconds=20.0):
            calls.append((method,params))
            if method=="getSlot": return 900000
            if method=="getBlocks":
                return []
            raise AssertionError(method)

        with patch.object(m,"_rpc",side_effect=fake_rpc):
            m.acquire_finalized_block_batch(start_slot=100,limit=8,timeout_seconds=1.0)

        p=[x[1] for x in calls if x[0]=="getBlocks"][0]
        self.assertEqual(p[0],100)
        self.assertEqual(p[1],107)
        print("[BOUNDED] head=900000 request=",p[0],"->",p[1])

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-318 bounded finalized-block range repair certified")
