from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_165_convergence_surface_registry import ConvergenceSurfaceRegistry
from qseries_v2.universal_market_discovery.umd_168_convergence_context_registry import ConvergenceContextRegistry
from qseries_v2.universal_market_discovery.umd_169_convergence_market_profile import *

FIXED=datetime(2026,8,10,16,0,tzinfo=timezone.utc)
L="a"*64; P="b"*64

def surface():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-165",revision="UMD_165_CONVERGENCE_SURFACE_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://169/165",),created_at=FIXED
    )
    return ConvergenceSurfaceRegistry(
        (),(),
        {"m1":("convergence-added",),"m2":("convergence-composition-changed",)},
        {L:("m1","m2")},{P:("m2",)},
        {"kalshi":("m1","m2"),"polymarket":("m1",)},
        {"convergence-added":("m1",),"convergence-composition-changed":("m2",)},
        l
    )

def context():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-168",revision="UMD_168_CONVERGENCE_CONTEXT_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://169/168",),created_at=FIXED
    )
    return ConvergenceContextRegistry(
        (),(),
        {"m1":("convergence-added",),"m2":("convergence-composition-changed",)},
        {"asset=bitcoin":("m1",),"metric=cpi":("m2",)},
        {"required":("m1",),"supporting":("m2",)},
        {"implies":("m1",),"threshold_monotonic":("m2",)},
        {"impacted":("m1",),"boundary":("m2",)},
        {"convergence-added":("m1",),"convergence-composition-changed":("m2",)},
        l
    )

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-169",revision=UMD_169_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://169",),created_at=FIXED
    )

class TestUMD169(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_169_convergence_market_profile())
    def test_profile(self):
        s=ConvergenceMarketProfiler(surface(),context()).build(lineage_factory=lf)
        p=s.get("m1")
        self.assertEqual(p.change_types,("convergence-added",))
        self.assertEqual(p.ladder_hashes,(L,))
        self.assertEqual(p.venue_keys,("kalshi","polymarket"))
        self.assertEqual(p.dependency_keys,("asset=bitcoin",))
        self.assertEqual(p.constraint_types,("implies",))
    def test_second_profile(self):
        s=ConvergenceMarketProfiler(surface(),context()).build(lineage_factory=lf)
        p=s.get("m2")
        self.assertEqual(p.partition_hashes,(P,))
        self.assertEqual(p.dependency_roles,("supporting",))
        self.assertEqual(p.relation_types,("boundary",))
    def test_unknown(self):
        s=ConvergenceMarketProfiler(surface(),context()).build(lineage_factory=lf)
        self.assertIsNone(s.get("missing"))
    def test_deterministic(self):
        profiler=ConvergenceMarketProfiler(surface(),context())
        a=profiler.build(lineage_factory=lf); b=profiler.build(lineage_factory=lf)
        self.assertEqual(a.profile_set_hash,b.profile_set_hash)
    def test_bad_surface(self):
        with self.assertRaises(TypeError): ConvergenceMarketProfiler(object(),context())
    def test_mismatch_rejected(self):
        c=context()
        bad_l=ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-165",revision="UMD_165_CONVERGENCE_SURFACE_REGISTRY_V1",
            schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://169/bad",),created_at=FIXED
        )
        bad=ConvergenceSurfaceRegistry(
            (),(),{"m1":("convergence-removed",)}, {},{}, {},{"convergence-removed":("m1",)},bad_l
        )
        with self.assertRaises(ValueError):
            ConvergenceMarketProfiler(bad,c).build(lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_169_certification_manifest()
        self.assertEqual(m["semantics"],"canonical_structural_profile_no_score_probability_or_prediction")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-169 CERTIFICATION TEST");print(" CONVERGENCE MARKET PROFILE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD169))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_169_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Canonical convergence market profiles combine topology, venue, dependency, constraint, and relation context")
    print("[PASS] Surface/context convergence change-type alignment certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-169 CERTIFIED")
