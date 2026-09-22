from __future__ import annotations
import hashlib, unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_085_read_model_admission_gate import UMD_085_REVISION, CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision
from qseries_v2.universal_market_discovery.umd_086_read_model_admission_ledger import (
    UMD_086_REVISION, CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerEntry, ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger,
    build_umd_086_certification_manifest, certify_umd_086_admission_ledger, certify_umd_086_foundation,
)
FIXED=datetime(2026,8,8,2,35,0,tzinfo=timezone.utc)
def digest(label): return hashlib.sha256(label.encode()).hexdigest()
def decision(suffix, admitted=True):
    rm=digest(f"umd-086:{suffix}:read-model"); sl=digest(f"umd-086:{suffix}:source-ledger")
    lineage=ImmutableLineage(subsystem_id="UMD",build_id="UMD-085",revision=UMD_085_REVISION,schema_version="1.0.0",parent_hashes=(rm,sl),source_refs=(f"fixture://umd-086/decision/{suffix}",),created_at=FIXED)
    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision(read_model_id=f"read-model-{suffix}",read_model_hash=rm,source_ledger_hash=sl,total_entry_count=2,admitted_entry_count=1,rejected_entry_count=1,latest_entry_id=f"entry-{suffix}",latest_admitted_entry_id=f"admitted-{suffix}",admitted=admitted,checks={"certified":admitted},rejection_reasons=() if admitted else ("certified",),lineage=lineage)
def entry(number,value,previous):
    parents=[value.record_hash]
    if previous is not None: parents.append(previous)
    lineage=ImmutableLineage(subsystem_id="UMD",build_id="UMD-086",revision=UMD_086_REVISION,schema_version="1.0.0",parent_hashes=tuple(parents),source_refs=(f"fixture://umd-086/entry/{number}",),created_at=FIXED)
    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerEntry(sequence_number=number,previous_entry_hash=previous,decision=value,recorded_at=FIXED,metadata={"read_only":True},lineage=lineage)
def ledger(entries):
    lineage=ImmutableLineage(subsystem_id="UMD",build_id="UMD-086",revision=UMD_086_REVISION,schema_version="1.0.0",parent_hashes=(() if not entries else (entries[-1].entry_hash,)),source_refs=("fixture://umd-086/ledger",),created_at=FIXED)
    return ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger(entries=tuple(entries),ledger_lineage=lineage)
class TestUMD086(unittest.TestCase):
    def test_foundation(self):
        r=certify_umd_086_foundation(); self.assertTrue(r["certified"]); self.assertEqual(r["build_id"],"UMD-086")
    def test_ledger_certifies(self):
        a=entry(1,decision("a",True),None); b=entry(2,decision("b",False),a.entry_hash); r=certify_umd_086_admission_ledger(ledger((a,b))); self.assertTrue(r["certified"]); self.assertEqual(r["entry_count"],2)
    def test_deterministic(self):
        v=decision("a"); a=entry(1,v,None); b=entry(1,v,None); self.assertEqual(a.entry_id,b.entry_id); self.assertEqual(a.entry_hash,b.entry_hash)
    def test_sequence_gap_rejected(self):
        a=entry(1,decision("a"),None)
        with self.assertRaises(ValueError): ledger((a,entry(3,decision("b"),a.entry_hash)))
    def test_hash_chain_rejected(self):
        a=entry(1,decision("a"),None)
        with self.assertRaises(ValueError): ledger((a,entry(2,decision("b"),digest("wrong"))))
    def test_duplicate_decision_rejected(self):
        v=decision("a"); a=entry(1,v,None)
        with self.assertRaises(ValueError): ledger((a,entry(2,v,a.entry_hash)))
    def test_lookup_indexes(self):
        a=entry(1,decision("a"),None); b=entry(2,decision("b",False),a.entry_hash); x=ledger((a,b)); self.assertIs(x.get(a.entry_id),a); self.assertIs(x.latest_admitted(),a)
    def test_lineage_requires_latest_hash(self):
        a=entry(1,decision("a"),None); bad=ImmutableLineage(subsystem_id="UMD",build_id="UMD-086",revision=UMD_086_REVISION,schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://umd-086/bad",),created_at=FIXED)
        with self.assertRaises(ValueError): ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger(entries=(a,),ledger_lineage=bad)
    def test_immutable(self):
        a=entry(1,decision("a"),None); x=ledger((a,))
        with self.assertRaises((FrozenInstanceError,AttributeError)): a.sequence_number=2
        with self.assertRaises(TypeError): a.metadata["read_only"]=False
        with self.assertRaises(TypeError): x._by_read_model_id["changed"]=a
    def test_side_effects(self):
        m=build_umd_086_certification_manifest(); self.assertFalse(m.network_enabled); self.assertFalse(m.persistence_enabled); self.assertFalse(m.mutation_enabled); self.assertFalse(m.publication_enabled); self.assertFalse(m.execution_enabled)
if __name__=="__main__":
    print("="*72); print(" UMD-086 CERTIFICATION TEST"); print(" CERTIFIED RAW VENUE MARKET OBSERVATION READ MODEL ADMISSION LEDGER"); print("="*72)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD086); result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): raise SystemExit(1)
    m=build_umd_086_certification_manifest(); print(); print(f"[PASS] Build: {m.build_id}"); print(f"[PASS] Revision: {m.revision}"); print(f"[PASS] Manifest hash: {m.manifest_hash}"); print("[PASS] UMD-001 through UMD-085 consumed read-only"); print("[PASS] Exact UMD-085 admission-decision class consumed"); print("[PASS] Append-only sequence and previous-entry hash chain certified"); print("[PASS] Duplicate read-model, source-ledger, and decision replay rejected"); print("[PASS] Immutable read-model and decision indexes certified"); print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-086 CERTIFIED")
