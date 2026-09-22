from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_159_change_convergence_registry import ChangeConvergenceRegistry
from qseries_v2.universal_market_discovery.umd_166_convergence_dependency_projection import ConvergenceDependencyContext,ConvergenceDependencyProjection
from qseries_v2.universal_market_discovery.umd_167_convergence_constraint_projection import *

FIXED=datetime(2026,8,10,15,10,tzinfo=timezone.utc)

def convergence_registry():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-159",revision="UMD_159_CHANGE_CONVERGENCE_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://167/159",),created_at=FIXED
    )
    return ChangeConvergenceRegistry(
        (),{},{},{},{},
        {"implies":("m1",),"threshold_monotonic":("m2",)},
        {"impacted":("m1",),"boundary":("m2",)},
        l,
    )

def dependency_projection():
    c1=ConvergenceDependencyContext("m1",("convergence-added",),("asset=bitcoin",),("required",))
    c2=ConvergenceDependencyContext("m2",("convergence-composition-changed",),("metric=cpi",),("supporting",))
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-166",revision="UMD_166_CONVERGENCE_DEPENDENCY_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(c1.context_hash,c2.context_hash),
        source_refs=("fixture://167/166",),created_at=FIXED
    )
    return ConvergenceDependencyProjection((c1,c2),l)

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-167",revision=UMD_167_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://167",),created_at=FIXED
    )

class TestUMD167(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_167_convergence_constraint_projection())
    def test_projection(self):
        p=ConvergenceConstraintProjector(convergence_registry()).project(dependency_projection(),lineage_factory=lf)
        self.assertEqual(tuple(c.canonical_market_id for c in p.contexts),("m1","m2"))
    def test_constraint_context(self):
        p=ConvergenceConstraintProjector(convergence_registry()).project(dependency_projection(),lineage_factory=lf)
        self.assertEqual(p.context_for_market("m1").constraint_types,("implies",))
        self.assertEqual(p.context_for_market("m2").constraint_types,("threshold_monotonic",))
    def test_relation_context(self):
        p=ConvergenceConstraintProjector(convergence_registry()).project(dependency_projection(),lineage_factory=lf)
        self.assertEqual(p.context_for_market("m1").relation_types,("impacted",))
        self.assertEqual(p.context_for_market("m2").relation_types,("boundary",))
    def test_change_type_preserved(self):
        p=ConvergenceConstraintProjector(convergence_registry()).project(dependency_projection(),lineage_factory=lf)
        self.assertEqual(p.context_for_market("m2").convergence_change_types,("convergence-composition-changed",))
    def test_unknown(self):
        p=ConvergenceConstraintProjector(convergence_registry()).project(dependency_projection(),lineage_factory=lf)
        self.assertIsNone(p.context_for_market("missing"))
    def test_deterministic(self):
        projector=ConvergenceConstraintProjector(convergence_registry()); d=dependency_projection()
        a=projector.project(d,lineage_factory=lf); b=projector.project(d,lineage_factory=lf)
        self.assertEqual(a.projection_hash,b.projection_hash)
    def test_bad_projection(self):
        with self.assertRaises(TypeError):
            ConvergenceConstraintProjector(convergence_registry()).project(object(),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_167_certification_manifest()
        self.assertEqual(m["semantics"],"constraint_and_relation_context_only_no_score_or_prediction")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-167 CERTIFICATION TEST");print(" CONVERGENCE CONSTRAINT PROJECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD167))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_167_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Convergence-changing markets enriched with certified constraint and relation context")
    print("[PASS] Constraint context remains deterministic, structural, and non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-167 CERTIFIED")
