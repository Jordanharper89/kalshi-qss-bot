import unittest
from qseries_v2.oracle_adapters.independent.oad_368_solana_physical_checkpoint_contract import *

class T(unittest.TestCase):
    def test_discovery(self):
        x=discover_checkpoint_contract()
        print("[CHECKPOINT-CONTRACT] load=",x.load_symbol,"commit=",x.commit_symbol)
        print("[CHECKPOINT-CONTRACT] path=",x.checkpoint_path)
        print("[CHECKPOINT-CONTRACT] current_slot=",x.current_slot,"generation=",x.generation,"slot_source=",x.slot_source)
        print("[CHECKPOINT-CONTRACT] raw_fields=",x.raw_fields)

        self.assertTrue(x.load_symbol)
        self.assertTrue(x.commit_symbol)
        self.assertTrue(x.checkpoint_path.endswith("checkpoint.json"))
        self.assertNotEqual(x.slot_source,"NONE")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-368 actual durable Solana checkpoint field/path physically resolved")
