from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_136_observation_equivalence import ObservationEquivalenceGroup
from qseries_v2.universal_market_discovery.umd_137_observation_contradiction import *

FIXED=datetime(2026,8,10,3,10,tzinfo=timezone.utc)

def group(signature,ids,hashes):
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-136",revision="UMD_136_OBSERVATION_EQUIVALENCE_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=hashes,
        source_refs=("fixture://137/136",),created_at=FIXED
    )
    return ObservationEquivalenceGroup(signature,tuple(ids)[0],tuple(ids),tuple(hashes),l)

def groups():
    return (
        group("a"*64,("obs-a",),("1"*64,)),
        group("b"*64,("obs-b",),("2"*64,)),
        group("c"*64,("obs-c",),("3"*64,)),
    )

def lineage(gs):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-137",revision=UMD_137_REVISION,
        schema_version="1.0.0",parent_hashes=tuple(g.group_hash for g in gs),
        source_refs=("fixture://137",),created_at=FIXED
    )

class TestUMD137(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_137_observation_contradiction_model())

    def test_negation(self):
        gs=groups()
        s=ObservationContradictionBuilder().build(
            gs,(("obs-a","obs-b","negates","claim:inflation-direction"),),
            lineage=lineage(gs)
        )
        self.assertEqual(len(s.contradictions),1)
        self.assertEqual(s.contradictions[0].contradiction_type,"negates")

    def test_symmetric_canonicalization(self):
        gs=groups(); l=lineage(gs)
        a=ObservationContradictionBuilder().build(
            gs,(("obs-b","obs-a","mutually-exclusive","event:result"),),lineage=l
        )
        b=ObservationContradictionBuilder().build(
            gs,(("obs-a","obs-b","mutually-exclusive","event:result"),),lineage=l
        )
        self.assertEqual(a.contradiction_set_hash,b.contradiction_set_hash)

    def test_duplicate_collapsed(self):
        gs=groups()
        spec=("obs-a","obs-b","supersedes","source:update")
        s=ObservationContradictionBuilder().build(gs,(spec,spec),lineage=lineage(gs))
        self.assertEqual(len(s.contradictions),1)

    def test_query(self):
        gs=groups()
        s=ObservationContradictionBuilder().build(
            gs,(("obs-a","obs-c","temporal-conflict","time:event"),),lineage=lineage(gs)
        )
        self.assertEqual(len(s.contradictions_for("obs-c")),1)

    def test_unknown_observation_rejected(self):
        gs=groups()
        with self.assertRaises(ValueError):
            ObservationContradictionBuilder().build(
                gs,(("obs-a","missing","negates","claim:x"),),lineage=lineage(gs)
            )

    def test_self_contradiction_rejected(self):
        gs=groups()
        with self.assertRaises(ValueError):
            ObservationContradictionBuilder().build(
                gs,(("obs-a","obs-a","negates","claim:x"),),lineage=lineage(gs)
            )

    def test_side_effects(self):
        m=build_umd_137_certification_manifest()
        self.assertEqual(m["contradiction_semantics"],"explicit_structural_relationships_only_no_inference")
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-137 CERTIFICATION TEST");print(" OBSERVATION CONTRADICTION MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD137))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_137_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Explicit negation, supersession, exclusivity, and temporal-conflict relationships certified")
    print("[PASS] No contradiction inference or probabilistic reasoning introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-137 CERTIFIED")
