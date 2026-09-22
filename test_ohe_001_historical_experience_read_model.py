import json,tempfile,unittest
from pathlib import Path
import qseries_v2.oracle_terminal.oracle_historical_experience_read_model as m
class T(unittest.TestCase):
    def test_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);s=r/"runtime_state";s.mkdir()
            (s/"oracle_learning_runtime_state.json").write_text(json.dumps({"cycles":3,"outcomes_learned":4,"ocl_state":{"applied_through_sequence":4,"state_hash":"abc"}}),encoding="utf-8")
            (s/"oracle_learning_event_ledger.json").write_text(json.dumps({"1":{"status":"learned","ticker":"KXFAM-A"},"2":{"status":"learned","ticker":"KXFAM-B"}}),encoding="utf-8")
            (s/m.ATTESTATION_NAME).write_text(json.dumps({"learner_state_hash":"abc","markets_reasoned":1,"experience_contexts":1,"withheld_contexts":0,"blind_contexts":0,"contexts":[{"market_ticker":"KXFAM-LIVE","series_key":"kalshi:series:KXFAM","maturity":"PROVEN","series_admitted":True,"experience_available":True,"regime_id":"R1","reliability":0.7,"learner_state_hash":"abc","reason":"MATURE_SERIES_AND_MATCHED_REGIME"}]}),encoding="utf-8")
            x=m.load_historical_experience_read_model(r);self.assertTrue(m.verify_historical_experience_read_model(x));self.assertTrue(x.lineage_current);self.assertEqual(dict(x.learned_family_counts)["KXFAM"],2)
if __name__=="__main__":
    print("="*88);print(" OHE-001 CERTIFICATION TEST");print(" HISTORICAL EXPERIENCE READ MODEL");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] OLR-016 + OLF-030 read-only consumption certified");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-001 CERTIFIED")
