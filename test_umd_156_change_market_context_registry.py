from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_155_change_structural_neighborhood import ChangeStructuralNeighborhood
from qseries_v2.universal_market_discovery.umd_156_change_market_context_registry import *

FIXED=datetime(2026,8,10,11,20,tzinfo=timezone.utc)

def neighborhood(change,impacted,boundary,family,topology):
    all_ids=tuple(sorted(set(impacted+boundary+family+topology)))
    relation={
        "impacted":tuple(impacted),
        "boundary":tuple(boundary),
        "family-neighbor":tuple(family),
        "topology-neighbor":tuple(topology),
    }
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-155",revision="UMD_155_CHANGE_STRUCTURAL_NEIGHBORHOOD_V1",
        schema_version="1.0.0",parent_hashes=(change,),
        source_refs=("fixture://156/155",),created_at=FIXED
    )
    return ChangeStructuralNeighborhood(
        change,tuple(impacted),tuple(boundary),tuple(family),tuple(topology),
        all_ids,relation,l
    )

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-156",revision=UMD_156_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://156",),created_at=FIXED
    )

class TestUMD156(unittest.TestCase):
    def setUp(self):
        self.c1="1"*64; self.c2="2"*64
        self.n1=neighborhood(self.c1,("m1",),("m2",),("m3",),("m4",))
        self.n2=neighborhood(self.c2,("m2",),(),("m5",),("m4",))
        self.r=ChangeMarketContextRegistryBuilder().build((self.n2,self.n1),lineage_factory=lf)

    def test_foundation(self): self.assertTrue(verify_umd_156_change_market_context_registry())
    def test_market_query(self):
        self.assertEqual(self.r.changes_for_market("m4"),(self.c1,self.c2))
    def test_impacted_query(self):
        self.assertEqual(self.r.impacted_changes_for_market("m2"),(self.c2,))
    def test_boundary_query(self):
        self.assertEqual(self.r.boundary_changes_for_market("m2"),(self.c1,))
    def test_family_query(self):
        self.assertEqual(self.r.family_neighbor_changes_for_market("m3"),(self.c1,))
    def test_topology_query(self):
        self.assertEqual(self.r.topology_neighbor_changes_for_market("m4"),(self.c1,self.c2))
    def test_change_query(self):
        self.assertEqual(self.r.markets_for_change(self.c1),("m1","m2","m3","m4"))
    def test_unknown(self):
        self.assertEqual(self.r.changes_for_market("missing"),())
    def test_deterministic(self):
        x=ChangeMarketContextRegistryBuilder().build((self.n1,self.n2),lineage_factory=lf)
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_empty(self):
        x=ChangeMarketContextRegistryBuilder().build((),lineage_factory=lf)
        self.assertEqual(x.neighborhoods,())
    def test_bad_neighborhood(self):
        with self.assertRaises(TypeError):
            ChangeMarketContextRegistryBuilder().build((object(),),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_156_certification_manifest()
        self.assertEqual(m["relation_types"],RELATION_TYPES)
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-156 CERTIFICATION TEST");print(" CHANGE MARKET CONTEXT REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD156))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_156_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Change market context queries by impacted, boundary, family, and topology relation certified")
    print("[PASS] Complete structural neighborhood remains read-only and non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-156 CERTIFIED")
