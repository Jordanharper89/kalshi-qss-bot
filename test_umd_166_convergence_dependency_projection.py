from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_159_change_convergence_registry import ChangeConvergenceRegistry
from qseries_v2.universal_market_discovery.umd_162_convergence_change_registry import ConvergenceChangeRecord,ConvergenceChangeRegistry
from qseries_v2.universal_market_discovery.umd_166_convergence_dependency_projection import *

FIXED=datetime(2026,8,10,15,0,tzinfo=timezone.utc)

def convergence_registry():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-159",revision="UMD_159_CHANGE_CONVERGENCE_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://166/159",),created_at=FIXED
    )
    return ChangeConvergenceRegistry(
        (),{},
        {},
        {"asset=bitcoin":("m1",),"metric=cpi":("m2",)},
        {"required":("m1",),"supporting":("m2",)},
        {},
        {},
        l,
    )

def change_registry():
    r1=ConvergenceChangeRecord("convergence-added","m1","1"*64,(),())
    r2=ConvergenceChangeRecord("convergence-composition-changed","m2","2"*64,("3"*64,),())
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-162",revision="UMD_162_CONVERGENCE_CHANGE_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://166/162",),created_at=FIXED
    )
    return ConvergenceChangeRegistry(
        (),
        tuple(sorted((r1,r2),key=lambda r:(r.change_type,r.canonical_market_id,r.diff_hash,r.record_hash))),
        {},{}, {},l
    )

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-166",revision=UMD_166_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://166",),created_at=FIXED
    )

class TestUMD166(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_166_convergence_dependency_projection())
    def test_projection(self):
        p=ConvergenceDependencyProjector(convergence_registry(),change_registry()).project(lineage_factory=lf)
        self.assertEqual(tuple(c.canonical_market_id for c in p.contexts),("m1","m2"))
    def test_dependency_context(self):
        p=ConvergenceDependencyProjector(convergence_registry(),change_registry()).project(lineage_factory=lf)
        self.assertEqual(p.context_for_market("m1").dependency_keys,("asset=bitcoin",))
        self.assertEqual(p.context_for_market("m2").dependency_keys,("metric=cpi",))
    def test_role_context(self):
        p=ConvergenceDependencyProjector(convergence_registry(),change_registry()).project(lineage_factory=lf)
        self.assertEqual(p.context_for_market("m1").dependency_roles,("required",))
        self.assertEqual(p.context_for_market("m2").dependency_roles,("supporting",))
    def test_change_type_preserved(self):
        p=ConvergenceDependencyProjector(convergence_registry(),change_registry()).project(lineage_factory=lf)
        self.assertEqual(p.context_for_market("m1").convergence_change_types,("convergence-added",))
    def test_unknown(self):
        p=ConvergenceDependencyProjector(convergence_registry(),change_registry()).project(lineage_factory=lf)
        self.assertIsNone(p.context_for_market("missing"))
    def test_deterministic(self):
        projector=ConvergenceDependencyProjector(convergence_registry(),change_registry())
        a=projector.project(lineage_factory=lf); b=projector.project(lineage_factory=lf)
        self.assertEqual(a.projection_hash,b.projection_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ConvergenceDependencyProjector(object(),change_registry())
    def test_side_effects(self):
        m=build_umd_166_certification_manifest()
        self.assertEqual(m["semantics"],"dependency_context_only_no_score_or_prediction")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-166 CERTIFICATION TEST");print(" CONVERGENCE DEPENDENCY PROJECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD166))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_166_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Convergence-changing markets enriched with certified dependency keys and roles")
    print("[PASS] Dependency context remains structural, deterministic, and non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-166 CERTIFIED")
