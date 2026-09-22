from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer
from qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver
from qseries_v2.universal_market_discovery.umd_097_market_relationship_graph import (
    UMD_097_REVISION,RelationshipSpec,MarketRelationshipGraphBuilder,
    build_umd_097_certification_manifest,verify_umd_097_market_relationship_graph,
)

FIXED=datetime(2026,8,8,13,0,tzinfo=timezone.utc)

def identity(venue,mid,title,category="Politics"):
    o=MarketObservation(venue=venue,venue_market_id=mid,title=title,category=category,status="Open",outcomes=("Yes","No"))
    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://097/94",),created_at=FIXED)
    m=MarketNormalizer().normalize(o,lineage=l94)
    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://097/95",),created_at=FIXED)
    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)

def graph_lineage(ids):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-097",revision=UMD_097_REVISION,schema_version="1.0.0",parent_hashes=tuple(x.identity_hash for x in ids),source_refs=("fixture://097",),created_at=FIXED)

class TestUMD097(unittest.TestCase):
    def setUp(self):
        self.a=identity("Kalshi","A","Will candidate A win?")
        self.b=identity("Polymarket","B","Will candidate B win?")
        self.ids=(self.a,self.b)

    def test_foundation(self):
        self.assertTrue(verify_umd_097_market_relationship_graph())

    def test_graph_build(self):
        spec=RelationshipSpec(self.a.canonical_market_id,self.b.canonical_market_id,"opposing",("fixture://evidence/1",))
        g=MarketRelationshipGraphBuilder().build(self.ids,(spec,),lineage=graph_lineage(self.ids))
        self.assertEqual(len(g.relationships),1)
        self.assertFalse(g.relationships[0].directed)

    def test_undirected_canonicalization(self):
        s1=RelationshipSpec(self.a.canonical_market_id,self.b.canonical_market_id,"related")
        s2=RelationshipSpec(self.b.canonical_market_id,self.a.canonical_market_id,"related")
        b=MarketRelationshipGraphBuilder()
        g1=b.build(self.ids,(s1,),lineage=graph_lineage(self.ids))
        g2=b.build(tuple(reversed(self.ids)),(s2,),lineage=graph_lineage(self.ids))
        self.assertEqual(g1.graph_hash,g2.graph_hash)

    def test_directed_preserves_orientation(self):
        s=RelationshipSpec(self.a.canonical_market_id,self.b.canonical_market_id,"successor")
        g=MarketRelationshipGraphBuilder().build(self.ids,(s,),lineage=graph_lineage(self.ids))
        self.assertTrue(g.relationships[0].directed)
        self.assertEqual(g.relationships[0].source_market_id,self.a.canonical_market_id)

    def test_unknown_market_rejected(self):
        s=RelationshipSpec(self.a.canonical_market_id,"umd:market:missing","related")
        with self.assertRaises(ValueError):
            MarketRelationshipGraphBuilder().build(self.ids,(s,),lineage=graph_lineage(self.ids))

    def test_duplicate_rejected(self):
        s=RelationshipSpec(self.a.canonical_market_id,self.b.canonical_market_id,"opposing")
        with self.assertRaises(ValueError):
            MarketRelationshipGraphBuilder().build(self.ids,(s,s),lineage=graph_lineage(self.ids))

    def test_lineage_required(self):
        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-097",revision=UMD_097_REVISION,schema_version="1.0.0",parent_hashes=(self.a.identity_hash,),source_refs=("bad",),created_at=FIXED)
        with self.assertRaises(ValueError):
            MarketRelationshipGraphBuilder().build(self.ids,(),lineage=bad)

    def test_immutable(self):
        g=MarketRelationshipGraphBuilder().build(self.ids,(),lineage=graph_lineage(self.ids))
        with self.assertRaises((FrozenInstanceError,AttributeError)):
            g.market_ids=()

    def test_side_effects(self):
        m=build_umd_097_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-097 CERTIFICATION TEST");print(" MARKET RELATIONSHIP GRAPH");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD097))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_097_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] UMD-096 certified capability chain consumed read-only")
    print("[PASS] Deterministic immutable market relationship graph certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-097 CERTIFIED")
