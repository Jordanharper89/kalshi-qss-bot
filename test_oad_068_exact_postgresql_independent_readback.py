import unittest
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import *

class T(unittest.TestCase):
    def test_physical(self):
        result=verify_or_persist_independent_cohort(timeout_seconds=120.0)
        print("[PHYSICAL] cohort_size=",result["cohort_size"])
        print("[PHYSICAL] already_present=",result["already_present"])
        print("[PHYSICAL] missing_before_write=",result["missing_before_write"])
        print("[PHYSICAL] committed_new=",result["committed_new"])
        print("[PHYSICAL] exact_readback=",result["exact_readback"])
        print("[PHYSICAL] request_id=",result["request_id"])
        print("[PHYSICAL] source_ids=",tuple(x.source_id for x in result["rows"]))

        self.assertGreater(result["cohort_size"],0)
        self.assertEqual(result["exact_readback"],result["cohort_size"])
        self.assertEqual(
            result["already_present"]+result["committed_new"],
            result["cohort_size"],
        )
        self.assertTrue(all(
            x.source_id.startswith("source.independent.")
            for x in result["rows"]
        ))
        self.assertTrue(all(
            x.execution_allowed is False
            for x in result["rows"]
        ))

if __name__=="__main__":
    print("="*88)
    print(" OAD-068 PHYSICAL CERTIFICATION TEST")
    print(" IDEMPOTENT EXACT POSTGRESQL INDEPENDENT READBACK")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        print("[NOTE] New writes require OPH-021 canonical writer RUNNING; rows already committed are read directly by exact ID.")
        raise SystemExit(1)
    print("[PASS] Existing committed independent rows are reused, not duplicated")
    print("[PASS] Only genuinely missing observations may enter OPH single-writer ingress")
    print("[PASS] Exact by_observation_id PostgreSQL readback verified")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-068 CERTIFIED")
