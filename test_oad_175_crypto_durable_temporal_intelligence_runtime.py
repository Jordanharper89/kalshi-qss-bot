import unittest
from datetime import datetime,timezone
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_175_crypto_durable_temporal_intelligence_runtime as m
def s(t,v):
    return SimpleNamespace(asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate",value=v,unit="sat/vB",condition="OBSERVED",basis="raw",independent_evidence=True,market_native_reference=False,observed_at=t)
class T(unittest.TestCase):
    def test_source_read_before_persist(self):
        order=[]; cur=s("2026-08-29T02:00:00+00:00",12); hist=s("2026-08-29T01:00:00+00:00",10)
        with patch.object(m,"build_crypto_live_multi_source_cohort",return_value=SimpleNamespace(state="FULL_COVERAGE")), \
             patch.object(m,"extract_crypto_condition_metrics",return_value=(1,)), \
             patch.object(m,"normalize_crypto_condition_states",return_value=(cur,)), \
             patch.object(m,"stamp_crypto_condition_states",return_value=(cur,)), \
             patch.object(m,"read_crypto_condition_history_for_current_states",side_effect=lambda *a,**k:(order.append("read") or SimpleNamespace(states=(hist,)))), \
             patch.object(m,"build_crypto_cross_source_consistency_profiles",return_value=(SimpleNamespace(asset="BTC",evidence_state="CROSS_SOURCE_PRESENT"),)), \
             patch.object(m,"persist_crypto_condition_snapshot",side_effect=lambda *a,**k:(order.append("persist") or SimpleNamespace(committed_new=1,exact_readback=1))):
            r=m.run_crypto_durable_temporal_intelligence(snapshot_at=datetime(2026,8,29,2,0,0,tzinfo=timezone.utc))
        print("[ORDER]",order); print("[COMPARABLE]",r.comparable_temporal_metrics)
        self.assertEqual(order,["read","persist"]); self.assertEqual(r.comparable_temporal_metrics,1)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-175 source-scoped prior read before persistence certified")
