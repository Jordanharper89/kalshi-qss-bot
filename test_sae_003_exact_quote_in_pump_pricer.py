from pathlib import Path
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_018_exact_sdk_hot_lane_cutover
    as q18
)

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as canonical
)


ROOT=Path.cwd()

WORKER=(
    ROOT/
    "qseries_v2"/
    "oracle_strategy_intelligence"/
    "solana_money"/
    "qsb059d_pump_native"/
    "sae003_pump_exact_quote_worker.mjs"
)


class T(unittest.TestCase):

    def test_safety(self):
        self.assertFalse(
            canonical.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            canonical.PAPER_ONLY
        )

        self.assertFalse(
            canonical.REAL_MONEY_MOVED
        )

    def test_oracle018_points_to_sae003(self):
        self.assertEqual(
            q18.WORKER_JS.name,
            "sae003_pump_exact_quote_worker.mjs"
        )

    def test_worker_exists(self):
        self.assertTrue(
            WORKER.is_file()
        )

    def test_forward_uses_quote_input(self):
        src=WORKER.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "buyQuoteInput({",
            src
        )

        self.assertIn(
            "quote,",
            src
        )

        self.assertIn(
            "slippage:0",
            src
        )

    def test_full_fee_context_present(self):
        src=WORKER.read_text(
            encoding="utf-8"
        )

        required=[
            "virtualQuoteReserves",
            "globalConfig",
            "feeConfig",
            "baseMint",
            "baseMintAccount",
            "coinCreator",
            "creator",
            "quoteMint",
            "isMayhemMode",
            "creatorFeeBps",
        ]

        for field in required:
            self.assertIn(
                field,
                src
            )

    def test_hot_buy_has_no_rpc(self):
        src=WORKER.read_text(
            encoding="utf-8"
        )

        start=src.index(
            "function buy(req)"
        )

        end=src.index(
            "function sell(req)"
        )

        buy_src=src[
            start:end
        ]

        self.assertNotIn(
            "getAccountInfo",
            buy_src
        )

        self.assertNotIn(
            "swapSolanaState",
            buy_src
        )

        self.assertNotIn(
            "connection.",
            buy_src
        )

    def test_warm_is_only_online_state_fetch(self):
        src=WORKER.read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            src.count(
                "swapSolanaState("
            ),
            1
        )

    def test_oracle018_forward_contract_preserved(self):
        src=inspect.getsource(
            q18.exact_snapshot_opportunities
        )

        self.assertIn(
            'pump_buy[\n            "baseOut"\n        ]',
            src
        )

        self.assertIn(
            '"PUMP_TO_METEORA"',
            src
        )

    def test_sae001_hot_meteora_preserved(self):
        src=inspect.getsource(
            canonical.build_meteora_ix_hot
        )

        for bad in (
            "c.rpc(",
            "c.account(",
            "dlmm_arrays(",
            "urlopen(",
        ):
            self.assertNotIn(
                bad,
                src
            )

    def test_sae002_truth_gate_preserved(self):
        src=inspect.getsource(
            canonical.attack
        )

        self.assertIn(
            "pump_6040_actual_base_out",
            src
        )

        self.assertIn(
            "reprice_from_pump_chain_truth",
            src
        )

    def test_no_broadcast(self):
        src=inspect.getsource(
            canonical
        )

        self.assertNotIn(
            "sendTransaction",
            src
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
