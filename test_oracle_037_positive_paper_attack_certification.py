import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from qseries_v2.oracle_execution import oracle_037_positive_paper_attack_certification as q37

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q37.EXECUTION_AUTHORITY)
        self.assertTrue(q37.PAPER_ONLY)
        self.assertFalse(q37.REAL_MONEY_MOVED)

    def test_hold_without_measurement(self):
        with tempfile.TemporaryDirectory() as d:
            lp=Path(d)/"lat.json";ep=Path(d)/"life.json";rp=Path(d)/"r.json"
            lp.write_text(json.dumps({"attack_rows":[],"summary":{}}),encoding="utf-8")
            ep.write_text(json.dumps({"episodes":[]}),encoding="utf-8")
            with patch.object(q37.q36,"REPORT",lp),patch.object(q37.q35,"REPORT",ep),patch.object(q37,"REPORT",rp):
                x=q37.certify()
            self.assertEqual(x["status"],"HOLD_NO_MEASURED_EXECUTABLE_ECONOMICS")

if __name__=="__main__":
    unittest.main(verbosity=2)
