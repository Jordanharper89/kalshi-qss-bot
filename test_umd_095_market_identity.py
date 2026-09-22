from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer
from qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver,canonical_identity_key,build_umd_095_certification_manifest,verify_umd_095_canonical_market_identity_resolution
FIXED=datetime(2026,8,8,12,5,tzinfo=timezone.utc)
def normalized(venue="Kalshi",mid="A"):
    o=MarketObservation(venue=venue,venue_market_id=mid,title="Will BTC exceed 100K?",category="Crypto",status="Open",close_time="2026-12-31T23:59:59Z",outcomes=("Yes","No"))
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://095/94",),created_at=FIXED)
    return MarketNormalizer().normalize(o,lineage=l)
def lineage(h): return ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(h,),source_refs=("fixture://095",),created_at=FIXED)
class TestUMD095(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_095_canonical_market_identity_resolution())
    def test_same_semantics_same_identity(self):
        a=normalized("Kalshi","A"); b=normalized("Polymarket","B"); self.assertEqual(canonical_identity_key(a),canonical_identity_key(b))
    def test_resolve(self):
        a=normalized(); x=CanonicalMarketIdentityResolver().resolve(a,lineage=lineage(a.normalized_market_hash)); self.assertTrue(x.canonical_market_id.startswith("umd:market:")); self.assertEqual(x.identity_key,canonical_identity_key(a))
    def test_deterministic(self):
        a=normalized(); l=lineage(a.normalized_market_hash); r=CanonicalMarketIdentityResolver(); self.assertEqual(r.resolve(a,lineage=l).identity_hash,r.resolve(a,lineage=l).identity_hash)
    def test_lineage(self):
        a=normalized(); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)
        with self.assertRaises(ValueError): CanonicalMarketIdentityResolver().resolve(a,lineage=bad)
    def test_immutable(self):
        a=normalized(); x=CanonicalMarketIdentityResolver().resolve(a,lineage=lineage(a.normalized_market_hash));
        with self.assertRaises((FrozenInstanceError,AttributeError)): x.identity_key="x"
    def test_side_effects(self):
        m=build_umd_095_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))
if __name__=="__main__":
    print("="*72); print(" UMD-095 CERTIFICATION TEST"); print(" CANONICAL MARKET IDENTITY RESOLUTION"); print("="*72); r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD095));
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_095_certification_manifest(); print(); print(f"[PASS] Build: {m['build_id']}"); print(f"[PASS] Revision: {m['revision']}"); print(f"[PASS] Manifest hash: {m['manifest_hash']}"); print("[PASS] UMD-094 normalized markets consumed read-only"); print("[PASS] Deterministic canonical identity resolution certified"); print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-095 CERTIFIED")
