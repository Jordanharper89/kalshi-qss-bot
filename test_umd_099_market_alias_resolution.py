from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer
from qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver
from qseries_v2.universal_market_discovery.umd_098_market_taxonomy import UMD_098_REVISION,TaxonomyPath,TaxonomyRule,MarketTaxonomyClassifier
from qseries_v2.universal_market_discovery.umd_099_market_alias_resolution import (
    UMD_099_REVISION,MarketAliasResolver,normalize_alias,
    build_umd_099_certification_manifest,verify_umd_099_market_alias_resolution,
)

FIXED=datetime(2026,8,8,13,20,tzinfo=timezone.utc)

def identity(venue,mid,title,category="Crypto"):
    o=MarketObservation(venue=venue,venue_market_id=mid,title=title,category=category,status="Open",outcomes=("Yes","No"))
    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://099/94",),created_at=FIXED)
    m=MarketNormalizer().normalize(o,lineage=l94)
    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://099/95",),created_at=FIXED)
    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)

def classification(i):
    rule=TaxonomyRule("crypto",TaxonomyPath("btc","digital-assets","crypto","bitcoin","price-threshold"),category_keys=("crypto",),priority=1)
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-098",revision=UMD_098_REVISION,schema_version="1.0.0",parent_hashes=(i.identity_hash,),source_refs=("fixture://099/98",),created_at=FIXED)
    return MarketTaxonomyClassifier((rule,)).classify(i,lineage=l)

def lineage(ids):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-099",revision=UMD_099_REVISION,schema_version="1.0.0",parent_hashes=tuple(i.identity_hash for i in ids),source_refs=("fixture://099",),created_at=FIXED)

class TestUMD099(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_umd_099_market_alias_resolution())

    def test_alias_normalization(self):
        self.assertEqual(normalize_alias("  BTC > $100K?  "),"btc-100k")

    def test_resolution(self):
        i=identity("Kalshi","A","Will BTC exceed 100K?")
        idx=MarketAliasResolver().build_index(((i,classification(i),("Bitcoin above 100k","BTC > $100K?"),"fixture://source"),),lineage=lineage((i,)))
        self.assertEqual(idx.resolve("bitcoin above 100K"),i.canonical_market_id)
        self.assertEqual(idx.resolve("BTC > $100K?"),i.canonical_market_id)

    def test_unknown_alias(self):
        i=identity("Kalshi","A","Will BTC exceed 100K?")
        idx=MarketAliasResolver().build_index(((i,classification(i),("Bitcoin above 100k",),"fixture://source"),),lineage=lineage((i,)))
        self.assertIsNone(idx.resolve("ethereum above 10k"))

    def test_conflict_rejected(self):
        a=identity("Kalshi","A","Will BTC exceed 100K?")
        b=identity("Kalshi","B","Will BTC exceed 200K?")
        entries=(
            (a,classification(a),("BTC breakout",),"fixture://a"),
            (b,classification(b),("BTC breakout",),"fixture://b"),
        )
        with self.assertRaises(ValueError):
            MarketAliasResolver().build_index(entries,lineage=lineage((a,b)))

    def test_duplicate_same_market_collapsed(self):
        i=identity("Kalshi","A","Will BTC exceed 100K?")
        idx=MarketAliasResolver().build_index(((i,classification(i),("BTC 100K","btc 100k"),"fixture://source"),),lineage=lineage((i,)))
        self.assertEqual(len(idx.bindings),1)

    def test_deterministic(self):
        i=identity("Kalshi","A","Will BTC exceed 100K?")
        c=classification(i)
        l=lineage((i,))
        r=MarketAliasResolver()
        a=r.build_index(((i,c,("Bitcoin above 100k","BTC 100K"),"fixture://source"),),lineage=l)
        b=r.build_index(((i,c,("BTC 100K","Bitcoin above 100k"),"fixture://source"),),lineage=l)
        self.assertEqual(a.index_hash,b.index_hash)

    def test_lineage_required(self):
        i=identity("Kalshi","A","Will BTC exceed 100K?")
        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-099",revision=UMD_099_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)
        with self.assertRaises(ValueError):
            MarketAliasResolver().build_index(((i,classification(i),("BTC 100K",),"fixture://source"),),lineage=bad)

    def test_immutable(self):
        i=identity("Kalshi","A","Will BTC exceed 100K?")
        idx=MarketAliasResolver().build_index(((i,classification(i),("BTC 100K",),"fixture://source"),),lineage=lineage((i,)))
        with self.assertRaises((FrozenInstanceError,AttributeError)):
            idx.bindings=()

    def test_side_effects(self):
        m=build_umd_099_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-099 CERTIFICATION TEST");print(" MARKET ALIAS RESOLUTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD099))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_099_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] UMD-098 taxonomy classifications consumed read-only")
    print("[PASS] Deterministic alias indexing, conflict rejection, and resolution certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-099 CERTIFIED")
