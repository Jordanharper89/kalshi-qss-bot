import unittest
from unittest.mock import patch

from qseries_v2.oracle_execution import (
    oracle_038_candidate_compile_isolation_compact_recovery as q38
)

class T(unittest.TestCase):

    def test_safety(self):
        self.assertFalse(q38.EXECUTION_AUTHORITY)
        self.assertTrue(q38.PAPER_ONLY)
        self.assertFalse(q38.REAL_MONEY_MOVED)

    def test_bool_compile_return_isolated(self):
        candidate={"name":"FULL","instructions":[]}
        with patch.object(q38.q87,"compile_candidate",return_value=False):
            row=q38.compile_isolated("u",candidate,[[]],"b")
        self.assertFalse(row["ok"])
        self.assertIn("COMPILE_RETURN_NOT_MAPPING",row["error"])

    def test_candidate_exception_does_not_escape(self):
        candidate={"name":"FULL","instructions":[]}
        with patch.object(
            q38.q87,
            "compile_candidate",
            side_effect=TypeError("bool object is not a mapping"),
        ):
            with patch.object(
                q38.q87.c,
                "compile_v0",
                side_effect=RuntimeError("ATOMIC_TX_TOO_LARGE:1300"),
            ):
                row=q38.compile_isolated("u",candidate,[[]],"b")
        self.assertFalse(row["ok"])
        self.assertIn("TypeError",row["error"])

    def test_compact_fallback_can_compile(self):
        candidate={
            "name":"PUMP_OPTIONAL_TRIM_NO_COMPUTE_MEMO",
            "instructions":[],
        }
        with patch.object(
            q38.q87,
            "compile_candidate",
            side_effect=TypeError("bad mapping"),
        ):
            with patch.object(
                q38.q87.c,
                "compile_v0",
                return_value=(b"MSG",b"x"*1229),
            ):
                row=q38.compile_isolated("u",candidate,[[]],"b")
        self.assertTrue(row["ok"])
        self.assertEqual(row["bytes"],1229)

    def test_install_rebinds_oracle033_attack(self):
        q38.install()
        self.assertIs(q38.q33.attack,q38.isolated_attack)

if __name__=="__main__":
    unittest.main(verbosity=2)
