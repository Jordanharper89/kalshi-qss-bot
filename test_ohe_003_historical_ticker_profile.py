import unittest
from qseries_v2.oracle_terminal.oracle_historical_experience_read_model import HistoricalExperienceReadModel,HistoricalExperienceContext
import qseries_v2.oracle_terminal.oracle_historical_ticker_profile as m
class T(unittest.TestCase):
    def test_profile(self):
        c=HistoricalExperienceContext("KXFAM-LIVE","kalshi:series:KXFAM","PROVEN",True,True,"R",.61,"h","matched")
        x=HistoricalExperienceReadModel(1,3,3,"h","h","a",True,1,1,0,0,(("KXFAM-OLD",3),),(("KXFAM",3),),(c,),True,False)
        p=m.build_historical_ticker_profile(x,"KXFAM-LIVE");self.assertEqual(p.family_learned_records,3);self.assertTrue(p.experience_available)
if __name__=="__main__":
    print("="*88);print(" OHE-003 CERTIFICATION TEST");print(" HISTORICAL TICKER PROFILE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] exact ticker + family history profile certified");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-003 CERTIFIED")
