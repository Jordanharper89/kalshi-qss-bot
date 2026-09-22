from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_115_observation_impact import DirectImpactResult
from qseries_v2.universal_market_discovery.umd_116_dependency_propagation import PropagationResult,PropagationStep
from qseries_v2.universal_market_discovery.umd_118_impact_paths import *

FIXED=datetime(2026,8,9,20,0,tzinfo=timezone.utc)

def direct():
    obs="a"*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision="UMD_115_OBSERVATION_IMPACT_MAPPING_V1",
        schema_version="1.0.0",parent_hashes=(obs,),source_refs=("fixture://118/115",),created_at=FIXED)
    return DirectImpactResult(obs,("m1",),(),l)

def propagation():
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-116",revision="UMD_116_DEPENDENCY_PROPAGATION_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://118/116",),created_at=FIXED)
    return PropagationResult(
        ("m1",),("m2","m3"),
        (PropagationStep(1,"m1","m2","implies"),PropagationStep(2,"m2","m3","threshold_monotonic")),
        l
    )

def lineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-118",revision=UMD_118_REVISION,
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://118",),created_at=FIXED)

class TestUMD118(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_118_impact_path_resolution())
    def test_direct_path(self):
        r=ImpactPathResolver().resolve(direct(),propagation(),lineage=lineage())
        p=r.paths_to("m1")[0]
        self.assertTrue(p.direct)
        self.assertEqual(p.market_path,("m1",))
    def test_propagated_path(self):
        r=ImpactPathResolver().resolve(direct(),propagation(),lineage=lineage())
        p=r.paths_to("m3")[0]
        self.assertFalse(p.direct)
        self.assertEqual(p.market_path,("m1","m2","m3"))
        self.assertEqual(p.constraint_path,("implies","threshold_monotonic"))
    def test_complete_coverage(self):
        r=ImpactPathResolver().resolve(direct(),propagation(),lineage=lineage())
        self.assertEqual(tuple(p.target_market_id for p in r.paths),("m1","m2","m3"))
    def test_mismatch_rejected(self):
        p=propagation()
        wrong=PropagationResult(("x",),p.propagated_market_ids,p.steps,p.lineage)
        with self.assertRaises(ValueError):
            ImpactPathResolver().resolve(direct(),wrong,lineage=lineage())
    def test_unreachable_step_rejected(self):
        p=propagation()
        bad=PropagationResult(("m1",),("m2",),(PropagationStep(1,"x","m2","implies"),),p.lineage)
        with self.assertRaises(ValueError):
            ImpactPathResolver().resolve(direct(),bad,lineage=lineage())
    def test_deterministic(self):
        a=ImpactPathResolver().resolve(direct(),propagation(),lineage=lineage())
        b=ImpactPathResolver().resolve(direct(),propagation(),lineage=lineage())
        self.assertEqual(a.path_set_hash,b.path_set_hash)
    def test_side_effects(self):
        m=build_umd_118_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-118 CERTIFICATION TEST");print(" IMPACT PATH RESOLUTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD118))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_118_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Direct and propagated observation-to-market paths certified")
    print("[PASS] UMD-115 through UMD-117 consumed read-only")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-118 CERTIFIED")
