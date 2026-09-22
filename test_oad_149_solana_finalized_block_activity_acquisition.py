import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_149_solana_finalized_block_activity_acquisition as m
class T(unittest.TestCase):
    def test_block(self):
        def rpc(method,params,timeout):
            if method=="getSlot": return 1000
            if method=="getBlock": return {"blockHeight":900,"blockTime":1787970000,"blockhash":"abc","previousBlockhash":"def","parentSlot":999,"signatures":["s1","s2","s3"]}
        with patch.object(m,"_rpc",side_effect=rpc):
            r=m.acquire_solana_finalized_block_activity()
        print("[BLOCK_SLOT]",r[0].payload["slot"]); print("[SIGNATURE_COUNT]",r[0].payload["signature_count"])
        self.assertEqual(r[0].payload["signature_count"],3)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-149 Solana finalized block-activity acquisition certified")
