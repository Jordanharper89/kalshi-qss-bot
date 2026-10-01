import inspect
import unittest

from qseries_v2.solana_live_execution import (
    qarb_096_sequential_live_micro_executor as q
)


class T(unittest.TestCase):

    def test_execution_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "Q_SERIES"
        )


    def test_oracle_nonexecuting(self):
        self.assertFalse(
            q.ORACLE_EXECUTION_AUTHORITY
        )


    def test_exact_micro_sol(self):
        self.assertEqual(
            q.MICRO_SOL,
            0.001
        )


    def test_exact_micro_lamports(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_runtime_cap(self):
        self.assertEqual(
            q.MAX_RUNTIME_SECONDS,
            120
        )


    def test_one_in_flight(self):
        self.assertEqual(
            q.MAX_IN_FLIGHT,
            1
        )


    def test_native_route_exists(self):
        self.assertTrue(
            callable(
                q.native_live_route
            )
        )


    def test_native_pump_sdk_used(self):
        s=inspect.getsource(
            q.native_live_route
        )

        self.assertIn(
            "native_pump_buy_ixs",
            s
        )


    def test_exact_meteora_after_native_pump(self):
        s=inspect.getsource(
            q.native_live_route
        )

        pump=s.index(
            "native_pump_buy_ixs"
        )

        meteora=s.index(
            "exact_quote"
        )

        self.assertLess(
            pump,
            meteora
        )


    def test_native_profit_uses_exact_start(self):
        s=inspect.getsource(
            q.native_live_route
        )

        self.assertIn(
            "net=end-start",
            s
        )


    def test_native_quote_source(self):
        s=inspect.getsource(
            q.native_live_route
        )

        self.assertIn(
            "PUMP_NATIVE_SDK_LIVE_STATE",
            s
        )


    def test_fresh_candidates_no_q92(self):
        s=inspect.getsource(
            q.fresh_candidates
        )

        self.assertNotIn(
            "q92.revalidate_route",
            s
        )

        self.assertIn(
            "native_live_route",
            s
        )


    def test_final_prepare_no_q92(self):
        s=inspect.getsource(
            q.final_prepare
        )

        self.assertNotIn(
            "q92.revalidate_route",
            s
        )

        self.assertIn(
            "native_live_route",
            s
        )


    def test_final_prepare_second_native_refresh(self):
        s=inspect.getsource(
            q.final_prepare
        )

        self.assertIn(
            "native_live_route",
            s
        )


    def test_old_q95_candidate_not_forced(self):
        s=inspect.getsource(
            q.final_prepare
        )

        self.assertIn(
            "route,\n        None",
            s
        )


    def test_native_live_candidates_preserve_accounts(self):
        s=inspect.getsource(
            q.native_live_route
        )

        self.assertIn(
            '"pump_optional_removed":\n                0',
            s
        )


    def test_shell_forbidden(self):
        s=inspect.getsource(
            q.native_live_route
        )

        self.assertIn(
            "PUMP_METEORA_ONLY",
            s
        )


    def test_compile_uses_live_candidates(self):
        s=inspect.getsource(
            q.compile_signed
        )

        self.assertIn(
            'route.get("live_candidates")',
            s
        )


    def test_signed_sim_value_wrapper(self):
        s=inspect.getsource(
            q.signed_simulation
        )

        self.assertIn(
            'result.get("value")',
            s
        )

        self.assertIn(
            'value.get("err")',
            s
        )


    def test_sigverify_true(self):
        s=inspect.getsource(
            q.signed_simulation
        )

        self.assertIn(
            '"sigVerify":True',
            s
        )


    def test_no_manual_prompt(self):
        s=inspect.getsource(
            q.run
        )

        self.assertNotIn(
            "input(",
            s
        )

        self.assertIn(
            "[AUTO_BROADCAST]",
            s
        )


    def test_preflight_enabled(self):
        s=inspect.getsource(
            q.send_once
        )

        self.assertIn(
            '"skipPreflight":False',
            s
        )


    def test_no_automatic_rpc_resend(self):
        s=inspect.getsource(
            q.send_once
        )

        self.assertIn(
            '"maxRetries":0',
            s
        )


    def test_fee_not_double_counted(self):
        s=inspect.getsource(
            q.reconcile
        )

        self.assertIn(
            "wallet_delta+fee",
            s
        )

        self.assertNotIn(
            "wallet_delta-fee",
            s
        )


    def test_residue_gate(self):
        s=inspect.getsource(
            q.reconcile
        )

        self.assertIn(
            "token_delta==0",
            s
        )

        self.assertIn(
            "wsol_delta==0",
            s
        )




    def test_native_route_rejections_visible(self):
        s=inspect.getsource(
            q.fresh_candidates
        )

        self.assertIn(
            "[NATIVE_REJECT]",
            s
        )

        self.assertIn(
            "type(exc).__name__",
            s
        )


    def test_q59_windows_npm_cmd_resolution(self):
        s=inspect.getsource(
            q.q87.las.q59.native_pump_buy_ixs
        )

        self.assertIn(
            'shutil.which("npm.cmd")',
            s
        )

        self.assertIn(
            'os.name=="nt"',
            s
        )

        self.assertIn(
            "npm_exe",
            s
        )


    def test_q59_resolved_node_executable(self):
        s=inspect.getsource(
            q.q87.las.q59.native_pump_buy_ixs
        )

        self.assertIn(
            'shutil.which("node")',
            s
        )

        self.assertIn(
            "node_exe",
            s
        )




    def test_native_builder_uses_120_buy_quote_input(self):
        from pathlib import Path

        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "build_buy_ix.mjs"
        )

        s=p.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "PUMP_AMM_SDK",
            s
        )

        self.assertIn(
            "buyQuoteInput",
            s
        )

        self.assertIn(
            "PUMP_AMM_SDK.buyQuoteInput",
            s
        )


    def test_native_builder_no_broken_autocomplete(self):
        from pathlib import Path

        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "build_buy_ix.mjs"
        )

        s=p.read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "swapAutocompleteBaseFromQuote",
            s
        )

        self.assertNotIn(
            "new PumpAmmSdk",
            s
        )


    def test_native_builder_same_state_pricing_and_ix(self):
        from pathlib import Path

        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "build_buy_ix.mjs"
        )

        s=p.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "online.swapSolanaState",
            s
        )

        self.assertIn(
            "state.poolBaseAmount",
            s
        )

        self.assertIn(
            "state.poolQuoteAmount",
            s
        )

        self.assertIn(
            "state.feeConfig",
            s
        )

        self.assertIn(
            "state.globalConfig",
            s
        )


    def test_native_builder_exact_quote_input_preserved(self):
        from pathlib import Path

        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "build_buy_ix.mjs"
        )

        s=p.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "quoteLamports",
            s
        )

        self.assertIn(
            "pricingAuthority",
            s
        )




    def test_micro_alt_bootstrap_exists(self):
        self.assertTrue(
            callable(
                q.bootstrap_micro_alt
            )
        )


    def test_alt_exact_eight_address_cap(self):
        s=inspect.getsource(
            q._alt_addresses_from_route
        )

        self.assertIn(
            "out=out[:8]",
            s
        )


    def test_alt_does_not_strip_helpers(self):
        s=inspect.getsource(
            q.bootstrap_micro_alt
        )

        self.assertNotIn(
            "trim_optional_pump_accounts",
            s
        )

        self.assertNotIn(
            "PUMP_METEORA_ONLY",
            s
        )


    def test_alt_only_on_oversize(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "_oversize_only(final)",
            s
        )

        self.assertIn(
            "[ALT_COMPACTION]",
            s
        )


    def test_alt_requires_existing_session_arm(self):
        s=inspect.getsource(
            q.bootstrap_micro_alt
        )

        self.assertIn(
            "require_arm()",
            s
        )


    def test_alt_confirmation_unknown_hard_stop(self):
        s=inspect.getsource(
            q.bootstrap_micro_alt
        )

        self.assertIn(
            '"ALT_CONFIRMATION_UNKNOWN"',
            s
        )

        self.assertIn(
            '"hard_stop":',
            s
        )


    def test_final_prepare_applies_saved_alt(self):
        s=inspect.getsource(
            q.final_prepare
        )

        self.assertIn(
            "_apply_saved_alt",
            s
        )


    def test_native_route_carries_token(self):
        s=inspect.getsource(
            q.native_live_route
        )

        self.assertIn(
            '"token":',
            s
        )




    def test_alt_raw_rpc_uses_get_account_info(self):
        s=inspect.getsource(
            q._saved_alt
        )

        self.assertIn(
            '"getAccountInfo"',
            s
        )

        self.assertNotIn(
            '"getAddressLookupTable"',
            s
        )


    def test_alt_activation_uses_confirmed_tx_slot(self):
        s=inspect.getsource(
            q.bootstrap_micro_alt
        )

        self.assertIn(
            'tx.get(',
            s
        )

        self.assertIn(
            '"slot"',
            s
        )

        self.assertIn(
            '"getAccountInfo"',
            s
        )


    def test_alt_activation_no_fake_raw_rpc(self):
        s=inspect.getsource(
            q.bootstrap_micro_alt
        )

        self.assertNotIn(
            '"getAddressLookupTable"',
            s
        )


    def test_complete_print_four_placeholders(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "skipped=%d",
            s
        )


    def test_alt_reuse_visible(self):
        s=inspect.getsource(
            q._apply_saved_alt
        )

        self.assertIn(
            "[ALT_REUSE]",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
