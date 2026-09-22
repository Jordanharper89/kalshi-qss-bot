from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from qseries_v2.observation_adapter_runtime.oar_026_live_ask_dispatch_binding import (
    LiveAskDispatchBinding,
)
from .olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
)

BUILD_ID = "OLC-009"
OLC_009_REVISION = "OLC_009_LIVE_ASK_REGISTRY_OVERLAY_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveAskOverlayResult:
    live_handled: bool
    fallback_used: bool
    route: str
    observation_count: int
    read_only: bool


class LiveAskHandlerOverlay:
    read_only = True
    execution_allowed = False
    source_mutation_allowed = False
    publication_allowed = False

    def __init__(
        self,
        *,
        store: AtomicLiveReadModelStore,
        fallback_handler: Callable[..., Any],
    ):
        if not isinstance(
            store,
            AtomicLiveReadModelStore,
        ):
            raise TypeError(
                "store must be AtomicLiveReadModelStore"
            )

        if not callable(
            fallback_handler
        ):
            raise TypeError(
                "fallback_handler must be callable"
            )

        self.store = store
        self.fallback_handler = fallback_handler

    def dispatch(
        self,
        query: str,
        *args,
        **kwargs,
    ):
        snapshot = self.store.snapshot()

        result = (
            LiveAskDispatchBinding()
            .dispatch(
                query=query,
                read_model=snapshot.read_model,
            )
        )

        if (
            result.consume_existing_terminal
        ):
            fallback_value = (
                self.fallback_handler(
                    query,
                    *args,
                    **kwargs,
                )
            )

            return LiveAskOverlayResult(
                live_handled=False,
                fallback_used=True,
                route=(
                    result
                    .live_response
                    .route
                ),
                observation_count=0,
                read_only=True,
            ), fallback_value

        return LiveAskOverlayResult(
            live_handled=True,
            fallback_used=False,
            route=(
                result
                .live_response
                .route
            ),
            observation_count=(
                result
                .live_response
                .observation_count
            ),
            read_only=True,
        ), result.live_response


def verify_live_ask_registry_overlay() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_009_REVISION",
    "LiveAskOverlayResult",
    "LiveAskHandlerOverlay",
    "verify_live_ask_registry_overlay",
]
