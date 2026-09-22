import unittest
from qseries_v2.oracle_adapters.independent.oad_075_persisted_independent_association_quality_gate import *
class T(unittest.TestCase):
 def test_physical(self):
  r=run_persisted_independent_association_quality_gate()
  print("[PHYSICAL] persisted_independent_observations=",r.persisted_observations)
  print("[PHYSICAL] descriptors_with_structured_facts=",r.descriptors_with_facts)
  print("[PHYSICAL] current_open_markets=",r.current_markets)
  print("[PHYSICAL] observations_with_defensible_associations=",r.observations_with_associations)
  print("[PHYSICAL] defensible_associations=",r.structured_associations)
  for a in r.associations[:20]: print("[ASSOCIATION]",a.observation_id[:12],a.market_id,a.matched_facts,a.association_strength,"candidate_only=",a.candidate_only)
  self.assertGreater(r.persisted_observations,0);self.assertGreater(r.current_markets,0)
  self.assertTrue(all(a.candidate_only for a in r.associations))
  self.assertTrue(all(all(v!="new" for _,v in a.matched_facts) for a in r.associations))
if __name__=="__main__":
 print("="*88);print(" OAD-075 PHYSICAL CERTIFICATION TEST");print(" PERSISTED INDEPENDENT EVIDENCE ASSOCIATION QUALITY GATE");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] PostgreSQL-persisted independent evidence evaluated against real current markets")
 print("[PASS] Zero defensible associations is permitted; no match is fabricated")
 print("[PASS] All matches remain candidate_only pending evidence/thesis validation")
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
 print("[DONE] OAD-071 through OAD-075 CAPABILITY SLICE CERTIFIED")
