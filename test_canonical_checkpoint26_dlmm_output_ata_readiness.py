import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint26_dlmm_output_ata_readiness.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_create_idempotent(self):
        self.assertIn(
            "bytes([1])",
            self.s,
        )

    def test_exact_dlmm_destination(self):
        self.assertIn(
            'dest=str(ac[5]["pubkey"])',
            self.s,
        )

    def test_supports_both_token_programs(self):
        self.assertIn(
            "tx_prog=str(ac[11]",
            self.s,
        )
        self.assertIn(
            "ty_prog=str(ac[12]",
            self.s,
        )

    def test_ata_matches_destination(self):
        self.assertIn(
            "if dest==x_ata:",
            self.s,
        )
        self.assertIn(
            "elif dest==y_ata:",
            self.s,
        )

    def test_insert_before_dlmm(self):
        self.assertIn(
            "z.insert(",
            self.s,
        )
        self.assertIn(
            'x.get("programId")==c.DLMM',
            self.s,
        )

    def test_no_hot_rpc(self):
        helper=cls_slice(
            self.s,
            "def _ata_create_idempotent_for_dlmm",
            "def _install_candidate_patch",
        )
        self.assertNotIn(
            "c.account(",
            helper,
        )
        self.assertNotIn(
            "c.rpc(",
            helper,
        )

    def test_checkpoint25_preserved(self):
        self.assertIn(
            "return c25.main()",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


def cls_slice(s,a,b):
    return s[
        s.index(a):
        s.index(b)
    ]


if __name__=="__main__":
    unittest.main(verbosity=2)
