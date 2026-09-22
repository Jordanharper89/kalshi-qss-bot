import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_159_ethereum_fee_transaction_pressure_acquisition as m
class T(unittest.TestCase):
    def test_pressure(self):
        s=SimpleNamespace(provider="ethereum-rpc.publicnode.com",endpoint="https://ethereum-rpc.publicnode.com",failures=(("cloudflare-eth.com","RuntimeError","Cannot fulfill request"),))
        vals={"eth_gasPrice":"0x10","eth_feeHistory":{"oldestBlock":"0x60","baseFeePerGas":["0x1","0x2"],"gasUsedRatio":[0.5],"reward":[["0x3","0x4","0x5"]]},"eth_getBlockTransactionCountByNumber":"0x2","eth_getBlockByNumber":{"number":"0x65","hash":"0xabc","gasLimit":"0x100","gasUsed":"0x80","baseFeePerGas":"0x2"}}
        with patch.object(m,"select_ethereum_rpc",return_value=s),patch.object(m,"_rpc",side_effect=lambda endpoint,method,params,timeout: vals[method]):
            r=m.acquire_ethereum_fee_transaction_pressure_observations()
        self.assertEqual(len(r),2); self.assertEqual(r[0].provider,"ethereum-rpc.publicnode.com")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-159 resilient Ethereum pressure acquisition certified")
