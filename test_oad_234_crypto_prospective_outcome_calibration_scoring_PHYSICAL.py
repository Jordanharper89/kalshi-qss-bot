import unittest,time
from qseries_v2.oracle_adapters.independent.oad_234_crypto_prospective_outcome_calibration_scoring import read_and_score_mature_prospective_cases

class T(unittest.TestCase):
    def test_physical(self):
        t=time.monotonic()
        rows=read_and_score_mature_prospective_cases(per_source_limit=512)
        elapsed=time.monotonic()-t
        print("[PHYSICAL] query_seconds=",round(elapsed,3))
        print("[PHYSICAL] mature_scored_cases=",len(rows))
        if rows:
            print("[PHYSICAL] latest=",rows[-1])
        else:
            print("[PHYSICAL] state= HOLD_FUTURE_PROSPECTIVE_OUTCOME_REQUIRED")
        self.assertLess(elapsed,10.0)
        self.assertTrue(all(0<=x.forecast_probability<=1 for x in rows))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-234 physical source-indexed prospective scoring certified")
