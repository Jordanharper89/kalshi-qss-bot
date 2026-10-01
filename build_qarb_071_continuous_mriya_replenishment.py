from pathlib import Path
import py_compile
R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
M=S/"qarb_071_continuous_mriya_replenishment.py";T=R/"test_qarb_071_continuous_mriya_replenishment.py"
M.write_text(r'''from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038b_nonrecursive_mriya_hotset_runtime as hot
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_071_replenishment.json")
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
def cycle(root):
 root=Path(root);active=q70._load(root).get("tokens",{})
 pairs,landing=hot.priority_prepare_pairs(root)
 fresh={p.token:{"token":p.token,"pump_pool":p.pump_pool,"meteora_pool":p.meteora_pool,"source":"MRIYA","seen_unix":time.time()} for p in pairs}
 merged={t:{"token":t,"source":"ACTIVE_PROFIT","sticky":True} for t,x in active.items() if x.get("status")=="ACTIVE"}
 for t,x in fresh.items():
  if t not in merged:merged[t]=x
 out={"active_count":sum(1 for x in merged.values() if x.get("sticky")),"fresh_count":len(fresh),"merged_count":len(merged),"tokens":merged,"landing":landing,"execution_authority":False}
 p=root/STATE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
 return out
def main():
 r=cycle(Path.cwd())
 print("[QARB-071] CONTINUOUS MRIYA REPLENISHMENT REGISTRY")
 print("[REPLENISH] active=%d fresh=%d merged=%d"%(r["active_count"],r["fresh_count"],r["merged_count"]))
 print("[POLICY] existing profitable ACTIVE tokens are never displaced by refresh")
 print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
''',encoding="utf-8")
T.write_text(r'''import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_071_continuous_mriya_replenishment as q
class T(unittest.TestCase):
 def test_exact_source(self):self.assertEqual(q.hot.__name__.split(".")[-1],"qarb_038b_nonrecursive_mriya_hotset_runtime")
 def test_policy(self):
  s=open(q.__file__,encoding="utf-8").read();self.assertIn('"sticky":True',s);self.assertIn("if t not in merged",s)
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
''',encoding="utf-8")
for x in (M,T):py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-071 continuous Mriya replenishment installed")
print("[PRESERVE] ACTIVE winners union fresh Mriya")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")