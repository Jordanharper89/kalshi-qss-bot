from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import UMD_103_REVISION,CanonicalMarketRegistryBuilder
from qseries_v2.universal_market_discovery.umd_119_impact_provenance import MarketImpactProvenance,ImpactProvenanceBundle
from qseries_v2.universal_market_discovery.umd_122_impact_venue_projection import *

FIXED=datetime(2026,8,9,21,10,tzinfo=timezone.utc)

def record(cid,ih,bindings):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://122/102",),created_at=FIXED)
    return CanonicalMarketRecord(
        cid,ih,tuple(bindings),"fixture/domain/category/subcategory/type",
        "b"*64,"c"*64,(),(),"",{},l
    )

def registry():
    a=record("m1","a"*64,(VenueMarketBinding("kalshi","K-1","a"*64),VenueMarketBinding("polymarket","P-1","a"*64)))
    b=record("m2","b"*64,(VenueMarketBinding("kalshi","K-2","b"*64),))
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,
        schema_version="1.0.0",parent_hashes=(a.record_hash,b.record_hash),
        source_refs=("fixture://122/103",),created_at=FIXED)
    return CanonicalMarketRegistryBuilder().build((a,b),lineage=l)

def bundle(include_missing=False):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-119",revision="UMD_119_IMPACT_PROVENANCE_BUNDLE_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://122/119",),created_at=FIXED)
    entries=[
        MarketImpactProvenance("m1",True,(("asset","bitcoin"),),("m1",),()),
        MarketImpactProvenance("m2",False,(),("m1","m2"),("implies",)),
    ]
    if include_missing:
        entries.append(MarketImpactProvenance("missing",False,(),("m1","missing"),("implies",)))
    return ImpactProvenanceBundle("a"*64,tuple(sorted(entries,key=lambda e:e.canonical_market_id)),l)

def lineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-122",revision=UMD_122_REVISION,
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://122",),created_at=FIXED)

class TestUMD122(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_122_impact_venue_projection())
    def test_cross_venue_projection(self):
        p=ImpactVenueProjector().project(bundle(),registry(),lineage=lineage())
        self.assertEqual(p.venues(),("kalshi","polymarket"))
        self.assertEqual(len(p.bindings_for_venue("kalshi")),2)
    def test_direct_flag_preserved(self):
        p=ImpactVenueProjector().project(bundle(),registry(),lineage=lineage())
        m1=[b for b in p.bindings if b.canonical_market_id=="m1"]
        self.assertTrue(all(b.direct for b in m1))
    def test_missing_market(self):
        p=ImpactVenueProjector().project(bundle(True),registry(),lineage=lineage())
        self.assertEqual(p.missing_market_ids,("missing",))
    def test_deterministic(self):
        a=ImpactVenueProjector().project(bundle(),registry(),lineage=lineage())
        b=ImpactVenueProjector().project(bundle(),registry(),lineage=lineage())
        self.assertEqual(a.projection_hash,b.projection_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ImpactVenueProjector().project(bundle(),object(),lineage=lineage())
    def test_side_effects(self):
        m=build_umd_122_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-122 CERTIFICATION TEST");print(" IMPACT VENUE PROJECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD122))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_122_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Canonical observation impact projected across venue bindings")
    print("[PASS] Cross-venue and missing-market coverage certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-122 CERTIFIED")
