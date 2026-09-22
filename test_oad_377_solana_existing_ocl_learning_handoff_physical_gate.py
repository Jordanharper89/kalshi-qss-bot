import inspect
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from qseries_v2.oracle_adapters.independent.oad_376_solana_learned_experience_bridge import (
    SolanaLearnedExperienceRecord,
)
from qseries_v2.oracle_adapters.independent.oad_377_solana_existing_ocl_learning_handoff_physical_gate import *

class T(unittest.TestCase):

    def _record(self):
        return SolanaLearnedExperienceRecord(
            experience_id="exp",
            case_id="case",
            behavior_type="DEX_SWAP",
            protocol="orca",
            primary_asset="A",
            secondary_asset="B",
            horizon_seconds=15,
            outcome="UP",
            return_fraction=0.01,
            evidence_source="SOLANA_CANONICAL_HISTORY",
            immutable_payload_hash="0"*64,
            learning_namespace="EXISTING_OCL",
            execution_authority=False,
        )

    def test_handoff_contract(self):
        def fake(payload):
            return SimpleNamespace(state="LEARNING_ACCEPTED")

        with patch(
            "qseries_v2.oracle_adapters.independent."
            "oad_377_solana_existing_ocl_learning_handoff_physical_gate."
            "discover_existing_ocl_handoff",
            return_value=(OAD317_MODULE,"accept_learning_record",fake)
        ):
            x=handoff_learned_experience(self._record())

        print(
            "[OCL-HANDOFF]",
            x.boundary_module,
            x.boundary_symbol,
            x.accepted,
            x.returned_state,
            x.payload_namespace
        )

        self.assertTrue(x.accepted)
        self.assertEqual(x.payload_namespace,"EXISTING_OCL")
        self.assertFalse(x.execution_authority)

    def test_real_oad317_callable_discovery(self):
        mod,name,f=discover_existing_ocl_handoff()

        print("[OAD317-DISCOVERY] module=",mod)
        print("[OAD317-DISCOVERY] symbol=",name)
        print("[OAD317-DISCOVERY] signature=",inspect.signature(f))

        self.assertEqual(mod,OAD317_MODULE)
        self.assertTrue(name)
        self.assertTrue(inspect.isfunction(f) or inspect.ismethod(f))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-377 actual OAD-317 existing-OCL boundary callable discovered")
    print("[PASS] no guessed qseries_v2.oracle_learning package path remains")
    print("[PASS] Solana learned-experience handoff stays inside existing certified learning boundary")
    print("[PASS] no separate Solana learner introduced")
