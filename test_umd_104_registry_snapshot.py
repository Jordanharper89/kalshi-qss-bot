from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import CanonicalMarketRegistry
from qseries_v2.universal_market_discovery.umd_104_registry_snapshot import *
FIXED=datetime(2026,8,9,14,10,tzinfo=timezone.utc)

def registry():
    r=object.__new__(CanonicalMarketRegistry)
    object.__setattr__(r,"records",())
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision="UMD_103_CANONICAL_MARKET_REGISTRY_V1",schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://104/103",),created_at=FIXED)
    object.__setattr__(r,"lineage",l)
    return r
class TestUMD104(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_104_registry_snapshot())
    def test_build(self):
        g=registry(); l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-104",revision=UMD_104_REVISION,schema_version="1.0.0",parent_hashes=(g.registry_hash,),source_refs=("fixture://104",),created_at=FIXED)
        s=RegistrySnapshotBuilder().build(g,lineage=l); self.assertEqual(s.registry_hash,g.registry_hash)
    def test_deterministic(self):
        g=registry(); l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-104",revision=UMD_104_REVISION,schema_version="1.0.0",parent_hashes=(g.registry_hash,),source_refs=("fixture://104",),created_at=FIXED)
        a=RegistrySnapshotBuilder().build(g,lineage=l); b=RegistrySnapshotBuilder().build(g,lineage=l); self.assertEqual(a.snapshot_hash,b.snapshot_hash)
    def test_lineage_required(self):
        g=registry(); l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-104",revision=UMD_104_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://104",),created_at=FIXED)
        with self.assertRaises(ValueError): RegistrySnapshotBuilder().build(g,lineage=l)
    def test_immutable(self):
        g=registry(); l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-104",revision=UMD_104_REVISION,schema_version="1.0.0",parent_hashes=(g.registry_hash,),source_refs=("fixture://104",),created_at=FIXED)
        s=RegistrySnapshotBuilder().build(g,lineage=l)
        with self.assertRaises((FrozenInstanceError,AttributeError)): s.registry_hash="x"
    def test_side_effects(self):
        m=build_umd_104_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))
if __name__=="__main__":
    print("="*72);print(" UMD-104 CERTIFICATION TEST");print(" REGISTRY SNAPSHOT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD104))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_104_certification_manifest(); print(); print(f"[PASS] Build: {m['build_id']}"); print(f"[PASS] Revision: {m['revision']}"); print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] UMD-103 canonical registry consumed read-only"); print("[PASS] Deterministic immutable registry snapshot certified")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-104 CERTIFIED")
