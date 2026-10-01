
import base64,inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q

def ix(pid,tag=1):
    return {"programId":pid,"accounts":[],"data":base64.b64encode(bytes([tag])).decode()}

class T(unittest.TestCase):
    def test_python_only_runtime_path(self):
        src=inspect.getsource(q.compose_reverse_candidates)+inspect.getsource(q.api_pump_route)
        self.assertNotIn("subprocess",src.lower())
        self.assertNotIn("native_pump_buy_ixs",src)
        self.assertNotIn("npm install",src.lower())
        print("[PASS] QSB-059E active runtime path has no Node/npm dependency")

    def test_candidate_compaction_order(self):
        rows=[
            ix(q.COMPUTE_BUDGET,2),
            ix(q.c.SYSTEM,2),
            ix(q.c.TOKEN,17),
            ix("OPTIONAL_HELPER_PROGRAM",55),
            ix(q.c.PUMP,7),
            ix(q.c.TOKEN,9),
            ix(next(iter(q.MEMO_PROGRAMS)),1),
        ]
        m=ix(q.c.DLMM,8)
        sets=dict(q.candidate_instruction_sets(rows,m))
        self.assertEqual([x["programId"] for x in sets["WRAP_SWAP_CLOSE"]],
                         [q.c.SYSTEM,q.c.TOKEN,q.c.PUMP,q.c.DLMM,q.c.TOKEN])
        self.assertEqual([x["programId"] for x in sets["PUMP_METEORA_ONLY"]],
                         [q.c.PUMP,q.c.DLMM])
        print("[PASS] deterministic full-to-minimal atomic candidate ladder")

    def test_end_to_end_candidate_fallback(self):
        old_compile,old_sim=q.c.compile_v0,q.c.simulate
        def fake_compile(user,ixs,alts,bh):
            if len(ixs)>3:
                raise RuntimeError("ATOMIC_TX_TOO_LARGE:1348")
            return b"msg",b"x"*1190
        q.c.compile_v0=fake_compile
        q.c.simulate=lambda raw,user,sigverify=False:{"err":None,"units":111111,"pnl":500000,"logs":[]}
        try:
            route={"start_lamports":50_000_000,"alts":[],"candidates":[
                ("FULL",[ix("A")]*8),
                ("WRAP_SWAP_CLOSE",[ix("A")]*3),
            ]}
            win,rows=q.attempt_candidate_simulations("U",None,route,"BH")
            self.assertIsNotNone(win)
            self.assertEqual(win["name"],"WRAP_SWAP_CLOSE")
            self.assertEqual(win["bytes"],1190)
            self.assertTrue(win["profitable"])
        finally:
            q.c.compile_v0,q.c.simulate=old_compile,old_sim
        print("[PASS] 1348-byte failure falls through to <=1232 profitable simulation candidate")

    def test_no_broadcast(self):
        with open(q.__file__,encoding="utf-8") as f:
            src=f.read()
        self.assertNotIn("c.send(raw)",src)
        print("[PASS] QSB-059E remains simulation-only")

if __name__=="__main__":
    unittest.main(verbosity=2)
