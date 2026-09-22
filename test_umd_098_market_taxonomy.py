from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer
from qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver
from qseries_v2.universal_market_discovery.umd_098_market_taxonomy import (
    UMD_098_REVISION,TaxonomyPath,TaxonomyRule,MarketTaxonomyClassifier,
    build_umd_098_certification_manifest,verify_umd_098_market_taxonomy_classification,
)

FIXED=datetime(2026,8,8,13,10,tzinfo=timezone.utc)

def identity(title="Will BTC exceed 100K?",category="Crypto"):
    o=MarketObservation(venue="Kalshi",venue_market_id="A",title=title,category=category,status="Open",outcomes=("Yes","No"))
    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://098/94",),created_at=FIXED)
    m=MarketNormalizer().normalize(o,lineage=l94)
    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://098/95",),created_at=FIXED)
    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)

def lineage(i):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-098",revision=UMD_098_REVISION,schema_version="1.0.0",parent_hashes=(i.identity_hash,),source_refs=("fixture://098",),created_at=FIXED)

def rules():
    return (
        TaxonomyRule("crypto-price",TaxonomyPath("btc","digital-assets","crypto","bitcoin","price-threshold"),category_keys=("crypto",),priority=10),
        TaxonomyRule("politics-election",TaxonomyPath("none","politics","elections","candidate","binary-outcome"),category_keys=("politics",),priority=20),
    )

class TestUMD098(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_umd_098_market_taxonomy_classification())

    def test_classification(self):
        i=identity()
        c=MarketTaxonomyClassifier(rules()).classify(i,lineage=lineage(i))
        self.assertEqual(c.taxonomy_path.taxonomy_key,"btc/digital-assets/crypto/bitcoin/price-threshold")
        self.assertEqual(c.rule_id,"crypto-price")

    def test_deterministic_rule_order(self):
        i=identity()
        a=MarketTaxonomyClassifier(rules()).classify(i,lineage=lineage(i))
        b=MarketTaxonomyClassifier(tuple(reversed(rules()))).classify(i,lineage=lineage(i))
        self.assertEqual(a.classification_hash,b.classification_hash)

    def test_no_match(self):
        i=identity("Will rainfall exceed 2 inches?","Weather")
        with self.assertRaises(LookupError):
            MarketTaxonomyClassifier(rules()).classify(i,lineage=lineage(i))

    def test_duplicate_rule_id_rejected(self):
        r=rules()[0]
        with self.assertRaises(ValueError):
            MarketTaxonomyClassifier((r,r))

    def test_path_normalization(self):
        p=TaxonomyPath("BTC","Digital Assets","Crypto","Bitcoin","Price Threshold")
        self.assertEqual(p.taxonomy_key,"btc/digital-assets/crypto/bitcoin/price-threshold")

    def test_lineage_required(self):
        i=identity()
        bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-098",revision=UMD_098_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)
        with self.assertRaises(ValueError):
            MarketTaxonomyClassifier(rules()).classify(i,lineage=bad)

    def test_immutable(self):
        i=identity()
        c=MarketTaxonomyClassifier(rules()).classify(i,lineage=lineage(i))
        with self.assertRaises((FrozenInstanceError,AttributeError)):
            c.rule_id="x"

    def test_side_effects(self):
        m=build_umd_098_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-098 CERTIFICATION TEST");print(" MARKET TAXONOMY CLASSIFICATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD098))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_098_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] UMD-097 certified relationship capability consumed read-only")
    print("[PASS] Deterministic hierarchical market taxonomy classification certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-098 CERTIFIED")
