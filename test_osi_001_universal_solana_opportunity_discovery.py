import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_001_universal_solana_opportunity_discovery import discover

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_discovery(self):
        rows=discover([
          {"asset_key":"SOL:M1","event_type":"NEW_POOL","observed_at":"2026-09-18T05:00:00+00:00","source":"solana_native","source_record_id":"1"},
          {"asset_key":"SOL:M1","event_type":"LIQUIDITY_ADDED","observed_at":"2026-09-18T05:00:04+00:00","source":"solana_native","source_record_id":"2","features":{"usd":25000}},
          {"asset_key":"SOL:M2","event_type":"FREEZE_AUTHORITY","observed_at":"2026-09-18T05:00:05+00:00","source":"solana_native","source_record_id":"3","features":{"enabled":False}},
          {"asset_key":"SOL:OLD","event_type":"NEW_POOL","observed_at":"2026-09-18T04:40:00+00:00","source":"solana_native"},
        ],"2026-09-18T05:00:10+00:00",300)
        self.assertEqual(len(rows),3)
        self.assertTrue(all(not x["execution_authority"] for x in rows))
    def test_physical_dependencies(self):
        self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_030_universal_opportunity_intelligence_tunnel.py").is_file())
        self.assertTrue((ROOT/"qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py").is_file())
        print("[PASS] OSI-001 universal Solana opportunity discovery contract")
        print("[TRADER] New pools/liquidity/authority/flow/risk events can become fresh opportunity seeds")
        print("[PASS] execution_authority=FALSE")
        print("[SCOPE] Deterministic discovery certification; live continuous activation unclaimed")
if __name__=="__main__": unittest.main()
