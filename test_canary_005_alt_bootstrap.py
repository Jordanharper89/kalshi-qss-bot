from __future__ import annotations

import inspect
import unittest
from unittest.mock import patch

from qseries_v2.oracle_execution.solana_atomic_executor import (
    bootstrap_canary_005_alts as m
)


class Pair:
    def __init__(self,token,pump="PUMP"):
        self.token=token
        self.pump_pool=pump


class T(unittest.TestCase):
    def test_scope(self):
        self.assertFalse(m.EXECUTION_AUTHORITY)
        self.assertFalse(m.TRADE_BROADCAST)

    def test_cached_route_has_no_dlmm_discovery(self):
        src=inspect.getsource(
            m._cached_full_route
        )
        self.assertNotIn(
            "native_live_route",
            src,
        )
        self.assertNotIn(
            "dlmm_arrays",
            src,
        )
        self.assertNotIn(
            "getProgramAccounts",
            src,
        )

    def test_retry_rpc_is_bounded(self):
        src=inspect.getsource(
            m._retry_rpc
        )
        self.assertIn(
            "attempts=5",
            src,
        )
        self.assertIn(
            "CANARY_ALT_RPC_429",
            src,
        )
        self.assertIn(
            "8.0",
            src,
        )

    def test_send_transaction_is_not_retried(self):
        src=inspect.getsource(
            m._retry_rpc
        )
        self.assertIn(
            'method)=="sendTransaction"',
            src,
        )
        boot=inspect.getsource(
            m.bootstrap_one
        )
        self.assertIn(
            "signature=q96.send_once(raw)",
            boot,
        )
        self.assertNotIn(
            "_call_with_retry_rpc(\n        q96.send_once",
            boot,
        )

    def test_simulation_uses_retry_wrapper(self):
        src=inspect.getsource(
            m.bootstrap_one
        )
        self.assertIn(
            "_call_with_retry_rpc",
            src,
        )
        self.assertIn(
            "q96.signed_simulation",
            src,
        )

    def test_cached_addresses_use_prebuilt_templates(self):
        src=inspect.getsource(
            m._cached_full_route
        )
        self.assertIn(
            "rt.TEMPLATES",
            src,
        )
        self.assertIn(
            "rt.METEORA_TEMPLATES",
            src,
        )

    def test_dynamic_pair_selection(self):
        m.rt.READY_TOKENS.clear()
        m.rt.READY_TOKENS.update(
            {"B","A"}
        )

        state={
            "pairs":[
                Pair("B"),
                Pair("A"),
            ]
        }

        with patch.object(
            m,
            "_local_saved_tokens",
            return_value=set(),
        ):
            pair=m._select_current_pair(
                ".",
                state,
                None,
            )

        self.assertEqual(
            pair.token,
            "A",
        )

    def test_saved_pair_deprioritized(self):
        m.rt.READY_TOKENS.clear()
        m.rt.READY_TOKENS.update(
            {"A","B"}
        )

        state={
            "pairs":[
                Pair("A"),
                Pair("B"),
            ]
        }

        with patch.object(
            m,
            "_local_saved_tokens",
            return_value={"A"},
        ):
            pair=m._select_current_pair(
                ".",
                state,
                None,
            )

        self.assertEqual(
            pair.token,
            "B",
        )

    def test_no_trade_send_path(self):
        src=inspect.getsource(m)
        self.assertNotIn(
            "q87.c.send(",
            src,
        )
        self.assertIn(
            "trade_broadcast=FALSE",
            src,
        )

    def test_no_private_key_output(self):
        src=inspect.getsource(m)
        self.assertNotIn(
            "QSB_SOLANA_PRIVATE_KEY=",
            src,
        )
        self.assertNotIn(
            "str(kp)",
            src,
        )

    def test_runtime_not_rewritten(self):
        src=inspect.getsource(m)
        self.assertNotIn(
            "runtime.py",
            src,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
