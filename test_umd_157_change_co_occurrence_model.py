from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_155_change_structural_neighborhood import ChangeStructuralNeighborhood
from qseries_v2.universal_market_discovery.umd_156_change_market_context_registry import ChangeMarketContextRegistryBuilder
from qseries_v2.universal_market_discovery.umd_157_change_co_occurrence_model import *

FIXED=datetime(2026,8,10,12,0,tzinfo=timezone.utc)

def neighborhood(change,impacted=(),boundary=(),family=(),topology=()):
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
        source_refs=("fixture://157/155",),created_at=FIXED
    )
    return ChangeStructuralNeighborhood(
        change,tuple(impacted),tuple(boundary),tuple(family),tuple(topology),
        all_ids,relation,l
    )

def context_registry():
    c1="1"*64; c2="2"*64; c3="3"*64
    n1=neighborhood(c1,impacted=("m1",),topology=("m2",))
    n2=neighborhood(c2,boundary=("m1",),topology=("m2",))
    n3=neighborhood(c3,impacted=("m3",))
    def lf(parents):
        return ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-156",revision="UMD_156_CHANGE_MARKET_CONTEXT_REGISTRY_V1",
            schema_version="1.0.0",parent_hashes=parents,
            source_refs=("fixture://157/156",),created_at=FIXED
        )
    return ChangeMarketContextRegistryBuilder().build((n1,n2,n3),lineage_factory=lf),c1,c2,c3

def lf157(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-157",revision=UMD_157_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://157",),created_at=FIXED
    )

class TestUMD157(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_157_change_co_occurrence_model())
    def test_co_occurrence(self):
        r,c1,c2,_=context_registry()
        model=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)
        self.assertEqual(model.changes_for_market("m1"),(c1,c2))
        self.assertEqual(model.changes_for_market("m2"),(c1,c2))
        self.assertEqual(model.changes_for_market("m3"),())
    def test_pair_generation(self):
        r,c1,c2,_=context_registry()
        model=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)
        o=next(x for x in model.occurrences if x.canonical_market_id=="m1")
        self.assertEqual(o.change_pairs,((c1,c2),))
    def test_relation_union(self):
        r,_,_,_=context_registry()
        model=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)
        o=next(x for x in model.occurrences if x.canonical_market_id=="m1")
        self.assertEqual(o.relation_types,("impacted","boundary"))
    def test_change_reverse_query(self):
        r,c1,_,_=context_registry()
        model=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)
        self.assertEqual(model.markets_for_change(c1),("m1","m2"))
    def test_single_change_excluded(self):
        r,_,_,c3=context_registry()
        model=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)
        self.assertEqual(model.markets_for_change(c3),())
    def test_deterministic(self):
        r,_,_,_=context_registry()
        a=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)
        b=ChangeCoOccurrenceBuilder().build(r,lineage_factory=lf157)
        self.assertEqual(a.model_hash,b.model_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ChangeCoOccurrenceBuilder().build(object(),lineage_factory=lf157)
    def test_side_effects(self):
        m=build_umd_157_certification_manifest()
        self.assertEqual(m["semantics"],"shared_structural_context_only_no_importance_or_probability")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-157 CERTIFICATION TEST");print(" CHANGE CO-OCCURRENCE MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD157))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_157_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Multiple certified changes sharing canonical market context identified deterministically")
    print("[PASS] Co-occurrence remains structural and introduces no importance or probability score")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-157 CERTIFIED")
