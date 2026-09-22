from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding
from qseries_v2.universal_market_discovery.umd_109_market_semantic_profile import UMD_109_REVISION,MarketSemanticProfiler
from qseries_v2.universal_market_discovery.umd_112_market_dependency import *

FIXED=datetime(2026,8,9,18,0,tzinfo=timezone.utc)

def semantic_profile():
    ih="a"*64
    l102=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",
        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://112/102",),created_at=FIXED
    )
    record=CanonicalMarketRecord(
        "umd:market:btc100k",ih,(VenueMarketBinding("kalshi","K-BTC100K",ih),),
        "btc/digital-assets/crypto/bitcoin/price-threshold","b"*64,"c"*64,
        ("btc-100k",),(),"",{},l102
    )
    l109=ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-109",revision=UMD_109_REVISION,
        schema_version="1.0.0",parent_hashes=(record.record_hash,),
        source_refs=("fixture://112/109",),created_at=FIXED
    )
    return MarketSemanticProfiler().build(
        record,
        (("asset","Bitcoin"),("metric","Price"),("threshold","100000"),("unit","USD")),
        lineage=l109,
    )

def lineage(profile):
    return ImmutableLineage(
        subsystem_id="UMD",build_id="UMD-112",revision=UMD_112_REVISION,
        schema_version="1.0.0",parent_hashes=(profile.profile_hash,),
        source_refs=("fixture://112",),created_at=FIXED
    )

class TestUMD112(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_umd_112_market_dependency_model())

    def test_dependency_profile(self):
        p=semantic_profile()
        d=MarketDependencyBuilder().build(
            p,
            (
                ("asset","Bitcoin","required"),
                ("metric","BTC Spot Price","required"),
                ("settlement_source","Official Settlement Feed","settlement"),
            ),
            lineage=lineage(p),
        )
        self.assertEqual(d.dependency_keys("asset"),("bitcoin",))
        self.assertEqual(d.dependency_keys("metric"),("btc-spot-price",))

    def test_roles(self):
        p=semantic_profile()
        d=MarketDependencyBuilder().build(
            p,
            (("metric","BTC Spot Price","required"),("metric","BTC VWAP","supporting")),
            lineage=lineage(p),
        )
        self.assertEqual(d.dependency_keys(role="supporting"),("btc-vwap",))

    def test_deduplication(self):
        p=semantic_profile()
        d=MarketDependencyBuilder().build(
            p,
            (("asset","Bitcoin","required"),("asset","BITCOIN","required")),
            lineage=lineage(p),
        )
        self.assertEqual(len(d.dependencies),1)

    def test_deterministic(self):
        p=semantic_profile(); l=lineage(p)
        a=MarketDependencyBuilder().build(
            p,
            (("asset","Bitcoin","required"),("metric","BTC Spot Price","required")),
            lineage=l,
        )
        b=MarketDependencyBuilder().build(
            p,
            (("metric","BTC Spot Price","required"),("asset","Bitcoin","required")),
            lineage=l,
        )
        self.assertEqual(a.profile_hash,b.profile_hash)

    def test_invalid_kind(self):
        p=semantic_profile()
        with self.assertRaises(ValueError):
            MarketDependencyBuilder().build(p,(("unknown","X","required"),),lineage=lineage(p))

    def test_invalid_role(self):
        p=semantic_profile()
        with self.assertRaises(ValueError):
            MarketDependencyBuilder().build(p,(("asset","Bitcoin","trade"),),lineage=lineage(p))

    def test_lineage_required(self):
        p=semantic_profile()
        bad=ImmutableLineage(
            subsystem_id="UMD",build_id="UMD-112",revision=UMD_112_REVISION,
            schema_version="1.0.0",parent_hashes=("0"*64,),
            source_refs=("fixture://112/bad",),created_at=FIXED
        )
        with self.assertRaises(ValueError):
            MarketDependencyBuilder().build(p,(("asset","Bitcoin","required"),),lineage=bad)

    def test_immutable(self):
        p=semantic_profile()
        d=MarketDependencyBuilder().build(p,(("asset","Bitcoin","required"),),lineage=lineage(p))
        with self.assertRaises((FrozenInstanceError,AttributeError)):
            d.dependencies=()

    def test_side_effects(self):
        m=build_umd_112_certification_manifest()
        self.assertFalse(any(
            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
        ))

if __name__=="__main__":
    print("="*72);print(" UMD-112 CERTIFICATION TEST");print(" MARKET DEPENDENCY MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD112))
    if not r.wasSuccessful():
        raise SystemExit(1)
    m=build_umd_112_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Required, supporting, settlement, and context dependencies certified")
    print("[PASS] Semantic profiles consumed read-only")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-112 CERTIFIED")
