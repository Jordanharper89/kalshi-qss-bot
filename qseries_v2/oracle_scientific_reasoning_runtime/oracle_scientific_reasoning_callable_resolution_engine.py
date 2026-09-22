from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import importlib.util
import json
from typing import Any, Mapping

from .oracle_certified_callable_admission_gate import (
    CertifiedCallableAdmissionPackage,
    CertifiedCallableAdmissionRecord,
    verify_certified_callable_admission_package,
)

ENGINE_ID = "OSR-003"
SCHEMA_VERSION = "OSR-003.v1"
ALGORITHM_VERSION = "scientific-reasoning-callable-resolution-engine.v1"

RESOLUTION_STATUS = "resolved_reference_only_inactive_unbound_non_executable"
PACKAGE_STATUS = "certified_callable_references_resolved_read_only"


class OracleScientificReasoningResolutionInvariantError(ValueError):
    """Raised when an OSR-003 resolution invariant is violated."""


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [_canonical(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ),
        )
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ScientificReasoningCallableResolutionRecord:
    discipline_id: str
    callable_id: str
    source_admission_record_hash: str
    implementation_module: str
    implementation_symbol: str
    module_spec_available: bool
    symbol_lookup_performed: bool
    callable_loaded: bool
    active: bool
    resolved: bool
    bound: bool
    executable: bool
    read_only: bool
    resolution_status: str
    resolution_record_hash: str


@dataclass(frozen=True)
class ScientificReasoningCallableResolutionPackage:
    resolution_package_id: str
    source_admission_package_id: str
    source_admission_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_oii015_certification_hash: str
    source_frozen_evidence_set_hash: str
    resolution_records: tuple[ScientificReasoningCallableResolutionRecord, ...]
    resolved_disciplines: tuple[str, ...]
    resolved_callable_count: int
    unresolved_callable_count: int
    resolution_status: str
    resolution_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    callable_resolution_allowed: bool
    callable_binding_allowed: bool
    reasoning_execution_allowed: bool
    probability_estimation_allowed: bool
    final_intelligence_conclusion_allowed: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool


def _resolve_admitted_record(
    record: CertifiedCallableAdmissionRecord,
) -> ScientificReasoningCallableResolutionRecord:
    if record.admitted is not True:
        raise OracleScientificReasoningResolutionInvariantError(
            f"callable was not admitted: {record.callable_id}"
        )
    if (
        record.active
        or record.resolved
        or record.bound
        or record.executable
        or record.read_only is not True
    ):
        raise OracleScientificReasoningResolutionInvariantError(
            f"admission record boundary violated: {record.callable_id}"
        )

    try:
        module_spec_available = (
            importlib.util.find_spec(record.implementation_module) is not None
        )
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError):
        module_spec_available = False

    body = {
        "discipline_id": record.discipline_id,
        "callable_id": record.callable_id,
        "source_admission_record_hash": record.admission_record_hash,
        "implementation_module": record.implementation_module,
        "implementation_symbol": record.implementation_symbol,
        "module_spec_available": module_spec_available,
        "symbol_lookup_performed": False,
        "callable_loaded": False,
        "active": False,
        "resolved": True,
        "bound": False,
        "executable": False,
        "read_only": True,
        "resolution_status": RESOLUTION_STATUS,
    }
    return ScientificReasoningCallableResolutionRecord(
        **body,
        resolution_record_hash=stable_hash(body),
    )


def resolve_certified_scientific_reasoning_callables(
    *,
    admission_package: CertifiedCallableAdmissionPackage,
) -> ScientificReasoningCallableResolutionPackage:
    try:
        verify_certified_callable_admission_package(admission_package)
    except Exception as exc:
        raise OracleScientificReasoningResolutionInvariantError(
            "OSR-002 admission package verification failed"
        ) from exc

    ordered_records = tuple(
        sorted(
            admission_package.admission_records,
            key=lambda item: item.discipline_id,
        )
    )
    resolution_records = tuple(
        _resolve_admitted_record(record)
        for record in ordered_records
    )
    resolved_disciplines = tuple(
        record.discipline_id for record in resolution_records
    )

    if resolved_disciplines != admission_package.admitted_disciplines:
        raise OracleScientificReasoningResolutionInvariantError(
            "resolution discipline lineage mismatch"
        )
    if len({record.callable_id for record in resolution_records}) != len(
        resolution_records
    ):
        raise OracleScientificReasoningResolutionInvariantError(
            "duplicate callable identity detected during resolution"
        )

    body = {
        "source_admission_package_id":
            admission_package.admission_package_id,
        "source_admission_hash": admission_package.admission_hash,
        "source_registry_id": admission_package.source_registry_id,
        "source_registry_hash": admission_package.source_registry_hash,
        "source_oii015_certification_hash":
            admission_package.source_oii015_certification_hash,
        "source_frozen_evidence_set_hash":
            admission_package.source_frozen_evidence_set_hash,
        "resolution_records": resolution_records,
        "resolved_disciplines": resolved_disciplines,
        "resolved_callable_count": len(resolution_records),
        "unresolved_callable_count": 0,
        "resolution_status": PACKAGE_STATUS,
    }
    resolution_hash = stable_hash(body)

    return ScientificReasoningCallableResolutionPackage(
        resolution_package_id=(
            "scientific-reasoning-callable-resolution:" + resolution_hash
        ),
        **body,
        resolution_hash=resolution_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        callable_resolution_allowed=True,
        callable_binding_allowed=False,
        reasoning_execution_allowed=False,
        probability_estimation_allowed=False,
        final_intelligence_conclusion_allowed=False,
        publication_allowed=False,
        alerting_allowed=False,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
    )


def verify_scientific_reasoning_callable_resolution_record(
    record: ScientificReasoningCallableResolutionRecord,
) -> bool:
    if not isinstance(record, ScientificReasoningCallableResolutionRecord):
        raise OracleScientificReasoningResolutionInvariantError(
            "invalid resolution record"
        )

    body = {
        key: value
        for key, value in asdict(record).items()
        if key != "resolution_record_hash"
    }
    if stable_hash(body) != record.resolution_record_hash:
        raise OracleScientificReasoningResolutionInvariantError(
            "resolution record hash verification failed"
        )

    if (
        record.resolution_status != RESOLUTION_STATUS
        or record.resolved is not True
        or record.active
        or record.bound
        or record.executable
        or record.symbol_lookup_performed
        or record.callable_loaded
        or record.read_only is not True
    ):
        raise OracleScientificReasoningResolutionInvariantError(
            "resolution record safety boundary violated"
        )
    return True


def verify_scientific_reasoning_callable_resolution_package(
    package: ScientificReasoningCallableResolutionPackage,
) -> bool:
    if not isinstance(package, ScientificReasoningCallableResolutionPackage):
        raise OracleScientificReasoningResolutionInvariantError(
            "invalid resolution package"
        )

    for record in package.resolution_records:
        verify_scientific_reasoning_callable_resolution_record(record)

    if package.resolved_disciplines != tuple(
        record.discipline_id for record in package.resolution_records
    ):
        raise OracleScientificReasoningResolutionInvariantError(
            "resolved discipline set mismatch"
        )
    if package.resolved_callable_count != len(package.resolution_records):
        raise OracleScientificReasoningResolutionInvariantError(
            "resolved callable count mismatch"
        )
    if package.unresolved_callable_count != 0:
        raise OracleScientificReasoningResolutionInvariantError(
            "unresolved callable count must remain zero"
        )

    body = {
        "source_admission_package_id":
            package.source_admission_package_id,
        "source_admission_hash": package.source_admission_hash,
        "source_registry_id": package.source_registry_id,
        "source_registry_hash": package.source_registry_hash,
        "source_oii015_certification_hash":
            package.source_oii015_certification_hash,
        "source_frozen_evidence_set_hash":
            package.source_frozen_evidence_set_hash,
        "resolution_records": package.resolution_records,
        "resolved_disciplines": package.resolved_disciplines,
        "resolved_callable_count": package.resolved_callable_count,
        "unresolved_callable_count": package.unresolved_callable_count,
        "resolution_status": package.resolution_status,
    }
    expected_hash = stable_hash(body)
    if package.resolution_hash != expected_hash:
        raise OracleScientificReasoningResolutionInvariantError(
            "resolution package hash verification failed"
        )
    if package.resolution_package_id != (
        "scientific-reasoning-callable-resolution:" + expected_hash
    ):
        raise OracleScientificReasoningResolutionInvariantError(
            "resolution package identity verification failed"
        )

    forbidden = (
        package.callable_binding_allowed,
        package.reasoning_execution_allowed,
        package.probability_estimation_allowed,
        package.final_intelligence_conclusion_allowed,
        package.publication_allowed,
        package.alerting_allowed,
        package.qseries_handoff_allowed,
        package.qseries_execution_allowed,
        package.order_creation_allowed,
        package.funds_movement_allowed,
        package.portfolio_mutation_allowed,
    )
    if (
        package.engine_id != ENGINE_ID
        or package.read_only is not True
        or package.callable_resolution_allowed is not True
        or package.resolution_status != PACKAGE_STATUS
        or any(forbidden)
    ):
        raise OracleScientificReasoningResolutionInvariantError(
            "OSR-003 permanent safety boundary violated"
        )
    return True


def serialize_scientific_reasoning_callable_resolution_package(
    package: ScientificReasoningCallableResolutionPackage,
) -> str:
    verify_scientific_reasoning_callable_resolution_package(package)
    return canonical_json(package)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "RESOLUTION_STATUS",
    "PACKAGE_STATUS",
    "OracleScientificReasoningResolutionInvariantError",
    "ScientificReasoningCallableResolutionRecord",
    "ScientificReasoningCallableResolutionPackage",
    "resolve_certified_scientific_reasoning_callables",
    "verify_scientific_reasoning_callable_resolution_record",
    "verify_scientific_reasoning_callable_resolution_package",
    "serialize_scientific_reasoning_callable_resolution_package",
]
