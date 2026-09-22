from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import MarketSemanticProfile,SemanticFact
from qseries_v2.universal_market_discovery.umd_110_market_family_resolution import MarketFamily
from qseries_v2.universal_market_discovery.umd_111_semantic_registry import SemanticRegistry
from qseries_v2.universal_market_discovery.umd_127_market_ladder import LadderRung,MarketLadder
from qseries_v2.universal_market_discovery.umd_128_market_partition import PartitionMember,MarketPartition
from qseries_v2.universal_market_discovery.umd_129_market_topology import MarketTopologyRegistry
from qseries_v2.universal_market_discovery.umd_154_change_boundary_expansion import ChangeBoundaryNeighbor,ChangeBoundaryExpansion
from qseries_v2.universal_market_discovery.umd_155_change_structural_neighborhood import *

FIXED=datetime(2026,8,10,11,10,tzinfo=timezone.utc)
CHANGE="1"*64

def semantic_registry():
    ph1="a"*64; ph2="b"*64; ph3="c"*64
    def prof(mid,ph,value):
        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-109",revision="UMD_109_MARKET_SEMANTIC_PROFILE_V1",
            schema_version="1.0.0",parent_hashes=(ph,),source_refs=("fixture://155/109",),created_at=FIXED)
        return MarketSemanticProfile(mid,ph,(SemanticFact("asset",value,value.lower()),),l)
    p1=prof("m1",ph1,"Bitcoin"); p2=prof("m2",ph2,"Bitcoin"); p5=prof("m5",ph3,"Bitcoin")
    lf=ImmutableLineage(subsystem_id="UMD",build_id="UMD-110",revision="UMD_110_MARKET_FAMILY_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=(p1.profile_hash,p2.profile_hash,p5.profile_hash),
        source_refs=("fixture://155/110",),created_at=FIXED)
    fam=MarketFamily("asset=bitcoin",("asset",),("m1","m2","m5"),
        tuple(sorted((p1.profile_hash,p2.profile_hash,p5.profile_hash))),lf)
    l111=ImmutableLineage(subsystem_id="UMD",build_id="UMD-111",revision="UMD_111_SEMANTIC_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(p1.profile_hash,p2.profile_hash,p5.profile_hash,fam.family_hash),
        source_refs=("fixture://155/111",),created_at=FIXED)
    return SemanticRegistry((p1,p2,p5),(fam,),{"asset=bitcoin":("m1","m2","m5")},{"asset=bitcoin":("m1","m2","m5")},l111)

def topology_registry():
    p1="d"*64; p2="e"*64; p3="f"*64
    l127=ImmutableLineage(subsystem_id="UMD",build_id="UMD-127",revision="UMD_127_MARKET_LADDER_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(p1,p2,p3),source_refs=("fixture://155/127",),created_at=FIXED)
    ladder=MarketLadder("family-l","above",(
        LadderRung("m1","100","100","above",p1),
        LadderRung("m3","200","200","above",p2),
        LadderRung("m6","300","300","above",p3),
    ),l127)

    q1="1"*64; q2="2"*64
    l128=ImmutableLineage(subsystem_id="UMD",build_id="UMD-128",revision="UMD_128_MARKET_PARTITION_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(q1,q2),source_refs=("fixture://155/128",),created_at=FIXED)
    partition=MarketPartition("family-p",(
        PartitionMember("m7","no",q2),
        PartitionMember("m2","yes",q1),
    ),True,True,l128)

    l129=ImmutableLineage(subsystem_id="UMD",build_id="UMD-129",revision="UMD_129_MARKET_TOPOLOGY_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(ladder.ladder_hash,partition.partition_hash),
        source_refs=("fixture://155/129",),created_at=FIXED)
    return MarketTopologyRegistry(
        (ladder,),(partition,),
        {"m1":(ladder.ladder_hash,),"m3":(ladder.ladder_hash,),"m6":(ladder.ladder_hash,)},
        {"m2":(partition.partition_hash,),"m7":(partition.partition_hash,)},
        {"family-l":(ladder.ladder_hash,)},
        {"family-p":(partition.partition_hash,)},
        l129,
    )

def expansion():
    n=ChangeBoundaryNeighbor("m1","m3","implies","basis:x","9"*64)
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-154",revision="UMD_154_CHANGE_BOUNDARY_EXPANSION_V1",
        schema_version="1.0.0",parent_hashes=(CHANGE,),source_refs=("fixture://155/154",),created_at=FIXED)
    return ChangeBoundaryExpansion(CHANGE,("m1","m2"),("m3",),(n,),l)

def lineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-155",revision=UMD_155_REVISION,
        schema_version="1.0.0",parent_hashes=(CHANGE,),source_refs=("fixture://155",),created_at=FIXED)

class TestUMD155(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_155_change_structural_neighborhood())
    def test_neighborhood(self):
        n=ChangeStructuralNeighborhoodBuilder(semantic_registry(),topology_registry()).build(expansion(),lineage=lineage())
        self.assertEqual(n.impacted_market_ids,("m1","m2"))
        self.assertEqual(n.boundary_market_ids,("m3",))
        self.assertEqual(n.family_neighbor_ids,("m5",))
        self.assertEqual(n.topology_neighbor_ids,("m6","m7"))
        self.assertEqual(n.all_market_ids,("m1","m2","m3","m5","m6","m7"))
    def test_relation_query(self):
        n=ChangeStructuralNeighborhoodBuilder(semantic_registry(),topology_registry()).build(expansion(),lineage=lineage())
        self.assertEqual(n.markets_for_relation("topology-neighbor"),("m6","m7"))
    def test_seed_not_repeated_as_neighbor(self):
        n=ChangeStructuralNeighborhoodBuilder(semantic_registry(),topology_registry()).build(expansion(),lineage=lineage())
        self.assertFalse(set(n.family_neighbor_ids)&set(n.impacted_market_ids+n.boundary_market_ids))
        self.assertFalse(set(n.topology_neighbor_ids)&set(n.impacted_market_ids+n.boundary_market_ids))
    def test_deterministic(self):
        b=ChangeStructuralNeighborhoodBuilder(semantic_registry(),topology_registry()); e=expansion(); l=lineage()
        a=b.build(e,lineage=l); c=b.build(e,lineage=l)
        self.assertEqual(a.neighborhood_hash,c.neighborhood_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ChangeStructuralNeighborhoodBuilder(object(),topology_registry())
    def test_bad_expansion(self):
        with self.assertRaises(TypeError):
            ChangeStructuralNeighborhoodBuilder(semantic_registry(),topology_registry()).build(object(),lineage=lineage())
    def test_side_effects(self):
        m=build_umd_155_certification_manifest()
        self.assertEqual(m["semantics"],"structural_context_only_no_predicted_impact")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-155 CERTIFICATION TEST");print(" CHANGE STRUCTURAL NEIGHBORHOOD");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD155))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_155_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Impacted, boundary, family-neighbor, and topology-neighbor markets certified")
    print("[PASS] Structural neighborhood does not promote context markets to impacted status")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-155 CERTIFIED")
