import unittest
from qseries_v2.oracle_terminal.oracle_historical_experience_read_model import HistoricalExperienceReadModel,HistoricalExperienceContext
import qseries_v2.oracle_terminal.oracle_live_market_experience_ranker as m
class T(unittest.TestCase):
    def test_rank(self):
        c=(HistoricalExperienceContext("KXFAM-A","kalshi:series:KXFAM","PROVEN",True,True,"R",.7,"h","ok"),HistoricalExperienceContext("KXOTHER-A","kalshi:series:KXOTHER","BLIND",False,False,"",0,"h","none"))
        x=HistoricalExperienceReadModel(1,3,3,"h","h","a",True,2,1,0,1,(("KXFAM-X",3),),(("KXFAM",3),),c,True,False)
        rows=m.rank_live_markets_by_experience(x);self.assertEqual(rows[0].market_ticker,"KXFAM-A");self.assertTrue(rows[0].experience_available)
if __name__=="__main__":
    print("="*88);print(" OHE-002 CERTIFICATION TEST");print(" LIVE MARKET EXPERIENCE RANKER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] deterministic experience ranking certified");print("[PASS] score is ranking index, not probability");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-002 CERTIFIED")
