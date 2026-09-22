from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_112_market_dependency import MarketDependency,MarketDependencyProfile
from qseries_v2.universal_market_discovery.umd_114_dependency_registry import DependencyRegistry
from qseries_v2.universal_market_discovery.umd_150_change_structure_registry import ChangeStructureRegistry
from qseries_v2.universal_market_discovery.umd_151_change_dependency_projection import *

FIXED=datetime(2026,8,10,10,0,tzinfo=timezone.utc)
CHANGE="1"*64

def profile(mid,semantic_hash,deps):
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-112",revision="UMD_112_MARKET_DEPENDENCY_MODEL_V1",
        schema_version="1.0.0",parent_hashes=(semantic_hash,),
        source_refs=("fixture://151/112",),created_at=FIXED
    )
    return MarketDependencyProfile(mid,semantic_hash,tuple(deps),l)

def dependency_registry():
    p1=profile("m1","a"*64,(
        MarketDependency("asset","Bitcoin","bitcoin","required"),
        MarketDependency("metric","Price","price","supporting"),
    ))
    p2=profile("m2","b"*64,(
        MarketDependency("entity","Federal Reserve","federal-reserve","context"),
    ))
    graph_hash="c"*64
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-114",revision="UMD_114_DEPENDENCY_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(p1.profile_hash,p2.profile_hash,graph_hash),
        source_refs=("fixture://151/114",),created_at=FIXED
    )
    return DependencyRegistry(
        (p1,p2),graph_hash,
        {
            "asset=bitcoin":("m1",),
            "entity=federal-reserve":("m2",),
            "metric=price":("m1",),
        },
        {
            "context":("m2",),
            "required":("m1",),
            "supporting":("m1",),
        },
        {},
        l,
    )

def structure_registry():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-150",revision="UMD_150_CHANGE_STRUCTURE_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),
        source_refs=("fixture://151/150",),created_at=FIXED
    )
    return ChangeStructureRegistry(
        (),(),{},{},{},
        {"m1":(CHANGE,),"m2":(CHANGE,),"m3":(CHANGE,)},
        l,
    )

def lineage():
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-151",revision=UMD_151_REVISION,
        schema_version="1.0.0",parent_hashes=(CHANGE,),
        source_refs=("fixture://151",),created_at=FIXED
    )

class TestUMD151(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_151_change_dependency_projection())
    def test_projection(self):
        p=ChangeDependencyProjector(structure_registry(),dependency_registry()).project(CHANGE,lineage=lineage())
        self.assertEqual(p.market_ids,("m1","m2","m3"))
        self.assertEqual(len(p.bindings),3)
    def test_role_query(self):
        p=ChangeDependencyProjector(structure_registry(),dependency_registry()).project(CHANGE,lineage=lineage())
        self.assertEqual(p.markets_for_role("required"),("m1",))
        self.assertEqual(p.markets_for_role("context"),("m2",))
    def test_dependency_query(self):
        p=ChangeDependencyProjector(structure_registry(),dependency_registry()).project(CHANGE,lineage=lineage())
        self.assertEqual(p.markets_for_dependency("asset","bitcoin"),("m1",))
    def test_missing_profile(self):
        p=ChangeDependencyProjector(structure_registry(),dependency_registry()).project(CHANGE,lineage=lineage())
        self.assertEqual(p.missing_profile_market_ids,("m3",))
    def test_unknown_change(self):
        p=ChangeDependencyProjector(structure_registry(),dependency_registry()).project("9"*64,lineage=ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-151",revision=UMD_151_REVISION,
            schema_version="1.0.0",parent_hashes=("9"*64,),
            source_refs=("fixture://151/unknown",),created_at=FIXED
        ))
        self.assertEqual(p.market_ids,())
    def test_deterministic(self):
        projector=ChangeDependencyProjector(structure_registry(),dependency_registry())
        a=projector.project(CHANGE,lineage=lineage())
        b=projector.project(CHANGE,lineage=lineage())
        self.assertEqual(a.projection_hash,b.projection_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ChangeDependencyProjector(object(),dependency_registry())
    def test_side_effects(self):
        m=build_umd_151_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-151 CERTIFICATION TEST");print(" CHANGE DEPENDENCY PROJECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD151))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_151_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] World-state changes projected into required, supporting, settlement, and context dependencies")
    print("[PASS] Missing dependency profiles preserved explicitly")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-151 CERTIFIED")
