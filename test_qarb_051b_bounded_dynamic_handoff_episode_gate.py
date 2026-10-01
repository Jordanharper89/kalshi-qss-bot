import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_051b_bounded_dynamic_handoff_episode_gate as q

class T(unittest.TestCase):
    def test_duplicate(self):
        g=q.EpisodeGate()
        r={"qualified":True,"route":"SOL>A>SOL","size_sol":.28,"net_sol":.01,"net_bps":100.0}
        self.assertIsNotNone(g.admit(r,1.0))
        self.assertIsNone(g.admit(dict(r),1.5))
        self.assertEqual((g.raw_positive,g.duplicates,len(g.admitted)),(2,1,1))

    def test_reprice(self):
        g=q.EpisodeGate()
        r={"qualified":True,"route":"SOL>A>SOL","size_sol":.28,"net_sol":.01,"net_bps":100.0}
        g.admit(r,1.0);r2=dict(r);r2["net_bps"]=106.0
        self.assertIsNotNone(g.admit(r2,1.5))
        self.assertEqual(len(g.admitted),2)

    def test_no_execution(self):
        self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)

if __name__=="__main__":unittest.main(verbosity=2)
