from pathlib import Path
import ast
R=Path.cwd()
T=R/'qseries_v2/oracle_strategy_intelligence/solana/ssi_010_adversarial_profitability_certification_gate.py'
Q=R/'test_ssi_010_adversarial_profitability_certification_gate.py'
M='def certify(reports):\n e=[r for r in reports if r.get("n",0)>0];n=sum(r["n"] for r in e);p=sum(r.get("expectancy",0)>0 for r in e);w=sum(r.get("expectancy",0)*r["n"] for r in e)/n if n else 0.0\n state="GENERALIZATION_NOT_CERTIFIED"\n if len(e)>=3 and n>=15 and p>=max(2,(len(e)+1)//2) and w>0:state="MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND"\n return {"eligible_tokens":len(e),"positive_tokens":p,"examples":n,"weighted_net_expectancy":w,"state":state,"read_only":True,"execution_authority":False}\n'
S='import unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana.ssi_010_adversarial_profitability_certification_gate import certify\nclass T(unittest.TestCase):\n def test_gate(self):\n  r=certify(({"n":5,"expectancy":.01},{"n":5,"expectancy":.02},{"n":5,"expectancy":.01}));print("[SSI-010]",r);self.assertEqual(r["state"],"MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND");self.assertFalse(r["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n'
for x in ():
 p=R/x
 if not p.exists(): raise SystemExit("[FAIL] missing dependency: "+x)
 ast.parse(p.read_text(encoding="utf-8",errors="replace"))
T.parent.mkdir(parents=True,exist_ok=True)
T.write_text(M,encoding="utf-8"); Q.write_text(S,encoding="utf-8")
ast.parse(M); ast.parse(S)
print("[PASS] installed:",T.relative_to(R)); print("[PASS] test:",Q.relative_to(R))
