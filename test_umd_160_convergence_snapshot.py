from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_158_change_convergence_projection import ChangeConvergence,ChangeConvergenceProjection
from qseries_v2.universal_market_discovery.umd_159_change_convergence_registry import ChangeConvergenceRegistryBuilder
from qseries_v2.universal_market_discovery.umd_160_convergence_snapshot import *

FIXED=datetime(2026,8,10,13,0,tzinfo=timezone.utc)
C1="1"*64; C2="2"*64; C3="3"*64

def projection(market,changes,seed):
    conv=ChangeConvergence(
        market,tuple(changes),("impacted",),(),(),(),(),seed*64
    )
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-158",revision="UMD_158_CHANGE_CONVERGENCE_PROJECTION_V1",
        schema_version="1.0.0",parent_hashes=(conv.convergence_hash,),
        source_refs=("fixture://160/158",),created_at=FIXED
    )
    return ChangeConvergenceProjection((conv,),l)

def registry():
    p1=projection("m1",(C1,C2),"a")
    p2=projection("m2",(C2,C3),"b")
    def lf(parents):
        return ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-159",revision="UMD_159_CHANGE_CONVERGENCE_REGISTRY_V1",
            schema_version="1.0.0",parent_hashes=parents,
            source_refs=("fixture://160/159",),created_at=FIXED
        )
    return ChangeConvergenceRegistryBuilder().build((p1,p2),lineage_factory=lf)

def lineage(r):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-160",revision=UMD_160_REVISION,
        schema_version="1.0.0",parent_hashes=(r.registry_hash,),
        source_refs=("fixture://160",),created_at=FIXED
    )

class TestUMD160(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_160_convergence_snapshot())
    def test_snapshot(self):
        r=registry()
        s=ConvergenceSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))
        self.assertEqual(tuple(x.canonical_market_id for x in s.records),("m1","m2"))
        self.assertEqual(s.record_for_market("m1").change_hashes,(C1,C2))
    def test_unknown_market(self):
        r=registry()
        s=ConvergenceSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))
        self.assertIsNone(s.record_for_market("missing"))
    def test_naive_time_rejected(self):
        r=registry()
        with self.assertRaises(ValueError):
            ConvergenceSnapshotBuilder().build(
                r,as_of=datetime(2026,8,10,13,0),lineage=lineage(r)
            )
    def test_deterministic(self):
        r=registry(); l=lineage(r)
        a=ConvergenceSnapshotBuilder().build(r,as_of=FIXED,lineage=l)
        b=ConvergenceSnapshotBuilder().build(r,as_of=FIXED,lineage=l)
        self.assertEqual(a.snapshot_hash,b.snapshot_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ConvergenceSnapshotBuilder().build(
                object(),as_of=FIXED,
                lineage=ImmutableLineage(
                    subsystem_id="UMD",build_id="UMD-160",revision=UMD_160_REVISION,
                    schema_version="1.0.0",parent_hashes=(),
                    source_refs=("fixture://160/bad",),created_at=FIXED
                )
            )
    def test_side_effects(self):
        m=build_umd_160_certification_manifest()
        self.assertEqual(m["semantics"],"point_in_time_structural_convergence_only")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-160 CERTIFICATION TEST");print(" CONVERGENCE SNAPSHOT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD160))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_160_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Immutable timezone-aware multi-change convergence snapshots certified")
    print("[PASS] Market convergence membership and contributing changes captured deterministically")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-160 CERTIFIED")
