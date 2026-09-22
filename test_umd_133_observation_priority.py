from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_132_observation_routing import ObservationRoute,RoutedVenueBinding
from qseries_v2.universal_market_discovery.umd_133_observation_priority import *

FIXED=datetime(2026,8,10,0,0,tzinfo=timezone.utc)

def route():
    c="a"*64; e="b"*64
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-132",revision="UMD_132_OBSERVATION_ROUTING_V1",
        schema_version="1.0.0",parent_hashes=(c,e),
        source_refs=("fixture://133/132",),created_at=FIXED
    )
    return ObservationRoute(
        "obs-1","economics",c,e,
        (("asset","bitcoin"),("metric","consumer-price-index")),
        ("m1","m2"),
        ("asset=bitcoin","metric=consumer-price-index"),
        (
            RoutedVenueBinding("kalshi","K-1","m1"),
            RoutedVenueBinding("kalshi","K-2","m2"),
            RoutedVenueBinding("polymarket","P-1","m1"),
        ),
        (
            ("asset","bitcoin",("m1",)),
            ("metric","consumer-price-index",("m2",)),
        ),
        (("entity","unknown-entity"),),
        (),
        l,
    )

def lineage(r):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-133",revision=UMD_133_REVISION,
        schema_version="1.0.0",parent_hashes=(r.route_hash,),
        source_refs=("fixture://133",),created_at=FIXED
    )

class TestUMD133(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_133_observation_priority_profile())
    def test_profile_counts(self):
        r=route()
        p=ObservationPriorityProfiler().build(r,lineage=lineage(r))
        self.assertEqual(p.direct_dependency_count,2)
        self.assertEqual(p.canonical_market_count,2)
        self.assertEqual(p.family_count,2)
        self.assertEqual(p.venue_count,2)
        self.assertEqual(p.cross_venue_market_count,1)
        self.assertEqual(p.unresolved_entity_count,1)
    def test_structural_span(self):
        r=route()
        p=ObservationPriorityProfiler().build(r,lineage=lineage(r))
        self.assertEqual(p.structural_span,9)
    def test_deterministic(self):
        r=route(); l=lineage(r)
        a=ObservationPriorityProfiler().build(r,lineage=l)
        b=ObservationPriorityProfiler().build(r,lineage=l)
        self.assertEqual(a.profile_hash,b.profile_hash)
    def test_bad_route(self):
        with self.assertRaises(TypeError):
            ObservationPriorityProfiler().build(object(),lineage=ImmutableLineage(
                subsystem_id="UMD",build_id="UMD-133",revision=UMD_133_REVISION,
                schema_version="1.0.0",parent_hashes=(),
                source_refs=("fixture://133/bad",),created_at=FIXED
            ))
    def test_lineage_required(self):
        r=route()
        bad=ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-133",revision=UMD_133_REVISION,
            schema_version="1.0.0",parent_hashes=("0"*64,),
            source_refs=("fixture://133/bad",),created_at=FIXED
        )
        with self.assertRaises(ValueError):
            ObservationPriorityProfiler().build(r,lineage=bad)
    def test_side_effects(self):
        m=build_umd_133_certification_manifest()
        self.assertEqual(m["priority_semantics"],"structural_reach_only_not_trade_value")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-133 CERTIFICATION TEST");print(" OBSERVATION PRIORITY PROFILE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD133))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_133_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Structural observation reach profile certified")
    print("[PASS] Priority semantics explicitly exclude trading value and prediction")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-133 CERTIFIED")
