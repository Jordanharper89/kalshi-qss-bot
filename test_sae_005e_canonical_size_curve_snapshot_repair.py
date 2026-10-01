import ast
import inspect
import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as q
)


EXPECTED=(
    0.001,
    0.010,
    0.025,
    0.050,
    0.100,
    0.180,
    0.280,
    0.500,
    1.000,
    1.400,
)


class T(unittest.TestCase):

    def test_safety(self):
        self.assertFalse(q.EXECUTION_AUTHORITY)
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.REAL_MONEY_MOVED)

    def test_signature(self):
        sig=inspect.signature(q.exact_best)

        self.assertEqual(
            list(sig.parameters)[:4],
            [
                "lane",
                "token",
                "snap",
                "generation",
            ]
        )

    def test_full_curve(self):
        src=inspect.getsource(q.exact_best)

        for size in EXPECTED:
            self.assertIn(
                f"{size:.3f}",
                src
            )

    def test_pricer_receives_snapshot_not_lane(self):
        src=inspect.getsource(q.exact_best)
        tree=ast.parse(src)

        calls=[
            n
            for n in ast.walk(tree)
            if (
                isinstance(n,ast.Call)
                and isinstance(n.func,ast.Attribute)
                and n.func.attr=="exact_snapshot_opportunities"
            )
        ]

        self.assertEqual(
            len(calls),
            1
        )

        call=calls[0]

        self.assertGreaterEqual(
            len(call.args),
            2
        )

        self.assertIsInstance(
            call.args[0],
            ast.Name
        )

        self.assertEqual(
            call.args[0].id,
            "snap"
        )

    def test_maximum_net_lamports(self):
        src=inspect.getsource(q.exact_best)
        tree=ast.parse(src)

        max_calls=[
            n
            for n in ast.walk(tree)
            if (
                isinstance(n,ast.Call)
                and isinstance(n.func,ast.Name)
                and n.func.id=="max"
            )
        ]

        self.assertEqual(
            len(max_calls),
            1
        )

        call=max_calls[0]

        key=[
            kw.value
            for kw in call.keywords
            if kw.arg=="key"
        ]

        self.assertEqual(
            len(key),
            1
        )

        self.assertIsInstance(
            key[0],
            ast.Lambda
        )

        key_src=ast.unparse(
            key[0]
        )

        self.assertIn(
            "local_net",
            key_src
        )

    def test_canonical_price_uses_exact_best(self):
        src=inspect.getsource(
            q.canonical_price
        )

        self.assertIn(
            "exact_best(",
            src
        )

    def test_sae001_preserved(self):
        src=inspect.getsource(
            q.build_meteora_ix_hot
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

    def test_sae002_preserved(self):
        src=inspect.getsource(q.attack)

        self.assertIn(
            "pump_6040_actual_base_out",
            src
        )

        self.assertIn(
            "reprice_from_pump_chain_truth",
            src
        )

    def test_sae003_preserved(self):
        self.assertEqual(
            q.q18.WORKER_JS.name,
            "sae003_pump_exact_quote_worker.mjs"
        )

    def test_sae004_preserved(self):
        self.assertEqual(
            q.q87.PUMP_FIXED_ACCOUNTS,
            24
        )

    def test_no_broadcast(self):
        src=inspect.getsource(q)

        self.assertNotIn(
            "sendTransaction",
            src
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
