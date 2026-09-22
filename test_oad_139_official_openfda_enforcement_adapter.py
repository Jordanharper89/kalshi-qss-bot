import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_139_official_openfda_enforcement_adapter as m
class T(unittest.TestCase):
    def test_mapping(self):
        row={"recall_number":"D-001","report_date":"20260828","classification":"Class II","status":"Ongoing","product_description":"Test drug","reason_for_recall":"Test reason"}
        with patch.object(m,"_latest",return_value=((row,),"https://api.fda.gov/test")):
            r=m.acquire_openfda_enforcement_observations(limit_per_family=1)
        print("[FDA_OBSERVATIONS]",len(r))
        self.assertEqual(len(r),3); self.assertTrue(all(x.provider=="api.fda.gov" for x in r))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-139 official openFDA enforcement adapter contract certified")
