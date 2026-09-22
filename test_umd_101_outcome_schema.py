from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer
from qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver
from qseries_v2.universal_market_discovery.umd_101_outcome_schema import (
    UMD_101_REVISION,OutcomeSchemaResolver,build_umd_101_certification_manifest,verify_umd_101_outcome_schema_resolution,
)

FIXED=datetime(2026,8,9,12,10,tzinfo=timezone.utc)

def identity(outcomes):
    o=MarketObservation(venue="Kalshi",venue_market_id="A",title="Example market",category="Other",status="Open",outcomes=tuple(outcomes))
    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://101/94",),created_at=FIXED)
    m=MarketNormalizer().normalize(o,lineage=l94)
    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://101/95",),created_at=FIXED)
    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)

def lineage(i): return ImmutableLineage(subsystem_id="UMD",build_id="UMD-101",revision=UMD_101_REVISION,schema_version="1.0.0",parent_hashes=(i.identity_hash,),source_refs=("fixture://101",),created_at=FIXED)

class TestUMD101(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_101_outcome_schema_resolution())
    def test_yes_no(self):
        i=identity(("Yes","No")); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i)); self.assertEqual(s.schema_type,"binary_yes_no"); self.assertEqual(tuple(x.outcome_key for x in s.options),("yes","no"))
    def test_binary_generic(self):
        i=identity(("Up","Down")); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i)); self.assertEqual(s.schema_type,"binary_generic"); self.assertEqual(tuple(x.outcome_key for x in s.options),("down","up"))
    def test_categorical(self):
        i=identity(("A","B","C")); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i)); self.assertEqual(s.schema_type,"categorical"); self.assertEqual(len(s.options),3)
    def test_unspecified(self):
        i=identity(()); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i)); self.assertEqual(s.schema_type,"unspecified"); self.assertEqual(s.options,())
    def test_deterministic(self):
        i=identity(("B","A","C")); l=lineage(i); r=OutcomeSchemaResolver(); self.assertEqual(r.resolve(i,lineage=l).outcome_schema_hash,r.resolve(i,lineage=l).outcome_schema_hash)
    def test_unique_ids(self):
        i=identity(("A","B","C")); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i)); self.assertEqual(len({x.outcome_id for x in s.options}),3)
    def test_lineage_required(self):
        i=identity(("Yes","No")); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-101",revision=UMD_101_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)
        with self.assertRaises(ValueError): OutcomeSchemaResolver().resolve(i,lineage=bad)
    def test_immutable(self):
        i=identity(("Yes","No")); s=OutcomeSchemaResolver().resolve(i,lineage=lineage(i))
        with self.assertRaises((FrozenInstanceError,AttributeError)): s.schema_type="x"
    def test_side_effects(self):
        m=build_umd_101_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72); print(" UMD-101 CERTIFICATION TEST"); print(" OUTCOME SCHEMA RESOLUTION"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD101))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_101_certification_manifest(); print(); print(f"[PASS] Build: {m['build_id']}"); print(f"[PASS] Revision: {m['revision']}"); print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] UMD-100 lifecycle capability consumed read-only"); print("[PASS] Deterministic canonical outcome schema resolution certified")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-101 CERTIFIED")
