import unittest
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_049b_live_multibase_asset_graph as q

class T(unittest.TestCase):
    def test_multibase_cycle(self):
        E=q.Edge
        ident=lambda x:x
        w=q.m.c.WSOL
        edges=[
          E("PUMPSWAP","P1",w,"A",ident),
          E("RAYDIUM_CPMM","C1","A","B",ident),
          E("METEORA_DLMM","D1","B",w,ident)]
        rows=q.enumerate_cycles(edges,4)
        self.assertTrue(any(any(x.venue=="RAYDIUM_CPMM" for x in r) for r in rows))
    def test_same_pool_not_reused(self):
        E=q.Edge;ident=lambda x:x;w=q.m.c.WSOL
        edges=[E("X","P",w,"A",ident),E("X","P","A",w,ident)]
        self.assertEqual(q.enumerate_cycles(edges,4),[])
    def test_no_execution(self):
        self.assertFalse(q.EXECUTION_AUTHORITY);self.assertTrue(q.PAPER_ONLY)

if __name__=="__main__":unittest.main(verbosity=2)
