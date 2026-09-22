from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_136_observation_equivalence import ObservationEquivalenceGroup
from qseries_v2.universal_market_discovery.umd_137_observation_contradiction import ObservationContradiction,ObservationContradictionSet
from qseries_v2.universal_market_discovery.umd_138_observation_relationship_registry import *

FIXED=datetime(2026,8,10,3,20,tzinfo=timezone.utc)

def group(signature,ids,hashes):
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-136",revision="UMD_136_OBSERVATION_EQUIVALENCE_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=hashes,source_refs=("fixture://138/136",),created_at=FIXED
    )
    return ObservationEquivalenceGroup(signature,ids[0],ids,hashes,l)

def artifacts():
    g1=group("a"*64,("obs-a","obs-b"),("1"*64,"2"*64))
    g2=group("b"*64,("obs-c",),("3"*64,))
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-137",revision="UMD_137_OBSERVATION_CONTRADICTION_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(g1.group_hash,g2.group_hash),
        source_refs=("fixture://138/137",),created_at=FIXED
    )
    s=ObservationContradictionSet(
        ("obs-a","obs-b","obs-c"),
        (
            ObservationContradiction("obs-a","obs-c","negates","claim:x"),
            ObservationContradiction("obs-b","obs-c","supersedes","source:update"),
        ),
        tuple(sorted((g1.group_hash,g2.group_hash))),
        l,
    )
    return (g1,g2),(s,)

def lf(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-138",revision=UMD_138_REVISION,
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://138",),created_at=FIXED
    )

class TestUMD138(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_138_observation_relationship_registry())

    def test_equivalence_query(self):
        gs,ss=artifacts()
        r=ObservationRelationshipRegistryBuilder().build(gs,ss,lineage_factory=lf)
        self.assertEqual(r.equivalents_of("obs-a"),("obs-b",))
        self.assertEqual(r.canonical_for("obs-b"),"obs-a")

    def test_contradiction_query(self):
        gs,ss=artifacts()
        r=ObservationRelationshipRegistryBuilder().build(gs,ss,lineage_factory=lf)
        self.assertEqual(r.contradictions_of("obs-c"),("obs-a","obs-b"))

    def test_contradiction_type_query(self):
        gs,ss=artifacts()
        r=ObservationRelationshipRegistryBuilder().build(gs,ss,lineage_factory=lf)
        self.assertEqual(r.observations_for_contradiction_type("negates"),("obs-a","obs-c"))

    def test_unknown(self):
        gs,ss=artifacts()
        r=ObservationRelationshipRegistryBuilder().build(gs,ss,lineage_factory=lf)
        self.assertEqual(r.equivalents_of("missing"),())
        self.assertIsNone(r.canonical_for("missing"))

    def test_deterministic(self):
        gs,ss=artifacts()
        a=ObservationRelationshipRegistryBuilder().build(gs,ss,lineage_factory=lf)
        b=ObservationRelationshipRegistryBuilder().build(tuple(reversed(gs)),tuple(reversed(ss)),lineage_factory=lf)
        self.assertEqual(a.registry_hash,b.registry_hash)

    def test_empty(self):
        r=ObservationRelationshipRegistryBuilder().build((),(),lineage_factory=lf)
        self.assertEqual(r.equivalence_groups,())
        self.assertEqual(r.contradiction_sets,())

    def test_bad_group(self):
        _,ss=artifacts()
        with self.assertRaises(TypeError):
            ObservationRelationshipRegistryBuilder().build((object(),),ss,lineage_factory=lf)

    def test_side_effects(self):
        m=build_umd_138_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-138 CERTIFICATION TEST");print(" OBSERVATION RELATIONSHIP REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD138))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_138_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation equivalence and contradiction registry queries certified")
    print("[PASS] Canonical observation resolution and contradiction-type queries certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-138 CERTIFIED")
