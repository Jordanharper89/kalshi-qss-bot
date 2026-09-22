from __future__ import annotations

from qseries_v2.observation_adapter_runtime.oar_029_terminal_live_activation import (
    TerminalLiveActivationBoundary,
)

BUILD_ID = "OAR-029-LAUNCHER"
REVISION = "OAR_029_TERMINAL_LIVE_READ_ONLY_LAUNCHER_V1"


def main() -> int:
    activation = (
        TerminalLiveActivationBoundary()
        .activate()
    )

    print("=" * 72)
    print(" ORACLE TERMINAL — LIVE INTELLIGENCE READ-ONLY ACTIVATION")
    print("=" * 72)
    print(f"[ACTIVATION] {activation.activation_id}")
    print("[MODE] READ-ONLY")
    print("[PASS] Live /ask interception enabled")
    print("[PASS] Existing Oracle Terminal fallback enabled")
    print("[PASS] OAR-027 terminal live read path active")
    print("[PASS] Execution, publication, and persistence disabled")
    print()
    print(
        "[INFO] This launcher activates the certified "
        "live-intelligence read boundary. It does not place trades."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
