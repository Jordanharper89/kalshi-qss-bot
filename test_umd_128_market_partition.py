from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler
from qseries_v2.universal_market_discovery.umd_110_market_family_resolution import UMD_110_REVISION,MarketFamily
from qseries_v2.universal_market_discovery.umd_128_market_partition import *

FIXED=datetime(2026,8,9,23,10,tzinfo=timezone.utc)

def profile(cid,ih,event):
    l102=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://128/102",),created_at=FIXED
    )
    r=CanonicalMarketRecord(
        cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),
        "fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l102
    )
    l109=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,
        schema_version="1.0.0",parent_hashes=(r.record_hash,),
        source_refs=("fixture://128/109",),created_at=FIXED
    )
    return MarketSemanticProfiler().build(
        r,(("market_type","Election Winner"),("event",event)),lineage=l109
    )

def family(ps):
    ordered=tuple(sorted(ps,key=lambda p:p.canonical_market_id))
    hashes=tuple(p.profile_hash for p in ordered)
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,
        schema_version="1.0.0",parent_hashes=hashes,
        source_refs=("fixture://128/110",),created_at=FIXED
    )
    return MarketFamily(
        "market_type=election-winner",
        ("market_type",),
        tuple(p.canonical_market_id for p in ordered),
        hashes,
        l,
    )

def lineage(ps):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-128",revision=UMD_128_REVISION,
        schema_version="1.0.0",parent_hashes=tuple(p.profile_hash for p in ps),
        source_refs=("fixture://128",),created_at=FIXED
    )

class TestUMD128(unittest.TestCase):
    def setUp(self):
        self.a=profile("m1","a"*64,"Candidate A")
        self.b=profile("m2","b"*64,"Candidate B")
        self.c=profile("m3","c"*64,"Candidate C")
        self.ps=(self.a,self.b,self.c)
        self.f=family(self.ps)

    def test_foundation(self): self.assertTrue(verify_umd_128_market_partition_model())
    def test_partition_build(self):
        p=MarketPartitionBuilder().build(self.f,(self.c,self.a,self.b),lineage=lineage(self.ps))
        self.assertEqual(tuple(m.outcome_key for m in p.members),("candidate-a","candidate-b","candidate-c"))
        self.assertTrue(p.mutually_exclusive)
        self.assertTrue(p.collectively_exhaustive)
    def test_outcome_lookup(self):
        p=MarketPartitionBuilder().build(self.f,self.ps,lineage=lineage(self.ps))
        self.assertEqual(p.market_for_outcome("candidate-b"),"m2")
    def test_deterministic(self):
        a=MarketPartitionBuilder().build(self.f,self.ps,lineage=lineage(self.ps))
        b=MarketPartitionBuilder().build(self.f,tuple(reversed(self.ps)),lineage=lineage(self.ps))
        self.assertEqual(a.partition_hash,b.partition_hash)
    def test_duplicate_outcome_rejected(self):
        dup=profile("m3","c"*64,"Candidate B")
        ps=(self.a,self.b,dup)
        with self.assertRaises(ValueError):
            MarketPartitionBuilder().build(family(ps),ps,lineage=lineage(ps))
    def test_incomplete_family_rejected(self):
        with self.assertRaises(ValueError):
            MarketPartitionBuilder().build(self.f,(self.a,self.b),lineage=lineage(self.ps))
    def test_side_effects(self):
        m=build_umd_128_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-128 CERTIFICATION TEST");print(" MARKET PARTITION MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD128))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_128_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Mutually exclusive and collectively exhaustive market partitions certified")
    print("[PASS] Unique outcome membership and full family coverage certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-128 CERTIFIED")
