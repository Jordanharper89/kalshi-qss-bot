from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_139_observation_merge import ObservationMerge
from qseries_v2.universal_market_discovery.umd_140_observation_cluster import ObservationCluster
from qseries_v2.universal_market_discovery.umd_141_observation_state_registry import *

FIXED=datetime(2026,8,10,4,20,tzinfo=timezone.utc)

def merge(canonical,members,peers,seed):
    g=seed*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-139",revision="UMD_139_OBSERVATION_MERGE_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=(g,),source_refs=("fixture://141/139",),created_at=FIXED)
    return ObservationMerge(canonical,tuple(members),tuple(x for x in members if x!=canonical),tuple(peers),g,l)

def cluster(cid,ms):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-140",revision="UMD_140_OBSERVATION_CLUSTER_MODEL_V1",
        schema_version="1.0.0",parent_hashes=tuple(m.merge_hash for m in ms),
        source_refs=("fixture://141/140",),created_at=FIXED)
    return ObservationCluster(
        cid,
        tuple(sorted(m.canonical_observation_id for m in ms)),
        tuple(sorted({x for m in ms for x in m.member_observation_ids})),
        (),
        tuple(sorted(m.merge_hash for m in ms)),
        l,
    )

def lf(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-141",revision=UMD_141_REVISION,
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://141",),created_at=FIXED)

class TestUMD141(unittest.TestCase):
    def setUp(self):
        self.a=merge("obs-a",("obs-a","obs-b"),("obs-c",),"a")
        self.c=merge("obs-c",("obs-c",),("obs-a",),"b")
        self.cluster=cluster("cluster-1",(self.a,self.c))
        self.r=ObservationStateRegistryBuilder().build((self.c,self.a),(self.cluster,),lineage_factory=lf)

    def test_foundation(self): self.assertTrue(verify_umd_141_observation_state_registry())
    def test_canonical_query(self):
        self.assertEqual(self.r.canonical_for("obs-b"),"obs-a")
        self.assertEqual(self.r.canonical_for("obs-c"),"obs-c")
    def test_cluster_query(self):
        self.assertEqual(self.r.clusters_for("obs-b"),("cluster-1",))
    def test_contradiction_query(self):
        self.assertEqual(self.r.contradictions_for("obs-a"),("obs-c",))
    def test_unknown(self):
        self.assertIsNone(self.r.canonical_for("missing"))
        self.assertEqual(self.r.clusters_for("missing"),())
    def test_deterministic(self):
        x=ObservationStateRegistryBuilder().build((self.a,self.c),(self.cluster,),lineage_factory=lf)
        self.assertEqual(self.r.registry_hash,x.registry_hash)
    def test_overlap_rejected(self):
        # Valid UMD-139 merge whose canonical observation is the first sorted member.
        # It intentionally overlaps self.a on obs-b so UMD-141 must reject ownership conflict.
        other=merge("obs-b",("obs-b","obs-z"),(),"c")
        with self.assertRaises(ValueError):
            ObservationStateRegistryBuilder().build((self.a,other),(),lineage_factory=lf)
    def test_overlap_fixture_is_valid_umd139(self):
        other=merge("obs-b",("obs-b","obs-z"),(),"c")
        self.assertEqual(other.canonical_observation_id,"obs-b")
        self.assertEqual(other.member_observation_ids,("obs-b","obs-z"))

    def test_bad_cluster(self):
        with self.assertRaises(TypeError):
            ObservationStateRegistryBuilder().build((self.a,),(object(),),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_141_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-141 CERTIFICATION TEST");print(" OBSERVATION STATE REGISTRY — CORRECTION V2");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD141))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_141_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Canonical observation state and cluster membership queries certified")
    print("[PASS] Contradiction preservation and conflicting merge ownership rejection certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-141 CERTIFIED")
