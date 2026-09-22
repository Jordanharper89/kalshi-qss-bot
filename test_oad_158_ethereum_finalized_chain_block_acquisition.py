import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_158_ethereum_finalized_chain_block_acquisition as m
class T(unittest.TestCase):
    def test_fallback(self):
        def rpc(endpoint,method,params,timeout):
            if "cloudflare" in endpoint and method=="eth_blockNumber":
                raise RuntimeError("Cannot fulfill request")
            if method=="eth_chainId": return "0x1"
            if method=="eth_blockNumber": return "0x64"
            if method=="eth_getBlockByNumber": return {"number":"0x60","hash":"0xabc","parentHash":"0xdef","timestamp":"0x6a2f1000","transactions":["0x1"],"gasLimit":"0x100","gasUsed":"0x80","baseFeePerGas":"0x2","size":"0x1000"}
            raise AssertionError(method)
        with patch.object(m,"_rpc",side_effect=rpc):
            r=m.acquire_ethereum_finalized_chain_observations()
        print("[PROVIDER]",r[0].provider)
        print("[FAILURES]",r[0].payload["rpc_failures_before_selection"])
        self.assertEqual(r[0].provider,"ethereum-rpc.publicnode.com")
        self.assertEqual(len(r),2)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-158 Ethereum RPC fallback certified")
