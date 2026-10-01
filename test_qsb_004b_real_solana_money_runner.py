import os
import tempfile
import time
import unittest
from pathlib import Path

from qseries_v2.solana_real_money_runner import RealSolanaMoneyRunner

class FakeLiveFeed:
    def __init__(self):
        self.i = 0
        self.prices = [1.00,1.16,1.32,1.43,1.18,1.00,1.01,1.02,1.10,1.18,1.40]
    def __call__(self, max_tokens, timeout):
        i = min(self.i, len(self.prices)-1)
        px = self.prices[i]
        self.i += 1
        return {
            "discovered_tokens": 1,
            "errors": [],
            "rows": [{
                "market_address":"REAL-POOL-X",
                "token_mint":"REAL-TOKEN-X",
                "family":"PUMPSWAP",
                "last_price":px,
                "observed_unix":time.time(),
                "liquidity_usd":100000,
                "volume_usd":250000 + i*10000,
                "buy_count":50+i*2,
                "sell_count":20,
                "price_basis":"DEXSCREENER_PRICE_USD",
            }],
        }

class TestQSB004(unittest.TestCase):
    def test_real_feed_to_closed_net_pnl(self):
        old = {k: os.environ.get(k) for k in ("QSB_MIN_SCORE","QSB_TAKE_PROFIT","QSB_ROUNDTRIP_FRICTION")}
        os.environ["QSB_MIN_SCORE"] = "0.40"
        os.environ["QSB_TAKE_PROFIT"] = "0.10"
        os.environ["QSB_ROUNDTRIP_FRICTION"] = "0.03"
        try:
            with tempfile.TemporaryDirectory() as td:
                runner = RealSolanaMoneyRunner(Path(td), snapshot_provider=FakeLiveFeed())
                last = None
                for _ in range(11):
                    last = runner.cycle()
                m = last["money"]
                self.assertGreaterEqual(m["closed_trades"], 1)
                self.assertGreater(m["net_pnl_usdc"], 0)
                self.assertGreaterEqual(m["wins"], 1)
                self.assertFalse(last["real_money_moved"])
                ledger = Path(td)/"runtime_state/qseries/solana_real_money_runner/ledger.json"
                self.assertTrue(ledger.exists())
                print(
                    "[MONEY TEST] closed=%s wins=%s gross=$%.4f friction=$%.4f NET=$%.4f"
                    % (
                        m["closed_trades"], m["wins"], m["gross_pnl_usdc"],
                        m["modeled_friction_usdc"], m["net_pnl_usdc"]
                    )
                )
                print("[PASS] QSB-004 live-feed contract -> paper entry -> paper exit -> net P&L ledger")
        finally:
            for k,v in old.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k]=v

if __name__ == "__main__":
    unittest.main()
