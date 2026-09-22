from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_151_change_dependency_projection import ChangeDependencyBinding,ChangeDependencyProjection
from qseries_v2.universal_market_discovery.umd_152_change_constraint_projection import ChangeConstraintBinding,ChangeConstraintProjection
from qseries_v2.universal_market_discovery.umd_153_change_dependency_context_registry import ChangeDependencyContextRegistryBuilder
from qseries_v2.universal_market_discovery.umd_157_change_co_occurrence_model import ChangeCoOccurrence,ChangeCoOccurrenceModel
from qseries_v2.universal_market_discovery.umd_158_change_convergence_projection import *

FIXED=datetime(2026,8,10,12,10,tzinfo=timezone.utc)
C1="1"*64; C2="2"*64

def co_model():
    o=ChangeCoOccurrence("m1",(C1,C2),((C1,C2),),("impacted","boundary"))
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-157",revision="UMD_157_CHANGE_CO_OCCURRENCE_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(o.occurrence_hash,),
        source_refs=("fixture://158/157",),created_at=FIXED
    )
    return ChangeCoOccurrenceModel((o,),{"m1":(C1,C2)},{C1:("m1",),C2:("m1",)},l)

def dep_proj(change,kind,key,role,seed):
    b=ChangeDependencyBinding("m1",kind,key,role,seed*64)
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-151",revision="UMD_151_CHANGE_DEPENDENCY_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(change,),
        source_refs=("fixture://158/151",),created_at=FIXED
    )
    return ChangeDependencyProjection(
        change,("m1",),(b,),{role:("m1",)},{kind+"="+key:("m1",)},(),l
    )

def con_proj(change,ctype,boundary,seed):
    b=ChangeConstraintBinding(
        "m1","m2",ctype,"basis:"+seed,True,not boundary,seed*64
    )
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-152",revision="UMD_152_CHANGE_CONSTRAINT_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(change,),
        source_refs=("fixture://158/152",),created_at=FIXED
    )
    return ChangeConstraintProjection(
        change,("m1",),(b,),
        () if boundary else (b.constraint_hash,),
        (b.constraint_hash,) if boundary else (),
        l,
    )

def dependency_context():
    d1=dep_proj(C1,"asset","bitcoin","required","a")
    d2=dep_proj(C2,"metric","cpi","supporting","b")
    k1=con_proj(C1,"implies",True,"c")
    k2=con_proj(C2,"threshold_monotonic",False,"d")
    def lf(parents):
        return ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-153",revision="UMD_153_CHANGE_DEPENDENCY_CONTEXT_REGISTRY_V1",
            schema_version="1.0.0",parent_hashes=parents,
            source_refs=("fixture://158/153",),created_at=FIXED
        )
    return ChangeDependencyContextRegistryBuilder().build((d1,d2),(k1,k2),lineage_factory=lf)

def lf158(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-158",revision=UMD_158_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://158",),created_at=FIXED
    )

class TestUMD158(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_158_change_convergence_projection())
    def test_projection(self):
        p=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158)
        self.assertEqual(len(p.convergences),1)
        c=p.convergences[0]
        self.assertEqual(c.canonical_market_id,"m1")
        self.assertEqual(c.change_hashes,(C1,C2))
    def test_dependency_context(self):
        c=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158).convergences[0]
        self.assertEqual(c.dependency_keys,("asset=bitcoin","metric=cpi"))
        self.assertEqual(c.dependency_roles,("required","supporting"))
    def test_constraint_context(self):
        c=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158).convergences[0]
        self.assertEqual(c.constraint_types,("implies","threshold_monotonic"))
    def test_boundary_context(self):
        c=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158).convergences[0]
        self.assertEqual(c.boundary_change_hashes,(C1,))
    def test_relations_preserved(self):
        c=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158).convergences[0]
        self.assertEqual(c.relation_types,("boundary","impacted"))
    def test_deterministic(self):
        a=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158)
        b=ChangeConvergenceProjector().project(co_model(),dependency_context(),lineage_factory=lf158)
        self.assertEqual(a.projection_hash,b.projection_hash)
    def test_bad_model(self):
        with self.assertRaises(TypeError):
            ChangeConvergenceProjector().project(object(),dependency_context(),lineage_factory=lf158)
    def test_side_effects(self):
        m=build_umd_158_certification_manifest()
        self.assertEqual(m["semantics"],"context_enrichment_only_no_convergence_score")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-158 CERTIFICATION TEST");print(" CHANGE CONVERGENCE PROJECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD158))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_158_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Multi-change market convergence enriched with dependency and constraint context")
    print("[PASS] No convergence score, probability, or trade-value judgment introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-158 CERTIFIED")
