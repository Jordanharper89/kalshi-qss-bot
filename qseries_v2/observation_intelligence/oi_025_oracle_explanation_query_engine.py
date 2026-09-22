from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_013_observation_requirement_resolution import ObservationRequirementProfile
from .oi_024_oracle_explanation_read_model import OracleExplanationReadModel

BUILD_ID = "OI-025"
OI_025_REVISION = "OI_025_ORACLE_EXPLANATION_QUERY_ENGINE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False

QUERY_KIND_EXPLANATION = "explanation"
QUERY_KIND_EVIDENCE = "evidence"
QUERY_KIND_TIMELINE = "timeline"
SUPPORTED_QUERY_KINDS = (
    QUERY_KIND_EVIDENCE,
    QUERY_KIND_EXPLANATION,
    QUERY_KIND_TIMELINE,
)


class OracleExplanationQueryEngineError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleExplanationQuery:
    query_id: str
    raw_text: str
    normalized_text: str
    query_kind: str
    subject_hint: str
    profile_id: str
    query_hash: str


class OracleExplanationQueryEngine:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_claim_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def __init__(
        self,
        profile_map: Mapping[str, str],
    ) -> None:
        normalized = {}

        for key, value in dict(profile_map).items():
            route_key = " ".join(str(key).strip().lower().split())
            profile_id = " ".join(str(value).strip().lower().split())

            if not route_key or not profile_id:
                raise OracleExplanationQueryEngineError(
                    "profile map keys and values must not be empty"
                )

            normalized[route_key] = profile_id

        self._profile_map = MappingProxyType(
            dict(sorted(normalized.items()))
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(str(text).strip().lower().split())

    @staticmethod
    def _classify(text: str) -> str:
        normalized = OracleExplanationQueryEngine._normalize(text)

        if (
            "timeline" in normalized
            or "what happened before" in normalized
            or "what happened after" in normalized
        ):
            return QUERY_KIND_TIMELINE

        if (
            normalized.startswith("show evidence")
            or "what evidence" in normalized
            or "evidence supports" in normalized
            or "evidence contradicts" in normalized
        ):
            return QUERY_KIND_EVIDENCE

        if (
            normalized.startswith("why ")
            or " explain " in f" {normalized} "
            or normalized.startswith("explain ")
        ):
            return QUERY_KIND_EXPLANATION

        return QUERY_KIND_EXPLANATION

    def resolve(
        self,
        *,
        query_id: str,
        text: str,
        subject_hint: str,
        domain: str,
    ) -> OracleExplanationQuery:
        query_id_value = str(query_id).strip()
        raw_text = str(text).strip()
        subject = " ".join(str(subject_hint).strip().split())
        domain_key = self._normalize(domain)

        if not query_id_value:
            raise OracleExplanationQueryEngineError(
                "query_id must not be empty"
            )
        if not raw_text:
            raise OracleExplanationQueryEngineError(
                "text must not be empty"
            )
        if not subject:
            raise OracleExplanationQueryEngineError(
                "subject_hint must not be empty"
            )

        profile_id = self._profile_map.get(domain_key)

        if profile_id is None:
            profile_id = self._profile_map.get("*")

        if profile_id is None:
            raise OracleExplanationQueryEngineError(
                f"no explanation profile for domain: {domain_key}"
            )

        normalized_text = self._normalize(raw_text)
        query_kind = self._classify(raw_text)

        body = {
            "query_id": query_id_value,
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "query_kind": query_kind,
            "subject_hint": subject,
            "profile_id": profile_id,
        }

        return OracleExplanationQuery(
            query_id=query_id_value,
            raw_text=raw_text,
            normalized_text=normalized_text,
            query_kind=query_kind,
            subject_hint=subject,
            profile_id=profile_id,
            query_hash=deterministic_sha256(body),
        )

    def read_model_matches(
        self,
        query: OracleExplanationQuery,
        model: OracleExplanationReadModel,
    ) -> bool:
        if not isinstance(query, OracleExplanationQuery):
            raise TypeError("query must be OracleExplanationQuery")
        if not isinstance(model, OracleExplanationReadModel):
            raise TypeError("model must be OracleExplanationReadModel")

        return (
            model.query_id == query.query_id
            and model.profile_id == query.profile_id
        )


def default_explanation_profile_map() -> Mapping[str, str]:
    return MappingProxyType(
        {
            "*": "profile.market_explanation",
            "crypto": "profile.market_explanation",
            "economics": "profile.market_explanation",
            "politics": "profile.market_explanation",
            "sports": "profile.market_explanation",
            "weather": "profile.market_explanation",
        }
    )


def verify_oracle_explanation_query_engine() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-025 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
        )
    ):
        raise AssertionError("OI-025 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_025_REVISION",
    "QUERY_KIND_EXPLANATION",
    "QUERY_KIND_EVIDENCE",
    "QUERY_KIND_TIMELINE",
    "SUPPORTED_QUERY_KINDS",
    "OracleExplanationQueryEngineError",
    "OracleExplanationQuery",
    "OracleExplanationQueryEngine",
    "default_explanation_profile_map",
    "verify_oracle_explanation_query_engine",
]
