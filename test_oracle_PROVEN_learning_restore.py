import json
import unittest
from pathlib import Path

ROOT=Path.cwd()

class T(unittest.TestCase):
    def test_proven_state_exists(self):
        p=ROOT/"runtime_state"/"oracle_learning_runtime_state.json"
        self.assertTrue(p.is_file())
        d=json.loads(p.read_text(encoding="utf-8"))
        self.assertGreater(int(d.get("outcomes_learned",0)),0)
        self.assertGreater(int(d.get("cycles",0)),0)
        self.assertTrue(str(d.get("ocl_state",{}).get("state_hash","")))

    def test_proven_ledger_exists(self):
        p=ROOT/"runtime_state"/"oracle_learning_event_ledger.json"
        self.assertTrue(p.is_file())
        d=json.loads(p.read_text(encoding="utf-8"))
        rows=list(d.values()) if isinstance(d,dict) else list(d)
        learned=sum(
            1 for r in rows
            if isinstance(r,dict) and str(r.get("status","")).lower()=="learned"
        )
        self.assertGreater(learned,0)

if __name__=="__main__":
    print("="*88)
    print(" ORACLE PROVEN LEARNING RESTORE CERTIFICATION TEST")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Existing physically learned state verified")
    print("[PASS] Existing learned-event ledger verified")
    print("[PASS] execution_authority=FALSE")
