from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_152_change_constraint_projection import ChangeConstraintBinding,ChangeConstraintProjection
from qseries_v2.universal_market_discovery.umd_154_change_boundary_expansion import *

FIXED=datetime(2026,8,10,11,0,tzinfo=timezone.utc)
CHANGE="1"*64

def projection():
    internal=ChangeConstraintBinding("m1","m2","implies","basis:internal",True,True,"a"*64)
    boundary1=ChangeConstraintBinding("m2","m3","threshold_monotonic","basis:b1",True,False,"b"*64)
    boundary2=ChangeConstraintBinding("m4","m1","mutually_exclusive","basis:b2",False,True,"c"*64)
    constraints=tuple(sorted(
        (internal,boundary1,boundary2),
        key=lambda c:(c.source_market_id,c.target_market_id,c.constraint_type,c.basis,c.constraint_hash)
    ))
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-152",revision="UMD_152_CHANGE_CONSTRAINT_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(CHANGE,),
        source_refs=("fixture://154/152",),created_at=FIXED
    )
    return ChangeConstraintProjection(
        CHANGE,("m1","m2"),constraints,
        (internal.constraint_hash,),
        tuple(sorted((boundary1.constraint_hash,boundary2.constraint_hash))),
        l,
    )

def lineage():
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-154",revision=UMD_154_REVISION,
        schema_version="1.0.0",parent_hashes=(CHANGE,),
        source_refs=("fixture://154",),created_at=FIXED
    )

class TestUMD154(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_154_change_boundary_expansion())
    def test_expansion(self):
        x=ChangeBoundaryExpander().expand(projection(),lineage=lineage())
        self.assertEqual(x.impacted_market_ids,("m1","m2"))
        self.assertEqual(x.adjacent_market_ids,("m3","m4"))
        self.assertEqual(len(x.neighbors),2)
    def test_neighbors_for(self):
        x=ChangeBoundaryExpander().expand(projection(),lineage=lineage())
        self.assertEqual(x.neighbors_for("m2"),("m3",))
        self.assertEqual(x.neighbors_for("m1"),("m4",))
    def test_internal_excluded(self):
        x=ChangeBoundaryExpander().expand(projection(),lineage=lineage())
        self.assertNotIn("m2",x.neighbors_for("m1"))
    def test_disjoint_sets(self):
        x=ChangeBoundaryExpander().expand(projection(),lineage=lineage())
        self.assertFalse(set(x.impacted_market_ids)&set(x.adjacent_market_ids))
    def test_deterministic(self):
        p=projection(); l=lineage()
        a=ChangeBoundaryExpander().expand(p,lineage=l)
        b=ChangeBoundaryExpander().expand(p,lineage=l)
        self.assertEqual(a.expansion_hash,b.expansion_hash)
    def test_bad_projection(self):
        with self.assertRaises(TypeError):
            ChangeBoundaryExpander().expand(object(),lineage=lineage())
    def test_side_effects(self):
        m=build_umd_154_certification_manifest()
        self.assertEqual(m["semantics"],"structural_adjacent_markets_only_not_predicted_impact")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-154 CERTIFICATION TEST");print(" CHANGE BOUNDARY EXPANSION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD154))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_154_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Boundary-adjacent markets identified without promoting them to impacted status")
    print("[PASS] Internal constraints excluded from boundary expansion")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-154 CERTIFIED")
