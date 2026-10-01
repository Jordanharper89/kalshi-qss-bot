from pathlib import Path
import unittest

class T(unittest.TestCase):
    def test_exactly_one_audit(self):
        hits=[]
        for p in Path("qseries_v2").rglob("*.py"):
            try:
                s=p.read_text(encoding="utf-8")
            except Exception:
                continue
            if "[SAE007B_PUMP_ACCOUNTS]" in s:
                hits.append(str(p))
        self.assertEqual(len(hits),1)

    def test_no_broadcast(self):
        p=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
        self.assertNotIn("sendTransaction",p.read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main(verbosity=2)
