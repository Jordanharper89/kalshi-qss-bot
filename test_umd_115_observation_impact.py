from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_114_dependency_registry import DependencyRegistry
from qseries_v2.universal_market_discovery.umd_115_observation_impact import *

FIXED=datetime(2026,8,9,19,0,tzinfo=timezone.utc)

def registry():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-114",revision="UMD_114_DEPENDENCY_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=("a"*64,),
        source_refs=("fixture://115/114",),created_at=FIXED
    )
    r=object.__new__(DependencyRegistry)
    object.__setattr__(r,"profiles",())
    object.__setattr__(r,"constraint_graph_hash","a"*64)
    object.__setattr__(r,"dependency_index",MappingProxyType({
        "asset=bitcoin":("umd:market:a","umd:market:b"),
        "metric=btc-spot-price":("umd:market:a","umd:market:b"),
        "event=fomc-meeting":("umd:market:c",),
    }))
    object.__setattr__(r,"role_index",MappingProxyType({}))
    object.__setattr__(r,"constraint_index",MappingProxyType({}))
    object.__setattr__(r,"lineage",l)
    return r

def observation():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-115",revision=UMD_115_REVISION,
        schema_version="1.0.0",parent_hashes=(),
        source_refs=("fixture://115/obs",),created_at=FIXED
    )
    return ObservationDescriptor("obs-1",(("metric","BTC Spot Price"),("asset","Bitcoin")),l)

def impact_lineage(o):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-115",revision=UMD_115_REVISION,
        schema_version="1.0.0",parent_hashes=(o.observation_hash,),
        source_refs=("fixture://115/map",),created_at=FIXED
    )

class TestUMD115(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_115_observation_impact_mapping())
    def test_direct_mapping(self):
        o=observation()
        r=ObservationImpactMapper(registry()).map(o,lineage=impact_lineage(o))
        self.assertEqual(r.market_ids,("umd:market:a","umd:market:b"))
    def test_matched_dependencies(self):
        o=observation()
        r=ObservationImpactMapper(registry()).map(o,lineage=impact_lineage(o))
        self.assertEqual(len(r.matched_dependencies),2)
    def test_unknown_observation(self):
        l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision=UMD_115_REVISION,schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://115/x",),created_at=FIXED)
        o=ObservationDescriptor("obs-x",(("asset","Ethereum"),),l)
        r=ObservationImpactMapper(registry()).map(o,lineage=impact_lineage(o))
        self.assertEqual(r.market_ids,())
    def test_normalization(self):
        o=observation()
        self.assertIn(("metric","btc-spot-price"),o.facts)
    def test_deterministic(self):
        o=observation(); l=impact_lineage(o)
        a=ObservationImpactMapper(registry()).map(o,lineage=l)
        b=ObservationImpactMapper(registry()).map(o,lineage=l)
        self.assertEqual(a.impact_hash,b.impact_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError): ObservationImpactMapper(object())
    def test_lineage_required(self):
        o=observation()
        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision=UMD_115_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("fixture://115/bad",),created_at=FIXED)
        with self.assertRaises(ValueError): ObservationImpactMapper(registry()).map(o,lineage=bad)
    def test_side_effects(self):
        m=build_umd_115_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-115 CERTIFICATION TEST");print(" OBSERVATION IMPACT MAPPING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD115))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_115_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation facts map deterministically to directly dependent markets")
    print("[PASS] UMD-114 dependency registry consumed read-only")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-115 CERTIFIED")
