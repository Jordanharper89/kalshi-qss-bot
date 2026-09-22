from pathlib import Path
import ast
R=Path.cwd()
T=R/'qseries_v2/oracle_strategy_intelligence/solana/ssi_007_independent_token_episode_acquisition.py'
Q=R/'test_ssi_007_independent_token_episode_acquisition.py'
M='from qseries_v2.oracle_strategy_intelligence.solana.ssi_006_certified_oad312_contract_bridge import activate\ndef acquire(root=None,episodes=5,cycles=15):\n out=[]\n for i in range(episodes):\n  r=activate(root=root,cycles=cycles);print("[SSI-007-EPISODE]",i+1,r);out.append(r)\n return tuple(out)\n'
S='import unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana.ssi_007_independent_token_episode_acquisition import acquire\nclass T(unittest.TestCase):\n def test_acquisition(self):\n  r=acquire(episodes=1,cycles=15);self.assertEqual(len(r),1);print("[SSI-007]",r)\nif __name__=="__main__":unittest.main(verbosity=2)\n'
for x in ('qseries_v2/oracle_strategy_intelligence/solana/ssi_006_certified_oad312_contract_bridge.py',):
 p=R/x
 if not p.exists(): raise SystemExit("[FAIL] missing dependency: "+x)
 ast.parse(p.read_text(encoding="utf-8",errors="replace"))
T.parent.mkdir(parents=True,exist_ok=True)
T.write_text(M,encoding="utf-8"); Q.write_text(S,encoding="utf-8")
ast.parse(M); ast.parse(S)
print("[PASS] installed:",T.relative_to(R)); print("[PASS] test:",Q.relative_to(R))
