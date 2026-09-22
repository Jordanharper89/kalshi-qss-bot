from pathlib import Path
import ast
R=Path.cwd()
T=R/'qseries_v2/oracle_strategy_intelligence/solana/ssi_011_physical_multi_token_cohort.py'
Q=R/'test_ssi_011_physical_multi_token_cohort.py'
M='from qseries_v2.oracle_strategy_intelligence.solana.ssi_006_certified_oad312_contract_bridge import activate,FROZEN\ndef acquire_cohort(root=None,episodes=5,cycles=15):\n out=[]\n for i in range(episodes):\n  r=activate(root=root,cycles=cycles)\n  d={"episode":i+1,"token":r.token_address,"history_records":r.history_records,"successful_cycles":r.successful_cycles,\n     "temporal_state":r.temporal_state,"ready_windows":tuple(r.ready_windows),"execution_authority":r.execution_authority}\n  print("[SSI-011-EPISODE]",d);out.append(d)\n unique=tuple(dict.fromkeys(x["token"] for x in out))\n result={"episodes":tuple(out),"unique_tokens":unique,"independent_tokens":len(unique),"frozen_thesis":FROZEN,\n         "read_only":True,"execution_authority":False}\n print("[SSI-011]",result);return result\n'
S='import unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana.ssi_011_physical_multi_token_cohort import acquire_cohort\nclass T(unittest.TestCase):\n def test_physical_cohort(self):\n  r=acquire_cohort(episodes=5,cycles=15)\n  self.assertEqual(len(r["episodes"]),5);self.assertGreaterEqual(r["independent_tokens"],3)\n  self.assertTrue(all(x["temporal_state"]=="TEMPORAL_5_15_30_60_READY" for x in r["episodes"]))\n  self.assertFalse(r["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n'
for x in ('qseries_v2/oracle_strategy_intelligence/solana/ssi_006_certified_oad312_contract_bridge.py',):
 p=R/x
 if not p.exists(): raise SystemExit("[FAIL] missing dependency: "+x)
 ast.parse(p.read_text(encoding="utf-8",errors="replace"))
T.parent.mkdir(parents=True,exist_ok=True)
T.write_text(M,encoding="utf-8")
Q.write_text(S,encoding="utf-8")
ast.parse(M);ast.parse(S)
print("[PASS] installed:",T.relative_to(R))
print("[PASS] test:",Q.relative_to(R))
