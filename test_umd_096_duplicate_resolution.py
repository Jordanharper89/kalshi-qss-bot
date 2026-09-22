from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer
from qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver
from qseries_v2.universal_market_discovery.umd_096_duplicate_resolution import UMD_096_REVISION,CrossVenueDuplicateResolver,build_umd_096_certification_manifest,verify_umd_096_cross_venue_duplicate_resolution
FIXED=datetime(2026,8,8,12,10,tzinfo=timezone.utc)
def identity(venue,mid,title="Will BTC exceed 100K?"):
    o=MarketObservation(venue=venue,venue_market_id=mid,title=title,category="Crypto",status="Open",close_time="2026-12-31T23:59:59Z",outcomes=("Yes","No"))
    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://096/94",),created_at=FIXED)
    m=MarketNormalizer().normalize(o,lineage=l94)
    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://096/95",),created_at=FIXED)
    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)
def lineage(ids):return ImmutableLineage(subsystem_id="UMD",build_id="UMD-096",revision=UMD_096_REVISION,schema_version="1.0.0",parent_hashes=tuple(x.identity_hash for x in ids),source_refs=("fixture://096",),created_at=FIXED)
class TestUMD096(unittest.TestCase):
    def test_foundation(self):self.assertTrue(verify_umd_096_cross_venue_duplicate_resolution())
    def test_cross_venue_duplicate(self):
        ids=(identity("Kalshi","A"),identity("Polymarket","B")); groups=CrossVenueDuplicateResolver().resolve(ids,lineage=lineage(ids)); self.assertEqual(len(groups),1); self.assertEqual(set(groups[0].venue_keys),{"kalshi","polymarket"})
    def test_same_venue_not_duplicate_group(self):
        ids=(identity("Kalshi","A"),identity("Kalshi","B")); self.assertEqual(CrossVenueDuplicateResolver().resolve(ids,lineage=lineage(ids)),())
    def test_different_market_not_grouped(self):
        ids=(identity("Kalshi","A"),identity("Polymarket","B","Will ETH exceed 10K?")); self.assertEqual(CrossVenueDuplicateResolver().resolve(ids,lineage=lineage(ids)),())
    def test_deterministic(self):
        ids=(identity("Kalshi","A"),identity("Polymarket","B")); l=lineage(ids); r=CrossVenueDuplicateResolver(); a=r.resolve(ids,lineage=l); b=r.resolve(tuple(reversed(ids)),lineage=l); self.assertEqual(a[0].group_hash,b[0].group_hash)
    def test_lineage_requires_members(self):
        ids=(identity("Kalshi","A"),identity("Polymarket","B")); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-096",revision=UMD_096_REVISION,schema_version="1.0.0",parent_hashes=(ids[0].identity_hash,),source_refs=("bad",),created_at=FIXED)
        with self.assertRaises(ValueError):CrossVenueDuplicateResolver().resolve(ids,lineage=bad)
    def test_immutable(self):
        ids=(identity("Kalshi","A"),identity("Polymarket","B")); g=CrossVenueDuplicateResolver().resolve(ids,lineage=lineage(ids))[0]
        with self.assertRaises((FrozenInstanceError,AttributeError)):g.identity_key="x"
    def test_side_effects(self):
        m=build_umd_096_certification_manifest();self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))
if __name__=="__main__":
    print("="*72);print(" UMD-096 CERTIFICATION TEST");print(" CROSS-VENUE DUPLICATE RESOLUTION");print("="*72);r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD096));
    if not r.wasSuccessful():raise SystemExit(1)
    m=build_umd_096_certification_manifest();print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}");print("[PASS] UMD-095 canonical identities consumed read-only");print("[PASS] Cross-venue duplicate grouping and deterministic primary selection certified");print("[PASS] Network, persistence, publication, and execution disabled");print("[DONE] UMD-096 CERTIFIED")
