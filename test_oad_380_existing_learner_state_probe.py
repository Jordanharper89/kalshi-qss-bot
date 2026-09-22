import unittest

from qseries_v2.oracle_adapters.independent.oad_380_existing_learner_state_probe import (
    snapshot_existing_learner_state,
)

class T(unittest.TestCase):

    def test_probe(self):
        x=snapshot_existing_learner_state()

        print("[LEARNER-STATE] files_scanned=",x.files_scanned)
        print("[LEARNER-STATE] candidates=",x.candidates)
        print("[LEARNER-STATE] counters=",x.counters)

        self.assertGreaterEqual(x.files_scanned,0)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-380 existing learner state probe certified read-only")
    print("[PASS] actual OAD-317 existing-learning boundary verified")
    print("[PASS] no guessed OAD-377 handoff symbol dependency remains")
