from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_151_change_dependency_projection import ChangeDependencyBinding,ChangeDependencyProjection
from qseries_v2.universal_market_discovery.umd_152_change_constraint_projection import ChangeConstraintBinding,ChangeConstraintProjection
from qseries_v2.universal_market_discovery.umd_153_change_dependency_context_registry import *

FIXED=datetime(2026,8,10,10,20,tzinfo=timezone.utc)

def dep(change,market,kind,key,role,seed):
    binding=ChangeDependencyBinding(market,kind,key,role,seed*64)
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-151",revision="UMD_151_CHANGE_DEPENDENCY_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(change,),
        source_refs=("fixture://153/151",),created_at=FIXED
    )
    return ChangeDependencyProjection(
        change,(market,),(binding,),
        {role:(market,)},{kind+"="+key:(market,)},(),l
    )

def con(change,source,target,ctype,boundary,seed):
    binding=ChangeConstraintBinding(
        source,target,ctype,"basis:"+seed,
        True,not boundary,seed*64
    )
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-152",revision="UMD_152_CHANGE_CONSTRAINT_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(change,),
        source_refs=("fixture://153/152",),created_at=FIXED
    )
    internal=() if boundary else (binding.constraint_hash,)
    boundary_hashes=(binding.constraint_hash,) if boundary else ()
    impacted=(source,) if boundary else tuple(sorted((source,target)))
    return ChangeConstraintProjection(
        change,impacted,(binding,),internal,boundary_hashes,l
    )

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-153",revision=UMD_153_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://153",),created_at=FIXED
    )

class TestUMD153(unittest.TestCase):
    def setUp(self):
        self.c1="1"*64; self.c2="2"*64
        self.d1=dep(self.c1,"m1","asset","bitcoin","required","a")
        self.d2=dep(self.c2,"m2","entity","federal-reserve","context","b")
        self.k1=con(self.c1,"m1","m3","implies",True,"c")
        self.k2=con(self.c2,"m2","m4","mutually_exclusive",False,"d")
        self.r=ChangeDependencyContextRegistryBuilder().build(
            (self.d2,self.d1),(self.k2,self.k1),lineage_factory=lf
        )

    def test_foundation(self): self.assertTrue(verify_umd_153_change_dependency_context_registry())
    def test_dependency_query(self):
        self.assertEqual(self.r.changes_for_dependency("asset","bitcoin"),(self.c1,))
    def test_role_query(self):
        self.assertEqual(self.r.changes_for_role("context"),(self.c2,))
    def test_constraint_query(self):
        self.assertEqual(self.r.changes_for_constraint_type("implies"),(self.c1,))
    def test_market_query(self):
        self.assertEqual(self.r.changes_for_market("m1"),(self.c1,))
        self.assertEqual(self.r.changes_for_market("m4"),(self.c2,))
    def test_boundary_query(self):
        self.assertEqual(self.r.boundary_changes_for_market("m1"),(self.c1,))
        self.assertEqual(self.r.boundary_changes_for_market("m2"),())
    def test_deterministic(self):
        x=ChangeDependencyContextRegistryBuilder().build(
            (self.d1,self.d2),(self.k1,self.k2),lineage_factory=lf
        )
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_empty(self):
        x=ChangeDependencyContextRegistryBuilder().build((),(),lineage_factory=lf)
        self.assertEqual(x.dependency_projections,())
        self.assertEqual(x.constraint_projections,())
    def test_bad_dependency_projection(self):
        with self.assertRaises(TypeError):
            ChangeDependencyContextRegistryBuilder().build((object(),),(),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_153_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-153 CERTIFICATION TEST");print(" CHANGE DEPENDENCY CONTEXT REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD153))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_153_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Change dependency, role, constraint, market, and boundary-context queries certified")
    print("[PASS] World-state changes now retain deterministic dependency and constraint context")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-153 CERTIFIED")
