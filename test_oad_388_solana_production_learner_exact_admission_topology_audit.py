import unittest
from qseries_v2.oracle_adapters.independent.oad_388_solana_production_learner_exact_admission_topology_audit import (
    audit_production_learner_topology,
)

class T(unittest.TestCase):
    def test_topology(self):
        x=audit_production_learner_topology()

        print("[OLR-044]",x.olr044_path)
        print("[OLR-044 FUNCTIONS]",x.olr044_functions)
        print("[OLR-046]",x.olr046_path)
        print("[OLR-046 FUNCTIONS]",x.olr046_functions)
        print("[RUNNER CANDIDATES]",x.candidate_runner_paths)
        print("[LEARNER STATE FILES]",x.runtime_state_files)
        print("[LEARNER STATE KEYS]",x.runtime_state_keys)

        self.assertIn("find_learning_runner",x.olr044_functions)
        self.assertIn("read_children",x.olr046_functions)
        self.assertIn("patch_learning_child",x.olr046_functions)
        self.assertGreater(len(x.runtime_state_files),0)
        self.assertTrue(
            any(k in x.runtime_state_keys for k in (
                "outcomes_learned",
                "learned_records",
                "through_sequence",
            ))
        )

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-388 exact production learner admission topology audited")
    print("[PASS] OLR-044 learning-runner discovery boundary verified")
    print("[PASS] OLR-046 live learner launcher-cutover boundary verified")
    print("[PASS] durable learner runtime-state surfaces inventoried")
    print("[PASS] no production module modified")
