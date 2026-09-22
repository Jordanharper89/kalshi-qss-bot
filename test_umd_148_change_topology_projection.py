from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_127_market_ladder import LadderRung,MarketLadder
from qseries_v2.universal_market_discovery.umd_128_market_partition import PartitionMember,MarketPartition
from qseries_v2.universal_market_discovery.umd_129_market_topology import MarketTopologyRegistry
from qseries_v2.universal_market_discovery.umd_147_observation_change_impact_registry import ObservationChangeImpactRegistry
from qseries_v2.universal_market_discovery.umd_148_change_topology_projection import *

FIXED=datetime(2026,8,10,9,0,tzinfo=timezone.utc)

def topology():
    p1="a"*64; p2="b"*64
    l127=ImmutableLineage(subsystem_id="UMD",build_id="UMD-127",revision="UMD_127_MARKET_LADDER_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(p1,p2),source_refs=("fixture://148/127",),created_at=FIXED)
    ladder=MarketLadder("family-l","above",(
        LadderRung("m1","100","100","above",p1),
        LadderRung("m2","200","200","above",p2),
    ),l127)

    p3="c"*64; p4="d"*64
    l128=ImmutableLineage(subsystem_id="UMD",build_id="UMD-128",revision="UMD_128_MARKET_PARTITION_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(p3,p4),source_refs=("fixture://148/128",),created_at=FIXED)
    partition=MarketPartition("family-p",(
        PartitionMember("m3","no",p4),
        PartitionMember("m2","yes",p3),
    ),True,True,l128)

    l129=ImmutableLineage(subsystem_id="UMD",build_id="UMD-129",revision="UMD_129_MARKET_TOPOLOGY_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(ladder.ladder_hash,partition.partition_hash),
        source_refs=("fixture://148/129",),created_at=FIXED)
    return MarketTopologyRegistry(
        (ladder,),(partition,),
        {"m1":(ladder.ladder_hash,),"m2":(ladder.ladder_hash,)},
        {"m2":(partition.partition_hash,),"m3":(partition.partition_hash,)},
        {"family-l":(ladder.ladder_hash,)},
        {"family-p":(partition.partition_hash,)},
        l129,
    )

def impacts():
    change="1"*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-147",revision="UMD_147_OBSERVATION_CHANGE_IMPACT_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://148/147",),created_at=FIXED)
    return ObservationChangeImpactRegistry((),{"m1":(change,),"m2":(change,)},{},{},l),change

def lineage(change):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-148",revision=UMD_148_REVISION,
        schema_version="1.0.0",parent_hashes=(change,),source_refs=("fixture://148",),created_at=FIXED)

class TestUMD148(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_148_change_topology_projection())
    def test_fixture_respects_umd128_order(self):
        t=topology()
        p=t.partitions[0]
        expected=tuple(sorted(
            p.members,
            key=lambda m:(m.outcome_key,m.canonical_market_id),
        ))
        self.assertEqual(p.members,expected)
        self.assertEqual(
            tuple((m.canonical_market_id,m.outcome_key) for m in p.members),
            (("m3","no"),("m2","yes")),
        )

    def test_projection(self):
        ir,ch=impacts()
        p=ChangeTopologyProjector(ir,topology()).project(ch,lineage=lineage(ch))
        self.assertEqual(p.market_ids,("m1","m2"))
        self.assertEqual(len(p.ladder_hashes),1)
        self.assertEqual(len(p.partition_hashes),1)
    def test_market_maps(self):
        ir,ch=impacts()
        p=ChangeTopologyProjector(ir,topology()).project(ch,lineage=lineage(ch))
        self.assertIn("m1",p.market_to_ladders)
        self.assertIn("m2",p.market_to_partitions)
    def test_unknown_change(self):
        ir,_=impacts()
        ch="9"*64
        p=ChangeTopologyProjector(ir,topology()).project(ch,lineage=lineage(ch))
        self.assertEqual(p.market_ids,())
        self.assertEqual(p.ladder_hashes,())
    def test_deterministic(self):
        ir,ch=impacts(); proj=ChangeTopologyProjector(ir,topology()); l=lineage(ch)
        a=proj.project(ch,lineage=l); b=proj.project(ch,lineage=l)
        self.assertEqual(a.projection_hash,b.projection_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError): ChangeTopologyProjector(object(),topology())
    def test_side_effects(self):
        m=build_umd_148_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-148 CERTIFICATION TEST");print(" CHANGE TOPOLOGY PROJECTION — CORRECTION V2");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD148))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_148_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] World-state changes projected into market ladders and partitions")
    print("[PASS] Canonical market to topology membership preserved deterministically")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-148 CERTIFIED")
