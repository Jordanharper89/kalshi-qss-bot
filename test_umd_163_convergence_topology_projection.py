from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_127_market_ladder import LadderRung,MarketLadder
from qseries_v2.universal_market_discovery.umd_128_market_partition import PartitionMember,MarketPartition
from qseries_v2.universal_market_discovery.umd_129_market_topology import MarketTopologyRegistry
from qseries_v2.universal_market_discovery.umd_162_convergence_change_registry import ConvergenceChangeRecord,ConvergenceChangeRegistry
from qseries_v2.universal_market_discovery.umd_163_convergence_topology_projection import *

FIXED=datetime(2026,8,10,14,0,tzinfo=timezone.utc)

def topology():
    p1="a"*64;p2="b"*64
    l127=ImmutableLineage(subsystem_id="UMD",build_id="UMD-127",revision="UMD_127_MARKET_LADDER_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(p1,p2),source_refs=("fixture://163/127",),created_at=FIXED)
    ladder=MarketLadder("family-l","above",(
        LadderRung("m1","100","100","above",p1),
        LadderRung("m2","200","200","above",p2),
    ),l127)

    p3="c"*64;p4="d"*64
    l128=ImmutableLineage(subsystem_id="UMD",build_id="UMD-128",revision="UMD_128_MARKET_PARTITION_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(p3,p4),source_refs=("fixture://163/128",),created_at=FIXED)
    partition=MarketPartition("family-p",(
        PartitionMember("m3","no",p4),
        PartitionMember("m2","yes",p3),
    ),True,True,l128)

    l129=ImmutableLineage(subsystem_id="UMD",build_id="UMD-129",revision="UMD_129_MARKET_TOPOLOGY_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(ladder.ladder_hash,partition.partition_hash),
        source_refs=("fixture://163/129",),created_at=FIXED)
    return MarketTopologyRegistry(
        (ladder,),(partition,),
        {"m1":(ladder.ladder_hash,),"m2":(ladder.ladder_hash,)},
        {"m2":(partition.partition_hash,),"m3":(partition.partition_hash,)},
        {"family-l":(ladder.ladder_hash,)},{"family-p":(partition.partition_hash,)},l129
    )

def change_registry():
    r1=ConvergenceChangeRecord("convergence-added","m1","1"*64,(),())
    r2=ConvergenceChangeRecord("convergence-composition-changed","m2","2"*64,("3"*64,),())
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-162",revision="UMD_162_CONVERGENCE_CHANGE_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://163/162",),created_at=FIXED)
    return ConvergenceChangeRegistry((),tuple(sorted((r1,r2),key=lambda r:(r.change_type,r.canonical_market_id,r.diff_hash,r.record_hash))),
        {},{}, {},l)

def lineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-163",revision=UMD_163_REVISION,
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://163",),created_at=FIXED)

class TestUMD163(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_163_convergence_topology_projection())
    def test_projection(self):
        p=ConvergenceTopologyProjector(change_registry(),topology()).project(lineage=lineage())
        self.assertEqual(p.market_ids,("m1","m2"))
        self.assertEqual(len(p.ladder_hashes),1)
        self.assertEqual(len(p.partition_hashes),1)
    def test_change_types(self):
        p=ConvergenceTopologyProjector(change_registry(),topology()).project(lineage=lineage())
        self.assertEqual(p.market_to_change_types["m1"],("convergence-added",))
        self.assertEqual(p.market_to_change_types["m2"],("convergence-composition-changed",))
    def test_market_maps(self):
        p=ConvergenceTopologyProjector(change_registry(),topology()).project(lineage=lineage())
        self.assertIn("m1",p.market_to_ladders)
        self.assertIn("m2",p.market_to_partitions)
    def test_deterministic(self):
        projector=ConvergenceTopologyProjector(change_registry(),topology()); l=lineage()
        a=projector.project(lineage=l); b=projector.project(lineage=l)
        self.assertEqual(a.projection_hash,b.projection_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError): ConvergenceTopologyProjector(object(),topology())
    def test_side_effects(self):
        m=build_umd_163_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-163 CERTIFICATION TEST");print(" CONVERGENCE TOPOLOGY PROJECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD163))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_163_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Convergence changes projected into certified ladders and partitions")
    print("[PASS] Convergence change type preserved by canonical market")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-163 CERTIFIED")
