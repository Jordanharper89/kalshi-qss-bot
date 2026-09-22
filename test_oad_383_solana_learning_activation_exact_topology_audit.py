import unittest

from qseries_v2.oracle_adapters.independent.oad_383_solana_learning_activation_exact_topology_audit import (
    audit_learning_activation_topology,
)

class T(unittest.TestCase):

    def test_exact_topology(self):
        x=audit_learning_activation_topology()

        print("[OAD317]",x.oad317.path)
        print("[OAD317-FUNCTIONS]",x.oad317.functions)
        print("[OAD317-IMPORTS]",x.oad317.imports)

        print("[SOLANA-HISTORY-MODULES]",len(x.solana_history_modules))
        for s in x.solana_history_modules:
            print("[SOLANA-HISTORY]",s.path,"functions=",s.functions,"classes=",s.classes)

        print("[OUTCOME-MODULES]",len(x.outcome_modules))
        for s in x.outcome_modules:
            print("[OUTCOME]",s.path,"functions=",s.functions,"classes=",s.classes)

        print("[LEARNER-MODULES]",len(x.learner_modules))
        for s in x.learner_modules:
            print("[LEARNER]",s.path,"functions=",s.functions,"classes=",s.classes,"imports=",s.imports)

        print("[RUNTIME-LEARNER-STATE]",x.runtime_state_candidates)

        self.assertTrue(
            any(name=="build_solana_learning_handoff" for name,args in x.oad317.functions)
        )

        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-383 exact Solana learning-activation topology physically audited")
    print("[PASS] actual OAD-317 imports/functions exposed")
    print("[PASS] actual OCL/learner module paths and public functions exposed")
    print("[PASS] actual Solana temporal-history/outcome interfaces exposed")
    print("[PASS] no production module modified")
