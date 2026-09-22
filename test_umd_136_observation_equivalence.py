from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_135_observation_routing_registry import ObservationRoutingRecord
from qseries_v2.universal_market_discovery.umd_136_observation_equivalence import *

FIXED=datetime(2026,8,10,3,0,tzinfo=timezone.utc)

def record(obs,market_ids=("m1",),venue_keys=("kalshi",),domain="economics"):
    return ObservationRoutingRecord(
        obs,domain,
        "a"*64,"b"*64,"c"*64,"d"*64,"timeline-1",
        tuple(market_ids),
        ("macro=cpi",),
        tuple(venue_keys),
        (),
    )

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-136",revision=UMD_136_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://136",),created_at=FIXED
    )

class TestUMD136(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_136_observation_equivalence_resolution())

    def test_equivalent_group(self):
        a=record("obs-a"); b=record("obs-b")
        groups=ObservationEquivalenceResolver().resolve((b,a),lineage_factory=lf)
        self.assertEqual(len(groups),1)
        self.assertEqual(groups[0].canonical_observation_id,"obs-a")
        self.assertEqual(groups[0].member_observation_ids,("obs-a","obs-b"))
        self.assertTrue(groups[0].equivalent)

    def test_distinct_structure_separate(self):
        a=record("obs-a")
        b=record("obs-b",market_ids=("m2",))
        groups=ObservationEquivalenceResolver().resolve((a,b),lineage_factory=lf)
        self.assertEqual(len(groups),2)

    def test_signature_ignores_observation_id(self):
        self.assertEqual(observation_signature(record("obs-a")),observation_signature(record("obs-b")))

    def test_deterministic(self):
        a=record("obs-a"); b=record("obs-b")
        x=ObservationEquivalenceResolver().resolve((a,b),lineage_factory=lf)
        y=ObservationEquivalenceResolver().resolve((b,a),lineage_factory=lf)
        self.assertEqual(tuple(g.group_hash for g in x),tuple(g.group_hash for g in y))

    def test_duplicate_observation_id_rejected(self):
        with self.assertRaises(ValueError):
            ObservationEquivalenceResolver().resolve((record("obs-a"),record("obs-a")),lineage_factory=lf)

    def test_bad_record(self):
        with self.assertRaises(TypeError):
            ObservationEquivalenceResolver().resolve((object(),),lineage_factory=lf)

    def test_side_effects(self):
        m=build_umd_136_certification_manifest()
        self.assertEqual(m["equivalence_semantics"],"exact_structural_signature_only_no_fuzzy_reasoning")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-136 CERTIFICATION TEST");print(" OBSERVATION EQUIVALENCE RESOLUTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD136))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_136_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Exact structural observation equivalence grouping certified")
    print("[PASS] No fuzzy similarity, prediction, or semantic guessing introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-136 CERTIFIED")
