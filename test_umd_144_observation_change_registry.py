from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_143_observation_state_diff import ObservationStateDiff
from qseries_v2.universal_market_discovery.umd_144_observation_change_registry import *

FIXED=datetime(2026,8,10,7,0,tzinfo=timezone.utc)

def diff(seed,added=(),removed=(),clusters_a=(),clusters_r=(),contra_a=(),contra_r=()):
    before=seed*64
    after=chr(ord(seed)+1)*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-143",revision="UMD_143_OBSERVATION_STATE_DIFF_V1",
        schema_version="1.0.0",parent_hashes=(before,after),source_refs=("fixture://144/143",),created_at=FIXED)
    return ObservationStateDiff(before,after,tuple(added),tuple(removed),tuple(clusters_a),tuple(clusters_r),tuple(contra_a),tuple(contra_r),l)

def lf(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-144",revision=UMD_144_REVISION,
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://144",),created_at=FIXED)

class TestUMD144(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_144_observation_change_registry())
    def test_change_types(self):
        d=diff("a",added=("obs-a",),removed=("obs-b",),clusters_a=("c1",),clusters_r=("c2",),
               contra_a=(("obs-a","obs-c"),),contra_r=(("obs-b","obs-d"),))
        r=ObservationChangeRegistryBuilder().build((d,),lineage_factory=lf)
        self.assertEqual(set(c.change_type for c in r.changes),set(CHANGE_TYPES))
    def test_type_query(self):
        d=diff("a",added=("obs-a","obs-b"))
        r=ObservationChangeRegistryBuilder().build((d,),lineage_factory=lf)
        self.assertEqual(r.subjects_for_type("canonical-added"),("obs-a","obs-b"))
    def test_observation_query(self):
        d=diff("a",contra_a=(("obs-a","obs-c"),))
        r=ObservationChangeRegistryBuilder().build((d,),lineage_factory=lf)
        self.assertEqual(len(r.changes_for_observation("obs-a")),1)
        self.assertEqual(r.changes_for_observation("obs-a"),r.changes_for_observation("obs-c"))
    def test_unknown(self):
        r=ObservationChangeRegistryBuilder().build((),lineage_factory=lf)
        self.assertEqual(r.subjects_for_type("canonical-added"),())
        self.assertEqual(r.changes_for_observation("missing"),())
    def test_deterministic(self):
        a=diff("a",added=("obs-a",))
        c=diff("c",removed=("obs-b",))
        x=ObservationChangeRegistryBuilder().build((a,c),lineage_factory=lf)
        y=ObservationChangeRegistryBuilder().build((c,a),lineage_factory=lf)
        self.assertEqual(x.registry_hash,y.registry_hash)
    def test_bad_diff(self):
        with self.assertRaises(TypeError):
            ObservationChangeRegistryBuilder().build((object(),),lineage_factory=lf)
    def test_side_effects(self):
        m=build_umd_144_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-144 CERTIFICATION TEST");print(" OBSERVATION CHANGE REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD144))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_144_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation-state changes indexed by deterministic change type")
    print("[PASS] Canonical observation and contradiction change reverse queries certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-144 CERTIFIED")
