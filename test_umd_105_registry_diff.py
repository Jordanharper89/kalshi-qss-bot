from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_104_registry_snapshot import RegistrySnapshot
from qseries_v2.universal_market_discovery.umd_105_registry_diff import *
FIXED=datetime(2026,8,9,14,20,tzinfo=timezone.utc)

def snap(buildhash, ids, hashes):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-104",revision="UMD_104_REGISTRY_SNAPSHOT_V1",schema_version="1.0.0",parent_hashes=(buildhash,),source_refs=("fixture://105/104",),created_at=FIXED)
    return RegistrySnapshot(buildhash,tuple(ids),tuple(hashes),l)
class TestUMD105(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_105_registry_diff())
    def test_compare(self):
        a=snap("a"*64,("m1","m2"),("1"*64,"2"*64)); b=snap("b"*64,("m2","m3"),("9"*64,"3"*64))
        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-105",revision=UMD_105_REVISION,schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),source_refs=("fixture://105",),created_at=FIXED)
        d=RegistryDiffEngine().compare(a,b,lineage=l)
        self.assertEqual(d.added_ids,("m3",)); self.assertEqual(d.removed_ids,("m1",)); self.assertEqual(d.changed_ids,("m2",))
    def test_unchanged(self):
        a=snap("a"*64,("m1",),("1"*64,)); b=snap("b"*64,("m1",),("1"*64,))
        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-105",revision=UMD_105_REVISION,schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),source_refs=("fixture://105",),created_at=FIXED)
        d=RegistryDiffEngine().compare(a,b,lineage=l); self.assertEqual(d.unchanged_ids,("m1",))
    def test_deterministic(self):
        a=snap("a"*64,("m2","m1"),("2"*64,"1"*64)); b=snap("b"*64,("m3","m2"),("3"*64,"9"*64))
        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-105",revision=UMD_105_REVISION,schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),source_refs=("fixture://105",),created_at=FIXED)
        x=RegistryDiffEngine().compare(a,b,lineage=l); y=RegistryDiffEngine().compare(a,b,lineage=l); self.assertEqual(x.diff_hash,y.diff_hash)
    def test_lineage_required(self):
        a=snap("a"*64,(),()); b=snap("b"*64,(),())
        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-105",revision=UMD_105_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://105",),created_at=FIXED)
        with self.assertRaises(ValueError): RegistryDiffEngine().compare(a,b,lineage=l)
    def test_immutable(self):
        a=snap("a"*64,(),()); b=snap("b"*64,(),())
        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-105",revision=UMD_105_REVISION,schema_version="1.0.0",parent_hashes=(a.snapshot_hash,b.snapshot_hash),source_refs=("fixture://105",),created_at=FIXED)
        d=RegistryDiffEngine().compare(a,b,lineage=l)
        with self.assertRaises((FrozenInstanceError,AttributeError)): d.added_ids=()
    def test_side_effects(self):
        m=build_umd_105_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))
if __name__=="__main__":
    print("="*72);print(" UMD-105 CERTIFICATION TEST");print(" REGISTRY DIFF");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD105))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_105_certification_manifest(); print(); print(f"[PASS] Build: {m['build_id']}"); print(f"[PASS] Revision: {m['revision']}"); print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] UMD-104 registry snapshots consumed read-only"); print("[PASS] Deterministic added/removed/changed registry diff certified")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-105 CERTIFIED")
