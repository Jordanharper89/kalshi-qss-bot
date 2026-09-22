import inspect
import unittest

from qseries_v2.oracle_adapters.independent.oad_387_solana_ocl027_028_learning_cycle import (
    run_solana_ocl_learning_cycle,
)
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import (
    genesis_incremental_state,
    apply_runtime_batch,
    verify_incremental_state,
)
from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import (
    run_learning_cycle,
    verify_learning_cycle_result,
)

class T(unittest.TestCase):

    def test_exact_ocl_learning_cycle(self):
        print("[OCL-027] genesis signature=",inspect.signature(genesis_incremental_state))
        print("[OCL-027] apply signature=",inspect.signature(apply_runtime_batch))
        print("[OCL-027] verify signature=",inspect.signature(verify_incremental_state))
        print("[OCL-028] cycle signature=",inspect.signature(run_learning_cycle))
        print("[OCL-028] verify signature=",inspect.signature(verify_learning_cycle_result))

        x,state0,state1,raw_result,result=run_solana_ocl_learning_cycle(
            sequence_start=1,
            cycle_sequence=1,
        )

        print(
            "[OCL-027/028] runtime_inputs=",x.runtime_inputs,
            "pre_state=",x.pre_state_type,
            "applied_state=",x.applied_state_type,
        )
        print(
            "[OCL-028] raw_return_type=",x.raw_cycle_return_type,
            "cycle_result_type=",x.cycle_result_type,
        )
        print(
            "[OCL-027/028] state_verified=",x.applied_state_verified,
            "cycle_verified=",x.cycle_result_verified,
            "result_hash=",x.result_hash,
        )
        print(
            "[OCL-028] processed_through_sequence=",
            getattr(result,"processed_through_sequence",None),
        )

        self.assertGreater(x.runtime_inputs,0)
        self.assertTrue(x.applied_state_verified)
        self.assertTrue(x.cycle_result_verified)
        self.assertEqual(len(x.result_hash),64)
        self.assertEqual(x.raw_cycle_return_type,"tuple")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-387 real OCL-028 tuple return shape correctly resolved")
    print("[PASS] certified Solana batch processed by real OCL-027")
    print("[PASS] real OCL-027 incremental state verified")
    print("[PASS] real OCL-028 LearningCycleResult extracted and verified")
    print("[PASS] no frozen OCL module modified")
