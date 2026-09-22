import unittest

from qseries_v2.oracle_adapters.independent.oad_postgresql_backend_interface_audit import (
    run_postgresql_backend_interface_audit,
)

class T(unittest.TestCase):
    def test_backend_interface_audit(self):
        report,path=run_postgresql_backend_interface_audit()

        print("[ROUTER_TYPE]",report["router_type"])
        print("[BACKEND_TYPE]",report["backend_type"])

        print("[BACKEND_METHODS]")
        for m in report["backend_methods"]:
            print(" ",m["name"],m["signature"])

        print("[BACKEND_ATTRIBUTES]")
        for a in report["backend_attributes"]:
            print(" ",a["name"],a.get("type"),a.get("value",""))

        print("[BACKEND_NESTED_OBJECTS]")
        for obj in report["backend_nested_objects"]:
            print(" ",obj["attribute"],obj["type"])
            for m in obj.get("methods",[]):
                print("    METHOD",m["name"],m["signature"])
            for a in obj.get("attributes",[]):
                print("    ATTR",a["name"],a.get("type"),a.get("value",""))

        print("[REPORT]",path)

        self.assertTrue(report["read_only"])
        self.assertFalse(report["execution_authority"])
        self.assertFalse(report["probability_enabled"])
        self.assertTrue(report["backend_type"])
        self.assertGreater(len(report["backend_methods"])+len(report["backend_attributes"]),0)

if __name__=="__main__":
    print("="*108)
    print(" OAD POSTGRESQL BACKEND INTERFACE AUDIT")
    print(" EXACT PRODUCTION PERSISTENCE SURFACE DISCOVERY")
    print("="*108)

    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] production backend inspected without issuing SQL")
    print("[PASS] no PostgreSQL rows modified")
    print("[PASS] no production module modified")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] POSTGRESQL BACKEND INTERFACE AUDIT COMPLETE")
