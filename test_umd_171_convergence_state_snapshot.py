from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_169_convergence_market_profile import ConvergenceMarketProfile
from qseries_v2.universal_market_discovery.umd_170_convergence_market_registry import ConvergenceMarketRegistry
from qseries_v2.universal_market_discovery.umd_171_convergence_state_snapshot import *

FIXED=datetime(2026,8,10,16,20,tzinfo=timezone.utc)

def registry():
    p1=ConvergenceMarketProfile(
        "m1",("convergence-added",),("a"*64,),(),("kalshi","polymarket"),
        ("asset=bitcoin",),("required",),("implies",),("impacted",)
    )
    p2=ConvergenceMarketProfile(
        "m2",("convergence-composition-changed",),(),("b"*64,),("kalshi",),
        ("metric=cpi",),("supporting",),("threshold_monotonic",),("boundary",)
    )
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-170",revision="UMD_170_CONVERGENCE_MARKET_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(p1.profile_hash,p2.profile_hash),
        source_refs=("fixture://171/170",),created_at=FIXED
    )
    return ConvergenceMarketRegistry(
        (p1,p2),
        {"convergence-added":("m1",),"convergence-composition-changed":("m2",)},
        {"a"*64:("m1",)},{"b"*64:("m2",)},
        {"kalshi":("m1","m2"),"polymarket":("m1",)},
        {"asset=bitcoin":("m1",),"metric=cpi":("m2",)},
        {"required":("m1",),"supporting":("m2",)},
        {"implies":("m1",),"threshold_monotonic":("m2",)},
        {"impacted":("m1",),"boundary":("m2",)},
        l
    )

def lineage(r):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-171",revision=UMD_171_REVISION,
        schema_version="1.0.0",parent_hashes=(r.registry_hash,),
        source_refs=("fixture://171",),created_at=FIXED
    )

class TestUMD171(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_171_convergence_state_snapshot())
    def test_snapshot(self):
        r=registry()
        s=ConvergenceStateSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))
        self.assertEqual(tuple(x.canonical_market_id for x in s.records),("m1","m2"))
        self.assertEqual(s.record_for_market("m1").venue_keys,("kalshi","polymarket"))
    def test_profile_hash_preserved(self):
        r=registry()
        s=ConvergenceStateSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))
        self.assertEqual(s.record_for_market("m2").profile_hash,r.get("m2").profile_hash)
    def test_naive_time_rejected(self):
        r=registry()
        with self.assertRaises(ValueError):
            ConvergenceStateSnapshotBuilder().build(
                r,as_of=datetime(2026,8,10,16,20),lineage=lineage(r)
            )
    def test_unknown(self):
        r=registry()
        s=ConvergenceStateSnapshotBuilder().build(r,as_of=FIXED,lineage=lineage(r))
        self.assertIsNone(s.record_for_market("missing"))
    def test_deterministic(self):
        r=registry(); l=lineage(r)
        a=ConvergenceStateSnapshotBuilder().build(r,as_of=FIXED,lineage=l)
        b=ConvergenceStateSnapshotBuilder().build(r,as_of=FIXED,lineage=l)
        self.assertEqual(a.snapshot_hash,b.snapshot_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ConvergenceStateSnapshotBuilder().build(
                object(),as_of=FIXED,
                lineage=ImmutableLineage(
                    subsystem_id="UMD",build_id="UMD-171",revision=UMD_171_REVISION,
                    schema_version="1.0.0",parent_hashes=(),
                    source_refs=("fixture://171/bad",),created_at=FIXED
                )
            )
    def test_side_effects(self):
        m=build_umd_171_certification_manifest()
        self.assertEqual(m["semantics"],"enriched_point_in_time_convergence_state_only")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-171 CERTIFICATION TEST");print(" CONVERGENCE STATE SNAPSHOT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD171))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_171_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Enriched convergence market state captured in immutable timezone-aware snapshots")
    print("[PASS] Canonical profile identity and exact venue coverage preserved")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-171 CERTIFIED")
