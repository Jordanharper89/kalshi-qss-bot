from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_094_market_normalization import UMD_094_REVISION,MarketObservation,MarketNormalizer
from qseries_v2.universal_market_discovery.umd_095_market_identity import UMD_095_REVISION,CanonicalMarketIdentityResolver
from qseries_v2.universal_market_discovery.umd_096_duplicate_resolution import UMD_096_REVISION,CrossVenueDuplicateResolver
from qseries_v2.universal_market_discovery.umd_097_market_relationship_graph import UMD_097_REVISION,MarketRelationshipGraphBuilder
from qseries_v2.universal_market_discovery.umd_098_market_taxonomy import UMD_098_REVISION,TaxonomyPath,TaxonomyRule,MarketTaxonomyClassifier
from qseries_v2.universal_market_discovery.umd_099_market_alias_resolution import UMD_099_REVISION,MarketAliasResolver
from qseries_v2.universal_market_discovery.umd_100_market_lifecycle import UMD_100_REVISION,MarketLifecycleResolver
from qseries_v2.universal_market_discovery.umd_101_outcome_schema import UMD_101_REVISION,OutcomeSchemaResolver
from qseries_v2.universal_market_discovery.umd_102_canonical_market_record import (
    UMD_102_REVISION,CanonicalMarketRecordAssembler,build_umd_102_certification_manifest,verify_umd_102_canonical_market_record_assembly,
)

FIXED=datetime(2026,8,9,12,20,tzinfo=timezone.utc)

def identity(venue,mid):
    o=MarketObservation(venue=venue,venue_market_id=mid,title="Will BTC exceed 100K?",category="Crypto",status="Open",close_time="2026-08-10T00:00:00Z",settlement_time="2026-08-11T00:00:00Z",outcomes=("Yes","No"))
    l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://102/94",),created_at=FIXED)
    m=MarketNormalizer().normalize(o,lineage=l94)
    l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://102/95",),created_at=FIXED)
    return CanonicalMarketIdentityResolver().resolve(m,lineage=l95)

def artifacts(ids):
    primary=min(ids,key=lambda x:x.identity_hash)
    l98=ImmutableLineage(subsystem_id="UMD",build_id="UMD-098",revision=UMD_098_REVISION,schema_version="1.0.0",parent_hashes=(primary.identity_hash,),source_refs=("fixture://102/98",),created_at=FIXED)
    classification=MarketTaxonomyClassifier((TaxonomyRule("crypto",TaxonomyPath("btc","digital-assets","crypto","bitcoin","price-threshold"),category_keys=("crypto",),priority=1),)).classify(primary,lineage=l98)
    l100=ImmutableLineage(subsystem_id="UMD",build_id="UMD-100",revision=UMD_100_REVISION,schema_version="1.0.0",parent_hashes=(primary.identity_hash,),source_refs=("fixture://102/100",),created_at=FIXED)
    lifecycle=MarketLifecycleResolver().resolve(primary,as_of=FIXED,lineage=l100)
    l101=ImmutableLineage(subsystem_id="UMD",build_id="UMD-101",revision=UMD_101_REVISION,schema_version="1.0.0",parent_hashes=(primary.identity_hash,),source_refs=("fixture://102/101",),created_at=FIXED)
    outcome=OutcomeSchemaResolver().resolve(primary,lineage=l101)
    l99=ImmutableLineage(subsystem_id="UMD",build_id="UMD-099",revision=UMD_099_REVISION,schema_version="1.0.0",parent_hashes=tuple(x.identity_hash for x in ids),source_refs=("fixture://102/99",),created_at=FIXED)
    entries=tuple((x,classification if x is primary else classification,("BTC above 100K",),f"fixture://alias/{n}") for n,x in enumerate(ids))
    # Alias resolver requires classification identity to match each identity, so only bind aliases to primary here.
    alias_index=MarketAliasResolver().build_index(((primary,classification,("BTC above 100K","BTC 100K"),"fixture://alias/primary"),),lineage=ImmutableLineage(subsystem_id="UMD",build_id="UMD-099",revision=UMD_099_REVISION,schema_version="1.0.0",parent_hashes=(primary.identity_hash,),source_refs=("fixture://102/99",),created_at=FIXED))
    l97=ImmutableLineage(subsystem_id="UMD",build_id="UMD-097",revision=UMD_097_REVISION,schema_version="1.0.0",parent_hashes=tuple(x.identity_hash for x in ids),source_refs=("fixture://102/97",),created_at=FIXED)
    graph=MarketRelationshipGraphBuilder().build(ids,(),lineage=l97)
    dup=None
    if len({x.venue_key for x in ids})>1:
        l96=ImmutableLineage(subsystem_id="UMD",build_id="UMD-096",revision=UMD_096_REVISION,schema_version="1.0.0",parent_hashes=tuple(x.identity_hash for x in ids),source_refs=("fixture://102/96",),created_at=FIXED)
        dup=CrossVenueDuplicateResolver().resolve(ids,lineage=l96)[0]
    return primary,classification,lifecycle,outcome,alias_index,graph,dup

def record_lineage(ids,classification,lifecycle,outcome,alias_index,graph,dup):
    parents=[x.identity_hash for x in ids]+[classification.classification_hash,lifecycle.lifecycle_hash,outcome.outcome_schema_hash,alias_index.index_hash,graph.graph_hash]
    if dup is not None: parents.append(dup.group_hash)
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision=UMD_102_REVISION,schema_version="1.0.0",parent_hashes=tuple(parents),source_refs=("fixture://102",),created_at=FIXED)

class TestUMD102(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_102_canonical_market_record_assembly())
    def test_single_venue_record(self):
        ids=(identity("Kalshi","A"),); _,c,l,o,a,g,d=artifacts(ids); r=CanonicalMarketRecordAssembler().assemble(ids,classification=c,lifecycle=l,outcome_schema=o,alias_index=a,relationship_graph=g,duplicate_group=d,lineage=record_lineage(ids,c,l,o,a,g,d)); self.assertEqual(len(r.venue_bindings),1); self.assertEqual(r.duplicate_group_hash,"")
    def test_cross_venue_record(self):
        ids=(identity("Kalshi","A"),identity("Polymarket","B")); _,c,l,o,a,g,d=artifacts(ids); r=CanonicalMarketRecordAssembler().assemble(ids,classification=c,lifecycle=l,outcome_schema=o,alias_index=a,relationship_graph=g,duplicate_group=d,lineage=record_lineage(ids,c,l,o,a,g,d)); self.assertEqual(len(r.venue_bindings),2); self.assertTrue(r.duplicate_group_hash)
    def test_cross_venue_requires_duplicate_group(self):
        ids=(identity("Kalshi","A"),identity("Polymarket","B")); _,c,l,o,a,g,d=artifacts(ids)
        with self.assertRaises(ValueError): CanonicalMarketRecordAssembler().assemble(ids,classification=c,lifecycle=l,outcome_schema=o,alias_index=a,relationship_graph=g,duplicate_group=None,lineage=record_lineage(ids,c,l,o,a,g,d))
    def test_different_market_rejected(self):
        a=identity("Kalshi","A")
        o=MarketObservation(venue="Kalshi",venue_market_id="B",title="Will BTC exceed 200K?",category="Crypto",status="Open",outcomes=("Yes","No"))
        l94=ImmutableLineage(subsystem_id="UMD",build_id="UMD-094",revision=UMD_094_REVISION,schema_version="1.0.0",parent_hashes=(o.observation_hash,),source_refs=("fixture://102/diff94",),created_at=FIXED); m=MarketNormalizer().normalize(o,lineage=l94)
        l95=ImmutableLineage(subsystem_id="UMD",build_id="UMD-095",revision=UMD_095_REVISION,schema_version="1.0.0",parent_hashes=(m.normalized_market_hash,),source_refs=("fixture://102/diff95",),created_at=FIXED); b=CanonicalMarketIdentityResolver().resolve(m,lineage=l95)
        _,c,l,out,ai,g,d=artifacts((a,))
        with self.assertRaises(ValueError): CanonicalMarketRecordAssembler().assemble((a,b),classification=c,lifecycle=l,outcome_schema=out,alias_index=ai,relationship_graph=g,lineage=record_lineage((a,),c,l,out,ai,g,d))
    def test_aliases_canonical(self):
        ids=(identity("Kalshi","A"),); _,c,l,o,a,g,d=artifacts(ids); r=CanonicalMarketRecordAssembler().assemble(ids,classification=c,lifecycle=l,outcome_schema=o,alias_index=a,relationship_graph=g,lineage=record_lineage(ids,c,l,o,a,g,d)); self.assertEqual(r.alias_keys,("btc-100k","btc-above-100k"))
    def test_primary_deterministic(self):
        ids=(identity("Kalshi","A"),identity("Polymarket","B")); _,c,l,o,a,g,d=artifacts(ids); r=CanonicalMarketRecordAssembler().assemble(tuple(reversed(ids)),classification=c,lifecycle=l,outcome_schema=o,alias_index=a,relationship_graph=g,duplicate_group=d,lineage=record_lineage(ids,c,l,o,a,g,d)); self.assertEqual(r.primary_identity_hash,min(x.identity_hash for x in ids))
    def test_lineage_required(self):
        ids=(identity("Kalshi","A"),); _,c,l,o,a,g,d=artifacts(ids); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision=UMD_102_REVISION,schema_version="1.0.0",parent_hashes=("0"*64,),source_refs=("bad",),created_at=FIXED)
        with self.assertRaises(ValueError): CanonicalMarketRecordAssembler().assemble(ids,classification=c,lifecycle=l,outcome_schema=o,alias_index=a,relationship_graph=g,lineage=bad)
    def test_immutable(self):
        ids=(identity("Kalshi","A"),); _,c,l,o,a,g,d=artifacts(ids); r=CanonicalMarketRecordAssembler().assemble(ids,classification=c,lifecycle=l,outcome_schema=o,alias_index=a,relationship_graph=g,lineage=record_lineage(ids,c,l,o,a,g,d))
        with self.assertRaises((FrozenInstanceError,AttributeError)): r.alias_keys=()
    def test_deterministic(self):
        ids=(identity("Kalshi","A"),); _,c,l,o,a,g,d=artifacts(ids); ln=record_lineage(ids,c,l,o,a,g,d); x=CanonicalMarketRecordAssembler(); self.assertEqual(x.assemble(ids,classification=c,lifecycle=l,outcome_schema=o,alias_index=a,relationship_graph=g,lineage=ln).record_hash,x.assemble(ids,classification=c,lifecycle=l,outcome_schema=o,alias_index=a,relationship_graph=g,lineage=ln).record_hash)
    def test_side_effects(self):
        m=build_umd_102_certification_manifest(); self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72); print(" UMD-102 CERTIFICATION TEST"); print(" CANONICAL MARKET RECORD ASSEMBLY"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD102))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_102_certification_manifest(); print(); print(f"[PASS] Build: {m['build_id']}"); print(f"[PASS] Revision: {m['revision']}"); print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] UMD-095 through UMD-101 capability artifacts assembled read-only"); print("[PASS] Deterministic canonical market record assembly certified")
    print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-102 CERTIFIED")
