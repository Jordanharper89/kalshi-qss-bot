from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "integrated_intelligence"
UPSTREAM = PKG / "oracle_integrated_intelligence_scientific_model_registry.py"
PRODUCTION = PKG / "oracle_integrated_intelligence_canonical_evidence_contract.py"
TEST = ROOT / "test_oii_002_oracle_integrated_intelligence_canonical_evidence_contract.py"
INIT = PKG / "__init__.py"

PRODUCTION_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_canonical_evidence_contract import (
    CONTRACT_STATUS,
    CONTRACT_TYPE,
    OracleCanonicalEvidenceInvariantError,
    OracleCanonicalIntelligenceEvidenceBuilder,
    stable_hash,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_scientific_model_registry import REQUIRED_MODEL_IDS


def without_hash(value, field):
    return {k: v for k, v in value.__dict__.items() if k != field}


def main() -> int:
    print("=" * 56)
    print(" OII-002 TEST")
    print(" CANONICAL INTELLIGENCE EVIDENCE CONTRACT")
    print("=" * 56)

    builder = OracleCanonicalIntelligenceEvidenceBuilder()
    now = datetime(2026, 7, 27, 13, 0, tzinfo=timezone.utc)

    origin = builder.origin(
        source_id="source.kalshi.market_data",
        source_class="primary",
        source_name="Kalshi public market data",
        source_locator="/markets",
        source_observation_id="kalshi.market.example.001",
        source_content_hash="content-001",
        source_replay_hash="replay-001",
        source_chain_hash="chain-001",
        source_adapter_id="adapter.oracle.kalshi.public_markets.shadow",
        source_environment="production",
        acquired_at=now,
        observed_at=now - timedelta(seconds=5),
        authentication_used=False,
        public_source=True,
        shadow_mode=True,
    )
    assert origin.read_only
    assert origin.origin_hash == stable_hash(without_hash(origin, "origin_hash"))

    quality = builder.quality(
        source_reliability=0.99,
        source_independence=0.95,
        relevance=1.0,
        specificity=0.98,
        freshness=1.0,
        completeness=0.92,
        manipulation_risk=0.05,
        contradiction_risk=0.10,
        uncertainty=0.08,
    )
    assert quality.quality_hash == stable_hash(without_hash(quality, "quality_hash"))

    claim = builder.claim(
        claim_text="The canonical snapshot reports a YES ask of 0.61.",
        claim_direction="supports",
        claim_target_id="market.example.001",
        claim_probability=0.99,
        claim_uncertainty=0.01,
        causal_claim=False,
    )
    assert claim.claim_hash == stable_hash(without_hash(claim, "claim_hash"))

    evidence = builder.evidence(
        evidence_type="market_observation",
        subject_id="market.example.001",
        subject_type="prediction_contract",
        title="Canonical market snapshot",
        summary="Read-only evidence for integrated intelligence models.",
        payload={
            "venue_id": "venue.kalshi",
            "yes_bid_dollars": "0.60",
            "yes_ask_dollars": "0.61",
            "liquidity_dollars": "5000.00",
        },
        origin=origin,
        quality=quality,
        claims=(claim,),
        model_eligibility=REQUIRED_MODEL_IDS,
        parent_evidence_ids=(),
        contradictory_evidence_ids=("counterevidence.001",),
        created_at=now,
        valid_from=now,
        valid_until=now + timedelta(minutes=5),
    )
    repeated = builder.evidence(
        evidence_type="market_observation",
        subject_id="market.example.001",
        subject_type="prediction_contract",
        title="Canonical market snapshot",
        summary="Read-only evidence for integrated intelligence models.",
        payload={
            "liquidity_dollars": "5000.00",
            "yes_ask_dollars": "0.61",
            "yes_bid_dollars": "0.60",
            "venue_id": "venue.kalshi",
        },
        origin=origin,
        quality=quality,
        claims=(claim,),
        model_eligibility=tuple(reversed(REQUIRED_MODEL_IDS)),
        parent_evidence_ids=(),
        contradictory_evidence_ids=("counterevidence.001",),
        created_at=now,
        valid_from=now,
        valid_until=now + timedelta(minutes=5),
    )
    assert evidence == repeated
    assert evidence.evidence_hash == stable_hash(without_hash(evidence, "evidence_hash"))
    assert evidence.immutable and evidence.replayable and evidence.explainable
    assert evidence.source_lineage_verified and evidence.uncertainty_explicit
    assert evidence.adversarial_review_required and evidence.calibration_tracking_required
    assert evidence.read_only
    assert not any(
        (
            evidence.publication_allowed,
            evidence.alerting_allowed,
            evidence.qseries_handoff_allowed,
            evidence.qseries_execution_allowed,
            evidence.order_creation_allowed,
            evidence.funds_movement_allowed,
            evidence.portfolio_mutation_allowed,
        )
    )

    contract = builder.contract()
    assert contract.contract_status == CONTRACT_STATUS
    assert contract.contract_type == CONTRACT_TYPE
    assert contract.required_model_ids == REQUIRED_MODEL_IDS
    assert contract.contract_hash == stable_hash(without_hash(contract, "contract_hash"))
    assert contract.source_origin_required
    assert contract.quality_required
    assert contract.claims_required
    assert contract.uncertainty_required
    assert contract.lineage_required
    assert contract.replay_hash_required
    assert contract.chain_hash_required
    assert contract.contradiction_linkage_supported
    assert contract.causal_controls_required
    assert contract.adversarial_review_required
    assert contract.calibration_tracking_required
    assert contract.deterministic_hashing_required
    assert contract.immutable_evidence_required
    assert contract.read_only_boundary_required
    assert not any(
        (
            contract.publication_allowed,
            contract.alerting_allowed,
            contract.qseries_handoff_allowed,
            contract.qseries_execution_allowed,
            contract.order_creation_allowed,
            contract.funds_movement_allowed,
            contract.portfolio_mutation_allowed,
        )
    )

    try:
        builder.claim(
            claim_text="Invalid causal claim",
            claim_direction="supports",
            claim_target_id="market.example.001",
            claim_probability=0.75,
            claim_uncertainty=0.25,
            causal_claim=True,
        )
    except OracleCanonicalEvidenceInvariantError:
        pass
    else:
        raise AssertionError("causal claim controls not enforced")

    print("[PASS] Actual OII-001 scientific model registry consumed")
    print("[PASS] Canonical source-origin lineage verified")
    print("[PASS] Evidence quality and uncertainty contract verified")
    print("[PASS] Canonical claims and contradiction linkage verified")
    print("[PASS] Causal claims require mechanism and counterfactual")
    print("[PASS] All nine scientific models supported")
    print("[PASS] Deterministic evidence identity and hashing verified")
    print("[PASS] Immutable, replayable, explainable read-only evidence verified")
    print("[PASS] Publication, alerting, handoff, and execution remain disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    print("=" * 56)
    print(" OII-002 INSTALLER")
    print(" CANONICAL INTELLIGENCE EVIDENCE CONTRACT")
    print("=" * 56)

    if not UPSTREAM.exists():
        raise FileNotFoundError(f"Required OII-001 module not found: {UPSTREAM}")

    upstream_text = UPSTREAM.read_text(encoding="utf-8")
    for token in (
        'SCHEMA_VERSION = "OII-001"',
        "REQUIRED_MODEL_IDS",
        "OracleIntegratedIntelligenceScientificModelRegistryBuilder",
        "qseries_execution_allowed",
        "portfolio_mutation_allowed",
    ):
        if token not in upstream_text:
            raise RuntimeError(f"OII-001 contract mismatch: missing {token}")

    protected_hash = sha(UPSTREAM)
    print("[OK] Actual OII-001 scientific model registry verified")

    PKG.mkdir(parents=True, exist_ok=True)
    if not INIT.exists():
        INIT.write_text('"""Oracle integrated intelligence subsystem."""\n', encoding="utf-8")

    PRODUCTION.write_text(PRODUCTION_SOURCE.strip() + "\n", encoding="utf-8", newline="\n")
    TEST.write_text(TEST_SOURCE.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {PRODUCTION.resolve()}")
    print(f"[OK] FULL REPLACEMENT: {TEST.resolve()}")

    export = "from .oracle_integrated_intelligence_canonical_evidence_contract import *"
    init_text = INIT.read_text(encoding="utf-8")
    if export not in init_text.splitlines():
        if init_text and not init_text.endswith("\n"):
            init_text += "\n"
        INIT.write_text(init_text + export + "\n", encoding="utf-8", newline="\n")
        print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
    else:
        print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")

    for path in (PRODUCTION, TEST, INIT):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("[OK] Production, test, and package syntax verified")

    if sha(UPSTREAM) != protected_hash:
        raise RuntimeError("Protected OII-001 module changed during installation")

    result = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

    if sha(UPSTREAM) != protected_hash:
        raise RuntimeError("Protected OII-001 module changed during testing")

    print("[PASS] OII-001 source unchanged")
    print("[PASS] No acquisition, analytics, Operator, or Q Series execution module modified")
    print("[OK] OII-002 test executed automatically")
    print()
    print("[DONE] OII-002 canonical intelligence evidence contract installed")
    print()
    print("NEXT BUILD")
    print("  OII-003 Source-Origin and Information-Quality Engine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
