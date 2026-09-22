from pathlib import Path
import ast
R=Path.cwd()
T=R/'qseries_v2/oracle_strategy_intelligence/solana/ssi_009_independent_episode_identity_gate.py'
Q=R/'test_ssi_009_independent_episode_identity_gate.py'
M='def independence(rows):\n tokens=tuple(r["token"] for r in rows if r.get("token")); unique=tuple(dict.fromkeys(tokens))\n return {"episodes":len(rows),"identified_tokens":len(tokens),"unique_tokens":unique,"independent_tokens":len(unique),"duplicates":len(tokens)-len(unique)}\n'
S='import unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana.ssi_009_independent_episode_identity_gate import independence\nclass T(unittest.TestCase):\n def test_identity(self):\n  r=independence(({"token":"a"},{"token":"b"},{"token":"a"}));print("[SSI-009]",r);self.assertEqual(r["independent_tokens"],2);self.assertEqual(r["duplicates"],1)\nif __name__=="__main__":unittest.main(verbosity=2)\n'
for x in ():
 p=R/x
 if not p.exists(): raise SystemExit("[FAIL] missing dependency: "+x)
 ast.parse(p.read_text(encoding="utf-8",errors="replace"))
T.parent.mkdir(parents=True,exist_ok=True)
T.write_text(M,encoding="utf-8"); Q.write_text(S,encoding="utf-8")
ast.parse(M); ast.parse(S)
print("[PASS] installed:",T.relative_to(R)); print("[PASS] test:",Q.relative_to(R))
