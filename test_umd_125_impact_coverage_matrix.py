from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_121_impact_family_projection import FamilyImpact,FamilyImpactProjection
from qseries_v2.universal_market_discovery.umd_124_cross_venue_cohort import MarketVenueCohort,CrossVenueImpactCohort
from qseries_v2.universal_market_discovery.umd_125_impact_coverage_matrix import *

FIXED=datetime(2026,8,9,22,10,tzinfo=timezone.utc)

def family_projection():
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-121",revision="UMD_121_IMPACT_FAMILY_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://125/121",),created_at=FIXED)
    return FamilyImpactProjection(
        "a"*64,
        (
            FamilyImpact("asset=bitcoin","b"*64,("m1","m2"),("m1",),("m2",)),
            FamilyImpact("asset=ethereum","c"*64,("m3",),("m3",),()),
        ),
        (),
        l,
    )

def cohort():
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-124",revision="UMD_124_CROSS_VENUE_IMPACT_COHORT_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://125/124",),created_at=FIXED)
    return CrossVenueImpactCohort(
        "a"*64,
        (
            MarketVenueCohort("m1",("kalshi","polymarket"),(("kalshi","K-1"),("polymarket","P-1")),True),
            MarketVenueCohort("m2",("kalshi",),(("kalshi","K-2"),),False),
            MarketVenueCohort("m3",("polymarket",),(("polymarket","P-3"),),True),
        ),
        l,
    )

def lineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-125",revision=UMD_125_REVISION,
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://125",),created_at=FIXED)

class TestUMD125(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_125_impact_coverage_matrix())
    def test_family_matrix(self):
        m=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())
        self.assertEqual(m.markets_for_family("asset=bitcoin"),("m1","m2"))
    def test_venue_matrix(self):
        m=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())
        self.assertEqual(m.markets_for_venue("kalshi"),("m1","m2"))
        self.assertEqual(m.markets_for_venue("polymarket"),("m1","m3"))
    def test_cross_venue_markets(self):
        m=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())
        self.assertEqual(m.cross_venue_market_ids,("m1",))
    def test_direct_propagated(self):
        m=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())
        self.assertEqual(m.direct_market_ids,("m1","m3"))
        self.assertEqual(m.propagated_market_ids,("m2",))
    def test_mismatch_rejected(self):
        c=cohort()
        wrong=CrossVenueImpactCohort("b"*64,c.markets,c.lineage)
        with self.assertRaises(ValueError):
            ImpactCoverageMatrixBuilder().build(family_projection(),wrong,lineage=lineage())
    def test_deterministic(self):
        a=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())
        b=ImpactCoverageMatrixBuilder().build(family_projection(),cohort(),lineage=lineage())
        self.assertEqual(a.matrix_hash,b.matrix_hash)
    def test_side_effects(self):
        m=build_umd_125_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-125 CERTIFICATION TEST");print(" IMPACT COVERAGE MATRIX");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD125))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_125_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation coverage matrix across families and venues certified")
    print("[PASS] Cross-venue, direct, and propagated market coverage certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-125 CERTIFIED")
