import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import (
    checkpoint17_pair_key_execution_templates as c17
)


class FakeC:
    WSOL="WSOL"


class FakeQ87:
    c=FakeC()


class FakeR:
    q87=FakeQ87()


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=c17.r
        c17.r=FakeR()

    @classmethod
    def tearDownClass(cls):
        c17.r=cls.old

    def test_token_x_wsol_forward(self):
        x=c17._direction_semantics(
            "WSOL","TOKEN",
            "ATA_WSOL","ATA_TOKEN",
            c17.FORWARD,
        )
        self.assertEqual(x["source"],"ATA_TOKEN")
        self.assertEqual(x["dest"],"ATA_WSOL")
        self.assertFalse(x["swap_for_y"])

    def test_token_x_wsol_reverse(self):
        x=c17._direction_semantics(
            "WSOL","TOKEN",
            "ATA_WSOL","ATA_TOKEN",
            c17.REVERSE,
        )
        self.assertEqual(x["source"],"ATA_WSOL")
        self.assertEqual(x["dest"],"ATA_TOKEN")
        self.assertTrue(x["swap_for_y"])

    def test_token_y_wsol_forward(self):
        x=c17._direction_semantics(
            "TOKEN","WSOL",
            "ATA_TOKEN","ATA_WSOL",
            c17.FORWARD,
        )
        self.assertEqual(x["source"],"ATA_TOKEN")
        self.assertEqual(x["dest"],"ATA_WSOL")
        self.assertTrue(x["swap_for_y"])

    def test_token_y_wsol_reverse(self):
        x=c17._direction_semantics(
            "TOKEN","WSOL",
            "ATA_TOKEN","ATA_WSOL",
            c17.REVERSE,
        )
        self.assertEqual(x["source"],"ATA_WSOL")
        self.assertEqual(x["dest"],"ATA_TOKEN")
        self.assertFalse(x["swap_for_y"])


if __name__=="__main__":
    unittest.main(verbosity=2)
