from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_113_market_constraints import MarketConstraint,MarketConstraintGraph
from qseries_v2.universal_market_discovery.umd_115_observation_impact import DirectImpactResult
from qseries_v2.universal_market_discovery.umd_116_dependency_propagation import *

FIXED=datetime(2026,8,9,19,10,tzinfo=timezone.utc)

def graph():
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-113",revision="UMD_113_MARKET_CONSTRAINT_GRAPH_V1",schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://116/113",),created_at=FIXED)
    return MarketConstraintGraph(
        ("m1","m2","m3","m4"),
        (
            MarketConstraint("m1","m2","implies","a"),
            MarketConstraint("m2","m3","threshold_monotonic","b"),
            MarketConstraint("m3","m4","mutually_exclusive","c"),
        ),
        (),
        l,
    )

def direct():
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision="UMD_115_OBSERVATION_IMPACT_MAPPING_V1",schema_version="1.0.0",parent_hashes=("a"*64,),source_refs=("fixture://116/115",),created_at=FIXED)
    return DirectImpactResult("a"*64,("m1",),(),l)

def lineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-116",revision=UMD_116_REVISION,schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://116",),created_at=FIXED)

class TestUMD116(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_116_dependency_propagation())
    def test_propagation(self):
        r=DependencyPropagationEngine(graph()).propagate(direct(),lineage=lineage())
        self.assertEqual(r.propagated_market_ids,("m2","m3"))
        self.assertNotIn("m4",r.all_market_ids)
    def test_depth_limit(self):
        r=DependencyPropagationEngine(graph()).propagate(direct(),max_depth=1,lineage=lineage())
        self.assertEqual(r.propagated_market_ids,("m2",))
    def test_steps(self):
        r=DependencyPropagationEngine(graph()).propagate(direct(),lineage=lineage())
        self.assertEqual(tuple(s.depth for s in r.steps),(1,2))
    def test_zero_depth(self):
        r=DependencyPropagationEngine(graph()).propagate(direct(),max_depth=0,lineage=lineage())
        self.assertEqual(r.propagated_market_ids,())
    def test_deterministic(self):
        e=DependencyPropagationEngine(graph())
        a=e.propagate(direct(),lineage=lineage())
        b=e.propagate(direct(),lineage=lineage())
        self.assertEqual(a.propagation_hash,b.propagation_hash)
    def test_bad_depth(self):
        with self.assertRaises(ValueError): DependencyPropagationEngine(graph()).propagate(direct(),max_depth=-1,lineage=lineage())
    def test_bad_graph(self):
        with self.assertRaises(TypeError): DependencyPropagationEngine(object())
    def test_side_effects(self):
        m=build_umd_116_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-116 CERTIFICATION TEST");print(" DEPENDENCY PROPAGATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD116))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_116_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Bounded deterministic propagation across implication constraints certified")
    print("[PASS] Non-propagating constraint types remain excluded")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-116 CERTIFIED")
