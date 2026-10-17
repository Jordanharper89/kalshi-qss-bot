import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint25_expanded_live_universe_cutover.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_uses_cp24_manifest(self):
        self.assertIn(
            "capacity_aware_warm_universe.json",
            self.s,
        )

    def test_cp11_schema(self):
        self.assertIn(
            "CHECKPOINT11_MULTI_POOL_REGISTRY_V1",
            self.s,
        )
        self.assertIn(
            '"pair_key":pair_key',
            self.s,
        )

    def test_pair_key_contract(self):
        self.assertIn(
            'pair_key=token+"|"+pool',
            self.s,
        )
        self.assertIn(
            'row.get("pair_key")!=expected',
            self.s,
        )

    def test_actual_state_owner(self):
        self.assertIn(
            "multi_dlmm_pair_registry.json",
            self.s,
        )

    def test_native_execution_chain(self):
        self.assertIn(
            "return c22.main()",
            self.s,
        )

    def test_restores_original_registry(self):
        self.assertIn(
            "[CHECKPOINT25_REGISTRY_RESTORED]",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
