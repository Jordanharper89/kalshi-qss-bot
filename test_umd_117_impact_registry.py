from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_115_observation_impact import DirectImpactResult
from qseries_v2.universal_market_discovery.umd_116_dependency_propagation import PropagationResult,PropagationStep
from qseries_v2.universal_market_discovery.umd_117_impact_registry import *

FIXED=datetime(2026,8,9,19,20,tzinfo=timezone.utc)

def pair(obs_hash="a"*64):
    l115=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision="UMD_115_OBSERVATION_IMPACT_MAPPING_V1",schema_version="1.0.0",parent_hashes=(obs_hash,),source_refs=("fixture://117/115",),created_at=FIXED)
    direct=DirectImpactResult(obs_hash,("m1",),(),l115)
    l116=ImmutableLineage(subsystem_id="UMD",build_id="UMD-116",revision="UMD_116_DEPENDENCY_PROPAGATION_V1",schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://117/116",),created_at=FIXED)
    prop=PropagationResult(("m1",),("m2","m3"),(PropagationStep(1,"m1","m2","implies"),PropagationStep(2,"m2","m3","threshold_monotonic")),l116)
    return direct,prop

def lineage_factory(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-117",revision=UMD_117_REVISION,schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://117",),created_at=FIXED)

class TestUMD117(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_117_impact_registry())
    def test_observation_query(self):
        d,p=pair()
        r=ImpactRegistryBuilder().build(((d,p),),lineage_factory=lineage_factory)
        self.assertEqual(r.markets_for_observation(d.observation_hash),("m1","m2","m3"))
    def test_market_reverse_query(self):
        d,p=pair()
        r=ImpactRegistryBuilder().build(((d,p),),lineage_factory=lineage_factory)
        self.assertEqual(r.observations_for_market("m2"),(d.observation_hash,))
    def test_unknown_market(self):
        d,p=pair()
        r=ImpactRegistryBuilder().build(((d,p),),lineage_factory=lineage_factory)
        self.assertEqual(r.observations_for_market("missing"),())
    def test_mismatch_rejected(self):
        d,p=pair()
        wrong=PropagationResult(("x",),p.propagated_market_ids,p.steps,p.lineage)
        with self.assertRaises(ValueError):
            ImpactRegistryBuilder().build(((d,wrong),),lineage_factory=lineage_factory)
    def test_deterministic(self):
        a1,p1=pair("a"*64); a2,p2=pair("b"*64)
        x=ImpactRegistryBuilder().build(((a1,p1),(a2,p2)),lineage_factory=lineage_factory)
        y=ImpactRegistryBuilder().build(((a2,p2),(a1,p1)),lineage_factory=lineage_factory)
        self.assertEqual(x.registry_hash,y.registry_hash)
    def test_immutable_index(self):
        d,p=pair()
        r=ImpactRegistryBuilder().build(((d,p),),lineage_factory=lineage_factory)
        with self.assertRaises(TypeError): r.market_index["m1"]=()
    def test_empty_registry(self):
        r=ImpactRegistryBuilder().build((),lineage_factory=lineage_factory)
        self.assertEqual(r.records,())
    def test_side_effects(self):
        m=build_umd_117_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-117 CERTIFICATION TEST");print(" IMPACT REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD117))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_117_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation-to-market and market-to-observation impact queries certified")
    print("[PASS] Direct and propagated impact lineage assembled read-only")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-117 CERTIFIED")
