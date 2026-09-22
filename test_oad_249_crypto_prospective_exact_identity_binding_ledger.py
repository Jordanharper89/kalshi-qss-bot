import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_249_crypto_prospective_exact_identity_binding_ledger import canonicalize_binding
class T(unittest.TestCase):
 def test_explicit_identity(self):
  r=SimpleNamespace(observation_id="o"*64,payload={"forecast_id":"f"*64,"asset":"BTC","created_at":"2026-09-01T00:00:00+00:00","horizon_seconds":60,"training_snapshot_hash":"s"*64,"internal_forecast_probability":.6,"source_claims":(("coinbase",1,.6,True),)})
  x=canonicalize_binding(r,"crypto-exp:BTC:abc",12);p=dict(x.payload);print("[BIND]",p["forecast_id"],"->",p["experience_id"]);self.assertEqual(p["cycle_sequence"],12);self.assertFalse(x.execution_allowed)
if __name__=="__main__":
 x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not x.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-249 immutable explicit identity binding ledger certified")
