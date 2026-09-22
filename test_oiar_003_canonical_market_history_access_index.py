import unittest
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import (
    OIAR_003_BUILD_ID, INDEX_NAME, MARKET_ID_EXPRESSION, CanonicalMarketHistoryIndexStatus
)

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(OIAR_003_BUILD_ID,"OIAR-003")

    def test_contract(self):
        x=CanonicalMarketHistoryIndexStatus(
            INDEX_NAME,True,True,True,True,"KXTEST",250,True,True,False
        )
        self.assertTrue(x.plan_uses_index)
        self.assertFalse(x.execution_authority)

    def test_expression_contract(self):
        self.assertIn("source_market_id",MARKET_ID_EXPRESSION)
        self.assertIn("market_id",MARKET_ID_EXPRESSION)
        self.assertIn("source_symbol",MARKET_ID_EXPRESSION)

if __name__=="__main__":
    print("="*88)
    print(" OIAR-003 CERTIFICATION TEST")
    print(" CANONICAL MARKET-HISTORY ACCESS INDEX")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] market identity/index contract certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-003 CERTIFIED")
