import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_132_resilient_authoritative_economic_provider_isolation as m
class T(unittest.TestCase):
    def test_provider_isolation(self):
        with patch.object(m,"acquire_bls_latest_economic_observations",return_value=("b1","b2")), \
             patch.object(m,"acquire_treasury_debt_observation",side_effect=RuntimeError("tls blocked")):
            results,obs=m.acquire_resilient_authoritative_economic()
        print("[PROVIDER_STATES]",[(x.provider,x.state) for x in results])
        print("[OBSERVATIONS]",len(obs))
        self.assertEqual(len(obs),2)
        self.assertEqual(results[0].state,"AVAILABLE")
        self.assertEqual(results[1].state,"UNAVAILABLE")
        self.assertFalse(results[1].execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-132 resilient provider isolation certified")
