from pathlib import Path
import ast
R=Path.cwd()
T=R/'qseries_v2/oracle_strategy_intelligence/solana/ssi_008_frozen_thesis_cross_episode_validation.py'
Q=R/'test_ssi_008_frozen_thesis_cross_episode_validation.py'
M='from qseries_v2.oracle_strategy_intelligence.solana.ssi_006_certified_oad312_contract_bridge import FROZEN\ndef validate_episode_metadata(episodes):\n return tuple({"token":r.get("token") or r.get("token_address"),"history_rows":r.get("history_records") or r.get("history_rows") or r.get("history_count") or 0,"frozen_thesis":FROZEN} for r in episodes)\n'
S='import unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana.ssi_008_frozen_thesis_cross_episode_validation import validate_episode_metadata\nclass T(unittest.TestCase):\n def test_freeze(self):\n  r=validate_episode_metadata(({"token":"physical-token","history_records":15},));print("[SSI-008]",r);self.assertEqual(r[0]["frozen_thesis"]["friction_bps"],200)\nif __name__=="__main__":unittest.main(verbosity=2)\n'
for x in ('qseries_v2/oracle_strategy_intelligence/solana/ssi_006_certified_oad312_contract_bridge.py',):
 p=R/x
 if not p.exists(): raise SystemExit("[FAIL] missing dependency: "+x)
 ast.parse(p.read_text(encoding="utf-8",errors="replace"))
T.parent.mkdir(parents=True,exist_ok=True)
T.write_text(M,encoding="utf-8"); Q.write_text(S,encoding="utf-8")
ast.parse(M); ast.parse(S)
print("[PASS] installed:",T.relative_to(R)); print("[PASS] test:",Q.relative_to(R))
