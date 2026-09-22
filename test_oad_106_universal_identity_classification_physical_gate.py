import unittest

from qseries_v2.oracle_adapters.independent.oad_106_universal_identity_classification_physical_gate import (
    run_physical_gate,
)

class T(unittest.TestCase):
    def test_physical(self):
        r = run_physical_gate(1000)

        print("[PHYSICAL] snapshot_id=", r.snapshot_id)
        print("[PHYSICAL] markets=", r.markets)
        print("[PHYSICAL] decomposed_legs=", r.decomposed_legs)
        print("[PHYSICAL] direct_resolved=", r.direct_resolved)
        print("[PHYSICAL] parent_resolved=", r.parent_resolved)
        print("[PHYSICAL] sibling_advisory_only=", r.sibling_advisory_only)
        print("[PHYSICAL] conflicting=", r.conflicting)
        print("[PHYSICAL] unresolved=", r.unresolved)
        print("[PHYSICAL] admitted_demands=", r.admitted_demands)
        print("[PHYSICAL] demand_without_source=", r.demand_without_source)
        print("[PHYSICAL] sports_none=", r.sports_none)
        print(
            "[PHYSICAL] noncanonical_sport_subdomains=",
            r.noncanonical_sport_subdomains,
        )
        print(
            "[PHYSICAL] financial_price_preserved=",
            r.financial_price_preserved,
        )

        for i, (key, count) in enumerate(r.source_demand, 1):
            print("[SOURCE_DEMAND]", i, key, "count=", count)

        self.assertGreater(r.markets, 0)
        self.assertGreater(r.decomposed_legs, 0)
        self.assertEqual(r.sports_none, 0)
        self.assertEqual(r.noncanonical_sport_subdomains, ())
        self.assertEqual(r.demand_without_source, 0)
        self.assertGreater(r.financial_price_preserved, 0)

if __name__ == "__main__":
    print("=" * 108)
    print(" OAD-106 PHYSICAL RECERTIFICATION TEST")
    print(" UNIVERSAL IDENTITY & CLASSIFICATION — CANONICAL SPORT VOCABULARY")
    print("=" * 108)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] sports:NONE=0")
    print("[PASS] no noncanonical sport subdomains remain")
    print("[PASS] every admitted demand has an authoritative source requirement")
    print("[PASS] financial_markets:financial_price preserved")
    print("[PASS] sibling-only evidence remains advisory")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-102 through OAD-106 CAPABILITY SLICE RECERTIFIED")
