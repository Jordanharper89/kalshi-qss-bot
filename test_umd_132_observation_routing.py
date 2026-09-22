from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import UMD_103_REVISION,CanonicalMarketRegistryBuilder
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import MarketSemanticProfile,SemanticFact
from qseries_v2.universal_market_discovery.umd_110_market_family_resolution import MarketFamily
from qseries_v2.universal_market_discovery.umd_111_semantic_registry import SemanticRegistry
from qseries_v2.universal_market_discovery.umd_114_dependency_registry import DependencyRegistry
from qseries_v2.universal_market_discovery.umd_130_observation_classification import UMD_130_REVISION,ObservationClassifier
from qseries_v2.universal_market_discovery.umd_131_observation_entity_resolution import UMD_131_REVISION,ObservationEntityResolver
from qseries_v2.universal_market_discovery.umd_132_observation_routing import *

FIXED=datetime(2026,8,9,23,50,tzinfo=timezone.utc)

def canonical_record(cid,ih,bindings):
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://132/102",),created_at=FIXED
    )
    return CanonicalMarketRecord(
        cid,
        min(b.identity_hash for b in bindings),
        tuple(bindings),
        "fixture/domain/category/subcategory/type",
        "b"*64,
        "c"*64,
        (),
        (),
        "",
        {},
        l,
    )

def market_registry():
    a=canonical_record(
        "m1","a"*64,
        (
            VenueMarketBinding("kalshi","K-BTC","a"*64),
            VenueMarketBinding("polymarket","P-BTC","b"*64),
        ),
    )
    b=canonical_record(
        "m2","c"*64,
        (VenueMarketBinding("kalshi","K-CPI","c"*64),),
    )
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,
        schema_version="1.0.0",parent_hashes=(a.record_hash,b.record_hash),
        source_refs=("fixture://132/103",),created_at=FIXED
    )
    return CanonicalMarketRegistryBuilder().build((a,b),lineage=l)

def semantic_registry():
    ph1="d"*64
    ph2="e"*64
    f1="f"*64
    f2="1"*64
    l1=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-109",revision="UMD_109_MARKET_SEMANTIC_PROFILE_V1",
        schema_version="1.0.0",parent_hashes=(ph1,),source_refs=("fixture://132/109a",),created_at=FIXED
    )
    l2=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-109",revision="UMD_109_MARKET_SEMANTIC_PROFILE_V1",
        schema_version="1.0.0",parent_hashes=(ph2,),source_refs=("fixture://132/109b",),created_at=FIXED
    )
    p1=MarketSemanticProfile("m1",ph1,(SemanticFact("asset","Bitcoin","bitcoin"),),l1)
    p2=MarketSemanticProfile("m2",ph2,(SemanticFact("metric","Consumer Price Index","consumer-price-index"),),l2)

    lf1=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-110",revision="UMD_110_MARKET_FAMILY_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=(p1.profile_hash,),source_refs=("fixture://132/110a",),created_at=FIXED
    )
    lf2=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-110",revision="UMD_110_MARKET_FAMILY_RESOLUTION_V1",
        schema_version="1.0.0",parent_hashes=(p2.profile_hash,),source_refs=("fixture://132/110b",),created_at=FIXED
    )
    fam1=MarketFamily("asset=bitcoin",("asset",),("m1",),(p1.profile_hash,),lf1)
    fam2=MarketFamily("metric=consumer-price-index",("metric",),("m2",),(p2.profile_hash,),lf2)

    l111=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-111",revision="UMD_111_SEMANTIC_REGISTRY_V1",
        schema_version="1.0.0",
        parent_hashes=(p1.profile_hash,p2.profile_hash,fam1.family_hash,fam2.family_hash),
        source_refs=("fixture://132/111",),created_at=FIXED
    )
    return SemanticRegistry(
        (p1,p2),
        tuple(sorted((fam1,fam2),key=lambda f:f.family_key)),
        {
            "asset=bitcoin":("m1",),
            "metric=consumer-price-index":("m2",),
        },
        {
            fam1.family_key:("m1",),
            fam2.family_key:("m2",),
        },
        l111,
    )

def dependency_registry():
    graph_hash="2"*64
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-114",revision="UMD_114_DEPENDENCY_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(graph_hash,),
        source_refs=("fixture://132/114",),created_at=FIXED
    )
    return DependencyRegistry(
        (),
        graph_hash,
        {
            "asset=bitcoin":("m1",),
            "metric=consumer-price-index":("m2",),
        },
        {},
        {},
        l,
    )

def classification():
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-130",revision=UMD_130_REVISION,
        schema_version="1.0.0",parent_hashes=(),
        source_refs=("fixture://132/130",),created_at=FIXED
    )
    return ObservationClassifier().classify(
        "obs-cpi-btc",
        "economics",
        (("metric","Consumer Price Index"),),
        lineage=l,
    )

def entity_resolution(c):
    sr=semantic_registry()
    dr=dependency_registry()
    resolver=ObservationEntityResolver(sr,dr)
    l=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-131",revision=UMD_131_REVISION,
        schema_version="1.0.0",parent_hashes=(c.classification_hash,),
        source_refs=("fixture://132/131",),created_at=FIXED
    )
    return resolver.resolve(c,(("asset","Bitcoin"),),lineage=l)

def route_lineage(c,e):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-132",revision=UMD_132_REVISION,
        schema_version="1.0.0",parent_hashes=(c.classification_hash,e.resolution_hash),
        source_refs=("fixture://132",),created_at=FIXED
    )

class TestUMD132(unittest.TestCase):
    def setUp(self):
        self.sr=semantic_registry()
        self.dr=dependency_registry()
        self.mr=market_registry()
        self.c=classification()
        self.e=entity_resolution(self.c)
        self.router=ObservationRouter(self.dr,self.sr,self.mr)

    def test_foundation(self):
        self.assertTrue(verify_umd_132_observation_routing())

    def test_route_markets(self):
        r=self.router.route(self.c,self.e,lineage=route_lineage(self.c,self.e))
        self.assertEqual(r.market_ids,("m1","m2"))

    def test_route_families(self):
        r=self.router.route(self.c,self.e,lineage=route_lineage(self.c,self.e))
        self.assertEqual(
            r.family_keys,
            ("asset=bitcoin","metric=consumer-price-index"),
        )

    def test_cross_venue_route(self):
        r=self.router.route(self.c,self.e,lineage=route_lineage(self.c,self.e))
        self.assertEqual(r.venues(),("kalshi","polymarket"))
        self.assertEqual(r.markets_for_venue("polymarket"),("m1",))

    def test_matched_dependencies(self):
        r=self.router.route(self.c,self.e,lineage=route_lineage(self.c,self.e))
        self.assertEqual(
            tuple((kind,key) for kind,key,_ in r.matched_dependencies),
            (("asset","bitcoin"),("metric","consumer-price-index")),
        )

    def test_routing_facts_include_entities(self):
        r=self.router.route(self.c,self.e,lineage=route_lineage(self.c,self.e))
        self.assertEqual(
            r.routing_facts,
            (("asset","bitcoin"),("metric","consumer-price-index")),
        )

    def test_deterministic(self):
        a=self.router.route(self.c,self.e,lineage=route_lineage(self.c,self.e))
        b=self.router.route(self.c,self.e,lineage=route_lineage(self.c,self.e))
        self.assertEqual(a.route_hash,b.route_hash)

    def test_observation_mismatch_rejected(self):
        c2_l=ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-130",revision=UMD_130_REVISION,
            schema_version="1.0.0",parent_hashes=(),
            source_refs=("fixture://132/other",),created_at=FIXED
        )
        c2=ObservationClassifier().classify("other","economics",(),lineage=c2_l)
        with self.assertRaises(ValueError):
            self.router.route(c2,self.e,lineage=route_lineage(self.c,self.e))

    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ObservationRouter(object(),self.sr,self.mr)

    def test_side_effects(self):
        m=build_umd_132_certification_manifest()
        self.assertFalse(any(
            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
        ))

if __name__=="__main__":
    print("="*72);print(" UMD-132 CERTIFICATION TEST");print(" OBSERVATION ROUTING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD132))
    if not r.wasSuccessful():
        raise SystemExit(1)
    m=build_umd_132_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Classified observations and resolved entities routed to canonical markets")
    print("[PASS] Semantic families, venue bindings, and dependency matches preserved")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-132 CERTIFIED")
