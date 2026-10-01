import inspect, unittest
from unittest.mock import patch
from qseries_v2.oracle_execution import oracle_033_simulation_interface_compatibility_cutover as q33

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q33.EXECUTION_AUTHORITY)
        self.assertTrue(q33.PAPER_ONLY)
        self.assertFalse(q33.REAL_MONEY_MOVED)

    def test_positional_sigverify(self):
        seen={}
        def fake(*a):
            seen["args"]=a
            return {"ok":1}
        with patch.object(q33.q32.q88,"simulate_wealth",fake):
            self.assertEqual(q33.compatible_simulate_wealth(b"r",b"m","u","t"),{"ok":1})
        self.assertEqual(seen["args"],(b"r",b"m","u","t",False))

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction(",inspect.getsource(q33))

if __name__=="__main__":
    unittest.main(verbosity=2)
