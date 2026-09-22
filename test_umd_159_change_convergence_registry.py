from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_158_change_convergence_projection import ChangeConvergence,ChangeConvergenceProjection
from qseries_v2.universal_market_discovery.umd_159_change_convergence_registry import *

FIXED=datetime(2026,8,10,12,20,tzinfo=timezone.utc)
C1="1"*64; C2="2"*64; C3="3"*64

def projection(market,changes,deps,roles,constraints,relations,seed):
    conv=ChangeConvergence(
        market,tuple(changes),tuple(relations),tuple(deps),tuple(roles),
        tuple(constraints),(),seed*64
    )
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-158",revision="UMD_158_CHANGE_CONVERGENCE_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(conv.convergence_hash,),
        source_refs=("fixture://159/158",),created_at=FIXED
    )
    return ChangeConvergenceProjection((conv,),l)

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-159",revision=UMD_159_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://159",),created_at=FIXED
    )

class TestUMD159(unittest.TestCase):
    def setUp(self):
        self.p1=projection(
            "m1",(C1,C2),("asset=bitcoin",),("required",),("implies",),
            ("impacted",),"a"
        )
        self.p2=projection(
            "m2",(C2,C3),("metric=cpi",),("supporting",),("threshold_monotonic",),
            ("boundary",),"b"
        )
        self.r=ChangeConvergenceRegistryBuilder().build((self.p2,self.p1),lineage_factory=lf)

    def test_foundation(self): self.assertTrue(verify_umd_159_change_convergence_registry())
    def test_market_query(self):
        self.assertEqual(len(self.r.convergence_hashes_for_market("m1")),1)
    def test_change_query(self):
        self.assertEqual(self.r.markets_for_change(C2),("m1","m2"))
    def test_dependency_query(self):
        self.assertEqual(self.r.markets_for_dependency("asset=bitcoin"),("m1",))
    def test_role_query(self):
        self.assertEqual(self.r.markets_for_role("supporting"),("m2",))
    def test_constraint_query(self):
        self.assertEqual(self.r.markets_for_constraint_type("implies"),("m1",))
    def test_relation_query(self):
        self.assertEqual(self.r.markets_for_relation("boundary"),("m2",))
    def test_unknown(self):
        self.assertEqual(self.r.markets_for_change("9"*64),())
    def test_deterministic(self):
        x=ChangeConvergenceRegistryBuilder().build((self.p1,self.p2),lineage_factory=lf)
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_empty(self):
        x=ChangeConvergenceRegistryBuilder().build((),lineage_factory=lf)
        self.assertEqual(x.projections,())
    def test_bad_projection(self):
        with self.assertRaises(TypeError):
            ChangeConvergenceRegistryBuilder().build((object(),),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_159_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-159 CERTIFICATION TEST");print(" CHANGE CONVERGENCE REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD159))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_159_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Multi-change convergence reverse queries by market, dependency, role, constraint, and relation certified")
    print("[PASS] Convergence registry remains deterministic, structural, read-only, and non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-159 CERTIFIED")
