from __future__ import annotations
import unittest
from datetime import datetime,timezone,timedelta

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_160_convergence_snapshot import ConvergenceSnapshotRecord,ConvergenceSnapshot
from qseries_v2.universal_market_discovery.umd_161_convergence_diff import *

BASE=datetime(2026,8,10,13,10,tzinfo=timezone.utc)
C1="1"*64; C2="2"*64; C3="3"*64; C4="4"*64

def snapshot(seed,when,records):
    registry_hash=seed*64
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-160",revision="UMD_160_CONVERGENCE_SNAPSHOT_V1",
        schema_version="1.0.0",parent_hashes=(registry_hash,),
        source_refs=("fixture://161/160",),created_at=when
    )
    return ConvergenceSnapshot(when,registry_hash,tuple(records),l)

def record(market,changes,seed):
    return ConvergenceSnapshotRecord(market,(seed*64,),tuple(changes))

def lineage(a,b):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-161",revision=UMD_161_REVISION,
        schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),
        source_refs=("fixture://161",),created_at=b.as_of
    )

class TestUMD161(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_161_convergence_diff())
    def test_added_removed_markets(self):
        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))
        b=snapshot("b",BASE+timedelta(minutes=1),(record("m2",(C2,C3),"2"),))
        d=ConvergenceDiffer().diff(a,b,lineage=lineage(a,b))
        self.assertEqual(d.added_market_ids,("m2",))
        self.assertEqual(d.removed_market_ids,("m1",))
    def test_changed_convergence_membership(self):
        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))
        b=snapshot("b",BASE+timedelta(minutes=1),(record("m1",(C1,C2,C3),"2"),))
        d=ConvergenceDiffer().diff(a,b,lineage=lineage(a,b))
        self.assertEqual(len(d.changed_markets),1)
        self.assertEqual(d.changed_markets[0].added_change_hashes,(C3,))
        self.assertEqual(d.changed_markets[0].removed_change_hashes,())
    def test_removed_change_membership(self):
        a=snapshot("a",BASE,(record("m1",(C1,C2,C3),"1"),))
        b=snapshot("b",BASE+timedelta(minutes=1),(record("m1",(C1,C2),"2"),))
        d=ConvergenceDiffer().diff(a,b,lineage=lineage(a,b))
        self.assertEqual(d.changed_markets[0].removed_change_hashes,(C3,))
    def test_empty(self):
        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))
        b=snapshot("b",BASE+timedelta(minutes=1),(record("m1",(C1,C2),"2"),))
        d=ConvergenceDiffer().diff(a,b,lineage=lineage(a,b))
        self.assertTrue(d.empty)
    def test_reverse_time_rejected(self):
        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))
        b=snapshot("b",BASE-timedelta(minutes=1),(record("m1",(C1,C2),"2"),))
        with self.assertRaises(ValueError):
            ConvergenceDiffer().diff(a,b,lineage=lineage(b,a))
    def test_deterministic(self):
        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))
        b=snapshot("b",BASE+timedelta(minutes=1),(record("m1",(C1,C2,C3),"2"),))
        l=lineage(a,b)
        x=ConvergenceDiffer().diff(a,b,lineage=l)
        y=ConvergenceDiffer().diff(a,b,lineage=l)
        self.assertEqual(x.diff_hash,y.diff_hash)
    def test_bad_snapshot(self):
        a=snapshot("a",BASE,(record("m1",(C1,C2),"1"),))
        with self.assertRaises(TypeError):
            ConvergenceDiffer().diff(a,object(),lineage=ImmutableLineage(
                subsystem_id="UMD",build_id="UMD-161",revision=UMD_161_REVISION,
                schema_version="1.0.0",parent_hashes=(),
                source_refs=("fixture://161/bad",),created_at=BASE
            ))
    def test_side_effects(self):
        m=build_umd_161_certification_manifest()
        self.assertEqual(m["semantics"],"structural_convergence_change_detection_only")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-161 CERTIFICATION TEST");print(" CONVERGENCE DIFF");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD161))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_161_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Added, removed, and composition-changed market convergence certified")
    print("[PASS] Convergence evolution detected without urgency, score, or prediction")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-161 CERTIFIED")
