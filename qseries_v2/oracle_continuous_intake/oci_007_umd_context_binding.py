from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping,Any
from .oci_006_oi_intake_binding import OIIntakeBinding,verify_oi_binding
OCI_007_BUILD_ID="OCI-007"; OCI_007_REVISION="OCI_007_UMD_MARKET_CONTEXT_BINDING_V1"
def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class UMDMarketContext:
 canonical_market_id:str; venue:str; market_title:str; taxonomy:tuple[str,...]=(); aliases:tuple[str,...]=()
@dataclass(frozen=True)
class UMDContextEnvelope:
 observation_id:str; context:UMDMarketContext; oi_envelope_hash:str; context_hash:str
@dataclass(frozen=True)
class UMDContextBinding:
 oi_binding_hash:str; contexts:tuple[UMDContextEnvelope,...]; binding_hash:str; umd_read_only:bool=True
def bind_oi_to_umd_context(oi:OIIntakeBinding,contexts:Mapping[str,UMDMarketContext])->UMDContextBinding:
 if not verify_oi_binding(oi): raise ValueError("invalid OCI-006 binding")
 rows=[]
 for e in oi.envelopes:
  c=contexts.get(e.observation_id)
  if c is None: continue
  if not c.canonical_market_id or not c.venue: raise ValueError("canonical UMD identity required")
  raw={"observation_id":e.observation_id,"canonical_market_id":c.canonical_market_id,"venue":c.venue,
       "market_title":c.market_title,"taxonomy":c.taxonomy,"aliases":c.aliases,"oi_envelope_hash":e.envelope_hash}
  rows.append(UMDContextEnvelope(e.observation_id,c,e.envelope_hash,_h(raw)))
 raw={"oi_binding_hash":oi.binding_hash,"contexts":[x.context_hash for x in rows],"umd_read_only":True}
 return UMDContextBinding(oi.binding_hash,tuple(rows),_h(raw))
def verify_umd_context_binding(b): return b.umd_read_only and all(x.context.canonical_market_id and x.context.venue for x in b.contexts)
def build_oci_007_certification_manifest(): return MappingProxyType({"build_id":OCI_007_BUILD_ID,"revision":OCI_007_REVISION,"umd_mutation":False,"network":False,"execution":False})
def verify_oci_007_umd_market_context_binding():
 from .oci_004_intake_cursor import build_genesis_cursor
 from .oci_005_intake_batch import IntakeRecord,assemble_intake_batch
 from .oci_006_oi_intake_binding import bind_batch_to_oi
 b=assemble_intake_batch(build_genesis_cursor("s","id"),(IntakeRecord.from_payload(1,"r",{"x":1}),),"2026-08-12T00:00:00Z")
 oi=bind_batch_to_oi(b); c={oi.envelopes[0].observation_id:UMDMarketContext("m1","kalshi","Market")}
 return verify_umd_context_binding(bind_oi_to_umd_context(oi,c))
