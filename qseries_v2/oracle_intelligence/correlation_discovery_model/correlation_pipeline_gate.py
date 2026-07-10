
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping

from .correlation_discovery_engine import CorrelationDiscoveryResult


READ_ONLY = True
SCHEMA_VERSION = "CRD-004"
ENGINE_ID = "oracle.discovery.correlation.pipeline_gate"


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _deep_sort(value[key])
            for key in sorted(value.keys(), key=str)
        }
    if isinstance(value, list):
        return [_deep_sort(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(item) for item in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = repr(_deep_sort(payload)).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CorrelationPipelineGateResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    reason: str
    discovery_result_hash: str
    opportunity_count: int
    checks: Dict[str, bool] = field(default_factory=dict)
    read_only: bool = True
    gate_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class CorrelationPipelineGate:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def validate(
        self,
        result: CorrelationDiscoveryResult,
    ) -> CorrelationPipelineGateResult:
        if not isinstance(result, CorrelationDiscoveryResult):
            raise TypeError(
                "result must be a CorrelationDiscoveryResult"
            )

        checks = {
            "read_only": result.read_only is True,
            "schema_present": bool(result.schema_version),
            "schema_matches": result.schema_version == "CRD-003",
            "engine_present": bool(result.engine_id),
            "engine_matches": (
                result.engine_id
                == "oracle.discovery.correlation.discovery_engine"
            ),
            "hash_present": bool(result.result_hash),
            "count_matches": (
                result.opportunity_count
                == len(result.opportunities)
            ),
            "valid_status": result.status in {"ok", "empty"},
            "empty_status_consistent": (
                result.status != "empty"
                or result.opportunity_count == 0
            ),
            "ok_status_consistent": (
                result.status != "ok"
                or result.opportunity_count > 0
            ),
            "opportunities_have_ids": all(
                bool(opportunity.opportunity_id)
                for opportunity in result.opportunities
            ),
            "opportunities_have_hashes": all(
                bool(opportunity.opportunity_hash)
                for opportunity in result.opportunities
            ),
            "market_pairs_present": all(
                bool(opportunity.primary_market_id)
                and bool(opportunity.related_market_id)
                for opportunity in result.opportunities
            ),
            "distinct_market_pairs": all(
                opportunity.primary_market_id
                != opportunity.related_market_id
                for opportunity in result.opportunities
            ),
            "signal_types_present": all(
                bool(opportunity.signal_type)
                for opportunity in result.opportunities
            ),
            "relationships_present": all(
                bool(opportunity.relationship)
                for opportunity in result.opportunities
            ),
            "confidence_in_range": all(
                0.0 <= opportunity.confidence <= 1.0
                for opportunity in result.opportunities
            ),
            "magnitude_in_range": all(
                0.0 <= opportunity.magnitude <= 1.0
                for opportunity in result.opportunities
            ),
            "observed_at_present": all(
                bool(opportunity.observed_at)
                for opportunity in result.opportunities
            ),
            "explanations_present": all(
                bool(opportunity.explanation)
                for opportunity in result.opportunities
            ),
            "evidence_is_mapping": all(
                isinstance(opportunity.evidence, dict)
                for opportunity in result.opportunities
            ),
            "record_hashes_present": all(
                bool(opportunity.evidence.get("record_hash"))
                for opportunity in result.opportunities
            ),
        }

        accepted = all(checks.values())
        status = "accepted" if accepted else "rejected"

        failed_checks = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        reason = (
            "all correlation pipeline checks passed"
            if accepted
            else "failed checks: " + ", ".join(failed_checks)
        )

        unsigned = CorrelationPipelineGateResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            reason=reason,
            discovery_result_hash=result.result_hash,
            opportunity_count=result.opportunity_count,
            checks=checks,
            read_only=True,
            gate_hash="",
        )

        return CorrelationPipelineGateResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            reason=unsigned.reason,
            discovery_result_hash=unsigned.discovery_result_hash,
            opportunity_count=unsigned.opportunity_count,
            checks=unsigned.checks,
            read_only=True,
            gate_hash=_stable_hash(unsigned.canonical()),
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "discovery_result_validation",
                "schema_validation",
                "engine_validation",
                "opportunity_integrity_validation",
                "market_pair_validation",
                "confidence_range_validation",
                "magnitude_range_validation",
                "deterministic_gate_hashing",
            ],
        }

    def assert_read_only(self) -> bool:
        forbidden = [
            "buy",
            "sell",
            "trade",
            "execute",
            "order",
            "sign",
            "submit",
            "broadcast",
        ]

        offenders = sorted(
            word
            for word in forbidden
            if word in set(dir(self))
        )

        if offenders:
            raise AssertionError(
                f"mutation-like methods are forbidden: {offenders}"
            )

        return True


def validate_correlation_discovery_result(
    result: CorrelationDiscoveryResult,
) -> CorrelationPipelineGateResult:
    return CorrelationPipelineGate().validate(result)


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationPipelineGate",
    "CorrelationPipelineGateResult",
    "validate_correlation_discovery_result",
]
