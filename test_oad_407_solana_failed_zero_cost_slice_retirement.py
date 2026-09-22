import importlib, json, unittest
from pathlib import Path
class T(unittest.TestCase):
    def test_failed_slice_not_active(self):
        d=Path.cwd()/"qseries_v2/oracle_adapters/independent"
        for n in range(393,407): self.assertEqual(list(d.glob(f"oad_{n}_*.py")),[])
    def test_package_imports(self): self.assertIsNotNone(importlib.import_module("qseries_v2.oracle_adapters.independent"))
    def test_manifest(self):
        hits=sorted((Path.cwd()/"retired").glob("solana_failed_zero_cost_slice_393_406.*/RETIREMENT_MANIFEST.json")); self.assertTrue(hits)
        x=json.loads(hits[-1].read_text()); self.assertEqual(x["state"],"RETIRED_FAILED_PRODUCTION_SLICE"); self.assertFalse(x["execution_authority"])
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-407 failed Solana zero-cost slice retired")
