from __future__ import annotations

import os
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
    build_real_oracle_shadow_graph,
)


ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("========================================")
    print(" ORACLE LIVE SHADOW OPERATOR LAUNCH")
    print(" READ-ONLY PRODUCTION RUNTIME")
    print("========================================")

    graph = build_real_oracle_shadow_graph(
        runtime_root=ROOT,
        environment=dict(os.environ),
        service_tick_interval_seconds=5,
    )

    if not isinstance(graph, dict):
        raise RuntimeError(
            "OLA-030 production graph did not return a mapping"
        )

    activator = graph.get(
        "production_live_shadow_persistent_service_activator"
    )

    if activator is None:
        raise RuntimeError(
            "OLA-063 persistent service activator is missing "
            "from the OLA-030 production graph"
        )

    if getattr(activator, "read_only", None) is not True:
        raise RuntimeError(
            "OLA-063 activator is not read-only"
        )

    if getattr(activator, "execution_allowed", None) is not False:
        raise RuntimeError(
            "OLA-063 activator exposes execution permission"
        )

    print("[OK] OLA-030 production graph assembled")
    print(f"[OK] Runtime root: {ROOT}")
    print("[OK] Current environment passed to production graph")
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
        print("\n[STOP] Operator shutdown requested")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
