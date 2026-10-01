import base64,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q

class T(unittest.TestCase):
    def test_exact_array_width_not_three_minimum(self):
        with open(q.__file__,encoding="utf-8") as f: src=f.read()
        self.assertIn("(crossed+69)//70",src)
        self.assertNotIn("max(3,int(quote_result.get",src)
        print("[PASS] narrow DLMM quote no longer forces 3 bin-array accounts")

    def test_compact_drops_memo_and_dedupes_compute(self):
        def ix(pid,data):
            return {"programId":pid,"accounts":[],"data":base64.b64encode(data).decode()}
        memo=next(iter(q.MEMO_PROGRAMS))
        rows=[ix(memo,b"x"),ix(q.COMPUTE_BUDGET,b"\x02aaa"),ix("SWAP",b"x"),ix(q.COMPUTE_BUDGET,b"\x02bbb")]
        out=q.compact_ixs(rows)
        self.assertEqual(sum(1 for x in out if x["programId"]==q.COMPUTE_BUDGET),1)
        self.assertEqual(sum(1 for x in out if x["programId"] in q.MEMO_PROGRAMS),0)
        self.assertTrue(any(x["programId"]=="SWAP" for x in out))
        print("[PASS] memo removed and duplicate compute-budget instructions compacted")

    def test_alt_retry_after_1414(self):
        old_compile=q.c.compile_v0; old_alts=q.recent_mriya_alt_keys
        calls=[]
        def fake_compile(user,ixs,alts,bh):
            calls.append(list(alts))
            if "MRIYA_ALT" not in alts:
                raise RuntimeError("ATOMIC_TX_TOO_LARGE:1414")
            return b"msg",b"x"*1200
        q.c.compile_v0=fake_compile; q.recent_mriya_alt_keys=lambda:["MRIYA_ALT"]
        try:
            msg,raw,alts=q.compile_compact("U",[],["PUMP_ALT"],"BH")
            self.assertEqual(len(raw),1200); self.assertIn("MRIYA_ALT",alts); self.assertEqual(len(calls),2)
        finally:
            q.c.compile_v0=old_compile; q.recent_mriya_alt_keys=old_alts
        print("[PASS] 1414-byte failure retries using recent Mriya ALTs")

    def test_no_broadcast(self):
        with open(q.__file__,encoding="utf-8") as f: src=f.read()
        self.assertNotIn("c.send(raw)",src)
        print("[PASS] QSB-059C still simulation-only")

if __name__=="__main__": unittest.main(verbosity=2)
