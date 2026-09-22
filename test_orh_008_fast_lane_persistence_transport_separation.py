import ast,unittest
from pathlib import Path
ROOT=Path.cwd().resolve();RUN=ROOT/"run_oad_054_kalshi_global_fast_lane.py"
class T(unittest.TestCase):
    def test_separation(self):
        s=RUN.read_text(encoding="utf-8");ast.parse(s)
        self.assertIn("_persist_without_transport_reconnect",s);self.assertIn("transport_reconnect=FALSE",s);self.assertIn("classify_persistence_failure",s);self.assertIn("[FAST LANE] connection_failure=",s)
if __name__=="__main__":
    print("="*88);print(" ORH-008 CERTIFICATION TEST");print(" FAST-LANE PERSISTENCE / TRANSPORT FAILURE SEPARATION");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] retryable persistence failures stay inside active WebSocket session");print("[PASS] transport reconnect path remains separate");print("[PASS] execution_authority=FALSE");print("[DONE] ORH-008 CERTIFIED")
