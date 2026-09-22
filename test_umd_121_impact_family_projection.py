from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_110_market_family_resolution import MarketFamily
from qseries_v2.universal_market_discovery.umd_119_impact_provenance import MarketImpactProvenance,ImpactProvenanceBundle
from qseries_v2.universal_market_discovery.umd_121_impact_family_projection import *

FIXED=datetime(2026,8,9,21,0,tzinfo=timezone.utc)

def bundle():
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-119",revision="UMD_119_IMPACT_PROVENANCE_BUNDLE_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://121/119",),created_at=FIXED)
    return ImpactProvenanceBundle(
        "a"*64,
        (
            MarketImpactProvenance("m1",True,(("asset","bitcoin"),),("m1",),()),
            MarketImpactProvenance("m2",False,(),("m1","m2"),("implies",)),
            MarketImpactProvenance("m3",True,(("asset","ethereum"),),("m3",),()),
        ),
        l,
    )

def family(key,members,seed):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-110",revision="UMD_110_MARKET_FAMILY_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=tuple((seed+i)*64 for i in range(len(members))) if False else tuple("a"*64 for _ in members),
        source_refs=("fixture://121/110",),created_at=FIXED)
    # Construct directly through the certified dataclass with valid member hashes and lineage.
    hashes=tuple(chr(ord("a")+i)*64 for i in range(len(members)))
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-110",revision="UMD_110_MARKET_FAMILY_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=hashes,source_refs=("fixture://121/110",),created_at=FIXED)
    return MarketFamily(key,("asset",),tuple(members),hashes,l)

def lineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-121",revision=UMD_121_REVISION,
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://121",),created_at=FIXED)

class TestUMD121(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_121_impact_family_projection())
    def test_family_projection(self):
        f1=family("asset=bitcoin",("m1","m2"),0)
        f2=family("asset=ethereum",("m3",),2)
        p=ImpactFamilyProjector().project(bundle(),(f2,f1),lineage=lineage())
        self.assertEqual(tuple(x.family_key for x in p.family_impacts),("asset=bitcoin","asset=ethereum"))
        self.assertEqual(p.markets_in_family("asset=bitcoin"),("m1","m2"))
    def test_direct_propagated_split(self):
        f1=family("asset=bitcoin",("m1","m2"),0)
        p=ImpactFamilyProjector().project(bundle(),(f1,),lineage=lineage())
        x=p.family_impacts[0]
        self.assertEqual(x.direct_market_ids,("m1",))
        self.assertEqual(x.propagated_market_ids,("m2",))
    def test_unmatched(self):
        f1=family("asset=bitcoin",("m1","m2"),0)
        p=ImpactFamilyProjector().project(bundle(),(f1,),lineage=lineage())
        self.assertEqual(p.unmatched_market_ids,("m3",))
    def test_deterministic(self):
        f1=family("asset=bitcoin",("m1","m2"),0)
        f2=family("asset=ethereum",("m3",),2)
        a=ImpactFamilyProjector().project(bundle(),(f1,f2),lineage=lineage())
        b=ImpactFamilyProjector().project(bundle(),(f2,f1),lineage=lineage())
        self.assertEqual(a.projection_hash,b.projection_hash)
    def test_bad_family(self):
        with self.assertRaises(TypeError):
            ImpactFamilyProjector().project(bundle(),(object(),),lineage=lineage())
    def test_side_effects(self):
        m=build_umd_121_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-121 CERTIFICATION TEST");print(" IMPACT FAMILY PROJECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD121))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_121_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation impact projected across semantic market families")
    print("[PASS] Direct, propagated, and unmatched family coverage certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-121 CERTIFIED")
