from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_139_observation_merge import ObservationMerge
from qseries_v2.universal_market_discovery.umd_140_observation_cluster import *

FIXED=datetime(2026,8,10,4,10,tzinfo=timezone.utc)

def merge(canonical,members,peers,seed):
    g=seed*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-139",revision="UMD_139_OBSERVATION_MERGE_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=(g,),source_refs=("fixture://140/139",),created_at=FIXED)
    return ObservationMerge(
        canonical,tuple(members),tuple(x for x in members if x!=canonical),
        tuple(peers),g,l
    )

def lineage(ms):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-140",revision=UMD_140_REVISION,
        schema_version="1.0.0",parent_hashes=tuple(m.merge_hash for m in ms),
        source_refs=("fixture://140",),created_at=FIXED)

class TestUMD140(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_140_observation_cluster_model())
    def test_cluster_build(self):
        a=merge("obs-a",("obs-a","obs-b"),("obs-c",),"a")
        c=merge("obs-c",("obs-c",),("obs-a",),"b")
        x=ObservationClusterBuilder().build("cluster-1",(c,a),lineage=lineage((a,c)))
        self.assertEqual(x.canonical_observation_ids,("obs-a","obs-c"))
        self.assertEqual(x.member_observation_ids,("obs-a","obs-b","obs-c"))
    def test_contradiction_link(self):
        a=merge("obs-a",("obs-a","obs-b"),("obs-c",),"a")
        c=merge("obs-c",("obs-c",),("obs-a",),"b")
        x=ObservationClusterBuilder().build("cluster-1",(a,c),lineage=lineage((a,c)))
        self.assertEqual(x.contradiction_links,(("obs-a","obs-c"),))
    def test_external_peer_excluded(self):
        a=merge("obs-a",("obs-a",),("outside",),"a")
        x=ObservationClusterBuilder().build("cluster-1",(a,),lineage=lineage((a,)))
        self.assertEqual(x.contradiction_links,())
    def test_deterministic(self):
        a=merge("obs-a",("obs-a","obs-b"),("obs-c",),"a")
        c=merge("obs-c",("obs-c",),("obs-a",),"b")
        x=ObservationClusterBuilder().build("cluster-1",(a,c),lineage=lineage((a,c)))
        y=ObservationClusterBuilder().build("cluster-1",(c,a),lineage=lineage((a,c)))
        self.assertEqual(x.cluster_hash,y.cluster_hash)
    def test_bad_merge(self):
        with self.assertRaises(TypeError):
            ObservationClusterBuilder().build("cluster-1",(object(),),lineage=ImmutableLineage(
                subsystem_id="UMD",build_id="UMD-140",revision=UMD_140_REVISION,
                schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://140/bad",),created_at=FIXED
            ))
    def test_side_effects(self):
        m=build_umd_140_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-140 CERTIFICATION TEST");print(" OBSERVATION CLUSTER MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD140))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_140_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Canonical observation clusters and internal contradiction links certified")
    print("[PASS] External contradiction peers remain outside cluster membership")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-140 CERTIFIED")
