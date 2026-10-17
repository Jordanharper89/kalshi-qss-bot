import unittest
from types import SimpleNamespace
from qseries_v2.oracle_execution.solana_atomic_executor import mry_009_atomic_warm_admission as m

class T(unittest.TestCase):
    def test_register(self):
        p=SimpleNamespace(
            token="T",
            pump_base_vault="a",
            pump_quote_vault="b",
            meteora_pool="c",
            arrays=[(0,"d",b"")],
            watched_accounts=lambda:["a","b","c","d"],
        )

        s={
            "pairs":[],
            "preg":{},
            "addresses":[],
        }

        self.assertTrue(
            m._register_pair(s,p)
        )

        self.assertFalse(
            m._register_pair(s,p)
        )

        self.assertEqual(
            len(s["pairs"]),
            1,
        )

        self.assertEqual(
            len(s["addresses"]),
            4,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
