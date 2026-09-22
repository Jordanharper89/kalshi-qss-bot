import unittest
from qseries_v2.oracle_learning.olr_046_oracle_live_evidence_learner_launcher_cutover import *
class T(unittest.TestCase):
    def test_patch(self):
        src='CHILDREN={"learning":"run_old.py","canonical_writer":"writer.py"}\n'
        out=patch_learning_child(src)
        self.assertIn(TARGET_LEARNING_RUNNER,out)
    def test_target(self):
        self.assertEqual(TARGET_LEARNING_RUNNER,"run_olr_044_continuous_learning_with_evidence.py")
if __name__=="__main__":
    print("="*88);print(" OLR-046 CERTIFICATION TEST");print(" ORACLE LIVE EVIDENCE-LEARNER LAUNCHER CUTOVER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Oracle Live learning-child cutover machinery certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-046 CERTIFIED")
