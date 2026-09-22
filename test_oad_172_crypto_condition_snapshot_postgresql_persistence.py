import unittest
from types import SimpleNamespace
from datetime import datetime,timezone
from qseries_v2.oracle_adapters.independent.oad_172_crypto_condition_snapshot_postgresql_persistence import (
    canonicalize_crypto_condition_state,stamp_crypto_condition_states
)
class T(unittest.TestCase):
    def test_snapshot_contract(self):
        s=SimpleNamespace(
            asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate",
            value=12.0,unit="sat/vB",condition="ELEVATED",basis="10<=sat_vb<50",
            independent_evidence=True,market_native_reference=False,
            observed_at="2026-08-29T00:00:00+00:00"
        )
        stamp=datetime(2026,8,29,1,0,0,tzinfo=timezone.utc)
        stamped=stamp_crypto_condition_states((s,),stamp)[0]
        c=canonicalize_crypto_condition_state(stamped,"test",stamp,s.observed_at)
        p=dict(c.payload)
        print("[SOURCE_ID]",c.source_id)
        print("[SNAPSHOT_AT]",p["snapshot_at"])
        print("[EVIDENCE_AT]",p["evidence_observed_at"])
        self.assertTrue(c.source_id.startswith("source.crypto.condition.btc.bitcoin."))
        self.assertEqual(c.observed_at,stamp)
        self.assertEqual(p["evidence_observed_at"],s.observed_at)
        self.assertTrue(c.read_only)
        self.assertFalse(c.execution_allowed)
        self.assertIsNone(p["direction"])
        self.assertIsNone(p["probability"])
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-172 durable crypto condition snapshot contract certified")
