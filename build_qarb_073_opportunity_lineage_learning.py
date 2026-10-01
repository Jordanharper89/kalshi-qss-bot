from pathlib import Path
import py_compile

R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
M=S/"qarb_073_opportunity_lineage_learning.py"
T=R/"test_qarb_073_opportunity_lineage_learning.py"
X=R/"run_qarb_073_opportunity_lineage_learning.py"

M.write_text(r'''from __future__ import annotations
import hashlib,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_071_continuous_mriya_replenishment as q71
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_072_promotion_aging_retirement as q72
STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_073_opportunity_lineage.json")
JOURNAL=Path("runtime_state/qseries/qarb_clean_bot/qarb_073_outcomes.jsonl")
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
_BASE_OBSERVE=q70.observe
def _load(p,d):
 try:return json.loads(Path(p).read_text(encoding="utf-8"))
 except Exception:return d
def _hash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def observe(root,row):
 x=_BASE_OBSERVE(root,row);e={"ts":time.time(),"outcome":dict(row),"status":x.get("status"),"samples":x.get("samples"),"wins":x.get("wins"),"pnl_sol":x.get("pnl_sol"),"execution_authority":False}
 p=Path(root)/JOURNAL;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("a",encoding="utf-8") as f:f.write(json.dumps(e,sort_keys=True)+"\n")
 return x
def snapshot(root):
 root=Path(root);a=q70._load(root);r=_load(root/q71.STATE,{"tokens":{}});life=q72.run(root);rows={};coverage=set()
 for t,p in sorted(a.get("tokens",{}).items()):
  src=dict(r.get("tokens",{}).get(t,{}) or {});lf=dict(life.get("tokens",{}).get(t,{}) or {});hs=dict(p.get("horizons",{}));coverage.update(hs)
  n=int(p.get("samples",0));w=int(p.get("wins",0));learn={"win_rate":w/n if n else 0.0,"positive_horizons":sorted(k for k,v in hs.items() if float(v.get("pnl_sol",0))>0),"best_horizon":max(hs,key=lambda k:float(hs[k].get("pnl_sol",0))) if hs else None}
  z={"token":t,"source":src.get("source"),"sticky":bool(src.get("sticky",False)),"pump_pool":src.get("pump_pool"),"meteora_pool":src.get("meteora_pool"),"pool_lineage_complete":bool(src.get("pump_pool") and src.get("meteora_pool")),"status":p.get("status"),"lifecycle":lf.get("lifecycle",p.get("status")),"samples":n,"wins":w,"pnl_sol":float(p.get("pnl_sol",0)),"horizons":hs,"last_profitable_unix":p.get("last_profitable_unix"),"learning":learn}
  z["lineage_hash"]=_hash(z);rows[t]=z
 core={"revision":"QARB_073","tokens":rows,"token_count":len(rows),"active_count":sum(x.get("status")=="ACTIVE" for x in rows.values()),"horizon_coverage":sorted(coverage,key=float),"outcome_journal_exists":(root/JOURNAL).is_file(),"execution_authority":False};core["content_hash"]=_hash(core)
 out=dict(core,created_unix=time.time());p=root/STATE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
def install():
 runtime=q70.install();q70.observe=observe;return runtime
def main(argv=None):
 runtime=install();print("[QARB-073] DURABLE OPPORTUNITY LINEAGE + ORACLE LEARNING");print("[CAPTURE] QARB-070 matured outcomes -> append-only lineage journal");print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
 result=runtime.main(argv);x=snapshot(Path.cwd());print("[LINEAGE] tokens=%d active=%d horizons=%s hash=%s"%(x["token_count"],x["active_count"],x["horizon_coverage"],x["content_hash"][:16]));return result
if __name__=="__main__":main()
''',encoding="utf-8")

T.write_text(r'''import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_073_opportunity_lineage_learning as q
class T(unittest.TestCase):
 def test_lineage(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);q.observe(r,{"token":"TOK","horizon_seconds":2,"paper_net_sol":.01})
   (r/q.q71.STATE).parent.mkdir(parents=True,exist_ok=True);(r/q.q71.STATE).write_text(json.dumps({"tokens":{"TOK":{"source":"ACTIVE_PROFIT","sticky":True}}}))
   x=q.snapshot(r);self.assertEqual(x["active_count"],1);self.assertIn("2",x["horizon_coverage"]);self.assertTrue((r/q.JOURNAL).is_file())
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
''',encoding="utf-8")

X.write_text("from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_073_opportunity_lineage_learning import main\nif __name__=='__main__':main()\n",encoding="utf-8")
for f in (M,T,X):py_compile.compile(str(f),doraise=True)
print("[PASS] QARB-073 durable lineage + Oracle learning installed")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")