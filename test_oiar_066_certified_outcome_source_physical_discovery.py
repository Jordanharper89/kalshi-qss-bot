import unittest
from pathlib import Path
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_066_certified_outcome_source_physical_discovery as m

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(m.verify_oiar_066_certified_outcome_source_physical_discovery())

    def test_physical_source(self):
        x=m.physical_probe(Path.cwd())
        self.assertEqual(x["settled_read_model_build_id"],"OLR-002")
        self.assertTrue(x["settled_normalization_proven"])
        self.assertTrue(x["pre_settlement_linkage_contract_proven"])
        self.assertIn("ticker",x["ledger_columns"])
        self.assertIn("result",x["ledger_columns"])
        self.assertIn("settlement_ts",x["ledger_columns"])
        self.assertIn("evidence_sequence_number",x["ledger_columns"])
        self.assertIn("sequence_number",x["evidence_columns"])
        self.assertTrue(x["read_only"])
        self.assertFalse(x["outcome_source_bound"])
        self.assertFalse(x["probability_enabled"])
        self.assertFalse(x["execution_authority"])

if __name__=="__main__":
    print("="*88)
    print(" OIAR-066 CERTIFICATION TEST")
    print(" CERTIFIED OUTCOME SOURCE PHYSICAL DISCOVERY")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] existing settled-outcome read model physically identified")
    print("[PASS] production learning ledger/evidence index contract physically identified")
    print("[PASS] strict pre-settlement linkage contract proven")
    print("[PASS] probability remains gated")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-066 CERTIFIED")
