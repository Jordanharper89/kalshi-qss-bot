from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_094_market_normalization import (
    UMD_094_REVISION, MarketObservation, MarketNormalizer,
    build_umd_094_certification_manifest, verify_umd_094_market_normalization_foundation,
)

FIXED = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)

def lineage(parent):
    return ImmutableLineage(subsystem_id="UMD", build_id="UMD-094", revision=UMD_094_REVISION, schema_version="1.0.0", parent_hashes=(parent,), source_refs=("fixture://umd-094",), created_at=FIXED)

class TestUMD094(unittest.TestCase):
    def observation(self):
        return MarketObservation(venue=" Kalshi ", venue_market_id="KX-BTC-001", title="  Will BTC exceed $100K?  ", category=" Crypto ", status=" Open ", outcomes=(" Yes ", "No"), source_ref="fixture://market/1", metadata={"read_only": True})
    def test_foundation(self): self.assertTrue(verify_umd_094_market_normalization_foundation())
    def test_normalization(self):
        o=self.observation(); m=MarketNormalizer().normalize(o, lineage=lineage(o.observation_hash))
        self.assertEqual(m.venue_key,"kalshi"); self.assertEqual(m.title_key,"will-btc-exceed-100k"); self.assertEqual(m.outcome_keys,("yes","no"))
    def test_deterministic(self):
        o=self.observation(); l=lineage(o.observation_hash); n=MarketNormalizer(); self.assertEqual(n.normalize(o,lineage=l).normalized_market_hash,n.normalize(o,lineage=l).normalized_market_hash)
    def test_lineage_bound(self):
        o=self.observation(); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://bad",),created_at=FIXED)
        with self.assertRaises(ValueError): MarketNormalizer().normalize(o,lineage=bad)
    def test_immutable(self):
        o=self.observation(); m=MarketNormalizer().normalize(o,lineage=lineage(o.observation_hash))
        with self.assertRaises((FrozenInstanceError,AttributeError)): m.title="x"
        with self.assertRaises(TypeError): m.metadata["x"]=1
    def test_side_effects(self):
        m=build_umd_094_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__ == "__main__":
    print("="*72); print(" UMD-094 CERTIFICATION TEST"); print(" MARKET NORMALIZATION FOUNDATION"); print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD094))
    if not result.wasSuccessful(): raise SystemExit(1)
    m=build_umd_094_certification_manifest(); print(); print(f"[PASS] Build: {m['build_id']}"); print(f"[PASS] Revision: {m['revision']}"); print(f"[PASS] Manifest hash: {m['manifest_hash']}"); print("[PASS] Certified UMD-093 baseline consumed read-only"); print("[PASS] Deterministic immutable normalization certified"); print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-094 CERTIFIED")
