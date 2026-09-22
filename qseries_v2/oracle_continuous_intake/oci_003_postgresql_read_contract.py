from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json, re
from types import MappingProxyType
from typing import Mapping, Any, Sequence
from .oci_001_foundation import verify_oci_001_continuous_intake_foundation
from .oci_002_upstream_boundary import verify_oci_002_upstream_boundary_inventory

OCI_003_BUILD_ID="OCI-003"
OCI_003_REVISION="OCI_003_POSTGRESQL_READ_ONLY_INTAKE_CONTRACT_V1"
_IDENT=re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
FORBIDDEN_SQL=("insert","update","delete","alter","drop","truncate","create","grant","revoke","copy","call","do")

def _hash(v:object)->str:
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class PostgreSQLReadConfig:
    host:str
    port:int
    database:str
    user:str
    connect_timeout_seconds:int=5
    statement_timeout_ms:int=5000
    application_name:str="oracle_continuous_intake"

    def __post_init__(self):
        if not self.host or not self.database or not self.user: raise ValueError("host/database/user required")
        if not 1 <= self.port <= 65535: raise ValueError("invalid port")
        if self.connect_timeout_seconds <= 0 or self.statement_timeout_ms <= 0: raise ValueError("timeouts must be positive")

    def safe_dict(self):
        return MappingProxyType(asdict(self))

@dataclass(frozen=True)
class ReadOnlyQuery:
    sql:str
    params:tuple[object,...]
    query_hash:str

def build_incremental_read_query(schema:str,table:str,cursor_column:str,after_value:object,limit:int=500)->ReadOnlyQuery:
    for value in (schema,table,cursor_column):
        if not _IDENT.fullmatch(value): raise ValueError("unsafe SQL identifier")
    if not 1 <= limit <= 10000: raise ValueError("limit outside certified bound")
    sql=f'SELECT * FROM "{schema}"."{table}" WHERE "{cursor_column}" > %s ORDER BY "{cursor_column}" ASC LIMIT %s'
    lowered=sql.lower()
    if any(re.search(r"\b"+word+r"\b",lowered) for word in FORBIDDEN_SQL): raise ValueError("write SQL forbidden")
    params=(after_value,limit)
    return ReadOnlyQuery(sql,params,_hash({"sql":sql,"params":params}))

def read_only_session_commands(statement_timeout_ms:int)->tuple[str,...]:
    if statement_timeout_ms <= 0: raise ValueError("timeout must be positive")
    return (
        "BEGIN READ ONLY",
        f"SET LOCAL statement_timeout = {int(statement_timeout_ms)}",
        "SET LOCAL idle_in_transaction_session_timeout = 10000",
    )

def verify_read_only_sql(sql:str)->bool:
    stripped=sql.strip().lower()
    return stripped.startswith("select ") and not any(re.search(r"\b"+w+r"\b",stripped) for w in FORBIDDEN_SQL)

def build_oci_003_certification_manifest()->Mapping[str,Any]:
    raw={"build_id":OCI_003_BUILD_ID,"revision":OCI_003_REVISION,"upstream_builds":("OCI-001","OCI-002"),
         "postgresql_read_enabled":True,"postgresql_write_enabled":False,"read_only_transaction_required":True,
         "network_listener_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**raw,"manifest_hash":_hash(raw)})

def verify_oci_003_postgresql_read_only_intake_contract()->bool:
    q=build_incremental_read_query("public","oracle_live_shadow","sequence_id",0,10)
    m=build_oci_003_certification_manifest()
    return (verify_oci_001_continuous_intake_foundation()
            and verify_oci_002_upstream_boundary_inventory()
            and verify_read_only_sql(q.sql)
            and read_only_session_commands(5000)[0]=="BEGIN READ ONLY"
            and m["postgresql_read_enabled"] and not m["postgresql_write_enabled"] and not m["execution_enabled"])
