from qseries_v2.oracle_adapters.independent.oad_311_solana_wallet_trader_continuous_coverage_runtime import (
    run_continuous_coverage,
)

if __name__ == "__main__":
    print("[BOOT] OAD-311 SOLANA WALLET/TRADER CONTINUOUS COVERAGE RUNTIME", flush=True)
    print("[BOUNDARY] read-only intelligence; execution_authority=FALSE", flush=True)
    run_continuous_coverage()
