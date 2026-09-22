from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_127_market_ladder import LadderRung,MarketLadder
from qseries_v2.universal_market_discovery.umd_128_market_partition import PartitionMember,MarketPartition
from qseries_v2.universal_market_discovery.umd_129_market_topology import *

FIXED=datetime(2026,8,9,23,20,tzinfo=timezone.utc)

def ladder():
    p1="a"*64; p2="b"*64
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-127",revision="UMD_127_MARKET_LADDER_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(p1,p2),
        source_refs=("fixture://129/127",),created_at=FIXED
    )
    return MarketLadder(
        "asset=bitcoin",
        "above",
        (
            LadderRung("m1","100000","100000","above",p1),
            LadderRung("m2","150000","150000","above",p2),
        ),
        l,
    )

def partition():
    p1="c"*64; p2="d"*64
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-128",revision="UMD_128_MARKET_PARTITION_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(p1,p2),
        source_refs=("fixture://129/128",),created_at=FIXED
    )
    return MarketPartition(
        "event=election",
        (
            PartitionMember("m3","candidate-a",p1),
            PartitionMember("m4","candidate-b",p2),
        ),
        True,
        True,
        l,
    )

def lineage_factory(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-129",revision=UMD_129_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://129",),created_at=FIXED
    )

class TestUMD129(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_129_market_topology_registry())
    def test_market_ladder_query(self):
        l=ladder(); p=partition()
        r=MarketTopologyRegistryBuilder().build((l,),(p,),lineage_factory=lineage_factory)
        self.assertEqual(r.ladders_for_market("m1"),(l.ladder_hash,))
    def test_market_partition_query(self):
        l=ladder(); p=partition()
        r=MarketTopologyRegistryBuilder().build((l,),(p,),lineage_factory=lineage_factory)
        self.assertEqual(r.partitions_for_market("m4"),(p.partition_hash,))
    def test_family_queries(self):
        l=ladder(); p=partition()
        r=MarketTopologyRegistryBuilder().build((l,),(p,),lineage_factory=lineage_factory)
        self.assertEqual(r.ladders_for_family("asset=bitcoin"),(l.ladder_hash,))
        self.assertEqual(r.partitions_for_family("event=election"),(p.partition_hash,))
    def test_unknown(self):
        r=MarketTopologyRegistryBuilder().build((ladder(),),(partition(),),lineage_factory=lineage_factory)
        self.assertEqual(r.ladders_for_market("missing"),())
    def test_deterministic(self):
        l=ladder(); p=partition()
        a=MarketTopologyRegistryBuilder().build((l,),(p,),lineage_factory=lineage_factory)
        b=MarketTopologyRegistryBuilder().build(tuple(reversed((l,))),tuple(reversed((p,))),lineage_factory=lineage_factory)
        self.assertEqual(a.registry_hash,b.registry_hash)
    def test_bad_ladder(self):
        with self.assertRaises(TypeError):
            MarketTopologyRegistryBuilder().build((object(),),(partition(),),lineage_factory=lineage_factory)
    def test_empty(self):
        r=MarketTopologyRegistryBuilder().build((),(),lineage_factory=lineage_factory)
        self.assertEqual(r.ladders,())
        self.assertEqual(r.partitions,())
    def test_side_effects(self):
        m=build_umd_129_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-129 CERTIFICATION TEST");print(" MARKET TOPOLOGY REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD129))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_129_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Ladder and partition topology registry certified")
    print("[PASS] Reverse queries by canonical market and semantic family certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-129 CERTIFIED")
