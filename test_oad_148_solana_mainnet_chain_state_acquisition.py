import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_148_solana_mainnet_chain_state_acquisition as m
class T(unittest.TestCase):
    def test_mapping(self):
        vals={"getSlot":500,"getBlockHeight":450,"getEpochInfo":{"epoch":700,"slotIndex":12,"slotsInEpoch":432000},"getTransactionCount":123456}
        with patch.object(m,"_rpc",side_effect=lambda method,params,timeout: vals[method]):
            r=m.acquire_solana_mainnet_chain_state()
        print("[CHAIN_STATE]",r[0].payload)
        self.assertEqual(r[0].payload["slot"],500); self.assertEqual(r[0].payload["transaction_count"],123456)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-148 Solana mainnet chain-state acquisition certified")
