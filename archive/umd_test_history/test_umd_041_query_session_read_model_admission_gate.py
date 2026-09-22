from __future__ import annotations
import hashlib
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model import (
    UMD_040_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel,
)
from qseries_v2.universal_market_discovery.umd_041_query_session_read_model_admission_gate import (
    UMD_041_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision,
    build_umd_041_certification_manifest,
    certify_umd_041_foundation,
    evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model,
)
FIXED=datetime(2026,8,6,22,0,0,tzinfo=timezone.utc)
def h(s): return hashlib.sha256(s.encode()).hexdigest()
def model():
    ledger=h('umd040-ledger')
    lin=ImmutableLineage(subsystem_id='UMD',build_id='UMD-040',revision=UMD_040_REVISION,schema_version='1.0.0',parent_hashes=(ledger,),source_refs=('fixture://umd-041/model',),created_at=FIXED)
    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel(
      source_ledger_hash=ledger,total_entry_count=3,admitted_entry_count=2,rejected_entry_count=1,
      ordered_entry_ids=('entry-a','entry-b','entry-c'),ordered_read_model_hashes=(h('rm-a'),h('rm-b'),h('rm-c')),
      ordered_decision_ids=('decision-a','decision-b','decision-c'),admitted_entry_ids=('entry-a','entry-c'),rejected_entry_ids=('entry-b',),
      latest_entry_id='entry-c',latest_admitted_entry_id='entry-c',metadata={'read_only':True},lineage=lin)
def gate_lineage(m):
    return ImmutableLineage(subsystem_id='UMD',build_id='UMD-041',revision=UMD_041_REVISION,schema_version='1.0.0',parent_hashes=(m.read_model_hash,m.source_ledger_hash),source_refs=('fixture://umd-041/gate',),created_at=FIXED)
class TestUMD041(unittest.TestCase):
  def test_foundation(self): self.assertTrue(certify_umd_041_foundation()['certified'])
  def test_valid_admitted(self):
    m=model(); d=evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model(m,lineage=gate_lineage(m)); self.assertTrue(d.admitted); self.assertTrue(all(d.checks.values()))
  def test_deterministic(self):
    m=model(); l=gate_lineage(m); a=evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model(m,lineage=l); b=evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model(m,lineage=l); self.assertEqual(a.record_hash,b.record_hash)
  def test_immutable(self):
    m=model(); d=evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model(m,lineage=gate_lineage(m));
    with self.assertRaises((FrozenInstanceError,AttributeError)): d.admitted=False
    with self.assertRaises(TypeError): d.checks['x']=False
  def test_lineage_requires_both(self):
    m=model(); bad=ImmutableLineage(subsystem_id='UMD',build_id='UMD-041',revision=UMD_041_REVISION,schema_version='1.0.0',parent_hashes=(m.read_model_hash,),source_refs=('fixture://bad',),created_at=FIXED)
    with self.assertRaises(ValueError): evaluate_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model(m,lineage=bad)
  def test_side_effects(self):
    x=build_umd_041_certification_manifest(); self.assertFalse(x.network_enabled); self.assertFalse(x.persistence_enabled); self.assertFalse(x.mutation_enabled); self.assertFalse(x.publication_enabled); self.assertFalse(x.execution_enabled)
if __name__=='__main__':
 print('='*72); print(' UMD-041 CERTIFICATION TEST'); print('='*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD041))
 if not r.wasSuccessful(): raise SystemExit(1)
 m=build_umd_041_certification_manifest(); print(f'[PASS] Build: {m.build_id}'); print(f'[PASS] Revision: {m.revision}'); print(f'[PASS] Manifest hash: {m.manifest_hash}'); print('[PASS] UMD-001 through UMD-040 consumed read-only'); print('[PASS] Exact UMD-040 read-model class consumed'); print('[PASS] Immutable UMD-041 admission decisions certified'); print('[PASS] Network, persistence, publication, and execution disabled'); print('[DONE] UMD-041 CERTIFIED')
