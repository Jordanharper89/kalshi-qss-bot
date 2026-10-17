import unittest
from unittest.mock import patch
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_161_two_leg_unsigned_assembly as m

def package(direction="PUMP_TO_METEORA",size=10000000):
    programs=([m.core.PUMP,m.core.DLMM] if direction=="PUMP_TO_METEORA"
              else [m.core.DLMM,m.core.PUMP])
    return {"direction":direction,"size_lamports":size,"payer":"public",
            "blockhash":"public","alt_snapshot":{m.CANONICAL:["public"]},
            "instructions":[{"programId":p,"accounts":[],"data":"AQ=="} for p in programs]}
class T(unittest.TestCase):
    def test_forward_uses_existing_compiler(self):
        with patch.object(m,"compile_unsigned",return_value={"raw":b"x","details":{"instruction_count":2,"table_ids":[m.CANONICAL]}}) as f:
            self.assertEqual(m.assemble(package())["raw"],b"x")
            f.assert_called_once()
    def test_reverse(self):
        with patch.object(m,"compile_unsigned",return_value={"raw":b"x"}) as f:
            m.assemble(package("METEORA_TO_PUMP"))
            f.assert_called_once()
    def test_incorrect_order(self):
        p=package("PUMP_TO_METEORA")
        p["instructions"].reverse()
        with self.assertRaises(m.AssemblyHold):m.assemble(p)
    def test_no_duplicate_leg(self):
        p=package()
        p["instructions"][1]["programId"]=m.core.PUMP
        with self.assertRaises(m.AssemblyHold):m.assemble(p)
    def test_size_guard(self):
        with self.assertRaises(m.AssemblyHold):m.assemble(package(size=1000000))
    def test_missing_alt(self):
        p=package();p["alt_snapshot"]={}
        with self.assertRaises(m.AssemblyHold):m.assemble(p)
    def test_no_sign_or_broadcast(self):
        import inspect
        src=inspect.getsource(m.assemble)
        self.assertNotIn("signed_tx(",src)
        self.assertNotIn("send(",src)
        self.assertNotIn("keypair(",src)

if __name__=="__main__":unittest.main(verbosity=2)
