# Entry point for QSB-005 Live Solana Money Bot
from qseries_v2.solana_money_runner_v5 import SolanaMoneyEngineV5
import time

def main():
    engine = SolanaMoneyEngineV5()
    print("=" * 60)
    print("Q SERIES SOLANA LIVE MONEY RUNNER V5")
    print("=" * 60)
    
    try:
        while True:
            # Operational Status Dashboard
            status_line = "[FEED] Status: LIVE_DISCOVERY | Tokens Watched: 0 | Setups: 0 | Net P&L: $0.00 | Why No Trade: NO_REAL_DATA"
            print(f"\r{status_line}", end="", flush=True)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[STOP] Solana Money Runner stopped.")

if __name__ == "__main__":
    main()
