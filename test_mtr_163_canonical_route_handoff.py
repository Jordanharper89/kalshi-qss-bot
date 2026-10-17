import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_163_canonical_route_handoff as m

def ix(p):
    return {"programId":p,"accounts":[],"data":"AQ=="}

def route():
    return {"direction":"PUMP_TO_METEORA","start_lamports":10000000,
            "pump_ixs":[ix(m.core.PUMP)],"pump_index":0,
            "meteora_ix":ix(m.core.DLMM)}

class T(unittest.TestCase):
    def test_canonical_order(self):
        d,ixs=m.canonical_instructions(route())
        self.assertEqual([x["programId"] for x in ixs],[m.core.PUMP,m.core.DLMM])
    def test_wrong_program_hold(self):
        r=route();r["meteora_ix"]=ix(m.core.PUMP)
        with self.assertRaises(m.HandoffHold):m.canonical_instructions(r)
    def test_missing_route_holds(self):
        with self.assertRaises(m.HandoffHold):m.canonical_instructions({})
    def test_requires_public_alt_context(self):
        with self.assertRaises(m.HandoffHold):
            m.package(route(),"public","public",{})
    def test_integer_size_guard(self):
        r=route();r["start_lamports"]=0.01
        with self.assertRaises(m.HandoffHold):
            m.package(r,"public","public",{m.CANONICAL:[]})
    def test_no_trading_authority(self):
        import inspect
        src=inspect.getsource(m.main)
        for bad in ("signed_tx(", "keypair(", "send(", "simulate("):
            self.assertNotIn(bad,src)

if __name__=="__main__":unittest.main(verbosity=2)
