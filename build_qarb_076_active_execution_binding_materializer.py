from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money"
P=S/"qarb_execution_engineering"
P.mkdir(parents=True,exist_ok=True)
(P/"__init__.py").touch()

M=P/"qarb_076_active_execution_binding_materializer.py"
T=R/"test_qarb_076_active_execution_binding_materializer.py"

M.write_text(r'''from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_073_opportunity_lineage_learning as q73
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038b_nonrecursive_mriya_hotset_runtime as hot
STATE=Path("runtime_state/qseries/qarb_execution_engineering/qarb_076_active_execution_bindings.json")
EXECUTION_AUTHORITY=False;REAL_MONEY_MOVED=False
def _sizes(root):
    p=Path(root)/q73.JOURNAL;s={}
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:r=json.loads(line).get("outcome",{});t=str(r["token"]);z=float(r["size_sol"]);v=float(r["paper_net_sol"])
            except Exception:continue
            if v>0:s[(t,z)]=s.get((t,z),0.0)+v
    out={}
    for (t,z),v in s.items():
        if t not in out or v>out[t][1]:out[t]=(z,v)
    return {t:z for t,(z,_) in out.items()}
def materialize(root):
    root=Path(root);a=q70._load(root);pairs,_=hot.priority_prepare_pairs(root);pm={p.token:p for p in pairs};sz=_sizes(root);rows={}
    for t,x in a.get("tokens",{}).items():
        if x.get("status")!="ACTIVE":continue
        p=pm.get(t);rows[t]={"token":t,"bound":p is not None,"pump_pool":getattr(p,"pump_pool",None),"meteora_pool":getattr(p,"meteora_pool",None),"size_sol":float(sz.get(t,.05)),"samples":x.get("samples",0),"wins":x.get("wins",0),"pnl_sol":x.get("pnl_sol",0)}
    out={"revision":"QARB_076","bindings":rows,"active":len(rows),"bound":sum(x["bound"] for x in rows.values()),"execution_authority":False,"real_money_moved":False}
    p=root/STATE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
def main():
    x=materialize(Path.cwd());print("[QARB-076] ACTIVE EXECUTION BINDING MATERIALIZER");print("[BINDINGS] active=%d bound=%d"%(x["active"],x["bound"]));print("[MODE] simulation_only execution_authority=FALSE real_money_moved=FALSE")
if __name__=="__main__":main()
''',encoding="utf-8")

T.write_text(r'''import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_076_active_execution_binding_materializer as q
class T(unittest.TestCase):
 def test_binding_and_learned_size(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/q.q73.JOURNAL;p.parent.mkdir(parents=True,exist_ok=True)
   p.write_text(json.dumps({"outcome":{"token":"TOK","size_sol":.5,"paper_net_sol":.02}})+"\n")
   olda=q.q70._load;oldh=q.hot.priority_prepare_pairs
   try:
    q.q70._load=lambda _r:{"tokens":{"TOK":{"status":"ACTIVE","samples":3,"wins":3,"pnl_sol":.04}}}
    q.hot.priority_prepare_pairs=lambda _r:([SimpleNamespace(token="TOK",pump_pool="P",meteora_pool="M")],0)
    x=q.materialize(r);self.assertEqual(x["bound"],1);self.assertEqual(x["bindings"]["TOK"]["size_sol"],.5)
   finally:q.q70._load=olda;q.hot.priority_prepare_pairs=oldh
 def test_safety(self):self.assertFalse(q.EXECUTION_AUTHORITY);self.assertFalse(q.REAL_MONEY_MOVED)
if __name__=="__main__":unittest.main(verbosity=2)
''',encoding="utf-8")

for f in (M,T):py_compile.compile(str(f),doraise=True)
print("[PASS] QARB-076 ACTIVE execution binding materializer installed")
print("[MODE] simulation_only execution_authority=FALSE real_money_moved=FALSE")