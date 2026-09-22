from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_139_observation_merge import ObservationMerge
from qseries_v2.universal_market_discovery.umd_140_observation_cluster import ObservationCluster
from qseries_v2.universal_market_discovery.umd_141_observation_state_registry import ObservationStateRegistryBuilder
from qseries_v2.universal_market_discovery.umd_142_observation_state_snapshot import *

FIXED=datetime(2026,8,10,5,0,tzinfo=timezone.utc)

def merge(canonical,members,peers,seed):
    g=seed*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-139",revision="UMD_139_OBSERVATION_MERGE_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=(g,),source_refs=("fixture://142/139",),created_at=FIXED)
    return ObservationMerge(canonical,tuple(members),tuple(x for x in members if x!=canonical),tuple(peers),g,l)

def cluster(cid,ms):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-140",revision="UMD_140_OBSERVATION_CLUSTER_MODEL_V1",
        schema_version="1.0.0",parent_hashes=tuple(m.merge_hash for m in ms),
        source_refs=("fixture://142/140",),created_at=FIXED)
    return ObservationCluster(
        cid,
        tuple(sorted(m.canonical_observation_id for m in ms)),
        tuple(sorted({x for m in ms for x in m.member_observation_ids})),
        (),
        tuple(sorted(m.merge_hash for m in ms)),
        l,
    )

def lf141(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-141",revision="UMD_141_OBSERVATION_STATE_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://142/141",),created_at=FIXED)

def registry():
    a=merge("obs-a",("obs-a","obs-b"),("obs-c",),"a")
    c=merge("obs-c",("obs-c",),("obs-a",),"b")
    cl=cluster("cluster-1",(a,c))
    return ObservationStateRegistryBuilder().build((a,c),(cl,),lineage_factory=lf141)

def lineage(r):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-142",revision=UMD_142_REVISION,
        schema_version="1.0.0",parent_hashes=(r.registry_hash,),
        source_refs=("fixture://142",),created_at=FIXED)

class TestUMD142(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_142_observation_state_snapshot())
    def test_snapshot(self):
        r=registry()
        s=ObservationStateSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))
        self.assertEqual(s.canonical_observation_ids,("obs-a","obs-c"))
        self.assertEqual(s.cluster_ids,("cluster-1",))
        self.assertEqual(s.contradiction_pairs,(("obs-a","obs-c"),))
    def test_utc_normalization(self):
        r=registry()
        local=datetime(2026,8,10,0,0,tzinfo=timezone.utc)
        s=ObservationStateSnapshotBuilder().build(r,as_of=local,lineage=lineage(r))
        self.assertEqual(s.as_of,local)
    def test_naive_time_rejected(self):
        r=registry()
        with self.assertRaises(ValueError):
            ObservationStateSnapshotBuilder().build(r,as_of=datetime(2026,8,10,5,0),lineage=lineage(r))
    def test_lineage_required(self):
        r=registry()
        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-142",revision=UMD_142_REVISION,
            schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://142/bad",),created_at=FIXED)
        with self.assertRaises(ValueError):
            ObservationStateSnapshotBuilder().build(r,as_of=FIXED,lineage=bad)
    def test_deterministic(self):
        r=registry(); l=lineage(r)
        a=ObservationStateSnapshotBuilder().build(r,as_of=FIXED,lineage=l)
        b=ObservationStateSnapshotBuilder().build(r,as_of=FIXED,lineage=l)
        self.assertEqual(a.snapshot_hash,b.snapshot_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ObservationStateSnapshotBuilder().build(object(),as_of=FIXED,lineage=ImmutableLineage(
                subsystem_id="UMD",build_id="UMD-142",revision=UMD_142_REVISION,
                schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://142/bad",),created_at=FIXED))
    def test_side_effects(self):
        m=build_umd_142_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-142 CERTIFICATION TEST");print(" OBSERVATION STATE SNAPSHOT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD142))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_142_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Immutable timezone-aware observation state snapshots certified")
    print("[PASS] Canonical observations, clusters, and contradiction pairs captured deterministically")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-142 CERTIFIED")
