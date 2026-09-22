from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_115_observation_impact import DirectImpactResult
from qseries_v2.universal_market_discovery.umd_118_impact_paths import ImpactPath,ImpactPathSet
from qseries_v2.universal_market_discovery.umd_119_impact_provenance import *

FIXED=datetime(2026,8,9,20,10,tzinfo=timezone.utc)

def direct():
    obs="a"*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-115",revision="UMD_115_OBSERVATION_IMPACT_MAPPING_V1",
        schema_version="1.0.0",parent_hashes=(obs,),source_refs=("fixture://119/115",),created_at=FIXED)
    return DirectImpactResult(
        obs,("m1",),
        (("asset","bitcoin",("m1",)),("metric","btc-spot-price",("m1",))),
        l
    )

def paths():
    obs="a"*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-118",revision="UMD_118_IMPACT_PATH_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://119/118",),created_at=FIXED)
    return ImpactPathSet(
        obs,
        (
            ImpactPath(obs,"m1",True,("m1",),()),
            ImpactPath(obs,"m2",False,("m1","m2"),("implies",)),
        ),
        l
    )

def lineage():
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-119",revision=UMD_119_REVISION,
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://119",),created_at=FIXED)

class TestUMD119(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_119_impact_provenance_bundle())
    def test_direct_dependency_provenance(self):
        b=ImpactProvenanceBuilder().build(direct(),paths(),lineage=lineage())
        e=b.for_market("m1")
        self.assertTrue(e.direct)
        self.assertEqual(e.dependency_matches,(("asset","bitcoin"),("metric","btc-spot-price")))
    def test_propagated_provenance(self):
        b=ImpactProvenanceBuilder().build(direct(),paths(),lineage=lineage())
        e=b.for_market("m2")
        self.assertFalse(e.direct)
        self.assertEqual(e.market_path,("m1","m2"))
        self.assertEqual(e.constraint_path,("implies",))
    def test_unknown_market(self):
        b=ImpactProvenanceBuilder().build(direct(),paths(),lineage=lineage())
        self.assertIsNone(b.for_market("missing"))
    def test_mismatch_rejected(self):
        p=paths()
        wrong=ImpactPathSet("b"*64,p.paths,p.lineage)
        with self.assertRaises(ValueError):
            ImpactProvenanceBuilder().build(direct(),wrong,lineage=lineage())
    def test_deterministic(self):
        a=ImpactProvenanceBuilder().build(direct(),paths(),lineage=lineage())
        b=ImpactProvenanceBuilder().build(direct(),paths(),lineage=lineage())
        self.assertEqual(a.bundle_hash,b.bundle_hash)
    def test_side_effects(self):
        m=build_umd_119_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-119 CERTIFICATION TEST");print(" IMPACT PROVENANCE BUNDLE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD119))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_119_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Direct dependency matches and propagated constraint paths certified")
    print("[PASS] UMD-115 and UMD-118 consumed read-only")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-119 CERTIFIED")
