from __future__ import annotations

from qseries_v2.observation_adapter_runtime.oar_027_terminal_live_query_e2e import (
    TerminalLiveQueryEndToEnd,
)

BUILD_ID = "OAR-027-LAUNCHER"
REVISION = "OAR_027_TERMINAL_LIVE_INTELLIGENCE_LAUNCHER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


def build_terminal_live_query_path():
    return TerminalLiveQueryEndToEnd()


def main() -> int:
    print("=" * 72)
    print(" ORACLE TERMINAL LIVE INTELLIGENCE READ PATH")
    print("=" * 72)
    print("[MODE] READ-ONLY")
    print("[PASS] OAR-027 live query path available")
    print("[PASS] Existing Oracle Terminal remains fallback-safe")
    print("[PASS] Execution, publication, and persistence disabled")
    print()
    print(
        "[INFO] This launcher certifies the live-intelligence "
        "query path. Production terminal command-loop activation "
        "occurs only after final end-to-end certification."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
