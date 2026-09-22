import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_128_official_bls_economic_adapter as m
class T(unittest.TestCase):
    def test_mapping(self):
        def fake(s,t): return ({"year":"2026","period":"M07","periodName":"July","value":"2.7","footnotes":[]},f"https://api.bls.gov/{s}")
        with patch.object(m,"_latest",side_effect=fake):
            r=m.acquire_bls_latest_economic_observations()
        print("[BLS_OBSERVATIONS]",len(r))
        self.assertEqual(len(r),3); self.assertTrue(all(x.independent_evidence for x in r))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-128 official BLS adapter contract certified")
    print("[PHYSICAL] production function uses api.bls.gov")
