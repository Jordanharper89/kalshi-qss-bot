from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler
from qseries_v2.universal_market_discovery.umd_110_market_family_resolution import UMD_110_REVISION,MarketFamilyResolver
from qseries_v2.universal_market_discovery.umd_112_market_dependency import UMD_112_REVISION,MarketDependencyBuilder
from qseries_v2.universal_market_discovery.umd_113_market_constraints import UMD_113_REVISION,MarketConstraintGraphBuilder
from qseries_v2.universal_market_discovery.umd_114_dependency_registry import *

FIXED=datetime(2026,8,9,18,20,tzinfo=timezone.utc)

def semantic_profile(cid,ih,asset,threshold):
    l102=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://114/102",),created_at=FIXED
    )
    record=CanonicalMarketRecord(
        cid,ih,(VenueMarketBinding("kalshi",cid[-1],ih),),
        "fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l102
    )
    l109=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,
        schema_version="1.0.0",parent_hashes=(record.record_hash,),
        source_refs=("fixture://114/109",),created_at=FIXED
    )
    return MarketSemanticProfiler().build(
        record,
        (("asset",asset),("metric","Price"),("market_type","Price Threshold"),("threshold",threshold)),
        lineage=l109,
    )

def family_lineage(parents):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-110",revision=UMD_110_REVISION,
        schema_version="1.0.0",parent_hashes=parents,
        source_refs=("fixture://114/110",),created_at=FIXED
    )

def dependency_profile(profile,metric):
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-112",revision=UMD_112_REVISION,
        schema_version="1.0.0",parent_hashes=(profile.profile_hash,),
        source_refs=("fixture://114/112",),created_at=FIXED
    )
    return MarketDependencyBuilder().build(
        profile,
        (("asset","Bitcoin","required"),("metric",metric,"required")),
        lineage=l,
    )

def constraint_graph(ps,fs):
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-113",revision=UMD_113_REVISION,
        schema_version="1.0.0",parent_hashes=tuple(f.family_hash for f in fs),
        source_refs=("fixture://114/113",),created_at=FIXED
    )
    return MarketConstraintGraphBuilder().build(
        ps,fs,
        (("umd:market:b","umd:market:a","threshold_monotonic","higher-threshold-implies-lower-threshold"),),
        lineage=l,
    )

def registry_lineage(dps,graph):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-114",revision=UMD_114_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(d.profile_hash for d in dps)+(graph.graph_hash,),
        source_refs=("fixture://114",),created_at=FIXED
    )

class TestUMD114(unittest.TestCase):
    def setUp(self):
        self.a=semantic_profile("umd:market:a","a"*64,"Bitcoin","100000")
        self.b=semantic_profile("umd:market:b","b"*64,"Bitcoin","150000")
        self.ps=(self.a,self.b)
        self.fs=MarketFamilyResolver().resolve(self.ps,lineage_factory=family_lineage)
        self.da=dependency_profile(self.a,"BTC Spot Price")
        self.db=dependency_profile(self.b,"BTC Spot Price")
        self.dps=(self.da,self.db)
        self.graph=constraint_graph(self.ps,self.fs)
        self.registry=DependencyRegistryBuilder().build(
            self.dps,self.graph,lineage=registry_lineage(self.dps,self.graph)
        )

    def test_foundation(self):
        self.assertTrue(verify_umd_114_dependency_registry())

    def test_dependency_query(self):
        self.assertEqual(
            self.registry.markets_for_dependency("metric","btc-spot-price"),
            ("umd:market:a","umd:market:b"),
        )

    def test_asset_dependency_query(self):
        self.assertEqual(
            self.registry.markets_for_dependency("asset","bitcoin"),
            ("umd:market:a","umd:market:b"),
        )

    def test_role_query(self):
        self.assertEqual(
            self.registry.markets_for_role("required"),
            ("umd:market:a","umd:market:b"),
        )

    def test_constraint_query(self):
        self.assertEqual(
            self.registry.markets_for_constraint("threshold_monotonic"),
            ("umd:market:a","umd:market:b"),
        )

    def test_unknown_dependency(self):
        self.assertEqual(
            self.registry.markets_for_dependency("metric","eth-spot-price"),
            (),
        )

    def test_deterministic(self):
        x=DependencyRegistryBuilder().build(
            tuple(reversed(self.dps)),
            self.graph,
            lineage=registry_lineage(self.dps,self.graph),
        )
        self.assertEqual(self.registry.registry_hash,x.registry_hash)

    def test_immutable_index(self):
        with self.assertRaises(TypeError):
            self.registry.dependency_index["metric=btc-spot-price"]=()

    def test_bad_graph(self):
        with self.assertRaises(TypeError):
            DependencyRegistryBuilder().build(
                self.dps,
                object(),
                lineage=registry_lineage(self.dps,self.graph),
            )

    def test_lineage_required(self):
        bad=ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-114",revision=UMD_114_REVISION,
            schema_version="1.0.0",parent_hashes=("0"*64,),
            source_refs=("fixture://114/bad",),created_at=FIXED
        )
        with self.assertRaises(ValueError):
            DependencyRegistryBuilder().build(self.dps,self.graph,lineage=bad)

    def test_side_effects(self):
        m=build_umd_114_certification_manifest()
        self.assertFalse(any(
            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
        ))

if __name__=="__main__":
    print("="*72);print(" UMD-114 CERTIFICATION TEST");print(" DEPENDENCY REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD114))
    if not r.wasSuccessful():
        raise SystemExit(1)
    m=build_umd_114_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Dependency-to-market and constraint-to-market queries certified")
    print("[PASS] UMD-112 and UMD-113 consumed read-only")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-114 CERTIFIED")
