from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .oracle_integrated_intelligence_scientific_model_registry import (
    ENGINE_ID as OII_001_ENGINE_ID,
    REQUIRED_MODEL_IDS,
    OracleIntegratedIntelligenceScientificModelRegistryBuilder,
)

SCHEMA_VERSION = "OII-002"
ENGINE_ID = "OII-002"
POLICY_ID = "oracle.integrated-intelligence.canonical-evidence.v1"
CONTRACT_STATUS = "canonical_intelligence_evidence_contract_active"
CONTRACT_TYPE = "immutable_read_only_canonical_intelligence_evidence"

EVIDENCE_TYPES = (
    "market_observation",
    "external_source",
    "derived_analytic",
    "historical_analog",
    "causal_claim",
    "counterevidence",
    "model_output",
)
SOURCE_CLASSES = ("primary", "secondary", "derived", "synthetic")
CLAIM_DIRECTIONS = ("supports", "contradicts", "neutral", "context")


class OracleCanonicalEvidenceInvariantError(RuntimeError):
    pass


def _utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise OracleCanonicalEvidenceInvariantError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda p: str(p[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        return _utc(value, "datetime").isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleCanonicalEvidenceInvariantError(f"unsupported value type: {type(value)!r}")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _text(value: str, name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise OracleCanonicalEvidenceInvariantError(f"{name} must be nonempty")
    return normalized


def _probability(value: float, name: str) -> float:
    numeric = float(value)
    if not 0.0 <= numeric <= 1.0:
        raise OracleCanonicalEvidenceInvariantError(f"{name} must be between 0 and 1")
    return numeric


@dataclass(frozen=True)
class CanonicalEvidenceOrigin:
    source_id: str
    source_class: str
    source_name: str
    source_locator: str
    source_observation_id: str
    source_content_hash: str
    source_replay_hash: str
    source_chain_hash: str
    source_adapter_id: str
    source_environment: str
    acquired_at: datetime
    observed_at: datetime
    authentication_used: bool
    public_source: bool
    shadow_mode: bool
    read_only: bool
    origin_hash: str


@dataclass(frozen=True)
class CanonicalEvidenceQuality:
    source_reliability: float
    source_independence: float
    relevance: float
    specificity: float
    freshness: float
    completeness: float
    manipulation_risk: float
    contradiction_risk: float
    uncertainty: float
    quality_hash: str


@dataclass(frozen=True)
class CanonicalEvidenceClaim:
    claim_id: str
    claim_text: str
    claim_direction: str
    claim_target_id: str
    claim_probability: float
    claim_uncertainty: float
    causal_claim: bool
    causal_mechanism: str
    counterfactual_defined: bool
    claim_hash: str


@dataclass(frozen=True)
class CanonicalIntelligenceEvidence:
    evidence_id: str
    evidence_type: str
    subject_id: str
    subject_type: str
    title: str
    summary: str
    payload: Mapping[str, Any]
    origin: CanonicalEvidenceOrigin
    quality: CanonicalEvidenceQuality
    claims: tuple[CanonicalEvidenceClaim, ...]
    model_eligibility: tuple[str, ...]
    parent_evidence_ids: tuple[str, ...]
    contradictory_evidence_ids: tuple[str, ...]
    created_at: datetime
    valid_from: datetime
    valid_until: datetime | None
    immutable: bool
    replayable: bool
    explainable: bool
    source_lineage_verified: bool
    uncertainty_explicit: bool
    adversarial_review_required: bool
    calibration_tracking_required: bool
    read_only: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    evidence_hash: str


@dataclass(frozen=True)
class CanonicalIntelligenceEvidenceContract:
    contract_id: str
    contract_status: str
    contract_type: str
    schema_version: str
    engine_id: str
    policy_id: str
    upstream_engine_id: str
    evidence_types: tuple[str, ...]
    source_classes: tuple[str, ...]
    claim_directions: tuple[str, ...]
    required_model_ids: tuple[str, ...]
    source_origin_required: bool
    quality_required: bool
    claims_required: bool
    uncertainty_required: bool
    lineage_required: bool
    replay_hash_required: bool
    chain_hash_required: bool
    contradiction_linkage_supported: bool
    causal_controls_required: bool
    adversarial_review_required: bool
    calibration_tracking_required: bool
    deterministic_hashing_required: bool
    immutable_evidence_required: bool
    read_only_boundary_required: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    contract_hash: str


class OracleCanonicalIntelligenceEvidenceBuilder:
    def origin(
        self,
        *,
        source_id: str,
        source_class: str,
        source_name: str,
        source_locator: str,
        source_observation_id: str,
        source_content_hash: str,
        source_replay_hash: str,
        source_chain_hash: str,
        source_adapter_id: str,
        source_environment: str,
        acquired_at: datetime,
        observed_at: datetime,
        authentication_used: bool,
        public_source: bool,
        shadow_mode: bool,
    ) -> CanonicalEvidenceOrigin:
        if source_class not in SOURCE_CLASSES:
            raise OracleCanonicalEvidenceInvariantError("unsupported source class")
        body = {
            "source_id": _text(source_id, "source_id"),
            "source_class": source_class,
            "source_name": _text(source_name, "source_name"),
            "source_locator": _text(source_locator, "source_locator"),
            "source_observation_id": _text(source_observation_id, "source_observation_id"),
            "source_content_hash": _text(source_content_hash, "source_content_hash"),
            "source_replay_hash": _text(source_replay_hash, "source_replay_hash"),
            "source_chain_hash": _text(source_chain_hash, "source_chain_hash"),
            "source_adapter_id": _text(source_adapter_id, "source_adapter_id"),
            "source_environment": _text(source_environment, "source_environment"),
            "acquired_at": _utc(acquired_at, "acquired_at"),
            "observed_at": _utc(observed_at, "observed_at"),
            "authentication_used": bool(authentication_used),
            "public_source": bool(public_source),
            "shadow_mode": bool(shadow_mode),
            "read_only": True,
        }
        return CanonicalEvidenceOrigin(**body, origin_hash=stable_hash(body))

    def quality(
        self,
        *,
        source_reliability: float,
        source_independence: float,
        relevance: float,
        specificity: float,
        freshness: float,
        completeness: float,
        manipulation_risk: float,
        contradiction_risk: float,
        uncertainty: float,
    ) -> CanonicalEvidenceQuality:
        body = {
            "source_reliability": _probability(source_reliability, "source_reliability"),
            "source_independence": _probability(source_independence, "source_independence"),
            "relevance": _probability(relevance, "relevance"),
            "specificity": _probability(specificity, "specificity"),
            "freshness": _probability(freshness, "freshness"),
            "completeness": _probability(completeness, "completeness"),
            "manipulation_risk": _probability(manipulation_risk, "manipulation_risk"),
            "contradiction_risk": _probability(contradiction_risk, "contradiction_risk"),
            "uncertainty": _probability(uncertainty, "uncertainty"),
        }
        return CanonicalEvidenceQuality(**body, quality_hash=stable_hash(body))

    def claim(
        self,
        *,
        claim_text: str,
        claim_direction: str,
        claim_target_id: str,
        claim_probability: float,
        claim_uncertainty: float,
        causal_claim: bool,
        causal_mechanism: str = "",
        counterfactual_defined: bool = False,
    ) -> CanonicalEvidenceClaim:
        if claim_direction not in CLAIM_DIRECTIONS:
            raise OracleCanonicalEvidenceInvariantError("unsupported claim direction")
        mechanism = str(causal_mechanism).strip()
        if causal_claim and (not mechanism or not counterfactual_defined):
            raise OracleCanonicalEvidenceInvariantError(
                "causal claims require mechanism and defined counterfactual"
            )
        base = {
            "claim_text": _text(claim_text, "claim_text"),
            "claim_direction": claim_direction,
            "claim_target_id": _text(claim_target_id, "claim_target_id"),
            "claim_probability": _probability(claim_probability, "claim_probability"),
            "claim_uncertainty": _probability(claim_uncertainty, "claim_uncertainty"),
            "causal_claim": bool(causal_claim),
            "causal_mechanism": mechanism,
            "counterfactual_defined": bool(counterfactual_defined),
        }
        claim_id = stable_hash({"schema_version": SCHEMA_VERSION, "claim": base})
        body = {"claim_id": claim_id, **base}
        return CanonicalEvidenceClaim(**body, claim_hash=stable_hash(body))

    def evidence(
        self,
        *,
        evidence_type: str,
        subject_id: str,
        subject_type: str,
        title: str,
        summary: str,
        payload: Mapping[str, Any],
        origin: CanonicalEvidenceOrigin,
        quality: CanonicalEvidenceQuality,
        claims: Sequence[CanonicalEvidenceClaim],
        model_eligibility: Sequence[str],
        parent_evidence_ids: Sequence[str],
        contradictory_evidence_ids: Sequence[str],
        created_at: datetime,
        valid_from: datetime,
        valid_until: datetime | None = None,
    ) -> CanonicalIntelligenceEvidence:
        if evidence_type not in EVIDENCE_TYPES:
            raise OracleCanonicalEvidenceInvariantError("unsupported evidence type")
        created = _utc(created_at, "created_at")
        valid_start = _utc(valid_from, "valid_from")
        valid_end = None if valid_until is None else _utc(valid_until, "valid_until")
        if valid_end is not None and valid_end < valid_start:
            raise OracleCanonicalEvidenceInvariantError("invalid evidence validity window")

        normalized_models = tuple(sorted(set(model_eligibility)))
        if not normalized_models or any(m not in REQUIRED_MODEL_IDS for m in normalized_models):
            raise OracleCanonicalEvidenceInvariantError("invalid model eligibility")
        normalized_claims = tuple(claims)
        if not normalized_claims:
            raise OracleCanonicalEvidenceInvariantError("canonical evidence requires claims")

        normalized_payload = _canonical(dict(payload))
        parents = tuple(sorted(set(parent_evidence_ids)))
        contradictions = tuple(sorted(set(contradictory_evidence_ids)))

        identity = {
            "schema_version": SCHEMA_VERSION,
            "evidence_type": evidence_type,
            "subject_id": _text(subject_id, "subject_id"),
            "origin_hash": origin.origin_hash,
            "quality_hash": quality.quality_hash,
            "claim_hashes": tuple(c.claim_hash for c in normalized_claims),
            "payload_hash": stable_hash(normalized_payload),
            "model_eligibility": normalized_models,
            "parent_evidence_ids": parents,
            "contradictory_evidence_ids": contradictions,
            "valid_from": valid_start,
            "valid_until": valid_end,
        }
        evidence_id = stable_hash(identity)
        body = {
            "evidence_id": evidence_id,
            "evidence_type": evidence_type,
            "subject_id": _text(subject_id, "subject_id"),
            "subject_type": _text(subject_type, "subject_type"),
            "title": _text(title, "title"),
            "summary": _text(summary, "summary"),
            "payload": normalized_payload,
            "origin": origin,
            "quality": quality,
            "claims": normalized_claims,
            "model_eligibility": normalized_models,
            "parent_evidence_ids": parents,
            "contradictory_evidence_ids": contradictions,
            "created_at": created,
            "valid_from": valid_start,
            "valid_until": valid_end,
            "immutable": True,
            "replayable": True,
            "explainable": True,
            "source_lineage_verified": True,
            "uncertainty_explicit": True,
            "adversarial_review_required": True,
            "calibration_tracking_required": True,
            "read_only": True,
            "publication_allowed": False,
            "alerting_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        return CanonicalIntelligenceEvidence(**body, evidence_hash=stable_hash(body))

    def contract(self) -> CanonicalIntelligenceEvidenceContract:
        registry = OracleIntegratedIntelligenceScientificModelRegistryBuilder().build()
        if registry.model_ids != REQUIRED_MODEL_IDS:
            raise OracleCanonicalEvidenceInvariantError("OII-001 model registry mismatch")
        contract_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "policy_id": POLICY_ID,
                "upstream_engine_id": OII_001_ENGINE_ID,
                "models": REQUIRED_MODEL_IDS,
                "evidence_types": EVIDENCE_TYPES,
            }
        )
        body = {
            "contract_id": contract_id,
            "contract_status": CONTRACT_STATUS,
            "contract_type": CONTRACT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "policy_id": POLICY_ID,
            "upstream_engine_id": OII_001_ENGINE_ID,
            "evidence_types": EVIDENCE_TYPES,
            "source_classes": SOURCE_CLASSES,
            "claim_directions": CLAIM_DIRECTIONS,
            "required_model_ids": REQUIRED_MODEL_IDS,
            "source_origin_required": True,
            "quality_required": True,
            "claims_required": True,
            "uncertainty_required": True,
            "lineage_required": True,
            "replay_hash_required": True,
            "chain_hash_required": True,
            "contradiction_linkage_supported": True,
            "causal_controls_required": True,
            "adversarial_review_required": True,
            "calibration_tracking_required": True,
            "deterministic_hashing_required": True,
            "immutable_evidence_required": True,
            "read_only_boundary_required": True,
            "publication_allowed": False,
            "alerting_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
        }
        return CanonicalIntelligenceEvidenceContract(**body, contract_hash=stable_hash(body))


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONTRACT_STATUS",
    "CONTRACT_TYPE",
    "EVIDENCE_TYPES",
    "SOURCE_CLASSES",
    "CLAIM_DIRECTIONS",
    "CanonicalEvidenceOrigin",
    "CanonicalEvidenceQuality",
    "CanonicalEvidenceClaim",
    "CanonicalIntelligenceEvidence",
    "CanonicalIntelligenceEvidenceContract",
    "OracleCanonicalIntelligenceEvidenceBuilder",
    "OracleCanonicalEvidenceInvariantError",
    "stable_hash",
]
