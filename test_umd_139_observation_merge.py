from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_136_observation_equivalence import ObservationEquivalenceGroup
from qseries_v2.universal_market_discovery.umd_137_observation_contradiction import ObservationContradiction,ObservationContradictionSet
from qseries_v2.universal_market_discovery.umd_138_observation_relationship_registry import ObservationRelationshipRegistryBuilder
from qseries_v2.universal_market_discovery.umd_139_observation_merge import *

FIXED=datetime(2026,8,10,4,0,tzinfo=timezone.utc)

def group(sig,ids,hashes):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-136",revision="UMD_136_OBSERVATION_EQUIVALENCE_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=hashes,source_refs=("fixture://139/136",),created_at=FIXED)
    return ObservationEquivalenceGroup(sig,ids[0],ids,hashes,l)

def artifacts():
    g1=group("a"*64,("obs-a","obs-b"),("1"*64,"2"*64))
    g2=group("b"*64,("obs-c",),("3"*64,))
    l137=ImmutableLineage(subsystem_id="UMD",build_id="UMD-137",revision="UMD_137_OBSERVATION_CONTRADICTION_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(g1.group_hash,g2.group_hash),source_refs=("fixture://139/137",),created_at=FIXED)
    s=ObservationContradictionSet(
        ("obs-a","obs-b","obs-c"),
        (ObservationContradiction("obs-a","obs-c","negates","claim:x"),),
        tuple(sorted((g1.group_hash,g2.group_hash))),l137
    )
    def lf138(parents):
        return ImmutableLineage(subsystem_id="UMD",build_id="UMD-138",revision="UMD_138_OBSERVATION_RELATIONSHIP_REGISTRY_V1",
            schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://139/138",),created_at=FIXED)
    rel=ObservationRelationshipRegistryBuilder().build((g1,g2),(s,),lineage_factory=lf138)
    return (g1,g2),rel

def lf139(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-139",revision=UMD_139_REVISION,
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://139",),created_at=FIXED)

class TestUMD139(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_139_observation_merge_resolution())
    def test_equivalence_collapsed(self):
        gs,rel=artifacts()
        merges=ObservationMergeResolver(rel).resolve(gs,lineage_factory=lf139)
        m=next(x for x in merges if x.canonical_observation_id=="obs-a")
        self.assertEqual(m.member_observation_ids,("obs-a","obs-b"))
        self.assertEqual(m.equivalent_member_ids,("obs-b",))
    def test_contradiction_preserved(self):
        gs,rel=artifacts()
        merges=ObservationMergeResolver(rel).resolve(gs,lineage_factory=lf139)
        m=next(x for x in merges if x.canonical_observation_id=="obs-a")
        self.assertEqual(m.contradiction_peer_ids,("obs-c",))
    def test_singleton_merge(self):
        gs,rel=artifacts()
        merges=ObservationMergeResolver(rel).resolve(gs,lineage_factory=lf139)
        m=next(x for x in merges if x.canonical_observation_id=="obs-c")
        self.assertEqual(m.member_observation_ids,("obs-c",))
        self.assertEqual(m.equivalent_member_ids,())
    def test_deterministic(self):
        gs,rel=artifacts()
        a=ObservationMergeResolver(rel).resolve(gs,lineage_factory=lf139)
        b=ObservationMergeResolver(rel).resolve(tuple(reversed(gs)),lineage_factory=lf139)
        self.assertEqual(tuple(x.merge_hash for x in a),tuple(x.merge_hash for x in b))
    def test_bad_registry(self):
        with self.assertRaises(TypeError): ObservationMergeResolver(object())
    def test_bad_group(self):
        _,rel=artifacts()
        with self.assertRaises(TypeError): ObservationMergeResolver(rel).resolve((object(),),lineage_factory=lf139)
    def test_side_effects(self):
        m=build_umd_139_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-139 CERTIFICATION TEST");print(" OBSERVATION MERGE RESOLUTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD139))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_139_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Equivalent observations collapsed to canonical merges")
    print("[PASS] Contradiction peers preserved outside merge membership")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-139 CERTIFIED")
