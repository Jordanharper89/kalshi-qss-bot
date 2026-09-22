from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_161_convergence_diff import ConvergenceMarketChange,ConvergenceDiff
from qseries_v2.universal_market_discovery.umd_162_convergence_change_registry import *

FIXED=datetime(2026,8,10,13,20,tzinfo=timezone.utc)
C1="1"*64; C2="2"*64; C3="3"*64

def diff(seed,added=(),removed=(),changed=()):
    before=seed*64
    after=chr(ord(seed)+1)*64
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-161",revision="UMD_161_CONVERGENCE_DIFF_V1",
        schema_version="1.0.0",parent_hashes=(before,after),
        source_refs=("fixture://162/161",),created_at=FIXED
    )
    return ConvergenceDiff(before,after,tuple(added),tuple(removed),tuple(changed),l)

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-162",revision=UMD_162_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://162",),created_at=FIXED
    )

class TestUMD162(unittest.TestCase):
    def setUp(self):
        changed=ConvergenceMarketChange(
            "m3",(C1,C2),(C1,C2,C3),(C3,),()
        )
        self.d=diff("a",added=("m1",),removed=("m2",),changed=(changed,))
        self.r=ConvergenceChangeRegistryBuilder().build((self.d,),lineage_factory=lf)

    def test_foundation(self): self.assertTrue(verify_umd_162_convergence_change_registry())
    def test_change_types(self):
        self.assertEqual(set(r.change_type for r in self.r.records),set(CHANGE_TYPES))
    def test_market_query(self):
        self.assertEqual(len(self.r.record_hashes_for_market("m3")),1)
    def test_type_query(self):
        self.assertEqual(self.r.markets_for_type("convergence-added"),("m1",))
        self.assertEqual(self.r.markets_for_type("convergence-removed"),("m2",))
    def test_source_change_query(self):
        self.assertEqual(self.r.markets_for_source_change(C3),("m3",))
    def test_unknown(self):
        self.assertEqual(self.r.record_hashes_for_market("missing"),())
        self.assertEqual(self.r.markets_for_source_change("9"*64),())
    def test_deterministic(self):
        x=ConvergenceChangeRegistryBuilder().build((self.d,),lineage_factory=lf)
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_empty(self):
        x=ConvergenceChangeRegistryBuilder().build((),lineage_factory=lf)
        self.assertEqual(x.records,())
    def test_bad_diff(self):
        with self.assertRaises(TypeError):
            ConvergenceChangeRegistryBuilder().build((object(),),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_162_certification_manifest()
        self.assertEqual(m["change_types"],CHANGE_TYPES)
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-162 CERTIFICATION TEST");print(" CONVERGENCE CHANGE REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD162))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_162_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Added, removed, and composition-changed convergence registry queries certified")
    print("[PASS] Convergence evolution remains deterministic, read-only, structural, and non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-162 CERTIFIED")
