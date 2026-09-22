import unittest
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_395_solana_block_efficient_universal_acquisition_worker import acquire_missing_block_batch
@dataclass
class FakeBatch:
    blocks:tuple
class T(unittest.TestCase):
    def test_block_efficiency(self):
        def fake(**kwargs):
            return FakeBatch(({"transactions":[1,2,3]},{"transactions":[4,5]}))
        x=acquire_missing_block_batch(101,2,acquire_fn=fake)
        print("[ACQUISITION]",x)
        self.assertEqual(x.blocks_observed,2)
        self.assertEqual(x.transactions_observed,5)
        self.assertEqual(x.per_transaction_rpc_calls,0)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-395 block-efficient universal acquisition contract certified")