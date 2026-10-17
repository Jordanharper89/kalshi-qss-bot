
from __future__ import annotations
import ast
from pathlib import Path
import unittest

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=RT.read_text(encoding="utf-8")
        cls.tree=ast.parse(cls.src)

    def fn(self,name):
        rows=[
            n for n in self.tree.body
            if isinstance(
                n,
                (ast.FunctionDef,ast.AsyncFunctionDef),
            )
            and n.name==name
        ]

        self.assertEqual(len(rows),1,name)

        return ast.get_source_segment(
            self.src,
            rows[0],
        ) or ""

    def test_exact_arm(self):
        self.assertIn(
            "I_ACCEPT_0_005_SOL_CANARY",
            self.src,
        )

    def test_attempt_persisted_before_send(self):
        s=self.fn(
            "_live_005_certify_or_send"
        )

        self.assertLess(
            s.index(
                'state["send_attempted"]=True'
            ),
            s.index(
                "_live_005_send_once"
            ),
        )

    def test_no_rpc_auto_resend(self):
        s=self.fn(
            "_live_005_send_once"
        )

        self.assertIn(
            '"maxRetries":0',
            s,
        )

    def test_two_pass_gate(self):
        s=self.fn(
            "_live_005_certify_or_send"
        )

        self.assertIn(
            "LIVE_005_CERTIFICATION_RECORDED",
            s,
        )
        self.assertIn(
            "prior=",
            s,
        )

    def test_freshness_gate(self):
        s=self.fn(
            "_live_005_certify_or_send"
        )

        self.assertIn(
            "newer_waiting",
            s,
        )

    def test_actual_reconciliation(self):
        s=self.fn(
            "_live_005_certify_or_send"
        )

        self.assertIn(
            "q96.reconcile",
            s,
        )
        self.assertIn(
            "LIVE_005_REALIZED_PROFIT",
            s,
        )

    def test_hooks_both_directions(self):
        self.assertGreaterEqual(
            self.src.count(
                "_live_005_certify_or_send("
            ),
            3,
        )

    def test_signed_simulation_preserved(self):
        s=self.fn("simulate_current")

        self.assertIn(
            '"sigVerify"',
            s,
        )
        self.assertIn(
            "True",
            s,
        )

    def test_fee_path_preserved(self):
        s=self.fn("compile_current")

        self.assertIn(
            "getFeeForMessage",
            s,
        )
        self.assertIn(
            "signed_tx",
            s,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
