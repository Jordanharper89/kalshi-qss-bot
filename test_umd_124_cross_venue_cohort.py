from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_122_impact_venue_projection import VenueImpactBinding,VenueImpactProjection
from qseries_v2.universal_market_discovery.umd_124_cross_venue_cohort import *

FIXED=datetime(2026,8,9,22,0,tzinfo=timezone.utc)

def projection():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-122",revision="UMD_122_IMPACT_VENUE_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://124/122",),created_at=FIXED
    )
    return VenueImpactProjection(
        "a"*64,
        (
            VenueImpactBinding("kalshi","K-1","m1",True),
            VenueImpactBinding("kalshi","K-2","m2",False),
            VenueImpactBinding("polymarket","P-1","m1",True),
        ),
        (),
        l,
    )

def lineage():
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-124",revision=UMD_124_REVISION,
        schema_version="1.0.0",parent_hashes=(),
        source_refs=("fixture://124",),created_at=FIXED
    )

class TestUMD124(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_124_cross_venue_impact_cohort())
    def test_cross_venue_market(self):
        c=CrossVenueImpactCohortBuilder().build(projection(),lineage=lineage())
        self.assertEqual(c.cross_venue_market_ids(),("m1",))
        m1=c.for_market("m1")
        self.assertTrue(m1.cross_venue)
        self.assertEqual(m1.venue_keys,("kalshi","polymarket"))
        self.assertEqual(
            m1.venue_market_ids,
            (("kalshi","K-1"),("polymarket","P-1")),
        )
    def test_single_venue_market(self):
        c=CrossVenueImpactCohortBuilder().build(projection(),lineage=lineage())
        m2=c.for_market("m2")
        self.assertFalse(m2.cross_venue)
        self.assertEqual(m2.venue_keys,("kalshi",))
        self.assertEqual(m2.venue_market_ids,(("kalshi","K-2"),))

    def test_fixture_respects_umd122_order(self):
        p=projection()
        expected=tuple(sorted(
            p.bindings,
            key=lambda b:(b.venue_key,b.venue_market_id,b.canonical_market_id,b.direct),
        ))
        self.assertEqual(p.bindings,expected)
    def test_direct_flag_preserved(self):
        c=CrossVenueImpactCohortBuilder().build(projection(),lineage=lineage())
        self.assertTrue(c.for_market("m1").direct)
        self.assertFalse(c.for_market("m2").direct)
    def test_deterministic(self):
        a=CrossVenueImpactCohortBuilder().build(projection(),lineage=lineage())
        b=CrossVenueImpactCohortBuilder().build(projection(),lineage=lineage())
        self.assertEqual(a.cohort_hash,b.cohort_hash)
    def test_bad_projection(self):
        with self.assertRaises(TypeError):
            CrossVenueImpactCohortBuilder().build(object(),lineage=lineage())
    def test_side_effects(self):
        m=build_umd_124_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-124 CERTIFICATION TEST");print(" CROSS-VENUE IMPACT COHORT — CORRECTION V2");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD124))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_124_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Canonical impacted markets grouped across venue bindings")
    print("[PASS] Cross-venue and single-venue impact cohorts certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-124 CERTIFIED")
