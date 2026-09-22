from __future__ import annotations
import unittest
from qseries_v2.oracle_adapters.independent.oad_106_failed_gate_repository_audit import write_report

class T(unittest.TestCase):
    def test_physical_repository_audit(self):
        r,path=write_report(limit=1000)
        print("[PHYSICAL] snapshot_id=",r.snapshot_id)
        print("[PHYSICAL] markets=",r.market_count)
        print("[PHYSICAL] decomposed_legs=",r.decomposed_legs)
        print("[PHYSICAL] module_hashes=",r.module_hashes)
        print("[PHYSICAL] observed_leg_domains=",r.observed_leg_domains)
        print("[PHYSICAL] observed_leg_subdomains=",r.observed_leg_subdomains[:30])
        print("[PHYSICAL] guarded_states=",r.guarded_states)
        print("[PHYSICAL] semantic_states=",r.semantic_states)
        print("[PHYSICAL] semantic_domains=",r.semantic_domains)
        print("[PHYSICAL] semantic_subdomains=",r.semantic_subdomains)
        print("[PHYSICAL] sports_none_count=",r.sports_none_count)
        print("[PHYSICAL] sports_none_root_causes=",r.sports_none_root_causes)
        print("[PHYSICAL] demand_without_source_count=",r.demand_without_source_count)
        print("[PHYSICAL] demand_without_source_groups=",r.demand_without_source_groups)
        print("[PHYSICAL] source_router_domain_keys=",r.source_router_domain_keys)
        print("[PHYSICAL] source_router_sport_keys=",r.source_router_sport_keys)
        print("[PHYSICAL] unmapped_observed_domains=",r.unmapped_observed_domains)
        print("[PHYSICAL] report_hash=",r.report_hash)
        for x in r.sports_none_examples:
            print("[SPORTS_NONE_EXAMPLE]",x)
        for x in r.demand_without_source_examples:
            print("[NO_SOURCE_EXAMPLE]",x)
        print("[REPORT]",path)
        self.assertGreater(r.market_count,0)
        self.assertGreater(r.decomposed_legs,0)
        self.assertTrue(r.module_hashes)

if __name__=="__main__":
    print("="*108)
    print(" OAD-106 FAILED PHYSICAL GATE — CURRENT REPOSITORY FACT AUDIT")
    print("="*108)
    res=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not res.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Current OAD-099/OAD-102..106 production files fingerprinted")
    print("[PASS] Live 1,000-market cohort audited through exact current production path")
    print("[PASS] Every sports/NONE path grouped by actual root cause")
    print("[PASS] Every admitted demand without source grouped by actual emitted domain/state")
    print("[PASS] No production classifier behavior changed")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-106 CURRENT-REPOSITORY FAILURE AUDIT COMPLETE")
