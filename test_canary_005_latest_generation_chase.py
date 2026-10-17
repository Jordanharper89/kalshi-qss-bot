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
        cls.src=RT.read_text(
            encoding="utf-8"
        )
        cls.tree=ast.parse(
            cls.src
        )

    def fn(self,name):
        rows=[
            n for n in self.tree.body
            if isinstance(
                n,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and n.name==name
        ]

        self.assertEqual(
            len(rows),
            1,
            name,
        )

        return (
            ast.get_source_segment(
                self.src,
                rows[0],
            )
            or ""
        )

    def test_refresh_helper_exists(self):
        s=self.fn(
            "_fast_005_refresh_latest"
        )

        self.assertIn(
            "lane.latest.get",
            s,
        )

        self.assertIn(
            "lane.cv",
            s,
        )

    def test_refresh_exact_005_only(self):
        s=self.fn(
            "_fast_005_refresh_latest"
        )

        self.assertIn(
            "exact_snapshot_opportunities",
            s,
        )

        self.assertIn(
            "0.005",
            s,
        )

    def test_refresh_bounded(self):
        s=self.fn(
            "_fast_005_refresh_latest"
        )

        self.assertIn(
            "refreshes<3",
            s,
        )

        self.assertIn(
            "GENERATION_CHURN_LIMIT",
            s,
        )

    def test_negative_latest_holds(self):
        s=self.fn(
            "_fast_005_refresh_latest"
        )

        self.assertIn(
            "LATEST_NONPOSITIVE",
            s,
        )

    def test_fast_attack_uses_refresh(self):
        s=self.fn(
            "fast_live_attack"
        )

        self.assertIn(
            "_fast_005_refresh_latest(",
            s,
        )

        self.assertNotIn(
            "if lane.newer_waiting(token,generation):\n        return",
            s[:900],
        )

    def test_profit_lock_preserved(self):
        s=self.fn(
            "_fast_005_profit_lock_route"
        )

        self.assertIn(
            "PUMP_TO_METEORA",
            s,
        )

        self.assertIn(
            "METEORA_TO_PUMP",
            s,
        )

    def test_profit_floor_preserved(self):
        self.assertIn(
            "FAST_005_MIN_REALIZED_LAMPORTS=10_000",
            self.src,
        )

    def test_send_preflight_preserved(self):
        s=self.fn(
            "_live_005_send_once"
        )

        self.assertIn(
            '"skipPreflight":False',
            s,
        )

        self.assertIn(
            '"maxRetries":0',
            s,
        )

    def test_one_shot_reconciliation_preserved(self):
        s=self.fn(
            "_live_005_certify_or_send"
        )

        self.assertIn(
            'state["send_attempted"]=True',
            s,
        )

        self.assertIn(
            "q96.reconcile",
            s,
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
