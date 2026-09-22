from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    build_default_adapter_bundle,
)
from qseries_v2.observation_adapter_runtime.oar_001_runtime_foundation import (
    build_runtime_config,
)
from qseries_v2.observation_adapter_runtime.oar_006_production_launch_boundary import (
    ProductionLiveObservationLauncher,
)
from qseries_v2.observation_adapter_runtime.oar_010_canonical_live_observation_bus import (
    CanonicalLiveObservationBus,
)
from qseries_v2.observation_adapter_runtime.oar_011_live_observation_admission import (
    LiveObservationAdmissionGate,
)
from qseries_v2.observation_adapter_runtime.oar_021_live_intelligence_pipeline_coordinator import (
    LiveIntelligencePipelineCoordinator,
)
from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
    TerminalLiveIntelligenceReadModelBuilder,
)

from .olc_001_live_composition_foundation import (
    OracleLiveCompositionConfig,
)

BUILD_ID = "OLC-004"
OLC_004_REVISION = "OLC_004_LIVE_INTELLIGENCE_CYCLE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveIntelligenceCycleResult:
    composition_id: str
    runtime_id: str
    iteration_number: int
    adapter_request_count: int
    adapter_success_count: int
    adapter_failure_count: int
    raw_observation_count: int
    admitted_observation_count: int
    terminal_read_model: TerminalLiveIntelligenceReadModel
    read_only: bool
    execution_allowed: bool


class ProductionLiveIntelligenceCycle:
    read_only = True
    execution_allowed = False
    order_placement_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def run_once(
        self,
        *,
        config: OracleLiveCompositionConfig,
        clock_callable: Callable[[], datetime],
        subject_hints: dict[str, str | None] | None = None,
    ) -> LiveIntelligenceCycleResult:
        if not isinstance(
            config,
            OracleLiveCompositionConfig,
        ):
            raise TypeError(
                "config must be OracleLiveCompositionConfig"
            )

        if not callable(
            clock_callable
        ):
            raise TypeError(
                "clock_callable must be callable"
            )

        bundle = build_default_adapter_bundle()

        runtime_config = build_runtime_config(
            runtime_id=config.runtime_id,
            tick_interval_seconds=(
                config.tick_interval_seconds
            ),
        )

        launch_record, service_result = (
            ProductionLiveObservationLauncher()
            .launch(
                config=runtime_config,
                bundle=bundle,
                iterations=1,
                clock_callable=clock_callable,
                sleep_callable=lambda _: None,
                stop_requested_callable=lambda: False,
                subject_hints=subject_hints,
            )
        )

        if service_result.iterations_completed != 1:
            raise RuntimeError(
                "production live observation iteration did not complete"
            )

        run_result = (
            service_result
            .run_results[-1]
        )

        canonical_batch = (
            CanonicalLiveObservationBus()
            .materialize(
                run_result
            )
        )

        admission = (
            LiveObservationAdmissionGate()
            .admit(
                canonical_batch
            )
        )

        pipeline = (
            LiveIntelligencePipelineCoordinator()
            .coordinate(
                admission
            )
        )

        generated_at = clock_callable()

        read_model = (
            TerminalLiveIntelligenceReadModelBuilder()
            .build(
                pipeline=pipeline,
                generated_at=generated_at,
            )
        )

        if read_model.read_only is not True:
            raise RuntimeError(
                "terminal live read model is not read-only"
            )

        return LiveIntelligenceCycleResult(
            composition_id=config.composition_id,
            runtime_id=config.runtime_id,
            iteration_number=run_result.iteration_number,
            adapter_request_count=run_result.request_count,
            adapter_success_count=run_result.success_count,
            adapter_failure_count=run_result.failure_count,
            raw_observation_count=run_result.observation_count,
            admitted_observation_count=(
                admission.admitted_count
            ),
            terminal_read_model=read_model,
            read_only=True,
            execution_allowed=False,
        )


def verify_live_intelligence_cycle() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_004_REVISION",
    "LiveIntelligenceCycleResult",
    "ProductionLiveIntelligenceCycle",
    "verify_live_intelligence_cycle",
]
