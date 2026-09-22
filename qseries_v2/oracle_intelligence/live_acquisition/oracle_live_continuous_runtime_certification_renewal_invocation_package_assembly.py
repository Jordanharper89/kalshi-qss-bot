"""
OLA-089
Oracle Live Continuous Runtime Certification Renewal Invocation Package Assembly

Consumes the hash-verified OLA-088 invocation-readiness status and assembles a
sealed, deterministic, in-memory package for a later renewal executor.

OLA-089 never performs renewal, imports or invokes a renewal executor, contacts
PostgreSQL, starts Oracle, mutates runtime locks, or writes certification evidence.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_certification_renewal_invocation_readiness_gate import (
    OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessStatus,
    evaluate_oracle_live_continuous_runtime_certification_renewal_invocation_readiness,
)

SCHEMA_VERSION = "OLA-089"
ENGINE_ID = "OLA-089"
UPSTREAM_READINESS_SCHEMA_VERSION = "OLA-088"
READ_ONLY = True
EXECUTION_ALLOWED = False
FILES_WRITTEN = False
RENEWAL_PERFORMED = False
RENEWAL_EXECUTOR_IMPORTED = False
RENEWAL_EXECUTOR_INVOKED = False
CERTIFICATION_EVIDENCE_MUTATED = False
POSTGRESQL_READ_PERFORMED = False
POSTGRESQL_WRITE_PERFORMED = False
RUNTIME_IMPORTED = False
RUNTIME_INVOKED = False
RUNTIME_LOCK_MUTATED = False

class OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageError(RuntimeError): pass
class OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageContractError(OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageError): pass
class OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageNotReady(OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageError): pass

def _aware(value: Any, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageContractError(f"{name} must be timezone-aware")
    return value

def canonicalize(value: Any) -> Any:
    if value is None or isinstance(value,(bool,int,float,str)): return value
    if isinstance(value,datetime): return _aware(value,"canonical datetime").isoformat()
    if isinstance(value,Path): return str(value)
    if isinstance(value,dict): return {str(k):canonicalize(v) for k,v in sorted(value.items(),key=lambda p:str(p[0]))}
    if isinstance(value,(list,tuple)): return [canonicalize(v) for v in value]
    raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageContractError(f"unsupported canonical type: {type(value).__name__}")

def stable_hash(value: Any) -> str:
    import json
    return sha256(json.dumps(canonicalize(value),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def validate_upstream_readiness(status: OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessStatus) -> None:
    if not isinstance(status, OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessStatus):
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageContractError("upstream status must be OLA-088")
    if status.schema_version != "OLA-088" or status.engine_id != "OLA-088":
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageContractError("upstream schema/engine must be OLA-088")
    if status.verify_status_hash() is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageContractError("upstream OLA-088 hash invalid")
    expected = status.status in {"renewal_eligible_invocation_ready","renewal_required_invocation_ready"}
    if status.renewal_invocation_ready is not expected:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageContractError("upstream readiness contradicts status")
    if status.lineage_verified is not True or status.safety_boundary_verified is not True or status.read_only is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageContractError("upstream safety boundary invalid")
    for name in ("renewal_performed","renewal_executor_imported","renewal_executor_invoked","certification_evidence_mutated","postgresql_read_performed","postgresql_write_performed","runtime_imported","runtime_invoked","runtime_lock_mutated","files_written"):
        if getattr(status,name) is not False: raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageContractError(f"upstream unsafe field true: {name}")

@dataclass(frozen=True)
class OracleLiveContinuousRuntimeCertificationRenewalInvocationPackage:
    schema_version: str
    engine_id: str
    package_status: str
    package_ready: bool
    package_id: str
    assembled_at: datetime
    renewal_mode: str
    operator_authorization_id: str
    authorized_at: datetime
    attestation_id: str
    attestation_hash: str
    upstream_readiness_status: str
    upstream_readiness_status_hash: str
    upstream_readiness_schema_version: str
    lineage_verified: bool
    safety_boundary_verified: bool
    read_only: bool
    execution_allowed: bool
    files_written: bool
    renewal_performed: bool
    renewal_executor_imported: bool
    renewal_executor_invoked: bool
    certification_evidence_mutated: bool
    postgresql_read_performed: bool
    postgresql_write_performed: bool
    runtime_imported: bool
    runtime_invoked: bool
    runtime_lock_mutated: bool
    package_hash: str
    def hash_payload(self) -> dict[str,Any]:
        return {k:v for k,v in self.__dict__.items() if k != "package_hash"}
    def verify_package_hash(self) -> bool:
        return self.package_hash == stable_hash(self.hash_payload())

def assemble_oracle_live_continuous_runtime_certification_renewal_invocation_package(*, repository_root: str|Path, assembled_at: datetime, upstream_status: OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessStatus|None=None, **upstream_kwargs: Any) -> OracleLiveContinuousRuntimeCertificationRenewalInvocationPackage:
    Path(repository_root)
    assembled_at=_aware(assembled_at,"assembled_at")
    status=upstream_status or evaluate_oracle_live_continuous_runtime_certification_renewal_invocation_readiness(repository_root=repository_root,checked_at=assembled_at,**upstream_kwargs)
    validate_upstream_readiness(status)
    if not status.renewal_invocation_ready:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageNotReady(f"renewal invocation package cannot be assembled: status={status.status}")
    if not status.operator_authorization_id or status.authorized_at is None:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageContractError("ready status lacks operator authorization evidence")
    mode="required" if status.renewal_required else "eligible"
    seed={"schema_version":SCHEMA_VERSION,"assembled_at":assembled_at,"renewal_mode":mode,"operator_authorization_id":status.operator_authorization_id,"attestation_id":status.attestation_id,"upstream_readiness_status_hash":status.status_hash}
    package_id="ola089-"+stable_hash(seed)[:24]
    values=dict(schema_version=SCHEMA_VERSION,engine_id=ENGINE_ID,package_status="renewal_invocation_package_ready",package_ready=True,package_id=package_id,assembled_at=assembled_at,renewal_mode=mode,operator_authorization_id=status.operator_authorization_id,authorized_at=_aware(status.authorized_at,"authorized_at"),attestation_id=status.attestation_id,attestation_hash=status.attestation_hash,upstream_readiness_status=status.status,upstream_readiness_status_hash=status.status_hash,upstream_readiness_schema_version=status.schema_version,lineage_verified=True,safety_boundary_verified=True,read_only=True,execution_allowed=False,files_written=False,renewal_performed=False,renewal_executor_imported=False,renewal_executor_invoked=False,certification_evidence_mutated=False,postgresql_read_performed=False,postgresql_write_performed=False,runtime_imported=False,runtime_invoked=False,runtime_lock_mutated=False)
    return OracleLiveContinuousRuntimeCertificationRenewalInvocationPackage(**values,package_hash=stable_hash(values))

def require_oracle_live_continuous_runtime_certification_renewal_invocation_package_ready(**kwargs: Any) -> OracleLiveContinuousRuntimeCertificationRenewalInvocationPackage:
    result=assemble_oracle_live_continuous_runtime_certification_renewal_invocation_package(**kwargs)
    if not result.package_ready or not result.verify_package_hash():
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationPackageNotReady("renewal invocation package is not ready")
    return result
