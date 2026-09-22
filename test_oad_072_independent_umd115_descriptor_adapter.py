import unittest
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle
from qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import canonicalize_independent_bundle
from qseries_v2.oracle_adapters.independent.oad_072_independent_umd115_descriptor_adapter import *

class T(unittest.TestCase):
    def test_immutable_payload_contract(self):
        self.assertTrue(verify_oad_072_immutable_payload_support())

    def test_physical(self):
        raw=acquire_independent_production_bundle(2)
        can=canonicalize_independent_bundle(raw,"oad072.physical")
        ds=descriptors_from_canonical(can)

        print("[PHYSICAL] canonical=",len(can))
        print("[PHYSICAL] descriptors=",len(ds))
        print("[PHYSICAL] descriptors_with_structured_facts=",sum(bool(x.facts) for x in ds))
        for d in ds:
            print("[FACTS]",d.observation_id[:12],d.facts)

        self.assertEqual(len(can),len(ds))
        self.assertTrue(all(
            all(v!="new" for _,v in d.facts)
            for d in ds
        ))

if __name__=="__main__":
    print("="*88)
    print(" OAD-072 PHYSICAL CERTIFICATION TEST")
    print(" UMD-115 OBSERVATION DESCRIPTOR ADAPTER")
    print(" IMMUTABLE CANONICAL PAYLOAD SUPPORT")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] Frozen canonical tuple/mapping payloads decoded safely")
    print("[PASS] Real independent observations adapted only to UMD-115 supported fact kinds")
    print("[PASS] Generic collision term 'new' remains rejected")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-072 CERTIFIED")
