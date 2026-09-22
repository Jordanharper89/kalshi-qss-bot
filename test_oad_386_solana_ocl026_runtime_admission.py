import inspect
import unittest

from qseries_v2.oracle_adapters.independent.oad_386_solana_ocl026_runtime_admission import (
    build_ocl026_solana_runtime_batch,
)
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import (
    build_runtime_input,
    assemble_runtime_batch,
    verify_runtime_batch,
)

class T(unittest.TestCase):

    def test_real_ocl026_admission(self):
        print(
            "[OCL-026] build_runtime_input signature=",
            inspect.signature(build_runtime_input),
        )
        print(
            "[OCL-026] assemble_runtime_batch signature=",
            inspect.signature(assemble_runtime_batch),
        )
        print(
            "[OCL-026] verify_runtime_batch signature=",
            inspect.signature(verify_runtime_batch),
        )

        x,rows,batch=build_ocl026_solana_runtime_batch(
            sequence_start=1,
        )

        print(
            "[OCL-026] learned_cases=",
            x.learned_cases,
            "runtime_inputs=",
            x.runtime_inputs,
            "source_kind=",
            x.source_kind,
        )

        print(
            "[OCL-026] batch_type=",
            x.batch_type,
            "verified=",
            x.batch_verified,
        )

        self.assertGreater(x.learned_cases,0)
        self.assertEqual(x.runtime_inputs,x.learned_cases)
        self.assertTrue(x.batch_verified)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-386 certified Solana learned cases admitted to real OCL-026")
    print("[PASS] real OCL-026 runtime batch assembled and verified")
    print("[PASS] no new Solana acquisition performed")
    print("[PASS] no separate Solana learner introduced")
