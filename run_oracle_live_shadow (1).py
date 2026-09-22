from __future__ import annotations

import inspect
import sys

from qseries_v2.oracle_intelligence.live_acquisition_model import (
    oracle_first_real_shadow_corpus_launch_command as ola030,
)


def _find_graph_builder():
    preferred = getattr(
        ola030,
        "build_real_oracle_shadow_graph",
        None,
    )

    if callable(preferred):
        return preferred

    candidates = []

    for name, value in vars(ola030).items():
        if (
            callable(value)
            and "build" in name.lower()
            and "graph" in name.lower()
        ):
            candidates.append(
                (name, value)
            )

    if len(candidates) == 1:
        return candidates[0][1]

    raise RuntimeError(
        "Could not uniquely resolve the OLA-030 production graph builder. "
        f"Candidates: {[name for name, _ in candidates]}"
    )


def _call_if_no_required_args(fn):
    signature = inspect.signature(fn)

    required = [
        parameter
        for parameter in signature.parameters.values()
        if (
            parameter.default is inspect.Parameter.empty
            and parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
        )
    ]

    if required:
        raise RuntimeError(
            "The production graph builder requires explicit dependencies "
            "and cannot be safely guessed by the operator launcher. "
            f"Signature: {fn.__name__}{signature}"
        )

    return fn()


def main() -> int:
    print("========================================")
    print(" ORACLE LIVE SHADOW OPERATOR LAUNCH")
    print(" READ-ONLY PRODUCTION RUNTIME")
    print("========================================")

    builder = _find_graph_builder()

    print(
        f"[OK] Resolved production graph builder: "
        f"{builder.__module__}.{builder.__name__}"
    )

    print(
        f"[OK] Builder signature: "
        f"{builder.__name__}{inspect.signature(builder)}"
    )

    graph = _call_if_no_required_args(
        builder
    )

    if not isinstance(graph, dict):
        raise RuntimeError(
            "OLA-030 production graph builder did not return a mapping"
        )

    activator = graph.get(
        "production_live_shadow_persistent_service_activator"
    )

    if activator is None:
        raise RuntimeError(
            "OLA-063 persistent service activator is missing "
            "from the OLA-030 production graph"
        )

    if getattr(
        activator,
        "read_only",
        None,
    ) is not True:
        raise RuntimeError(
            "Persistent service activator is not read-only"
        )

    if getattr(
        activator,
        "execution_allowed",
        None,
    ) is not False:
        raise RuntimeError(
            "Persistent service activator exposes execution permission"
        )

    print("[OK] OLA-063 persistent service activator resolved")
    print("[OK] Oracle read-only boundary verified")
    print("[START] Launching Oracle live-shadow service")
    print("[INFO] Press Ctrl+C for operator shutdown")

    try:
        record, result = activator.activate(
            production_graph=graph,
        )

        print("[STOP] Oracle live-shadow service returned")
        print(record)
        print(result)

        return 0

    except KeyboardInterrupt:
        print(
            "\n[STOP] Operator shutdown requested"
        )

        return 130


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
