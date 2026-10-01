import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_049c_cpmm_connected_live_route_graph as q
class T(unittest.TestCase):
    def test_cpmm_cycle_requires_cpmm(self):
        E=q.Edge;f=lambda:True;ident=lambda x:x;w=q.c.WSOL
        es=[E("METEORA_DLMM","D1",w,"A",ident,f),
            E("RAYDIUM_CPMM","C1","A","B",ident,f),
            E("METEORA_DLMM","D2","B",w,ident,f)]
        self.assertEqual(len(q.cycles(es)),1)
    def test_stale_leg_blocks_evaluation(self):
        E=q.Edge;ident=lambda x:x;w=q.c.WSOL
        route=(E("METEORA_DLMM","D1",w,"A",ident,lambda:True),
               E("RAYDIUM_CPMM","C1","A","B",ident,lambda:False),
               E("METEORA_DLMM","D2","B",w,ident,lambda:True))
        st={"landing":0}
        self.assertIsNone(q.evaluate(st,[route],q.time.perf_counter_ns()))
    def test_no_execution(self):
        self.assertFalse(q.EXECUTION_AUTHORITY);self.assertTrue(q.PAPER_ONLY)
if __name__=="__main__":unittest.main(verbosity=2)
