from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_004_learning_event import LearningEvent,verify_learning_event
OCL_005_BUILD_ID="OCL-005";OCL_005_REVISION="OCL_005_LEARNING_EVIDENCE_LEDGER_FOUNDATION_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class LearningLedgerEntry:
 sequence:int; event_hash:str; parent_hash:str; entry_hash:str
@dataclass(frozen=True)
class LearningEvidenceLedger:
 entries:tuple[LearningLedgerEntry,...]; ledger_hash:str
def append_learning_event(ledger,event):
 if not verify_learning_event(event):raise ValueError("invalid learning event")
 parent=ledger.entries[-1].entry_hash if ledger.entries else "0"*64;seq=len(ledger.entries)+1
 raw={"sequence":seq,"event_hash":event.event_hash,"parent_hash":parent};entry=LearningLedgerEntry(seq,event.event_hash,parent,_h(raw))
 entries=ledger.entries+(entry,);return LearningEvidenceLedger(entries,_h([x.entry_hash for x in entries]))
def empty_learning_ledger():return LearningEvidenceLedger((),_h([]))
def verify_learning_ledger(l):
 parent="0"*64
 for i,e in enumerate(l.entries,1):
  if e.sequence!=i or e.parent_hash!=parent or e.entry_hash!=_h({"sequence":i,"event_hash":e.event_hash,"parent_hash":parent}):return False
  parent=e.entry_hash
 return l.ledger_hash==_h([x.entry_hash for x in l.entries])
def build_ocl_005_certification_manifest():return MappingProxyType({"build_id":OCL_005_BUILD_ID,"revision":OCL_005_REVISION,"ledger":"append_only_hash_chain","destructive_update":False,"next_capability":"calibration_and_source_reliability_learning"})
def verify_ocl_005_learning_evidence_ledger_foundation():
 from .ocl_003_outcome_observation import build_outcome_observation
 from .ocl_004_learning_event import assemble_learning_event
 o=build_outcome_observation("m","x",1,"t","s","a"*64);e=assemble_learning_event("m","b"*64,"c"*64,o)
 return verify_learning_ledger(append_learning_event(empty_learning_ledger(),e))
