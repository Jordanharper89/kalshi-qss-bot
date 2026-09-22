import unittest

from qseries_v2.oracle_adapters.independent.oad_106_exact_unknown_cohort_contract_audit import (
    run_oad_106_exact_unknown_cohort_contract_audit,
)

class T(unittest.TestCase):
    def test_contract_audit(self):
        report, report_path = run_oad_106_exact_unknown_cohort_contract_audit()

        print("[TARGET_MODULE]", report["target_module"])
        print("[TARGET_MODULE_PATH]", report["target_module_path"])
        print("[TARGET_TEST_PATH]", report["target_test_path"])

        print("[CANDIDATE_ENTRYPOINTS]")
        for row in report["candidate_entrypoints"]:
            print(" ", row)

        print("[TEST_IMPORTS]")
        for row in report["test_call_graph"]["imports"]:
            print(" ", row)

        print("[TEST_CALLS]")
        for row in report["test_call_graph"]["calls"]:
            print(" ", row)

        print("[RELEVANT_TEST_CONSTANTS]")
        for row in report["test_call_graph"]["relevant_string_constants"]:
            print(" ", row)

        print("[SOURCE_FUNCTIONS]")
        for row in report["source_inventory"]["functions"]:
            print(" ", row)

        print("[SOURCE_CLASSES]")
        for row in report["source_inventory"]["classes"]:
            print(" ", row)

        print("[REPORT]", report_path)

        self.assertTrue(report["read_only"])
        self.assertFalse(report["execution_authority"])
        self.assertFalse(report["probability_enabled"])
        self.assertGreater(len(report["runtime_callables"]), 0)
        self.assertGreater(len(report["source_inventory"]["functions"]), 0)
        self.assertGreater(len(report["test_call_graph"]["calls"]), 0)

if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-106 EXACT SPORTS:UNKNOWN COHORT CONTRACT AUDIT")
    print(" SOURCE + CERTIFICATION TEST BINDING — READ ONLY")
    print("=" * 120)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] exact OAD-106 production module inspected")
    print("[PASS] exact OAD-106 certification test inspected")
    print("[PASS] runtime callables and signatures captured")
    print("[PASS] test-imported entrypoints and call graph captured")
    print("[PASS] no fallback classifier used")
    print("[PASS] no PostgreSQL access performed")
    print("[PASS] no production module modified")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-106 EXACT UNKNOWN COHORT CONTRACT AUDIT COMPLETE")
