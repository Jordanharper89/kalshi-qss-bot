from __future__ import annotations
import unittest
from datetime import datetime,timezone,timedelta

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_142_observation_state_snapshot import ObservationStateSnapshot
from qseries_v2.universal_market_discovery.umd_143_observation_state_diff import *

BASE=datetime(2026,8,10,6,0,tzinfo=timezone.utc)

def snap(seed,when,obs,clusters,contra):
    registry_hash=seed*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-142",revision="UMD_142_OBSERVATION_STATE_SNAPSHOT_V1",
        schema_version="1.0.0",parent_hashes=(registry_hash,),source_refs=("fixture://143/142",),created_at=when)
    return ObservationStateSnapshot(when,registry_hash,tuple(obs),tuple(clusters),tuple(contra),l)

def lineage(a,b):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-143",revision=UMD_143_REVISION,
        schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),
        source_refs=("fixture://143",),created_at=b.as_of)

class TestUMD143(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_143_observation_state_diff())
    def test_additions(self):
        a=snap("a",BASE,("obs-a",),("c1",),())
        b=snap("b",BASE+timedelta(minutes=1),("obs-a","obs-b"),("c1","c2"),(("obs-a","obs-b"),))
        d=ObservationStateDiffer().diff(a,b,lineage=lineage(a,b))
        self.assertEqual(d.added_canonical_ids,("obs-b",))
        self.assertEqual(d.added_cluster_ids,("c2",))
        self.assertEqual(d.added_contradictions,(("obs-a","obs-b"),))
    def test_removals(self):
        a=snap("a",BASE,("obs-a","obs-b"),("c1","c2"),(("obs-a","obs-b"),))
        b=snap("b",BASE+timedelta(minutes=1),("obs-a",),("c1",),())
        d=ObservationStateDiffer().diff(a,b,lineage=lineage(a,b))
        self.assertEqual(d.removed_canonical_ids,("obs-b",))
        self.assertEqual(d.removed_cluster_ids,("c2",))
        self.assertEqual(d.removed_contradictions,(("obs-a","obs-b"),))
    def test_empty_diff(self):
        a=snap("a",BASE,("obs-a",),("c1",),())
        b=snap("b",BASE+timedelta(minutes=1),("obs-a",),("c1",),())
        d=ObservationStateDiffer().diff(a,b,lineage=lineage(a,b))
        self.assertTrue(d.empty)
    def test_reverse_time_rejected(self):
        a=snap("a",BASE,("obs-a",),(),())
        b=snap("b",BASE-timedelta(minutes=1),("obs-a",),(),())
        with self.assertRaises(ValueError):
            ObservationStateDiffer().diff(a,b,lineage=lineage(b,a))
    def test_bad_snapshot(self):
        a=snap("a",BASE,("obs-a",),(),())
        with self.assertRaises(TypeError):
            ObservationStateDiffer().diff(a,object(),lineage=ImmutableLineage(
                subsystem_id="UMD",build_id="UMD-143",revision=UMD_143_REVISION,
                schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://143/bad",),created_at=BASE))
    def test_deterministic(self):
        a=snap("a",BASE,("obs-a",),(),())
        b=snap("b",BASE+timedelta(minutes=1),("obs-a","obs-b"),(),())
        l=lineage(a,b)
        x=ObservationStateDiffer().diff(a,b,lineage=l)
        y=ObservationStateDiffer().diff(a,b,lineage=l)
        self.assertEqual(x.diff_hash,y.diff_hash)
    def test_side_effects(self):
        m=build_umd_143_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-143 CERTIFICATION TEST");print(" OBSERVATION STATE DIFF");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD143))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_143_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Added and removed observation-state structure certified")
    print("[PASS] Canonical observations, clusters, and contradiction changes diffed deterministically")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-143 CERTIFIED")
