import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "money_path_preflight.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(
            encoding="utf-8"
        )
        ast.parse(cls.s)

    def test_required_artifacts(self):
        self.assertIn(
            "capacity_aware_warm_universe.json",
            self.s,
        )
        self.assertIn(
            "multi_dlmm_pair_registry.json",
            self.s,
        )
        self.assertIn(
            "canonical_alt.json",
            self.s,
        )

    def test_signer_not_printed(self):
        self.assertIn(
            'os.environ.get(',
            self.s,
        )
        self.assertNotIn(
            'print(os.environ',
            self.s,
        )

    def test_money_readiness(self):
        self.assertIn(
            "[MONEY_PATH_READY]",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
