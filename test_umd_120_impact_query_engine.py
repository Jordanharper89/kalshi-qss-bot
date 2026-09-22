from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_119_impact_provenance import MarketImpactProvenance,ImpactProvenanceBundle
from qseries_v2.universal_market_discovery.umd_120_impact_query_engine import *

FIXED=datetime(2026,8,9,20,20,tzinfo=timezone.utc)

def bundle(obs_hash,market_suffix):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-119",revision="UMD_119_IMPACT_PROVENANCE_BUNDLE_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://120/119",),created_at=FIXED)
    return ImpactProvenanceBundle(
        obs_hash,
        (
            MarketImpactProvenance("direct-"+market_suffix,True,(("asset","bitcoin"),),("direct-"+market_suffix,),()),
            MarketImpactProvenance("prop-"+market_suffix,False,(),("direct-"+market_suffix,"prop-"+market_suffix),("implies",)),
        ),
        l
    )

def lineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-120",revision=UMD_120_REVISION,
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://120",),created_at=FIXED)

class TestUMD120(unittest.TestCase):
    def setUp(self):
        self.a=bundle("a"*64,"a")
        self.b=bundle("b"*64,"b")
        self.e=ImpactQueryEngine((self.b,self.a))

    def test_foundation(self): self.assertTrue(verify_umd_120_impact_query_engine())
    def test_observation_query(self):
        r=self.e.by_observation("a"*64,lineage=lineage())
        self.assertEqual(tuple(e.canonical_market_id for e in r.entries),("direct-a","prop-a"))
    def test_market_query(self):
        r=self.e.by_market("prop-b",lineage=lineage())
        self.assertEqual(tuple(e.canonical_market_id for e in r.entries),("prop-b",))
    def test_dependency_query(self):
        r=self.e.by_dependency("asset","bitcoin",lineage=lineage())
        self.assertEqual(tuple(e.canonical_market_id for e in r.entries),("direct-a","direct-b"))
    def test_direct_query(self):
        r=self.e.by_impact_type(True,lineage=lineage())
        self.assertEqual(tuple(e.canonical_market_id for e in r.entries),("direct-a","direct-b"))
    def test_propagated_query(self):
        r=self.e.by_impact_type(False,lineage=lineage())
        self.assertEqual(tuple(e.canonical_market_id for e in r.entries),("prop-a","prop-b"))
    def test_unknown(self):
        self.assertEqual(self.e.by_market("missing",lineage=lineage()).entries,())
    def test_deterministic(self):
        a=self.e.by_dependency("asset","bitcoin",lineage=lineage())
        b=self.e.by_dependency("asset","bitcoin",lineage=lineage())
        self.assertEqual(a.result_hash,b.result_hash)
    def test_bad_bundle(self):
        with self.assertRaises(TypeError):
            ImpactQueryEngine((object(),))

    def test_mixed_bundle_types_rejected(self):
        with self.assertRaises(TypeError):
            ImpactQueryEngine((self.a,object()))
    def test_side_effects(self):
        m=build_umd_120_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-120 CERTIFICATION TEST");print(" IMPACT QUERY ENGINE — CORRECTION V2");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD120))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_120_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation, market, dependency, direct, and propagated impact queries certified")
    print("[PASS] UMD-119 provenance bundles consumed read-only")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-120 CERTIFIED")
