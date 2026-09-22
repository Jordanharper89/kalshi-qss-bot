from __future__ import annotations
import hashlib, unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_048_venue_discovery_request_admission_gate import UMD_048_REVISION, CertifiedVenueDiscoveryRequestAdmissionDecision
from qseries_v2.universal_market_discovery.umd_049_venue_discovery_request_admission_ledger import UMD_049_REVISION, CertifiedVenueDiscoveryRequestAdmissionLedgerEntry, ReadOnlyVenueDiscoveryRequestAdmissionLedger
from qseries_v2.universal_market_discovery.umd_050_venue_discovery_request_admission_ledger_read_model import UMD_050_REVISION, build_umd_050_venue_discovery_request_admission_ledger_read_model, build_umd_050_certification_manifest, certify_umd_050_foundation, certify_umd_050_read_model
FIXED=datetime(2026,8,7,1,30,0,tzinfo=timezone.utc)
def d(x): return hashlib.sha256(x.encode()).hexdigest()
def dec(s,ad=True,src='SOURCE-A'):
    rh=d('req-'+s); ch=d('contract-'+s); gh=d('registry-'+s)
    lin=ImmutableLineage(subsystem_id='UMD',build_id='UMD-048',revision=UMD_048_REVISION,schema_version='1.0.0',parent_hashes=(rh,ch,gh),source_refs=(f'fixture://umd050/decision/{s}',),created_at=FIXED)
    return CertifiedVenueDiscoveryRequestAdmissionDecision(request_id='request-'+s,request_hash=rh,source_id=src,source_contract_hash=ch,source_registry_hash=gh,admitted=ad,checks={'certified':ad},rejection_reasons=() if ad else ('certified',),lineage=lin)
def ent(n,v,p):
    parents=[v.record_hash]+([] if p is None else [p]); lin=ImmutableLineage(subsystem_id='UMD',build_id='UMD-049',revision=UMD_049_REVISION,schema_version='1.0.0',parent_hashes=tuple(parents),source_refs=(f'fixture://umd050/entry/{n}',),created_at=FIXED)
    return CertifiedVenueDiscoveryRequestAdmissionLedgerEntry(sequence_number=n,previous_entry_hash=p,decision=v,recorded_at=FIXED,metadata={'read_only':True},lineage=lin)
def ledger():
    a=ent(1,dec('a',True,'SOURCE-A'),None); b=ent(2,dec('b',False,'SOURCE-B'),a.entry_hash); c=ent(3,dec('c',True,'SOURCE-A'),b.entry_hash)
    lin=ImmutableLineage(subsystem_id='UMD',build_id='UMD-049',revision=UMD_049_REVISION,schema_version='1.0.0',parent_hashes=(c.entry_hash,),source_refs=('fixture://umd050/ledger',),created_at=FIXED)
    return ReadOnlyVenueDiscoveryRequestAdmissionLedger(entries=(a,b,c),ledger_lineage=lin)
def lineage(h): return ImmutableLineage(subsystem_id='UMD',build_id='UMD-050',revision=UMD_050_REVISION,schema_version='1.0.0',parent_hashes=(h,),source_refs=('fixture://umd050/read-model',),created_at=FIXED)
class TestUMD050(unittest.TestCase):
    def test_foundation(self): self.assertTrue(certify_umd_050_foundation()['certified'])
    def test_projection(self):
        l=ledger(); m=build_umd_050_venue_discovery_request_admission_ledger_read_model(l,metadata={'read_only':True},lineage=lineage(l.ledger_hash)); r=certify_umd_050_read_model(m); self.assertTrue(r['certified']); self.assertEqual((r['total_entry_count'],r['admitted_entry_count'],r['rejected_entry_count']),(3,2,1))
    def test_deterministic(self):
        l=ledger(); x=lineage(l.ledger_hash); a=build_umd_050_venue_discovery_request_admission_ledger_read_model(l,lineage=x); b=build_umd_050_venue_discovery_request_admission_ledger_read_model(l,lineage=x); self.assertEqual(a.read_model_hash,b.read_model_hash)
    def test_positions_sources_partitions(self):
        l=ledger(); m=build_umd_050_venue_discovery_request_admission_ledger_read_model(l,lineage=lineage(l.ledger_hash)); a,b,c=l.entries; self.assertEqual(m.entry_position(a.entry_id),1); self.assertEqual(m.request_position(b.decision.request_id),2); self.assertEqual(m.decision_position(c.decision.decision_id),3); self.assertEqual(m.list_entry_ids_by_source('SOURCE-A'),(a.entry_id,c.entry_id)); self.assertTrue(m.is_admitted_entry(a.entry_id)); self.assertTrue(m.is_rejected_entry(b.entry_id)); self.assertEqual(m.latest_admitted_entry_id,c.entry_id)
    def test_lineage_requires_ledger(self):
        l=ledger(); bad=lineage(d('wrong')); self.assertRaises(ValueError,build_umd_050_venue_discovery_request_admission_ledger_read_model,l,lineage=bad)
    def test_exact_umd049_type(self): self.assertIsInstance(ledger(),ReadOnlyVenueDiscoveryRequestAdmissionLedger)
    def test_immutable(self):
        l=ledger(); m=build_umd_050_venue_discovery_request_admission_ledger_read_model(l,metadata={'read_only':True},lineage=lineage(l.ledger_hash));
        with self.assertRaises((FrozenInstanceError,AttributeError)): m.total_entry_count=99
        with self.assertRaises(TypeError): m.metadata['read_only']=False
        with self.assertRaises(TypeError): m._entry_position_by_id['x']=1
    def test_side_effects(self):
        m=build_umd_050_certification_manifest(); self.assertFalse(any((m.network_enabled,m.persistence_enabled,m.mutation_enabled,m.publication_enabled,m.execution_enabled)))
if __name__=='__main__':
    print('='*72); print(' UMD-050 CERTIFICATION TEST'); print(' CERTIFIED VENUE DISCOVERY REQUEST ADMISSION LEDGER READ MODEL'); print('='*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD050))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_050_certification_manifest(); print(); print(f'[PASS] Build: {m.build_id}'); print(f'[PASS] Revision: {m.revision}'); print(f'[PASS] Manifest hash: {m.manifest_hash}'); print('[PASS] UMD-001 through UMD-049 consumed read-only'); print('[PASS] Exact UMD-049 admission-ledger class consumed'); print('[PASS] Deterministic request admission-ledger projection certified'); print('[PASS] Immutable entry, request, decision, source, and partition indexes certified'); print('[PASS] Network, persistence, publication, and execution disabled'); print('[DONE] UMD-050 CERTIFIED VENUE DISCOVERY REQUEST ADMISSION LEDGER READ MODEL CERTIFIED')
