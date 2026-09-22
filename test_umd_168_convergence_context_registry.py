from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_166_convergence_dependency_projection import ConvergenceDependencyContext,ConvergenceDependencyProjection
from qseries_v2.universal_market_discovery.umd_167_convergence_constraint_projection import ConvergenceConstraintContext,ConvergenceConstraintProjection
from qseries_v2.universal_market_discovery.umd_168_convergence_context_registry import *

FIXED=datetime(2026,8,10,15,20,tzinfo=timezone.utc)

def dp():
    c1=ConvergenceDependencyContext("m1",("convergence-added",),("asset=bitcoin",),("required",))
    c2=ConvergenceDependencyContext("m2",("convergence-composition-changed",),("metric=cpi",),("supporting",))
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-166",revision="UMD_166_CONVERGENCE_DEPENDENCY_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(c1.context_hash,c2.context_hash),
        source_refs=("fixture://168/166",),created_at=FIXED
    )
    return ConvergenceDependencyProjection((c1,c2),l)

def cp():
    c1=ConvergenceConstraintContext("m1",("convergence-added",),("implies",),("impacted",))
    c2=ConvergenceConstraintContext("m2",("convergence-composition-changed",),("threshold_monotonic",),("boundary",))
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-167",revision="UMD_167_CONVERGENCE_CONSTRAINT_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(c1.context_hash,c2.context_hash),
        source_refs=("fixture://168/167",),created_at=FIXED
    )
    return ConvergenceConstraintProjection((c1,c2),l)

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-168",revision=UMD_168_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://168",),created_at=FIXED
    )

class TestUMD168(unittest.TestCase):
    def setUp(self):
        self.r=ConvergenceContextRegistryBuilder().build((dp(),),(cp(),),lineage_factory=lf)

    def test_foundation(self): self.assertTrue(verify_umd_168_convergence_context_registry())
    def test_market_query(self):
        self.assertEqual(self.r.change_types_for_market("m1"),("convergence-added",))
    def test_dependency_query(self):
        self.assertEqual(self.r.markets_for_dependency("asset=bitcoin"),("m1",))
    def test_role_query(self):
        self.assertEqual(self.r.markets_for_role("supporting"),("m2",))
    def test_constraint_query(self):
        self.assertEqual(self.r.markets_for_constraint("implies"),("m1",))
    def test_relation_query(self):
        self.assertEqual(self.r.markets_for_relation("boundary"),("m2",))
    def test_change_type_query(self):
        self.assertEqual(self.r.markets_for_change_type("convergence-composition-changed"),("m2",))
    def test_unknown(self):
        self.assertEqual(self.r.markets_for_dependency("missing"),())
    def test_deterministic(self):
        x=ConvergenceContextRegistryBuilder().build((dp(),),(cp(),),lineage_factory=lf)
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_empty(self):
        x=ConvergenceContextRegistryBuilder().build((),(),lineage_factory=lf)
        self.assertEqual(x.dependency_projections,())
        self.assertEqual(x.constraint_projections,())
    def test_bad_projection(self):
        with self.assertRaises(TypeError):
            ConvergenceContextRegistryBuilder().build((object(),),(),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_168_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-168 CERTIFICATION TEST");print(" CONVERGENCE CONTEXT REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD168))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_168_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Convergence context queries by market, dependency, role, constraint, relation, and change type certified")
    print("[PASS] Temporal convergence now retains deterministic structural context without prediction or scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-168 CERTIFIED")
