import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_051_dynamic_progression_independent_episode_gate as q

class T(unittest.TestCase):
    def test_duplicate_suppression(self):
        g=q.EpisodeGate()
        r={"qualified":True,"route":"SOL>A>SOL","size_sol":.28,"net_sol":.01,"net_bps":100.0}
        self.assertIsNotNone(g.admit(r,10.0))
        self.assertIsNone(g.admit(dict(r),10.5))
        self.assertEqual(g.duplicates,1)
        self.assertEqual(len(g.admitted),1)

    def test_material_reprice_new_episode(self):
        g=q.EpisodeGate()
        r={"qualified":True,"route":"SOL>A>SOL","size_sol":.28,"net_sol":.01,"net_bps":100.0}
        self.assertIsNotNone(g.admit(r,10.0))
        r2=dict(r);r2["net_bps"]=106.0
        self.assertIsNotNone(g.admit(r2,10.5))
        self.assertEqual(len(g.admitted),2)

    def test_no_execution(self):
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.EXECUTION_AUTHORITY)

if __name__=="__main__":unittest.main(verbosity=2)
