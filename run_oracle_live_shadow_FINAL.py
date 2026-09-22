from __future__ import annotations

import os
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
    build_real_oracle_shadow_graph,
)

ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("========================================")
    print(" ORACLE LIVE SHADOW FINAL LAUNCH")
    print(" READ-ONLY PRODUCTION RUNTIME")
    print("========================================")

    graph = build_real_oracle_shadow_graph(
        runtime_root=ROOT.resolve(),
        environment=dict(os.environ),
        service_tick_interval_seconds=5,
    )

    activator = graph[
        "production_live_shadow_persistent_service_activator"
    ]

    print("[OK] OLA-030 production graph assembled")
    print("[OK] PostgreSQL bootstrap completed")
    print("[OK] Dual-router lineage topology attested")
    print("[START] Oracle live-shadow service")
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
