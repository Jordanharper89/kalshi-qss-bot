from dataclasses import dataclass
from types import MappingProxyType
from .ois_007_state_versioning import StateVersion
OIS_008_BUILD_ID="OIS-008";OIS_008_REVISION="OIS_008_POSTGRESQL_PERSISTENCE_BOUNDARY_V1"
@dataclass(frozen=True)
class PostgreSQLStateRecord:
    subject_id:str;version:int;state_hash:str;parent_state_hash:str|None;transition_hash:str;version_hash:str
@dataclass(frozen=True)
class PostgreSQLPersistencePlan:
    table_name:str;columns:tuple[str,...];values:tuple[object,...];conflict_policy:str;network_io:bool=False
def build_postgresql_persistence_plan(version,table_name="oracle_intelligence_state_versions"):
    if not isinstance(version,StateVersion):raise ValueError("certified state version required")
    cols=("subject_id","version","state_hash","parent_state_hash","transition_hash","version_hash")
    vals=(version.subject_id,version.version,version.state_hash,version.parent_state_hash,version.transition_hash,version.version_hash)
    return PostgreSQLPersistencePlan(table_name,cols,vals,"reject_duplicate_subject_version",False)
def materialize_postgresql_record(plan):
    if plan.network_io:raise ValueError("certification boundary must not perform network IO")
    return PostgreSQLStateRecord(*plan.values)
def build_ois_008_certification_manifest():return MappingProxyType({"build_id":OIS_008_BUILD_ID,"revision":OIS_008_REVISION,"database":"PostgreSQL","network_io":False,"boundary":"persistence_contract_only","execution":False})
def verify_ois_008_postgresql_persistence_boundary():
    from .ois_006_state_update import IntelligenceStateUpdate
    from .ois_007_state_versioning import build_state_version
    v=build_state_version(IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64))
    p=build_postgresql_persistence_plan(v);r=materialize_postgresql_record(p)
    return not p.network_io and r.version==1 and p.conflict_policy=="reject_duplicate_subject_version"
