from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_049_venue_discovery_request_admission_ledger import ReadOnlyVenueDiscoveryRequestAdmissionLedger

UMD_050_BUILD_ID="UMD-050"
UMD_050_BUILD_NAME="Certified Venue Discovery Request Admission Ledger Read Model"
UMD_050_REVISION="UMD_050_CERTIFIED_VENUE_DISCOVERY_REQUEST_ADMISSION_LEDGER_READ_MODEL_V1"
UMD_050_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","automatic_discovery","ledger_append","ledger_mutation","read_model_mutation","persistence","publication","order_submission","trade_execution")

def _text(v,n):
    if not isinstance(v,str): raise TypeError(f"{n} must be a string")
    v=" ".join(v.strip().split())
    if not v: raise ValueError(f"{n} must not be empty")
    return v

def _sha(v,n):
    v=_text(v,n).lower()
    if len(v)!=64 or any(c not in '0123456789abcdef' for c in v): raise ValueError(f"{n} must be lowercase SHA-256 hexadecimal")
    return v

def _freeze(v):
    if not isinstance(v,Mapping): raise TypeError('metadata must be a mapping')
    return MappingProxyType(dict(sorted((str(k),x) for k,x in v.items())))

@dataclass(frozen=True,slots=True)
class CertifiedVenueDiscoveryRequestAdmissionLedgerReadModel:
    source_ledger_hash:str
    total_entry_count:int
    admitted_entry_count:int
    rejected_entry_count:int
    ordered_entry_ids:Tuple[str,...]
    ordered_request_ids:Tuple[str,...]
    ordered_request_hashes:Tuple[str,...]
    ordered_decision_ids:Tuple[str,...]
    ordered_source_ids:Tuple[str,...]
    admitted_entry_ids:Tuple[str,...]
    rejected_entry_ids:Tuple[str,...]
    latest_entry_id:str|None
    latest_admitted_entry_id:str|None
    metadata:Mapping[str,Any]
    lineage:ImmutableLineage
    _entry_position_by_id:Mapping[str,int]=field(init=False,repr=False)
    _request_position_by_id:Mapping[str,int]=field(init=False,repr=False)
    _decision_position_by_id:Mapping[str,int]=field(init=False,repr=False)
    _entry_ids_by_source_id:Mapping[str,Tuple[str,...]]=field(init=False,repr=False)
    def __post_init__(self):
        object.__setattr__(self,'source_ledger_hash',_sha(self.source_ledger_hash,'source_ledger_hash'))
        for n in ('total_entry_count','admitted_entry_count','rejected_entry_count'):
            v=getattr(self,n)
            if not isinstance(v,int): raise TypeError(f'{n} must be an integer')
            if v<0: raise ValueError(f'{n} must be non-negative')
        if self.admitted_entry_count+self.rejected_entry_count!=self.total_entry_count: raise ValueError('admission counts must partition total count')
        names=('ordered_entry_ids','ordered_request_ids','ordered_request_hashes','ordered_decision_ids','ordered_source_ids','admitted_entry_ids','rejected_entry_ids')
        for n in names:
            if not isinstance(getattr(self,n),tuple): object.__setattr__(self,n,tuple(getattr(self,n)))
        object.__setattr__(self,'ordered_entry_ids',tuple(_text(x,'entry_id') for x in self.ordered_entry_ids))
        object.__setattr__(self,'ordered_request_ids',tuple(_text(x,'request_id') for x in self.ordered_request_ids))
        object.__setattr__(self,'ordered_request_hashes',tuple(_sha(x,'request_hash') for x in self.ordered_request_hashes))
        object.__setattr__(self,'ordered_decision_ids',tuple(_text(x,'decision_id') for x in self.ordered_decision_ids))
        object.__setattr__(self,'ordered_source_ids',tuple(_text(x,'source_id') for x in self.ordered_source_ids))
        object.__setattr__(self,'admitted_entry_ids',tuple(_text(x,'admitted_entry_id') for x in self.admitted_entry_ids))
        object.__setattr__(self,'rejected_entry_ids',tuple(_text(x,'rejected_entry_id') for x in self.rejected_entry_ids))
        for n in ('ordered_entry_ids','ordered_request_ids','ordered_request_hashes','ordered_decision_ids','ordered_source_ids'):
            if len(getattr(self,n))!=self.total_entry_count: raise ValueError(f'{n} length mismatch')
        if len(self.admitted_entry_ids)!=self.admitted_entry_count or len(self.rejected_entry_ids)!=self.rejected_entry_count: raise ValueError('partition length mismatch')
        for n in ('ordered_entry_ids','ordered_request_ids','ordered_request_hashes','ordered_decision_ids'):
            if len(set(getattr(self,n)))!=len(getattr(self,n)): raise ValueError(f'{n} must be unique')
        if set(self.admitted_entry_ids)&set(self.rejected_entry_ids): raise ValueError('admission partitions must be disjoint')
        if set(self.admitted_entry_ids)|set(self.rejected_entry_ids)!=set(self.ordered_entry_ids): raise ValueError('admission partitions must cover entries')
        if self.latest_entry_id is None:
            if self.ordered_entry_ids: raise ValueError('latest_entry_id required')
        else:
            object.__setattr__(self,'latest_entry_id',_text(self.latest_entry_id,'latest_entry_id'))
            if self.latest_entry_id!=self.ordered_entry_ids[-1]: raise ValueError('latest_entry_id mismatch')
        if self.latest_admitted_entry_id is None:
            if self.admitted_entry_ids: raise ValueError('latest_admitted_entry_id required')
        else:
            object.__setattr__(self,'latest_admitted_entry_id',_text(self.latest_admitted_entry_id,'latest_admitted_entry_id'))
            if self.latest_admitted_entry_id!=self.admitted_entry_ids[-1]: raise ValueError('latest_admitted_entry_id mismatch')
        object.__setattr__(self,'metadata',_freeze(self.metadata))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_050_BUILD_ID: raise ValueError('read-model lineage identity invalid')
        if self.source_ledger_hash not in self.lineage.parent_hashes: raise ValueError('lineage must include source ledger hash')
        object.__setattr__(self,'_entry_position_by_id',MappingProxyType({x:i for i,x in enumerate(self.ordered_entry_ids,1)}))
        object.__setattr__(self,'_request_position_by_id',MappingProxyType({x:i for i,x in enumerate(self.ordered_request_ids,1)}))
        object.__setattr__(self,'_decision_position_by_id',MappingProxyType({x:i for i,x in enumerate(self.ordered_decision_ids,1)}))
        groups={}
        for eid,sid in zip(self.ordered_entry_ids,self.ordered_source_ids): groups.setdefault(sid,[]).append(eid)
        object.__setattr__(self,'_entry_ids_by_source_id',MappingProxyType({k:tuple(v) for k,v in groups.items()}))
    @property
    def read_model_id(self):
        return 'umd:venue-discovery-request-admission-ledger-read-model:'+deterministic_sha256({'source_ledger_hash':self.source_ledger_hash,'ordered_entry_ids':self.ordered_entry_ids,'ordered_request_ids':self.ordered_request_ids,'ordered_decision_ids':self.ordered_decision_ids})
    def entry_position(self,x): return self._entry_position_by_id.get(_text(x,'entry_id'))
    def request_position(self,x): return self._request_position_by_id.get(_text(x,'request_id'))
    def decision_position(self,x): return self._decision_position_by_id.get(_text(x,'decision_id'))
    def list_entry_ids_by_source(self,x): return self._entry_ids_by_source_id.get(_text(x,'source_id'),())
    def is_admitted_entry(self,x): return _text(x,'entry_id') in self.admitted_entry_ids
    def is_rejected_entry(self,x): return _text(x,'entry_id') in self.rejected_entry_ids
    def to_canonical_dict(self):
        return {'read_model_id':self.read_model_id,'source_ledger_hash':self.source_ledger_hash,'total_entry_count':self.total_entry_count,'admitted_entry_count':self.admitted_entry_count,'rejected_entry_count':self.rejected_entry_count,'ordered_entry_ids':self.ordered_entry_ids,'ordered_request_ids':self.ordered_request_ids,'ordered_request_hashes':self.ordered_request_hashes,'ordered_decision_ids':self.ordered_decision_ids,'ordered_source_ids':self.ordered_source_ids,'admitted_entry_ids':self.admitted_entry_ids,'rejected_entry_ids':self.rejected_entry_ids,'latest_entry_id':self.latest_entry_id,'latest_admitted_entry_id':self.latest_admitted_entry_id,'metadata':self.metadata,'lineage':self.lineage}
    @property
    def read_model_hash(self): return deterministic_sha256(self.to_canonical_dict())

def build_umd_050_venue_discovery_request_admission_ledger_read_model(ledger:ReadOnlyVenueDiscoveryRequestAdmissionLedger,*,metadata=None,lineage:ImmutableLineage):
    if not isinstance(ledger,ReadOnlyVenueDiscoveryRequestAdmissionLedger): raise TypeError('ledger must be certified UMD-049 ledger')
    e=ledger.entries; a=ledger.admitted_entries(); r=ledger.rejected_entries()
    return CertifiedVenueDiscoveryRequestAdmissionLedgerReadModel(source_ledger_hash=ledger.ledger_hash,total_entry_count=len(e),admitted_entry_count=len(a),rejected_entry_count=len(r),ordered_entry_ids=tuple(x.entry_id for x in e),ordered_request_ids=tuple(x.decision.request_id for x in e),ordered_request_hashes=tuple(x.decision.request_hash for x in e),ordered_decision_ids=tuple(x.decision.decision_id for x in e),ordered_source_ids=tuple(x.decision.source_id for x in e),admitted_entry_ids=tuple(x.entry_id for x in a),rejected_entry_ids=tuple(x.entry_id for x in r),latest_entry_id=None if not e else e[-1].entry_id,latest_admitted_entry_id=None if not a else a[-1].entry_id,metadata={} if metadata is None else metadata,lineage=lineage)

@dataclass(frozen=True,slots=True)
class UMD050CertificationManifest:
    subsystem_id:str; build_id:str; revision:str; schema_version:str; upstream_builds:Tuple[str,...]; read_model_mode:str; prohibited_capabilities:Tuple[str,...]; network_enabled:bool; persistence_enabled:bool; mutation_enabled:bool; publication_enabled:bool; execution_enabled:bool
    def to_canonical_dict(self): return {n:getattr(self,n) for n in self.__dataclass_fields__}
    @property
    def manifest_hash(self): return deterministic_sha256(self.to_canonical_dict())

def build_umd_050_certification_manifest():
    return UMD050CertificationManifest('UMD','UMD-050',UMD_050_REVISION,UMD_050_SCHEMA_VERSION,tuple(f'UMD-{n:03d}' for n in range(1,50)),'deterministic_read_only_projection',PROHIBITED_CAPABILITIES,False,False,False,False,False)

def certify_umd_050_read_model(m):
    checks={'count_partition_valid':m.admitted_entry_count+m.rejected_entry_count==m.total_entry_count,'entry_ids_unique':len(set(m.ordered_entry_ids))==len(m.ordered_entry_ids),'request_ids_unique':len(set(m.ordered_request_ids))==len(m.ordered_request_ids),'request_hashes_unique':len(set(m.ordered_request_hashes))==len(m.ordered_request_hashes),'decision_ids_unique':len(set(m.ordered_decision_ids))==len(m.ordered_decision_ids),'partition_complete':set(m.admitted_entry_ids)|set(m.rejected_entry_ids)==set(m.ordered_entry_ids),'partition_disjoint':not set(m.admitted_entry_ids)&set(m.rejected_entry_ids),'lineage_bound':m.source_ledger_hash in m.lineage.parent_hashes,'deterministic_replay':m.read_model_hash==deterministic_sha256(m.to_canonical_dict()),'read_only_indexes':all(isinstance(x,MappingProxyType) for x in (m._entry_position_by_id,m._request_position_by_id,m._decision_position_by_id,m._entry_ids_by_source_id))}
    failed=tuple(k for k,v in checks.items() if not v)
    return MappingProxyType({'certified':not failed,'read_model_id':m.read_model_id,'read_model_hash':m.read_model_hash,'source_ledger_hash':m.source_ledger_hash,'total_entry_count':m.total_entry_count,'admitted_entry_count':m.admitted_entry_count,'rejected_entry_count':m.rejected_entry_count,'checks':MappingProxyType(checks),'failed_checks':failed})

def certify_umd_050_foundation():
    m=build_umd_050_certification_manifest(); checks={'build_identity':m.build_id=='UMD-050','upstreams_frozen':m.upstream_builds==tuple(f'UMD-{n:03d}' for n in range(1,50)),'read_only_projection':m.read_model_mode=='deterministic_read_only_projection','network_disabled':not m.network_enabled,'persistence_disabled':not m.persistence_enabled,'mutation_disabled':not m.mutation_enabled,'publication_disabled':not m.publication_enabled,'execution_disabled':not m.execution_enabled,'deterministic_manifest':m.manifest_hash==deterministic_sha256(m.to_canonical_dict())}; failed=tuple(k for k,v in checks.items() if not v); return MappingProxyType({'certified':not failed,'build_id':m.build_id,'revision':m.revision,'manifest_hash':m.manifest_hash,'checks':MappingProxyType(checks),'failed_checks':failed})

def verify_umd_050_venue_discovery_request_admission_ledger_read_model():
    r=certify_umd_050_foundation()
    if not r['certified']: raise RuntimeError('UMD-050 foundation certification failed: '+', '.join(r['failed_checks']))
    return True
