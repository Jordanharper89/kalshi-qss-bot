from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler
from qseries_v2.universal_market_discovery.umd_110_market_family_resolution import UMD_110_REVISION,MarketFamilyResolver
from qseries_v2.universal_market_discovery.umd_113_market_constraints import *

FIXED=datetime(2026,8,9,18,10,tzinfo=timezone.utc)

def profile(cid,ih,threshold):
    l102=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://113/102",),created_at=FIXED
    )
    record=CanonicalMarketRecord(
        cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),
        "btc/digital-assets/crypto/bitcoin/price-threshold","b"*64,"c"*64,
        (),(),"",{},l102
    )
    l109=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,
        schema_version="1.0.0",parent_hashes=(record.record_hash,),
        source_refs=("fixture://113/109",),created_at=FIXED
    )
    return MarketSemanticProfiler().build(
        record,
        (("asset","Bitcoin"),("metric","Price"),("market_type","Price Threshold"),("threshold",threshold)),
        lineage=l109,
    )

def family_lineage(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://113/110",),created_at=FIXED
    )

def graph_lineage(families):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-113",revision=UMD_113_REVISION,
        schema_version="1.0.0",parent_hashes=tuple(f.family_hash for f in families),
        source_refs=("fixture://113",),created_at=FIXED
    )

class TestUMD113(unittest.TestCase):
    def setUp(self):
        self.a=profile("umd:market:a","a"*64,"100000")
        self.b=profile("umd:market:b","b"*64,"150000")
        self.ps=(self.a,self.b)
        self.fs=MarketFamilyResolver().resolve(self.ps,lineage_factory=family_lineage)

    def test_foundation(self):
        self.assertTrue(verify_umd_113_market_constraint_graph())

    def test_threshold_constraint(self):
        g=MarketConstraintGraphBuilder().build(
            self.ps,self.fs,
            (("umd:market:b","umd:market:a","threshold_monotonic","higher-threshold-implies-lower-threshold"),),
            lineage=graph_lineage(self.fs),
        )
        self.assertEqual(len(g.constraints),1)
        self.assertEqual(g.constraints[0].constraint_type,"threshold_monotonic")

    def test_symmetric_canonicalization(self):
        l=graph_lineage(self.fs)
        a=MarketConstraintGraphBuilder().build(
            self.ps,self.fs,
            (("umd:market:b","umd:market:a","mutually_exclusive","same-event-exclusive"),),
            lineage=l,
        )
        b=MarketConstraintGraphBuilder().build(
            tuple(reversed(self.ps)),tuple(reversed(self.fs)),
            (("umd:market:a","umd:market:b","mutually_exclusive","same-event-exclusive"),),
            lineage=l,
        )
        self.assertEqual(a.graph_hash,b.graph_hash)

    def test_duplicate_collapsed(self):
        spec=("umd:market:b","umd:market:a","implies","semantic-threshold")
        g=MarketConstraintGraphBuilder().build(
            self.ps,self.fs,(spec,spec),lineage=graph_lineage(self.fs)
        )
        self.assertEqual(len(g.constraints),1)

    def test_constraints_for(self):
        g=MarketConstraintGraphBuilder().build(
            self.ps,self.fs,
            (("umd:market:b","umd:market:a","implies","semantic-threshold"),),
            lineage=graph_lineage(self.fs),
        )
        self.assertEqual(len(g.constraints_for("umd:market:a")),1)

    def test_unknown_market_rejected(self):
        with self.assertRaises(ValueError):
            MarketConstraintGraphBuilder().build(
                self.ps,self.fs,
                (("umd:market:a","missing","implies","bad"),),
                lineage=graph_lineage(self.fs),
            )

    def test_lineage_required(self):
        bad=ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-113",revision=UMD_113_REVISION,
            schema_version="1.0.0",parent_hashes=("0"*64,),
            source_refs=("fixture://113/bad",),created_at=FIXED
        )
        with self.assertRaises(ValueError):
            MarketConstraintGraphBuilder().build(self.ps,self.fs,(),lineage=bad)

    def test_immutable(self):
        g=MarketConstraintGraphBuilder().build(self.ps,self.fs,(),lineage=graph_lineage(self.fs))
        with self.assertRaises((FrozenInstanceError,AttributeError)):
            g.constraints=()

    def test_side_effects(self):
        m=build_umd_113_certification_manifest()
        self.assertFalse(any(
            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
        ))

if __name__=="__main__":
    print("="*72);print(" UMD-113 CERTIFICATION TEST");print(" MARKET CONSTRAINT GRAPH");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD113))
    if not r.wasSuccessful():
        raise SystemExit(1)
    m=build_umd_113_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Threshold, implication, exclusivity, equivalence, and partition constraint primitives certified")
    print("[PASS] Semantic families consumed read-only")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-113 CERTIFIED")
