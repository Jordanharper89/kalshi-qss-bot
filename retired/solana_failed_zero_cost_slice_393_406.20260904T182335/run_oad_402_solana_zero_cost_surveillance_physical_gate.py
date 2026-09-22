from __future__ import annotations

from qseries_v2.oracle_adapters.independent.oad_402_solana_zero_cost_surveillance_physical_gate import (
    run_zero_cost_physical_gate,
)

def main():
    x = run_zero_cost_physical_gate(
        attempts=5,
        progress=lambda *a, **k: print("[LIVE]", *a),
    )

    print("[PHYSICAL]", x)

    if x.state != "ZERO_COST_SURVEILLANCE_CERTIFIED":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
