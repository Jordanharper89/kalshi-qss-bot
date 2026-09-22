from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from .oar_021_live_intelligence_pipeline_coordinator import (
    LiveIntelligencePipelinePackage,
)

BUILD_ID = "OAR-022"
OAR_022_REVISION = "OAR_022_TERMINAL_LIVE_INTELLIGENCE_READ_MODEL_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


def _stable_hash(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class TerminalLiveIntelligenceReadModel:
    read_model_id: str
    iteration_number: int
    observation_count: int
    observation_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    capability_ids: tuple[str, ...]
    oi_ready: bool
    umd_ready: bool
    oml_ready: bool
    lineage_valid: bool
    generated_at: datetime
    evidence_hash: str
    read_only: bool


class TerminalLiveIntelligenceReadModelBuilder:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def build(
        self,
        *,
        pipeline: LiveIntelligencePipelinePackage,
        generated_at: datetime,
    ) -> TerminalLiveIntelligenceReadModel:
        if not isinstance(
            pipeline,
            LiveIntelligencePipelinePackage,
        ):
            raise TypeError(
                "pipeline must be LiveIntelligencePipelinePackage"
            )

        if not isinstance(
            generated_at,
            datetime,
        ):
            raise TypeError(
                "generated_at must be datetime"
            )

        if generated_at.tzinfo is None:
            raise ValueError(
                "generated_at must be timezone-aware"
            )

        oi = pipeline.integration.oi_handoff

        if pipeline.integration.lineage_valid is not True:
            raise ValueError(
                "pipeline lineage must be valid"
            )

        if oi.observation_count != pipeline.observation_count:
            raise ValueError(
                "pipeline observation count mismatch"
            )

        body = {
            "iteration_number": pipeline.iteration_number,
            "observation_ids": oi.observation_ids,
            "provider_ids": oi.provider_ids,
            "capability_ids": oi.capability_ids,
            "oi_ready": pipeline.oi_ready,
            "umd_ready": pipeline.umd_ready,
            "oml_ready": pipeline.oml_ready,
            "lineage_valid": pipeline.integration.lineage_valid,
        }

        evidence_hash = _stable_hash(
            body
        )

        return TerminalLiveIntelligenceReadModel(
            read_model_id=(
                "terminal.live."
                + evidence_hash[:32]
            ),
            iteration_number=(
                pipeline.iteration_number
            ),
            observation_count=(
                pipeline.observation_count
            ),
            observation_ids=(
                oi.observation_ids
            ),
            provider_ids=(
                oi.provider_ids
            ),
            capability_ids=(
                oi.capability_ids
            ),
            oi_ready=(
                pipeline.oi_ready
            ),
            umd_ready=(
                pipeline.umd_ready
            ),
            oml_ready=(
                pipeline.oml_ready
            ),
            lineage_valid=True,
            generated_at=generated_at.astimezone(
                timezone.utc
            ),
            evidence_hash=evidence_hash,
            read_only=True,
        )


def verify_terminal_live_intelligence_read_model() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_022_REVISION",
    "TerminalLiveIntelligenceReadModel",
    "TerminalLiveIntelligenceReadModelBuilder",
    "verify_terminal_live_intelligence_read_model",
]
