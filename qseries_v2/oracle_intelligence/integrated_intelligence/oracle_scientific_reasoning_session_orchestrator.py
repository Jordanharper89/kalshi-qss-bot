from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_scientific_reasoning_input_manifest import (
    ScientificReasoningInputManifest,
    verify_scientific_reasoning_input_manifest,
)

ENGINE_ID = "OII-010"
SCHEMA_VERSION = "OII-010.v1"
ALGORITHM_VERSION = "scientific-reasoning-session-orchestrator.v1"

DISCIPLINE_EXECUTION_ORDER = (
    "information_theory",
    "source_origin",
    "bayesian_inference",
    "causal_inference",
    "signal_detection",
    "calibration_science",
    "consensus_reasoning",
    "decision_theory",
    "game_theory",
    "complex_systems",
    "adversarial_epistemology",
)


class OracleScientificReasoningSessionInvariantError(ValueError):
    """Raised when an OII-010 reasoning-session invariant is violated."""


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [_canonical(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item, sort_keys=True, separators=(",", ":"), ensure_ascii=False
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
class ReasoningDisciplineSession:
    discipline_id: str
    discipline_name: str
    ordinal: int
    source_manifest_id: str
    source_manifest_hash: str
    evidence_input_hashes: tuple[str, ...]
    evidence_count: int
    session_status: str
    execution_allowed: bool
    probability_estimation_allowed: bool
    conclusion_generation_allowed: bool
    discipline_session_hash: str


@dataclass(frozen=True)
class FrozenReasoningEvidenceSet:
    frozen_evidence_set_id: str
    source_manifest_id: str
    source_manifest_hash: str
    evidence_input_hashes: tuple[str, ...]
    certified_evidence_ids: tuple[str, ...]
    evidence_node_ids: tuple[str, ...]
    evidence_count: int
    frozen_evidence_set_hash: str


@dataclass(frozen=True)
class ScientificReasoningSession:
    session_id: str
    source_reasoning_input_manifest_id: str
    source_reasoning_input_manifest_hash: str
    request_id: str
    request_hash: str
    subject_id: str
    question_text: str
    frozen_evidence_set: FrozenReasoningEvidenceSet
    discipline_sessions: tuple[ReasoningDisciplineSession, ...]
    deterministic_execution_order: tuple[str, ...]
    session_state: str
    session_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    evidence_set_frozen: bool
    session_materialized: bool
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


def _resolve_execution_order(
    selected_disciplines: tuple[str, ...],
) -> tuple[str, ...]:
    selected = set(selected_disciplines)
    ordered = tuple(
        discipline
        for discipline in DISCIPLINE_EXECUTION_ORDER
        if discipline in selected
    )
    remainder = tuple(sorted(selected.difference(ordered)))
    return ordered + remainder


def materialize_scientific_reasoning_session(
    *,
    reasoning_input_manifest: ScientificReasoningInputManifest,
) -> ScientificReasoningSession:
    if not isinstance(reasoning_input_manifest, ScientificReasoningInputManifest):
        raise OracleScientificReasoningSessionInvariantError(
            "source must be the canonical OII-009 manifest"
        )

    try:
        verify_scientific_reasoning_input_manifest(reasoning_input_manifest)
    except Exception as exc:
        raise OracleScientificReasoningSessionInvariantError(
            "OII-009 manifest verification failed"
        ) from exc

    forbidden = (
        reasoning_input_manifest.reasoning_execution_allowed,
        reasoning_input_manifest.probability_estimation_allowed,
        reasoning_input_manifest.final_intelligence_conclusion_allowed,
        reasoning_input_manifest.publication_allowed,
        reasoning_input_manifest.alerting_allowed,
        reasoning_input_manifest.qseries_handoff_allowed,
        reasoning_input_manifest.qseries_execution_allowed,
        reasoning_input_manifest.order_creation_allowed,
        reasoning_input_manifest.funds_movement_allowed,
        reasoning_input_manifest.portfolio_mutation_allowed,
    )
    if (
        reasoning_input_manifest.read_only is not True
        or reasoning_input_manifest.reasoning_input_ready is not True
        or any(forbidden)
    ):
        raise OracleScientificReasoningSessionInvariantError(
            "OII-009 manifest violates permanent safety boundary"
        )

    evidence_inputs = tuple(
        sorted(
            reasoning_input_manifest.reasoning_evidence_inputs,
            key=lambda item: item.evidence_node_id,
        )
    )
    if not evidence_inputs:
        raise OracleScientificReasoningSessionInvariantError(
            "reasoning session requires certified evidence"
        )

    evidence_body = {
        "source_manifest_id": reasoning_input_manifest.manifest_id,
        "source_manifest_hash": reasoning_input_manifest.manifest_hash,
        "evidence_input_hashes": tuple(
            item.input_hash for item in evidence_inputs
        ),
        "certified_evidence_ids": tuple(
            item.certified_evidence_id for item in evidence_inputs
        ),
        "evidence_node_ids": tuple(
            item.evidence_node_id for item in evidence_inputs
        ),
        "evidence_count": len(evidence_inputs),
    }
    frozen_hash = stable_hash(evidence_body)
    frozen_set = FrozenReasoningEvidenceSet(
        frozen_evidence_set_id="frozen-reasoning-evidence:" + frozen_hash,
        **evidence_body,
        frozen_evidence_set_hash=frozen_hash,
    )

    execution_order = _resolve_execution_order(
        reasoning_input_manifest.selected_disciplines
    )
    if not execution_order:
        raise OracleScientificReasoningSessionInvariantError(
            "reasoning session requires at least one discipline"
        )

    discipline_sessions: list[ReasoningDisciplineSession] = []
    for ordinal, discipline in enumerate(execution_order, start=1):
        body = {
            "discipline_name": discipline,
            "ordinal": ordinal,
            "source_manifest_id": reasoning_input_manifest.manifest_id,
            "source_manifest_hash": reasoning_input_manifest.manifest_hash,
            "evidence_input_hashes": frozen_set.evidence_input_hashes,
            "evidence_count": frozen_set.evidence_count,
            "session_status": "materialized_not_executing",
            "execution_allowed": False,
            "probability_estimation_allowed": False,
            "conclusion_generation_allowed": False,
        }
        discipline_hash = stable_hash(body)
        discipline_sessions.append(
            ReasoningDisciplineSession(
                discipline_id=(
                    "reasoning-discipline-session:"
                    + discipline
                    + ":"
                    + discipline_hash
                ),
                **body,
                discipline_session_hash=discipline_hash,
            )
        )

    discipline_tuple = tuple(discipline_sessions)
    request = reasoning_input_manifest.reasoning_request

    session_body = {
        "source_reasoning_input_manifest_id":
            reasoning_input_manifest.manifest_id,
        "source_reasoning_input_manifest_hash":
            reasoning_input_manifest.manifest_hash,
        "request_id": request.request_id,
        "request_hash": request.request_hash,
        "subject_id": request.subject_id,
        "question_text": request.question_text,
        "frozen_evidence_set": frozen_set,
        "discipline_sessions": discipline_tuple,
        "deterministic_execution_order": execution_order,
        "session_state": "materialized_read_only_not_executing",
    }
    session_hash = stable_hash(session_body)

    return ScientificReasoningSession(
        session_id="scientific-reasoning-session:" + session_hash,
        **session_body,
        session_hash=session_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        evidence_set_frozen=True,
        session_materialized=True,
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


def verify_scientific_reasoning_session(
    session: ScientificReasoningSession,
) -> bool:
    if not isinstance(session, ScientificReasoningSession):
        raise OracleScientificReasoningSessionInvariantError(
            "invalid OII-010 session type"
        )

    frozen = session.frozen_evidence_set
    frozen_body = {
        "source_manifest_id": frozen.source_manifest_id,
        "source_manifest_hash": frozen.source_manifest_hash,
        "evidence_input_hashes": frozen.evidence_input_hashes,
        "certified_evidence_ids": frozen.certified_evidence_ids,
        "evidence_node_ids": frozen.evidence_node_ids,
        "evidence_count": frozen.evidence_count,
    }
    if stable_hash(frozen_body) != frozen.frozen_evidence_set_hash:
        raise OracleScientificReasoningSessionInvariantError(
            "frozen evidence-set hash verification failed"
        )
    if frozen.frozen_evidence_set_id != (
        "frozen-reasoning-evidence:" + frozen.frozen_evidence_set_hash
    ):
        raise OracleScientificReasoningSessionInvariantError(
            "frozen evidence-set identity verification failed"
        )
    if frozen.evidence_count != len(frozen.evidence_input_hashes):
        raise OracleScientificReasoningSessionInvariantError(
            "frozen evidence count mismatch"
        )
    if frozen.evidence_count <= 0:
        raise OracleScientificReasoningSessionInvariantError(
            "frozen evidence set is empty"
        )

    actual_order = tuple(
        item.discipline_name for item in session.discipline_sessions
    )
    if actual_order != session.deterministic_execution_order:
        raise OracleScientificReasoningSessionInvariantError(
            "discipline execution-order mismatch"
        )
    actual_ordinals = tuple(
        item.ordinal for item in session.discipline_sessions
    )
    expected_ordinals = tuple(range(1, len(session.discipline_sessions) + 1))
    if actual_ordinals != expected_ordinals:
        raise OracleScientificReasoningSessionInvariantError(
            "discipline ordinals are not contiguous"
        )

    for item in session.discipline_sessions:
        body = {
            key: value
            for key, value in asdict(item).items()
            if key not in {"discipline_id", "discipline_session_hash"}
        }
        if stable_hash(body) != item.discipline_session_hash:
            raise OracleScientificReasoningSessionInvariantError(
                "discipline-session hash verification failed"
            )
        expected_id = (
            "reasoning-discipline-session:"
            + item.discipline_name
            + ":"
            + item.discipline_session_hash
        )
        if item.discipline_id != expected_id:
            raise OracleScientificReasoningSessionInvariantError(
                "discipline-session identity verification failed"
            )
        if (
            item.execution_allowed
            or item.probability_estimation_allowed
            or item.conclusion_generation_allowed
        ):
            raise OracleScientificReasoningSessionInvariantError(
                "discipline session improperly enables reasoning activity"
            )
        if item.evidence_input_hashes != frozen.evidence_input_hashes:
            raise OracleScientificReasoningSessionInvariantError(
                "discipline session evidence set is not frozen"
            )

    session_body = {
        "source_reasoning_input_manifest_id":
            session.source_reasoning_input_manifest_id,
        "source_reasoning_input_manifest_hash":
            session.source_reasoning_input_manifest_hash,
        "request_id": session.request_id,
        "request_hash": session.request_hash,
        "subject_id": session.subject_id,
        "question_text": session.question_text,
        "frozen_evidence_set": session.frozen_evidence_set,
        "discipline_sessions": session.discipline_sessions,
        "deterministic_execution_order":
            session.deterministic_execution_order,
        "session_state": session.session_state,
    }
    if stable_hash(session_body) != session.session_hash:
        raise OracleScientificReasoningSessionInvariantError(
            "session hash verification failed"
        )
    if session.session_id != "scientific-reasoning-session:" + session.session_hash:
        raise OracleScientificReasoningSessionInvariantError(
            "session identity verification failed"
        )

    forbidden = (
        session.reasoning_execution_allowed,
        session.probability_estimation_allowed,
        session.final_intelligence_conclusion_allowed,
        session.publication_allowed,
        session.alerting_allowed,
        session.qseries_handoff_allowed,
        session.qseries_execution_allowed,
        session.order_creation_allowed,
        session.funds_movement_allowed,
        session.portfolio_mutation_allowed,
    )
    if (
        session.read_only is not True
        or session.evidence_set_frozen is not True
        or session.session_materialized is not True
        or any(forbidden)
    ):
        raise OracleScientificReasoningSessionInvariantError(
            "OII-010 safety boundary violated"
        )
    return True


def serialize_scientific_reasoning_session(
    session: ScientificReasoningSession,
) -> str:
    verify_scientific_reasoning_session(session)
    return canonical_json(session)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "DISCIPLINE_EXECUTION_ORDER",
    "ReasoningDisciplineSession",
    "FrozenReasoningEvidenceSet",
    "ScientificReasoningSession",
    "OracleScientificReasoningSessionInvariantError",
    "materialize_scientific_reasoning_session",
    "verify_scientific_reasoning_session",
    "serialize_scientific_reasoning_session",
]
