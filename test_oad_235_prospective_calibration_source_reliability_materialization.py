import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_235_prospective_calibration_source_reliability_materialization as m
class T(unittest.TestCase):
    def test_materialize(self):
        rows=(SimpleNamespace(learning_event_hash="a"*64,forecast_probability=.7,outcome_positive=True,brier_score=.09,source_correctness=(("bitcoin",True),("coinbase",False))),)
        with patch.object(m,"read_and_score_mature_prospective_cases",return_value=rows):
            r=m.materialize_prospective_calibration_source_reliability()
        print("[STATE]",r.state,"[CAL]",r.calibration_state_hash,"[REL]",r.source_reliability_state_hash)
        self.assertEqual(r.state,"MATERIALIZED");self.assertEqual(len(r.calibration_state_hash),64);self.assertEqual(len(r.source_reliability_state_hash),64)
if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-235 prospective calibration + source reliability materialization certified")
