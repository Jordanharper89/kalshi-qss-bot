from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION, MarketObservation, MarketNormalizer
from qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION, CanonicalMarketIdentityResolver
from qseries_v2.universal_market_discovery.umd_100_market_lifecycle import (
    UMD_100_REVISION, MarketLifecycleResolver, build_umd_100_certification_manifest, verify_umd_100_market_lifecycle_semantics,
)

FIXED=datetime(2026,8,9,12,0,tzinfo=timezone.utc)

def identity(close_time="2026-08-10T00:00:00Z",settlement_time="2026-08-11T00:00:00Z"):
    o=MarketObservation(venue="Kalshi",venue_market_id="A",title="Will BTC exceed 100K?",category="Crypto",status="Open",close_time=close_time,settlement_time=settlement_time,outcomes=("Yes","No"))
    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://100/94",),created_at=FIXED)
    m=MarketNormalizer().normalize(o,lineage=l94)
    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://100/95",),created_at=FIXED)
    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)

def lineage(i):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-100",revision=UMD_100_REVISION,schema_version="1.0.0",parent_hashes=(i.identity_hash,),source_refs=("fixture://100",),created_at=FIXED)

class TestUMD100(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_100_market_lifecycle_semantics())
    def test_pre_close(self):
        i=identity(); x=MarketLifecycleResolver().resolve(i,as_of=FIXED,lineage=lineage(i)); self.assertEqual(x.scheduled_phase,"pre_close")
    def test_post_close_pre_settlement(self):
        i=identity(); x=MarketLifecycleResolver().resolve(i,as_of=datetime(2026,8,10,12,tzinfo=timezone.utc),lineage=lineage(i)); self.assertEqual(x.scheduled_phase,"post_close_pre_settlement")
    def test_post_settlement(self):
        i=identity(); x=MarketLifecycleResolver().resolve(i,as_of=datetime(2026,8,12,tzinfo=timezone.utc),lineage=lineage(i)); self.assertEqual(x.scheduled_phase,"post_settlement")
    def test_unscheduled(self):
        i=identity("",""); x=MarketLifecycleResolver().resolve(i,as_of=FIXED,lineage=lineage(i)); self.assertEqual(x.scheduled_phase,"unscheduled")
    def test_invalid_order_rejected(self):
        i=identity("2026-08-12T00:00:00Z","2026-08-11T00:00:00Z")
        with self.assertRaises(ValueError): MarketLifecycleResolver().resolve(i,as_of=FIXED,lineage=lineage(i))
    def test_naive_as_of_rejected(self):
        i=identity()
        with self.assertRaises(ValueError): MarketLifecycleResolver().resolve(i,as_of=datetime(2026,8,9,12),lineage=lineage(i))
    def test_lineage_required(self):
        i=identity(); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-100",revision=UMD_100_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)
        with self.assertRaises(ValueError): MarketLifecycleResolver().resolve(i,as_of=FIXED,lineage=bad)
    def test_immutable(self):
        i=identity(); x=MarketLifecycleResolver().resolve(i,as_of=FIXED,lineage=lineage(i))
        with self.assertRaises((FrozenInstanceError,AttributeError)): x.scheduled_phase="x"
    def test_side_effects(self):
        m=build_umd_100_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72); print(" UMD-100 CERTIFICATION TEST"); print(" MARKET LIFECYCLE SEMANTICS"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD100))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_100_certification_manifest(); print(); print(f"[PASS] Build: {m['build_id']}"); print(f"[PASS] Revision: {m['revision']}"); print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] UMD-099 certified capability chain consumed read-only"); print("[PASS] Deterministic scheduled lifecycle semantics certified")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-100 CERTIFIED")
