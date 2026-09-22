from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_113_market_constraints import MarketConstraint,MarketConstraintGraph
from qseries_v2.universal_market_discovery.umd_151_change_dependency_projection import ChangeDependencyProjection
from qseries_v2.universal_market_discovery.umd_152_change_constraint_projection import *

FIXED=datetime(2026,8,10,10,10,tzinfo=timezone.utc)
CHANGE="1"*64

def dependency_projection():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-151",revision="UMD_151_CHANGE_DEPENDENCY_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(CHANGE,),
        source_refs=("fixture://152/151",),created_at=FIXED
    )
    return ChangeDependencyProjection(CHANGE,("m1","m2"),(),{},{},(),l)

def graph():
    constraints=(
        MarketConstraint("m1","m2","implies","basis:internal"),
        MarketConstraint("m2","m3","threshold_monotonic","basis:boundary"),
        MarketConstraint("m3","m4","mutually_exclusive","basis:outside"),
    )
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-113",revision="UMD_113_MARKET_CONSTRAINT_GRAPH_V1",
        schema_version="1.0.0",parent_hashes=(),
        source_refs=("fixture://152/113",),created_at=FIXED
    )
    return MarketConstraintGraph(("m1","m2","m3","m4"),constraints,(),l)

def lineage():
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-152",revision=UMD_152_REVISION,
        schema_version="1.0.0",parent_hashes=(CHANGE,),
        source_refs=("fixture://152",),created_at=FIXED
    )

class TestUMD152(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_152_change_constraint_projection())
    def test_projection(self):
        p=ChangeConstraintProjector(graph()).project(dependency_projection(),lineage=lineage())
        self.assertEqual(len(p.constraints),2)
    def test_internal_boundary(self):
        p=ChangeConstraintProjector(graph()).project(dependency_projection(),lineage=lineage())
        self.assertEqual(len(p.internal_constraint_hashes),1)
        self.assertEqual(len(p.boundary_constraint_hashes),1)
    def test_type_query(self):
        p=ChangeConstraintProjector(graph()).project(dependency_projection(),lineage=lineage())
        self.assertEqual(len(p.constraints_of_type("implies")),1)
        self.assertEqual(len(p.constraints_of_type("mutually_exclusive")),0)
    def test_outside_constraint_excluded(self):
        p=ChangeConstraintProjector(graph()).project(dependency_projection(),lineage=lineage())
        self.assertFalse(any(c.basis=="basis:outside" for c in p.constraints))
    def test_deterministic(self):
        projector=ChangeConstraintProjector(graph()); d=dependency_projection(); l=lineage()
        a=projector.project(d,lineage=l); b=projector.project(d,lineage=l)
        self.assertEqual(a.projection_hash,b.projection_hash)
    def test_bad_graph(self):
        with self.assertRaises(TypeError): ChangeConstraintProjector(object())
    def test_bad_projection(self):
        with self.assertRaises(TypeError): ChangeConstraintProjector(graph()).project(object(),lineage=lineage())
    def test_side_effects(self):
        m=build_umd_152_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-152 CERTIFICATION TEST");print(" CHANGE CONSTRAINT PROJECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD152))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_152_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Internal and boundary market constraints for world-state changes certified")
    print("[PASS] Unrelated external constraints excluded deterministically")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-152 CERTIFIED")
