from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_111_semantic_registry import SemanticRegistry
from qseries_v2.universal_market_discovery.umd_114_dependency_registry import DependencyRegistry
from qseries_v2.universal_market_discovery.umd_130_observation_classification import UMD_130_REVISION,ObservationClassifier
from qseries_v2.universal_market_discovery.umd_131_observation_entity_resolution import *

FIXED=datetime(2026,8,9,23,40,tzinfo=timezone.utc)

def semantic_registry():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-111",revision="UMD_111_SEMANTIC_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://131/111",),created_at=FIXED
    )
    return SemanticRegistry(
        (),(),
        {
            "asset=bitcoin":("m1",),
            "entity=federal-reserve":("m2",),
        },
        {},
        l,
    )

def dependency_registry():
    graph_hash="a"*64
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-114",revision="UMD_114_DEPENDENCY_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(graph_hash,),
        source_refs=("fixture://131/114",),created_at=FIXED
    )
    return DependencyRegistry(
        (),
        graph_hash,
        {
            "asset=bitcoin":("m1","m3"),
            "metric=consumer-price-index":("m4",),
        },
        {},
        {},
        l,
    )

def classification():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-130",revision=UMD_130_REVISION,
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://131/130",),created_at=FIXED
    )
    return ObservationClassifier().classify(
        "obs-1","economics",
        (("metric","Consumer Price Index"),),
        lineage=l,
    )

def lineage(c):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-131",revision=UMD_131_REVISION,
        schema_version="1.0.0",parent_hashes=(c.classification_hash,),
        source_refs=("fixture://131",),created_at=FIXED
    )

class TestUMD131(unittest.TestCase):
    def setUp(self):
        self.c=classification()
        self.r=ObservationEntityResolver(semantic_registry(),dependency_registry())

    def test_foundation(self):
        self.assertTrue(verify_umd_131_observation_entity_resolution())

    def test_asset_resolution(self):
        x=self.r.resolve(self.c,(("asset","Bitcoin"),),lineage=lineage(self.c))
        self.assertEqual(len(x.bindings),1)
        self.assertEqual(x.bindings[0].canonical_key,"bitcoin")
        self.assertEqual(x.bindings[0].known_market_ids,("m1","m3"))

    def test_entity_resolution(self):
        x=self.r.resolve(self.c,(("entity","Federal Reserve"),),lineage=lineage(self.c))
        self.assertEqual(x.bindings[0].canonical_key,"federal-reserve")
        self.assertEqual(x.bindings[0].known_market_ids,("m2",))

    def test_unresolved_preserved(self):
        x=self.r.resolve(self.c,(("asset","Solana"),),lineage=lineage(self.c))
        self.assertEqual(x.bindings,())
        self.assertEqual(x.unresolved,(("asset","solana"),))

    def test_deduplication(self):
        x=self.r.resolve(
            self.c,
            (("asset","Bitcoin"),("asset","BITCOIN")),
            lineage=lineage(self.c),
        )
        self.assertEqual(len(x.bindings),1)

    def test_deterministic(self):
        a=self.r.resolve(
            self.c,
            (("entity","Federal Reserve"),("asset","Bitcoin")),
            lineage=lineage(self.c),
        )
        b=self.r.resolve(
            self.c,
            (("asset","Bitcoin"),("entity","Federal Reserve")),
            lineage=lineage(self.c),
        )
        self.assertEqual(a.resolution_hash,b.resolution_hash)

    def test_bad_kind(self):
        with self.assertRaises(ValueError):
            self.r.resolve(self.c,(("time_window","tomorrow"),),lineage=lineage(self.c))

    def test_lineage_required(self):
        bad=ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-131",revision=UMD_131_REVISION,
            schema_version="1.0.0",parent_hashes=("0"*64,),
            source_refs=("fixture://131/bad",),created_at=FIXED
        )
        with self.assertRaises(ValueError):
            self.r.resolve(self.c,(("asset","Bitcoin"),),lineage=bad)

    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ObservationEntityResolver(object(),dependency_registry())

    def test_side_effects(self):
        m=build_umd_131_certification_manifest()
        self.assertFalse(any(
            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
        ))

if __name__=="__main__":
    print("="*72);print(" UMD-131 CERTIFICATION TEST");print(" OBSERVATION ENTITY RESOLUTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD131))
    if not r.wasSuccessful():
        raise SystemExit(1)
    m=build_umd_131_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation entity and asset resolution against certified market knowledge certified")
    print("[PASS] Unknown candidates preserved deterministically as unresolved")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-131 CERTIFIED")
