import base64
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_160_native_unsigned_compiler import (
    compile_unsigned, UnsignedCompileHold, CANONICAL
)

def key(n):
    return core.b58e(bytes([n])*32)

def sample():
    payer, blockhash = key(9), key(10)
    program, looked_up = key(11), key(12)
    instructions = [{"programId":program, "accounts":[
        {"pubkey":payer, "isSigner":True, "isWritable":True},
        {"pubkey":looked_up, "isSigner":False, "isWritable":True}],
        "data":base64.b64encode(bytes([1,2,3])).decode()}]
    return payer, instructions, blockhash, {CANONICAL:[looked_up]}

class Tests(unittest.TestCase):
    def test_real_compiler_and_unsigned_canonical(self):
        v=compile_unsigned(*sample())
        self.assertTrue(v["raw"].endswith(v["message"]))
        self.assertTrue(v["details"]["unsigned_placeholder"])
        self.assertIn(CANONICAL,v["details"]["table_ids"])
    def test_missing_canonical_holds(self):
        a,b,c,d=sample()
        with self.assertRaises(UnsignedCompileHold):
            compile_unsigned(a,b,c,{})
    def test_missing_instructions_holds(self):
        a,b,c,d=sample()
        with self.assertRaises(UnsignedCompileHold):
            compile_unsigned(a,[],c,d)
    def test_no_global_monkeypatch(self):
        before=core.alt_accounts
        compile_unsigned(*sample())
        self.assertIs(core.alt_accounts,before)
    def test_never_signs_or_authorizes(self):
        v=compile_unsigned(*sample())
        self.assertFalse(v["details"]["broadcast_authorized"])
        self.assertFalse(v["details"]["atomic_two_leg_proven"])
        self.assertFalse(v["details"]["protected_bounds_verified"])
    def test_modified_compiler_contract_holds(self):
        self.assertNotIn("signed_tx",core.compile_v0.__code__.co_names)

if __name__=="__main__":
    unittest.main(verbosity=2)
