from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_authorized_real_intelligence_read_invocation_execution_gate import (
    OracleRealIntelligenceReadInvocationExecutionReport,
    verify_read_invocation_execution_report,
)
from .oracle_real_intelligence_response_validation_gate import (
    OracleRealIntelligenceResponseValidationReport,
    verify_real_intelligence_response_validation_report,
)

SCHEMA_VERSION = "OIT-039"
ENGINE_ID = "OIT-039"
POLICY_ID = "oracle.certified-real-intelligence-source-envelope.v1"


class OracleRealIntelligenceSourceEnvelopeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleRealIntelligenceSourceEnvelope:
    schema_version: str
    engine_id: str
    policy_id: str
    execution_report_hash: str
    validation_report_hash: str
    invocation_result_hash: str
    canonical_result: Any
    canonical_result_hash: str
    execution_validation_lineage_verified: bool
    source_result_preserved: bool
    read_only: bool
    envelope_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleRealIntelligenceSourceEnvelopeInvariantError(
        f"unsupported canonical result type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_real_intelligence_source_envelope(
    execution_report: OracleRealIntelligenceReadInvocationExecutionReport,
    validation_report: OracleRealIntelligenceResponseValidationReport,
) -> OracleRealIntelligenceSourceEnvelope:
    verify_read_invocation_execution_report(execution_report)
    verify_real_intelligence_response_validation_report(validation_report)

    if not execution_report.execution_succeeded:
        raise OracleRealIntelligenceSourceEnvelopeInvariantError(
            "OIT-037 execution report is not successful"
        )
    if not validation_report.normalization_ready:
        raise OracleRealIntelligenceSourceEnvelopeInvariantError(
            "OIT-038 validation report is not normalization-ready"
        )
    if validation_report.execution_report_hash != execution_report.report_hash:
        raise OracleRealIntelligenceSourceEnvelopeInvariantError(
            "OIT-037/OIT-038 execution lineage mismatch"
        )

    result = execution_report.execution_receipt.invocation_result
    canonical_result = _canonical(result.canonical_result)
    canonical_hash = _stable_hash(canonical_result)

    lineage_verified = bool(
        validation_report.invocation_result_hash == result.result_hash
        and result.result_hash == canonical_hash
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "execution_report_hash": execution_report.report_hash,
        "validation_report_hash": validation_report.report_hash,
        "invocation_result_hash": result.result_hash,
        "canonical_result": canonical_result,
        "canonical_result_hash": canonical_hash,
        "execution_validation_lineage_verified": lineage_verified,
        "source_result_preserved": lineage_verified,
        "read_only": True,
    }
    envelope = OracleRealIntelligenceSourceEnvelope(
        **body,
        envelope_hash=_stable_hash(body),
    )
    verify_real_intelligence_source_envelope(envelope)
    return envelope


def verify_real_intelligence_source_envelope(
    envelope: OracleRealIntelligenceSourceEnvelope,
) -> bool:
    body = asdict(envelope)
    supplied = body.pop("envelope_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceSourceEnvelopeInvariantError(
            "source envelope hash mismatch"
        )
    if envelope.schema_version != SCHEMA_VERSION:
        raise OracleRealIntelligenceSourceEnvelopeInvariantError(
            "source envelope schema mismatch"
        )
    if envelope.policy_id != POLICY_ID:
        raise OracleRealIntelligenceSourceEnvelopeInvariantError(
            "source envelope policy mismatch"
        )
    if not envelope.read_only:
        raise OracleRealIntelligenceSourceEnvelopeInvariantError(
            "source envelope is not read-only"
        )
    if envelope.canonical_result_hash != _stable_hash(
        envelope.canonical_result
    ):
        raise OracleRealIntelligenceSourceEnvelopeInvariantError(
            "canonical result hash mismatch"
        )
    expected = bool(
        envelope.invocation_result_hash
        == envelope.canonical_result_hash
    )
    if envelope.execution_validation_lineage_verified != expected:
        raise OracleRealIntelligenceSourceEnvelopeInvariantError(
            "source envelope lineage state mismatch"
        )
    if envelope.source_result_preserved != expected:
        raise OracleRealIntelligenceSourceEnvelopeInvariantError(
            "source preservation state mismatch"
        )
    return True
