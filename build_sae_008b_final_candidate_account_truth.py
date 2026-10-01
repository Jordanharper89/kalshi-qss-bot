from pathlib import Path
import ast

ROOT=Path.cwd()

Q87=(
    ROOT/"qseries_v2"/"oracle_strategy_intelligence"/
    "solana_money"/"qarb_execution_engineering"/
    "qarb_087_two_second_compaction_liquidity_repair.py"
)

TEST=ROOT/"test_sae_008b_final_candidate_account_truth.py"

src=Q87.read_text(encoding="utf-8")

needle='''        out.append({
            "name":name,
            "instructions":ixs,
            "pump_optional_removed":
                int(removed),
        })'''

if needle not in src:
    raise RuntimeError(
        "SAE008B_CANDIDATE_APPEND_SEAM_MISSING"
    )

audit='''        for _ix in ixs:
            if _ix.get("programId")!=c.PUMP:
                continue
            _aa=list(_ix.get("accounts") or [])
            print(
                "[SAE008B_CANDIDATE] name=%s total=%d removed=%d"%(
                    name,len(_aa),int(removed)
                ),
                flush=True
            )
            for _i in range(max(0,len(_aa)-3),len(_aa)):
                _a=_aa[_i]
                print(
                    "[SAE008B_ACCOUNT] name=%s number=%d pubkey=%s writable=%s"%(
                        name,
                        _i+1,
                        _a.get("pubkey"),
                        _a.get("isWritable"),
                    ),
                    flush=True
                )

'''

src=src.replace(
    needle,
    audit+needle,
    1
)

ast.parse(src)

Q87.write_text(
    src,
    encoding="utf-8"
)

TEST.write_text(
'''from pathlib import Path
import unittest

class T(unittest.TestCase):

    def test_candidate_audit(self):
        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qarb_execution_engineering/"
            "qarb_087_two_second_compaction_liquidity_repair.py"
        )
        s=p.read_text(encoding="utf-8")
        self.assertIn("[SAE008B_CANDIDATE]",s)
        self.assertIn("[SAE008B_ACCOUNT]",s)

    def test_boundary_preserved(self):
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q
        self.assertEqual(q.PUMP_FIXED_ACCOUNTS,26)

if __name__=="__main__":
    unittest.main(verbosity=2)
''',
encoding="utf-8"
)

print("[PASS] SAE-008B final candidate account audit installed")
print("[TARGET] repaired_candidates()")
print("[CHECK] exact Pump accounts entering candidate")
print("[BOUNDARY] 26 preserved")
print("[TRANSACTION] unchanged")
print("[BROADCAST] disabled")