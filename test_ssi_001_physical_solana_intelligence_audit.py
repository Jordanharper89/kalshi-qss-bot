import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_001_physical_solana_intelligence_audit import audit_rows
class T(unittest.TestCase):
    def test_audit(self):
        r=audit_rows([
          {"observed_at":"2026-09-01T00:00:00Z","source_id":"source.onchain.solana.mainnet","observation_type":"price","mint":"A","price_usd":1.0,"liquidity_usd":1000},
          {"observed_at":"2026-09-01T00:00:05Z","source_id":"source.onchain.solana.mainnet","observation_type":"price","mint":"A","price_usd":1.1,"liquidity_usd":1100}])
        print("[AUDIT]",r); self.assertTrue(r["profitability_input_ready"]); self.assertFalse(r["execution_authority"])
if __name__=="__main__":
    unittest.main(verbosity=2)
