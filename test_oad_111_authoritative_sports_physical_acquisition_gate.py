import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation
from qseries_v2.oracle_adapters.independent.oad_111_authoritative_sports_physical_acquisition_gate import run_physical_gate

def obs(source_id, provider, family):
    return build_observation(
        source_id=source_id, provider=provider, sport_family=family,
        observation_type="official_game_schedule_state", subject="A at B",
        observed_at="2026-08-28T12:00:00+00:00",
        source_url="https://official.example/test", payload={"id": source_id},
    )

class T(unittest.TestCase):
    def test_gate_contract_without_network(self):
        with patch("qseries_v2.oracle_adapters.independent.oad_111_authoritative_sports_physical_acquisition_gate.fetch_mlb_schedule",
                   return_value=(obs("mlb:1","statsapi.mlb.com","baseball"),)), \
             patch("qseries_v2.oracle_adapters.independent.oad_111_authoritative_sports_physical_acquisition_gate.fetch_nhl_schedule",
                   return_value=(obs("nhl:1","api-web.nhle.com","hockey"),)):
            r=run_physical_gate(timeout_seconds=1)
        print("[TOTAL_OBSERVATIONS]",r["total_observations"])
        print("[CANONICAL_OBSERVATIONS]",r["canonical_observations"])
        print("[BRIDGE_MODULE]",r["bridge_module"])
        print("[BRIDGE_CALLABLE]",r["bridge_callable"])
        self.assertEqual(r["total_observations"],2)
        self.assertEqual(r["canonical_observations"],2)
        self.assertTrue(r["read_only"])
        self.assertFalse(r["execution_authority"])
        self.assertFalse(r["probability_enabled"])

if __name__ == "__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-111 exact bridge integration certified")
    print("[NOTE] production run_physical_gate remains physical MLB+NHL network acquisition")
