import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_138_official_cdc_public_health_adapter as m
class T(unittest.TestCase):
    def test_mapping_and_dedupe(self):
        rows=({"id":101,"name":"Influenza update","dateModified":"2026-08-28"},)
        with patch.object(m,"_search",return_value=(rows,"https://tools.cdc.gov/api/test")):
            r=m.acquire_cdc_public_health_observations(queries=("influenza","respiratory virus"))
        print("[CDC_OBSERVATIONS]",len(r))
        self.assertEqual(len(r),1); self.assertEqual(r[0].provider,"tools.cdc.gov")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-138 official CDC public-health adapter contract certified")
