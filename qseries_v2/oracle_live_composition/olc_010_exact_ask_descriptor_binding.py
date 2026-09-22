from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from qseries_v2.oracle_live_composition.olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
)
from qseries_v2.observation_adapter_runtime.oar_026_live_ask_dispatch_binding import (
    LiveAskDispatchBinding,
)

BUILD_ID = "OLC-010"
OLC_010_REVISION = "OLC_010_EXACT_ASK_DESCRIPTOR_BINDING_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False

INJECTION_SYMBOL = "display_query"
DISPATCH_SYMBOL = "dispatch_command"
ASK_HANDLER_NAME = "handle_ask"


@dataclass(frozen=True, slots=True)
class LiveDisplayQueryDispatch:
    query: str
    live_handled: bool
    fallback_used: bool
    route: str
    observation_count: int
    read_model_id: str | None
    evidence_hash: str | None
    read_only: bool


def build_live_display_query(
    *,
    store: AtomicLiveReadModelStore,
    original_display_query: Callable[..., Any],
) -> Callable[..., Any]:
    if not isinstance(
        store,
        AtomicLiveReadModelStore,
    ):
        raise TypeError(
            "store must be AtomicLiveReadModelStore"
        )

    if not callable(
        original_display_query
    ):
        raise TypeError(
            "original_display_query must be callable"
        )

    def live_display_query(
        query,
        *,
        session=None,
        root=None,
        builder=None,
        write=print,
    ):
        snapshot = store.snapshot()

        dispatch = (
            LiveAskDispatchBinding()
            .dispatch(
                query=str(query),
                read_model=snapshot.read_model,
            )
        )

        response = dispatch.live_response

        if dispatch.consume_existing_terminal:
            kwargs = {
                "session": session,
                "root": root,
                "write": write,
            }

            if builder is not None:
                kwargs["builder"] = builder

            return original_display_query(
                query,
                **kwargs,
            )

        # This boundary deliberately exposes only certified
        # read-model facts. It does not invent explanation,
        # probability, direction, or trade authorization.
        write(
            "================================================================"
        )
        write(
            "Oracle Live Intelligence Read Path"
        )
        write(
            "STATUS: LIVE EVIDENCE AVAILABLE | MODE: READ-ONLY"
        )
        write(
            f"route: {response.route}"
        )
        write(
            f"observations: {response.observation_count}"
        )
        write(
            f"read model: {response.read_model_id}"
        )
        write(
            f"evidence hash: {response.evidence_hash}"
        )
        write(
            "Live evidence is attached to the terminal query path. "
            "Reasoning remains bounded by the existing certified Oracle pipeline."
        )
        write(
            "================================================================"
        )

        if session is not None:
            if hasattr(
                session,
                "query_count",
            ):
                session.query_count += 1

            if hasattr(
                session,
                "last_query",
            ):
                session.last_query = str(
                    query
                )

            if hasattr(
                session,
                "last_session_id",
            ):
                session.last_session_id = (
                    response.read_model_id
                    or ""
                )

        return LiveDisplayQueryDispatch(
            query=str(query),
            live_handled=True,
            fallback_used=False,
            route=response.route,
            observation_count=(
                response.observation_count
            ),
            read_model_id=(
                response.read_model_id
            ),
            evidence_hash=(
                response.evidence_hash
            ),
            read_only=True,
        )

    live_display_query.__name__ = (
        "olc_live_display_query"
    )

    live_display_query.__doc__ = (
        "Read-only live intelligence overlay for the "
        "actual run_oracle_open_intelligence_terminal.display_query boundary."
    )

    return live_display_query


def verify_exact_ask_descriptor_binding() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert INJECTION_SYMBOL == "display_query"
    assert DISPATCH_SYMBOL == "dispatch_command"
    assert ASK_HANDLER_NAME == "handle_ask"
    return True


__all__ = [
    "BUILD_ID",
    "OLC_010_REVISION",
    "INJECTION_SYMBOL",
    "DISPATCH_SYMBOL",
    "ASK_HANDLER_NAME",
    "LiveDisplayQueryDispatch",
    "build_live_display_query",
    "verify_exact_ask_descriptor_binding",
]
